"""D48 measurement tool: does a move actually stop trembling.

Board-testing tool, hardened for D48's characterisation and confirmatory
trials (docs/backlog/D.md D48; the tool started life in D40d,
docs/history/CLOSED.md D40). The firmware's own settle metric
(servo.move.fine_approach's wait_elapsed_s) reported a fast, clean settle on
moves that raw position polling showed were still oscillating 10+ seconds
later - this tool polls output_deg/current_a continuously through the whole
move instead of trusting that event.

Two faults found reading D40d's version of this file, both fixed here:
1. Reversal counting had no way to separate real jitter from readout noise -
   both are the same 1-2 count (0.06-0.12 deg) amplitude, so an amplitude
   filter would have removed the defect itself. Fixed with a time window
   (reversals only count 5.0-15.0s after the move is issued, matching the
   pre-registered outcome definition) plus reversal-period reporting, so
   regular hunting can be told apart from irregular readout flicker.
2. A move settling more than 3 deg short of target used to report
   reversals=0, swing=0.0 - the exact shape of the original defect scoring
   as a perfect result. Fixed: settled_short is its own recorded outcome,
   computed unconditionally from the final reading.

Measures only - never writes a register or a setting.

Run example:
    python3 tools/jitter_probe.py --host 192.168.10.60 -60 --repeats 10 \\
        --label d48_baseline --tag rig_attached
"""
import argparse
import csv
import json
import math
import os
import time
import urllib.request
from typing import Optional

NEAR_TARGET_DEG = 3.0
DEFAULT_POLL_SECONDS = 0.08
WINDOW_SECONDS = 15.0

# A reversal only counts toward the primary metric if it happens in this
# range after the move is issued. Earlier reversals are the fine-approach
# overshoot-then-return itself, not sustained trembling.
SCORE_WINDOW_START_SECONDS = 5.0
SCORE_WINDOW_END_SECONDS = 15.0

# Above this the servo is meaningfully driving rather than resting. Settled
# trials read a flat 0.000A, so anything clear of the reading's own
# resolution counts.
DRIVE_THRESHOLD_A = 0.005
# Within half an encoder step counts as "on target" for the zero-error
# current reading.
ON_TARGET_DEG = 0.03

# A move that never gets this close to target is a settle-short failure,
# regardless of how quiet its final reading is.
SETTLE_SHORT_THRESHOLD_DEG = 0.5

# Consecutive invalid reads before a trial gives up. A servo oscillating
# hard enough to disturb its own bus reads as a run of these.
MAX_FAILED_READS = 20

# Renamed from RESET_STABLE_SECONDS, which was a degree threshold despite
# its name - it never measured a duration. Two readings closer than this
# count as the same position for reset-settling purposes; matches
# fine_approach_trial.py's SETTLE_POSITION_EPSILON_DEG.
RESET_POSITION_EPSILON_DEG = 0.03
# How long the position must stay within RESET_POSITION_EPSILON_DEG before
# reset_to() considers the servo settled. Time-based so it means the same
# thing at any --poll rate, unlike the old fixed poll-count.
RESET_STABLE_SECONDS_REQUIRED = 1.2
RESET_TIMEOUT_SECONDS = 12.0

ARCHIVE_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archive")


def get(base_url: str, path: str) -> dict:
    """Performs one GET request with retry, decoding the JSON reply.

    Args:
        base_url (str): API base URL.
        path (str): Endpoint path relative to base_url.

    Returns:
        dict: The decoded JSON body.
    """
    for attempt in range(3):
        try:
            with urllib.request.urlopen(f"{base_url}{path}", timeout=5) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.2)


def move(base_url: str, target_deg: float,
         acceleration: Optional[int] = None) -> dict:
    """Commands one move with retry.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.
        acceleration (Optional[int]): Ramp setting for this move, or None
            to let the backend use its configured default. Passing it per
            move avoids an EEPROM write per configuration change.

    Returns:
        dict: The decoded JSON body.
    """
    body: dict = {"target_deg": target_deg}
    if acceleration is not None:
        body["acceleration"] = acceleration
    req = urllib.request.Request(
        f"{base_url}/servo/move",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 2:
                raise
            time.sleep(0.2)


def reset_to(base_url: str, anchor_deg: float,
             poll_seconds: float = DEFAULT_POLL_SECONDS) -> None:
    """Moves to an anchor and waits for it to genuinely settle there.

    Args:
        base_url (str): API base URL.
        anchor_deg (float): Anchor angle in degrees.
        poll_seconds (float): Interval between position reads.
    """
    move(base_url, anchor_deg)
    last: Optional[float] = None
    stable_since: Optional[float] = None
    t0 = time.time()
    while time.time() - t0 < RESET_TIMEOUT_SECONDS:
        d = get(base_url, "/servo/state")["output_deg"]
        if d is None:
            # Same failed-read guard as the scored loop: a None position
            # must not reach the arithmetic below.
            time.sleep(poll_seconds)
            continue
        now = time.time()
        if last is not None and abs(d - last) < RESET_POSITION_EPSILON_DEG:
            if stable_since is None:
                stable_since = now
            elif now - stable_since >= RESET_STABLE_SECONDS_REQUIRED:
                return
        else:
            stable_since = None
        last = d
        time.sleep(poll_seconds)


def latest_fine_approach_event(base_url: str, after_iso: str) -> dict:
    """Finds the most recent fine-approach event issued after a timestamp.

    Args:
        base_url (str): API base URL.
        after_iso (str): ISO timestamp; only events at or after this count.

    Returns:
        dict: The matching event, or None if none was found yet.
    """
    events = get(base_url, "/system/events?limit=5")["events"]
    for e in events:
        if e["event"] == "servo.move.fine_approach" and e["timestamp"] >= after_iso:
            return e
    return None


def _stdev(values: list[float]) -> Optional[float]:
    """Returns the population standard deviation, or None for <2 values.

    Args:
        values (list[float]): Sample values.

    Returns:
        Optional[float]: Standard deviation, or None if not computable.
    """
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def _median(values: list[float]) -> Optional[float]:
    """Returns the median of a list, or None if it is empty.

    Args:
        values (list[float]): Sample values.

    Returns:
        Optional[float]: The median, or None on an empty list.
    """
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def score_trial(trace: list[tuple[float, float, float]],
                 target_deg: float,
                 window_start_s: float = SCORE_WINDOW_START_SECONDS,
                 window_end_s: float = SCORE_WINDOW_END_SECONDS) -> dict:
    """Scores one trial's position/current trace against D48's pre-registered outcome.

    A trial's primary outcome is FAIL if either: (a) more than the caller's
    own R_max reversals occur in the 5.0-15.0s window after the move was
    issued (this function reports the count and period; R_max itself is set
    by Step 4's noise-floor calibration, not here), or (b) the final reading
    is more than SETTLE_SHORT_THRESHOLD_DEG from target. No amplitude filter
    is applied to reversal detection - the real jitter and quantisation
    noise are the same 1-2 count size, so amplitude cannot separate them;
    reversal *period* (reported here) is the discriminator instead.

    Args:
        trace (list[tuple[float, float, float]]): (elapsed_s, output_deg,
            current_a) samples spanning the whole probe window.
        target_deg (float): Commanded target angle in degrees.
        window_start_s (float): Start of the scored window, seconds after
            the move was issued.
        window_end_s (float): End of the scored window. Scoring a late
            slice of a long trace and comparing it with an early one is how
            a self-sustaining cycle is told apart from one that decays.

    Returns:
        dict: reversals, reversal_times_s, median_period_s, period_stdev_s,
            swing_deg, final_deg, final_error_deg, settled_short,
            current_mean_a, current_peak_a, current_rms_a.
    """
    reversals = 0
    reversal_times: list[float] = []
    reversal_periods: list[float] = []
    trend: Optional[str] = None
    last_val: Optional[float] = None
    last_reversal_t: Optional[float] = None
    scored_vals: list[float] = []
    scored_currents: list[float] = []

    for elapsed, val, current_a in trace:
        in_window = window_start_s <= elapsed <= window_end_s
        if last_val is not None and val != last_val:
            new_trend = "up" if val > last_val else "down"
            if trend is not None and new_trend != trend and in_window:
                reversals += 1
                if last_reversal_t is not None:
                    reversal_periods.append(elapsed - last_reversal_t)
                reversal_times.append(elapsed)
                last_reversal_t = elapsed
            trend = new_trend
        last_val = val
        if in_window:
            scored_vals.append(val)
            scored_currents.append(current_a)

    swing = (max(scored_vals) - min(scored_vals)) if scored_vals else 0.0
    final_deg = trace[-1][1] if trace else None
    final_error_deg = (final_deg - target_deg) if final_deg is not None else None
    settled_short = (abs(final_error_deg) > SETTLE_SHORT_THRESHOLD_DEG
                      if final_error_deg is not None else None)

    current_mean = (sum(scored_currents) / len(scored_currents)
                     if scored_currents else None)
    current_peak = max(scored_currents) if scored_currents else None
    current_rms = (math.sqrt(sum(c * c for c in scored_currents) / len(scored_currents))
                    if scored_currents else None)

    # How much of the settled window the servo spends driving at all, and
    # what it draws while sitting on target. A proportional loop draws
    # nothing at zero error; a non-zero reading here is a minimum-drive
    # floor pushing regardless of how small the error is, which is what
    # turns a settled hold into a sustained bang-bang cycle.
    drive_duty = ((sum(1 for c in scored_currents if c > DRIVE_THRESHOLD_A)
                   / len(scored_currents)) if scored_currents else None)
    on_target = [c for elapsed, val, c in trace
                 if window_start_s <= elapsed <= window_end_s
                 and abs(val - target_deg) <= ON_TARGET_DEG]
    current_on_target = _median(on_target)

    return {
        "reversals": reversals,
        "drive_duty": drive_duty,
        "current_on_target_a": current_on_target,
        "reversal_times_s": reversal_times,
        "median_period_s": _median(reversal_periods),
        "period_stdev_s": _stdev(reversal_periods),
        "swing_deg": swing,
        "final_deg": final_deg,
        "final_error_deg": final_error_deg,
        "settled_short": settled_short,
        "current_mean_a": current_mean,
        "current_peak_a": current_peak,
        "current_rms_a": current_rms,
    }


def _csv_path(mode: str, label: str) -> str:
    """Builds the shared, appended CSV path for one mode and label.

    Matches fine_approach_trial.py's own convention so both tools' output
    lives in the same place, under the same naming scheme.

    Args:
        mode (str): "jitter_trial" or "jitter_trace".
        label (str): Operator-supplied campaign label.

    Returns:
        str: Path under archive/, stable across repeated invocations so
            runs with the same label accumulate into one comparable file.
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    return os.path.join(ARCHIVE_DIR, f"{mode}_{label}.csv")


def _append_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    """Appends rows to a CSV, writing the header only for a new file.

    Args:
        path (str): Destination CSV path.
        fields (list[str]): Column order.
        rows (list[dict]): Rows to append.
    """
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def probe(base_url: str, target_deg: float, label: str, tag: str,
          repeat: int, poll_seconds: float = DEFAULT_POLL_SECONDS,
          anchor_deg: float = 0.0,
          window_seconds: float = WINDOW_SECONDS,
          acceleration: Optional[int] = None) -> dict:
    """Resets to an anchor, commands one fresh move, and scores trembling near target.

    The anchor is a real parameter, not always 0: scoring only ever covers
    the move from anchor_deg to target_deg, so a fixed anchor of 0.0 can
    never produce a genuine scored arrival at 0 (a target_deg of 0.0 would
    be a 0-to-0 no-op), and it means every trial approaches its target from
    the same direction. Varying the anchor makes both a real arrival at any
    angle, including 0, and the approach-direction factor possible.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.
        label (str): Campaign label; selects the CSV files this trial appends to.
        tag (str): Condition tag (e.g. "rig_attached", "fine_approach_off").
        repeat (int): 1-based repeat number, recorded for later grouping.
        poll_seconds (float): Requested interval between position/current reads.
        anchor_deg (float): Angle to reset to before commanding the scored move.
        window_seconds (float): How long to observe after the move is issued.
            Longer than the default separates a self-sustaining limit cycle
            from residual energy that simply takes a while to die away.
        acceleration (Optional[int]): Ramp setting for the scored move, or
            None for the backend default.

    Returns:
        dict: The score_trial() result plus the matching server event and
            the achieved sampling rate.
    """
    reset_to(base_url, anchor_deg, poll_seconds=poll_seconds)
    print(f"\n--- {label} repeat {repeat} [{tag}]: {anchor_deg} -> {target_deg} deg ---")
    issued_iso = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
    t0 = time.time()
    move(base_url, target_deg, acceleration=acceleration)

    trace: list[tuple[float, float, float]] = []
    temperatures: list[float] = []
    failed_reads = 0
    while time.time() - t0 < window_seconds:
        d = get(base_url, "/servo/state")
        elapsed = time.time() - t0
        # A failed bus read reports position and current as None rather than
        # zero. Appending those straight into the trace turned "the servo
        # stopped answering" into an arithmetic TypeError further down, which
        # is a confusing way to be told the bus has stalled - so drop the
        # sample and fail loudly if it keeps happening.
        if d.get("output_deg") is None or d.get("current_a") is None:
            failed_reads += 1
            if failed_reads > MAX_FAILED_READS:
                raise RuntimeError(
                    f"servo stopped answering: {failed_reads} consecutive "
                    "invalid reads. Stop and check the servo before "
                    "commanding anything further.")
        else:
            failed_reads = 0
            trace.append((elapsed, d["output_deg"], d["current_a"]))
            if d.get("temperature_c") is not None:
                temperatures.append(d["temperature_c"])
        time.sleep(poll_seconds)

    if not trace:
        raise RuntimeError(
            "no valid readings for the whole window - the servo never "
            "answered. Stop and check it before commanding anything further.")

    achieved_hz = (len(trace) - 1) / trace[-1][0] if len(trace) > 1 else 0.0

    for elapsed, val, cur in trace:
        near = " *" if abs(val - target_deg) <= NEAR_TARGET_DEG else ""
        print(f"  {elapsed:6.2f}s  output_deg={val:8.3f}  current_a={cur:.3f}{near}")

    result = score_trial(trace, target_deg)
    print(f"  => reversals={result['reversals']}"
          f"  median_period_s={result['median_period_s']}"
          f"  settled_short={result['settled_short']}"
          f"  final={result['final_deg']}"
          f"  achieved_hz={achieved_hz:.1f}")
    print(f"  => current_mean_a={result['current_mean_a']}"
          f"  current_peak_a={result['current_peak_a']}"
          "  (0 reversals does not mean 0 current - check this too)")
    print(f"  => drive_duty={result['drive_duty']}"
          f"  current_on_target_a={result['current_on_target_a']}"
          f"  swing_deg={result['swing_deg']}")

    fa = latest_fine_approach_event(base_url, issued_iso)
    if fa:
        print(f"  server event: wait_elapsed_s={fa['data'].get('wait_elapsed_s')}"
              f"  overshoot_deg={fa['data'].get('overshoot_deg')}")
    else:
        print("  server event: none found yet (may still be settling past window)")

    trial_id = f"{label}_{tag}_{anchor_deg}to{target_deg}_{repeat}_{issued_iso}"

    trace_fields = ["trial_id", "elapsed_s", "output_deg", "current_a"]
    trace_rows = [{"trial_id": trial_id, "elapsed_s": e, "output_deg": v,
                   "current_a": c} for e, v, c in trace]
    _append_csv(_csv_path("jitter_trace", label), trace_fields, trace_rows)

    trial_fields = ["trial_id", "label", "tag", "anchor_deg", "target_deg",
                     "repeat", "reversals", "median_period_s", "period_stdev_s",
                     "swing_deg", "final_deg", "final_error_deg",
                     "settled_short", "current_mean_a", "current_peak_a",
                     "current_rms_a", "drive_duty",
                     "current_on_target_a",
                     "achieved_hz", "window_seconds",
                     "temperature_c_mean", "temperature_c_max",
                     "server_wait_elapsed_s", "timestamp"]
    trial_row = {
        "trial_id": trial_id, "label": label, "tag": tag,
        "anchor_deg": anchor_deg, "target_deg": target_deg, "repeat": repeat,
        "achieved_hz": round(achieved_hz, 2),
        "window_seconds": window_seconds,
        "temperature_c_mean": (round(sum(temperatures) / len(temperatures), 2)
                               if temperatures else None),
        "temperature_c_max": max(temperatures) if temperatures else None,
        "server_wait_elapsed_s": fa["data"].get("wait_elapsed_s") if fa else None,
        "timestamp": issued_iso,
        **{k: result[k] for k in (
            "reversals", "median_period_s", "period_stdev_s", "swing_deg",
            "final_deg", "final_error_deg", "settled_short",
            "current_mean_a", "current_peak_a", "current_rms_a",
            "drive_duty", "current_on_target_a")},
    }
    _append_csv(_csv_path("jitter_trial", label), trial_fields, [trial_row])

    return {**result, "event": fa, "achieved_hz": achieved_hz,
            "trial_id": trial_id,
            "temperature_c_mean": trial_row["temperature_c_mean"],
            "temperature_c_max": trial_row["temperature_c_max"],
            "trace": trace}


def main() -> int:
    """Parses arguments and runs repeated probes at one target."""
    parser = argparse.ArgumentParser(
        description="Measure real settling trembling via continuous "
                    "position/current polling, not the firmware's own "
                    "settle-completion event. Measures only.")
    parser.add_argument("target_deg", type=float, help="target output angle")
    parser.add_argument("--host", default="192.168.10.60")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--label", default="probe",
                        help="campaign label; selects the archive/ CSV files")
    parser.add_argument("--tag", default="rig_attached",
                        help="condition tag, e.g. rig_attached, fine_approach_off")
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--poll", type=float, default=DEFAULT_POLL_SECONDS,
                        help="requested seconds between reads; the achieved "
                             "rate is measured and reported, not assumed")
    parser.add_argument("--anchor", type=float, default=0.0,
                        help="angle to reset to before each scored move; "
                             "a target equal to the anchor is a no-op, not "
                             "a genuine arrival, so pick a different anchor "
                             "to test a target of 0 or to vary approach "
                             "direction")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}/api/v1"
    results = [probe(base_url, args.target_deg, args.label, args.tag, i,
                      poll_seconds=args.poll, anchor_deg=args.anchor)
               for i in range(1, args.repeats + 1)]

    print("\n=== summary ===")
    for i, r in enumerate(results, 1):
        wes = r["event"]["data"].get("wait_elapsed_s") if r["event"] else None
        print(f"repeat {i}: reversals={r['reversals']}"
              f"  median_period_s={r['median_period_s']}"
              f"  settled_short={r['settled_short']}"
              f"  final={r['final_deg']}"
              f"  achieved_hz={r['achieved_hz']:.1f}"
              f"  current_mean_a={r['current_mean_a']}"
              f"  current_peak_a={r['current_peak_a']}"
              f"  server_wait_elapsed_s={wes}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
