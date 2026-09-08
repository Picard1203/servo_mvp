#!/usr/bin/env python3
"""Prints one small, code-computed progress/ETA line for the D48 decisive run.

Reads archive/d48_decisive_findings.json only - never touches the servo.
Meant to be invoked periodically while tools/d48_decisive.py runs elsewhere.

Rate is measured from the actual gap between consecutive trial timestamps
recorded so far (not assumed), using the median rather than the mean so one
slow trial (a reconnect, a cooldown wait) does not distort the estimate.

The planned trial count for the phase in progress is computed from the same
functions the run itself uses (`d48_decisive.anchor_for`, its angle/N
constants), not hand-copied - so it stays correct if those change. P2's
count is inherently a range until a floor passes or every floor has been
tried, because the run stops early at the first passing floor; both ends of
that range are shown rather than picking one.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_decisive as dd


def _parse(timestamp: str) -> datetime:
    """Parses a trial timestamp, tolerating the recovered P1 rows' format.

    The live run writes bare "%Y-%m-%dT%H:%M:%S" (`time.strftime`). P1's
    8 Sept recovery pulled its rows straight from jitter_probe's CSV, whose
    own timestamps carry a "+00:00" UTC suffix - reading, not writing, the
    shared findings file here, so tolerating the mismatch is the safe fix
    rather than editing timestamps in a file the live run is still
    appending to.

    Args:
        timestamp (str): Timestamp as written by either source.

    Returns:
        datetime: The parsed timestamp (offset dropped if present).
    """
    return datetime.strptime(timestamp[:19], "%Y-%m-%dT%H:%M:%S")


def _count(findings: dict, phase: str) -> int:
    """Counts completed trials recorded so far in one phase.

    Args:
        findings (dict): Loaded findings.
        phase (str): Phase key.

    Returns:
        int: Trial count.
    """
    return sum(len(v) for v in findings.get("trials", {}).get(phase, {}).values())


def _all_timestamps(findings: dict, live_only: bool = False) -> list[datetime]:
    """Returns every trial timestamp across every phase, in order.

    Args:
        findings (dict): Loaded findings.
        live_only (bool): Skip rows recovered from a CSV after the fact
            (`reconstructed_from_csv`) - P1's 8 Sept recovery wrote UTC
            timestamps from jitter_probe's own CSV, hours apart in wall
            time from the live run's local ones, so mixing them in would
            put a multi-hour phantom gap in front of "elapsed" and the
            first real trial.

    Returns:
        list[datetime]: Sorted timestamps.
    """
    out = []
    for phase_trials in findings.get("trials", {}).values():
        for tag_trials in phase_trials.values():
            for t in tag_trials:
                if live_only and t.get("reconstructed_from_csv"):
                    continue
                if t.get("timestamp"):
                    out.append(_parse(t["timestamp"]))
    return sorted(out)


def _median(values: list[float]):
    """Returns the median of a list, or None if empty.

    Args:
        values (list[float]): Sample values.

    Returns:
        Optional[float]: The median, or None.
    """
    if not values:
        return None
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2.0


def p1_planned() -> int:
    """Total trials P1 will run, computed the way the run itself decides it.

    Returns:
        int: Planned trial count.
    """
    cells = sum(1 for a in dd.P1_ANGLES for arrival in ("up", "down")
               if dd.anchor_for(a, arrival) is not None)
    return cells * dd.P1_N


def p2_planned_range(phase: str, floors_order: tuple, angles: tuple, n: int,
                     findings: dict) -> tuple:
    """Returns (best_case, worst_case) trial counts for a P2 phase.

    Best case: the first floor tried passes and the phase stops there.
    Worst case: every floor in the order has to be tried.

    Args:
        phase (str): "p2a" or "p2b".
        floors_order (tuple): Floors in the order they are tried.
        angles (tuple): Angles tested per floor.
        n (int): Replicates per angle.
        findings (dict): Loaded findings, to count reachable cells once
            trials for a floor exist (falls back to len(angles) otherwise).

    Returns:
        tuple: (best_case_total, worst_case_total).
    """
    per_floor = len(angles) * n
    return per_floor, per_floor * len(floors_order)


def phase_rows(findings: dict) -> list[dict]:
    """Returns every phase's own done/planned counts, in run order.

    Unlike `current_phase`, this does not stop at the phase in progress -
    it reports P1, P2 and P3 each on their own row so a phase not yet
    started still shows its own planned size and duration, chained onto
    whichever phase runs before it.

    Args:
        findings (dict): Loaded findings.

    Returns:
        list[dict]: One row per phase: name, done, low, high, is_range,
            status ("done", "running", "pending").
    """
    verdicts = findings.get("verdicts", {})
    rows = []

    p1_done = _count(findings, "p1")
    planned1 = p1_planned()
    p1_status = "done" if "p1" in verdicts else (
        "running" if p1_done > 0 else "pending")
    rows.append({"name": "P1 (direction)", "done": p1_done,
                "low": planned1, "high": planned1, "is_range": False,
                "status": p1_status})

    a_low, a_high = p2_planned_range(
        "p2a", dd.P2_FLOOR_ORDER, dd.P2_ANGLES, dd.P2_N, findings)
    b_low, b_high = p2_planned_range(
        "p2b", dd.P2B_FLOORS, dd.P1_ANGLES[:5], dd.P2B_N, findings)
    branch_known = "p1" in verdicts
    if not branch_known:
        # P1 has not decided DOMINANT/PARTIAL vs NONE yet, so either branch
        # is still possible - report the envelope of both rather than
        # guessing one, which would silently understate the range if the
        # guess is wrong.
        p2_name = "P2 (branch pending)"
        p2_key = None
        low, high = min(a_low, b_low), max(a_high, b_high)
    elif verdicts["p1"].get("effect") in ("DOMINANT", "PARTIAL", "SIGN_DOMINANT"):
        p2_name, p2_key, low, high = "P2A (confirm)", "p2a", a_low, a_high
    else:
        p2_name, p2_key, low, high = "P2B (search)", "p2b", b_low, b_high
    p2_done = _count(findings, p2_key) if p2_key else 0
    p2_status = ("done" if p2_key and p2_key in verdicts else
                ("running" if p2_done > 0 else "pending"))
    rows.append({"name": p2_name, "done": p2_done, "low": low, "high": high,
                "is_range": low != high, "status": p2_status})

    p3_done = _count(findings, "p3")
    p3_planned = len(findings.get("trials", {}).get("p3", {})) * dd.P3_N
    p3_planned = max(p3_planned, p3_done, 4 * dd.P3_N if p3_done == 0 else 0)
    p3_status = "done" if "p3" in verdicts else (
        "running" if p3_done > 0 else "pending")
    rows.append({"name": "P3 (correction)", "done": p3_done,
                "low": p3_planned, "high": p3_planned, "is_range": False,
                "status": p3_status})
    return rows


def main() -> int:
    """Loads findings, computes progress and ETA, prints one small block.

    Returns:
        int: Process exit code; 1 if the findings file does not exist yet.
    """
    if not os.path.exists(dd.FINDINGS_PATH):
        print(f"[{time.strftime('%H:%M:%S')}] no findings file yet - "
              "preflight probably still running")
        return 1
    with open(dd.FINDINGS_PATH, encoding="utf-8") as handle:
        findings = json.load(handle)

    if findings.get("decision"):
        print(f"[{time.strftime('%H:%M:%S')}] RUN COMPLETE - "
              f"{findings['decision']['headline']}")
        return 0
    if findings.get("aborted"):
        print(f"[{time.strftime('%H:%M:%S')}] RUN ABORTED - "
              f"{findings['aborted']}")
        return 0

    timestamps = _all_timestamps(findings)
    total_done = len(timestamps)
    gaps = [(b - a).total_seconds()
            for a, b in zip(timestamps, timestamps[1:])]
    # Drop gaps over 3 minutes: a temperature cooldown wait or a reconnect,
    # not representative of a normal trial and would blow up the estimate.
    normal_gaps = [g for g in gaps if g <= 180]
    rate = _median(normal_gaps)

    live_timestamps = _all_timestamps(findings, live_only=True)
    started = (live_timestamps[0] if live_timestamps
              else (timestamps[0] if timestamps else datetime.now()))
    elapsed = datetime.now() - started

    def fmt_dur(seconds: float) -> str:
        return f"{int(seconds // 60)}m"

    def fmt_clock(seconds_from_now: float) -> str:
        return (datetime.now()
                + timedelta(seconds=seconds_from_now)).strftime("%H:%M")

    active = next((r for r in phase_rows(findings)
                  if r["status"] == "running"), None)
    active_name = active["name"] if active else "-"
    print(f"[{time.strftime('%H:%M:%S')}] D48 decisive run - "
          f"active: {active_name} | total so far {total_done} trials "
          f"in {fmt_dur(elapsed.total_seconds())}")

    if rate is None:
        print("  rate: not enough trials yet to estimate")
        return 0

    # Each phase's own ETA, chained onto the one before it - a phase not
    # yet started still gets a real duration and a real clock window,
    # rather than only the phase currently running being estimated.
    clock_low = clock_high = 0.0
    for row in phase_rows(findings):
        remaining_low = max(0, row["low"] - row["done"])
        remaining_high = max(0, row["high"] - row["done"])
        dur_low, dur_high = remaining_low * rate, remaining_high * rate
        start_low, start_high = clock_low, clock_high
        clock_low += dur_low
        clock_high += dur_high
        if row["status"] == "done":
            print(f"  {row['name']:<16s} done   ({row['done']} trials)")
        elif row["is_range"]:
            print(f"  {row['name']:<16s} {row['status']:<7s} "
                  f"{row['done']}/{row['low']}-{row['high']} | "
                  f"ETA {fmt_dur(dur_low)}-{fmt_dur(dur_high)} | "
                  f"clock {fmt_clock(start_low)}-{fmt_clock(clock_high)}")
        else:
            print(f"  {row['name']:<16s} {row['status']:<7s} "
                  f"{row['done']}/{row['high']} | ETA {fmt_dur(dur_high)} | "
                  f"clock {fmt_clock(start_high)}-{fmt_clock(clock_high)}")

    print(f"  rate={rate:.0f}s/trial | FULL RUN ETA: "
          f"clock {fmt_clock(clock_low)}-{fmt_clock(clock_high)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
