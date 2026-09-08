#!/usr/bin/env python3
"""Milestone reports and a live "is the hypothesis holding up" read for D48.

Read-only against archive/d48_decisive_findings.json - never calls
save_findings, never writes into that file. That file is what a resumed
run trusts to know which trials are already done; a provisional verdict
written there early, from a partial or stale read, could make a restarted
run skip trials it has not actually performed. Every verdict function this
script calls is called with `dry_run=True` (or is naturally read-only, like
`score_floor`) for exactly this reason.

One invocation is one tick. It prints nothing when there is nothing new to
say - milestones (a phase reaching a real, persisted verdict) always print;
a live interim read of the arrival-direction hypothesis from P1's partial
data prints once enough of it exists to say anything, and again each time
its live read changes state. State (which milestones have already been
reported) lives in its own small file, never the run's own findings file.

    python3 tools/d48_decisive_watch.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_decisive as dd

STATE_PATH = os.path.join(dd.jp.ARCHIVE_DIR, "d48_decisive_watch_state.json")

# Below this many trials per arm, a live read is noise, not signal - do not
# report one yet. 4 is one replicate of every P1 cell.
MIN_TRIALS_FOR_INTERIM_READ = 4


def log(msg: str) -> None:
    """Prints a timestamped line.

    Args:
        msg (str): Message to print.
    """
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_state() -> dict:
    """Reads this script's own small state file, tolerating its absence.

    Returns:
        dict: State, or a fresh structure.
    """
    if not os.path.exists(STATE_PATH):
        return {"reported_milestones": [], "last_interim_key": None,
               "run_reported_done": False}
    try:
        with open(STATE_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {"reported_milestones": [], "last_interim_key": None,
               "run_reported_done": False}


def save_state(state: dict) -> None:
    """Writes this script's own state file - never the run's findings file.

    Args:
        state (dict): State to persist.
    """
    os.makedirs(dd.jp.ARCHIVE_DIR, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)


def milestone_p1(verdict: dict) -> str:
    """Formats P1's finished verdict as a milestone report.

    Args:
        verdict (dict): P1's persisted verdict.

    Returns:
        str: Multi-line report.
    """
    lines = [f"MILESTONE - P1 (arrival direction) decided: {verdict['effect']}"]
    if verdict["effect"] == "SIGN_DOMINANT":
        neg, pos = verdict["per_sign"]["negative"], verdict["per_sign"]["positive"]
        lines.append(
            "  HYPOTHESIS: PROVEN, sign-dependent. Arriving "
            f"{neg['better']} is right on negative angles "
            f"(p={neg['p_value']}), arriving {pos['better']} is right on "
            f"positive angles (p={pos['p_value']}). A single fixed "
            "direction would be wrong for half the angles.")
    elif verdict["effect"] in ("DOMINANT", "PARTIAL"):
        lines.append(
            f"  HYPOTHESIS: {'PROVEN' if verdict['effect'] == 'DOMINANT' else 'PARTIALLY SUPPORTED'} "
            f"- arriving {verdict['good_direction']} is better everywhere "
            f"(p={verdict['p_value']}).")
    elif verdict["effect"] == "NONE":
        lines.append(
            "  HYPOTHESIS: NOT SUPPORTED (pooled) - arrival direction does "
            f"not explain it (p={verdict['p_value']}). Moving to a floor "
            "search.")
    else:
        lines.append("  HYPOTHESIS: INCONCLUSIVE - not enough usable trials.")
    lines.append(f"  next: {verdict['directive']}")
    return "\n".join(lines)


def milestone_floor(phase: str, verdict: dict) -> str:
    """Formats a P2 phase's finished verdict as a milestone report.

    Args:
        phase (str): "p2a" or "p2b".
        verdict (dict): The phase's persisted verdict.

    Returns:
        str: Multi-line report.
    """
    label = "P2A (confirm)" if phase == "p2a" else "P2B (search)"
    lines = [f"MILESTONE - {label} decided: {verdict['status']}"]
    if verdict["chosen_floor"] is not None:
        lines.append(f"  min_start_force={verdict['chosen_floor']} passes "
                     "every angle tested (no oscillation, every landing "
                     f"inside {dd.GATE_DEG} deg).")
    else:
        lines.append("  No floor passed at the angles/direction(s) tested.")
    for floor, row in sorted(verdict["rows"].items()):
        lines.append(f"    floor {floor}: {row['status']} "
                     f"({row['failures']}/{row['n']} failed, worst "
                     f"{row['worst_abs_error_deg']} deg)")
    return "\n".join(lines)


def milestone_p3(verdict: dict) -> str:
    """Formats P3's finished verdict as a milestone report.

    Args:
        verdict (dict): P3's persisted verdict.

    Returns:
        str: Multi-line report.
    """
    lines = [f"MILESTONE - P3 (verify-and-correct) decided: {verdict['status']}"]
    lines.append(f"  {verdict['converged']}/{verdict['n']} converged "
                 f"(rate={verdict['converged_rate']}), median "
                 f"{verdict['median_corrections']} corrections needed.")
    lines.append("  HYPOTHESIS: a host-side verify-and-retry in "
                 f"motion_service would {'work' if verdict['status'] == 'CONVERGES' else 'NOT reliably work'} "
                 "as a fix.")
    return "\n".join(lines)


def interim_read_p1(findings: dict) -> tuple[str, str]:
    """Live provisional read of the arrival-direction hypothesis from P1.

    Read-only: calls verdict_p1 with dry_run=True, so nothing is written to
    the shared findings file. Skipped if there is not enough data yet to
    say anything more than noise.

    Args:
        findings (dict): A fresh, freely-mutable load of the findings file.

    Returns:
        tuple[str, str]: (dedup key, line) - both empty if not enough data
            yet. The key changes only when the leaning effect itself
            changes, not on every trial, so the caller can report on real
            state changes only rather than every incremental count.
    """
    by_arrival_n = {
        arrival: len(dd.flat_trials(findings, "p1", arrival=arrival))
        for arrival in ("up", "down")
    }
    if min(by_arrival_n.values(), default=0) < MIN_TRIALS_FOR_INTERIM_READ:
        return "", ""
    verdict = dd.verdict_p1(findings, dry_run=True)
    n_total = by_arrival_n["up"] + by_arrival_n["down"]
    planned = 2 * 7 * dd.P1_N  # 2 arrivals x len(P1_ANGLES) x N, matching P1
    line = (f"interim P1 read ({n_total}/{planned} trials so far, "
           f"provisional): effect leaning {verdict['effect']}, "
           f"rule={verdict['rule']}, p={verdict['p_value']}")
    return f"p1:{verdict['effect']}:{verdict['rule']}", line


def interim_read_p2(findings: dict, phase: str) -> tuple[str, str]:
    """Live provisional read of the floor being tested right now, if any.

    Args:
        findings (dict): A fresh load of the findings file.
        phase (str): "p2a" or "p2b".

    Returns:
        tuple[str, str]: (dedup key, line) - both empty if no floor has any
            data yet. The key is floor + status only, so a failure count
            ticking up trial by trial while the status stays e.g. FAILS
            does not re-report; only a real transition (PASSES/MARGINAL/
            FAILS) or moving to a new floor does.
    """
    touched = sorted({
        int(tag.split("__msf", 1)[1].split("_", 1)[0])
        for tag in findings.get("trials", {}).get(phase, {})
        if "__msf" in tag
    })
    if not touched:
        return "", ""
    current_floor = touched[-1]
    row = dd.score_floor(findings, phase, current_floor)
    # PASSES/MARGINAL/FAILS is unstable at tiny n - a floor's first 1-3
    # trials can flip status on every single one, which defeated the point
    # of reporting on status change rather than every trial. Wait for
    # enough data that a status change actually means something.
    if row["n"] < MIN_TRIALS_FOR_INTERIM_READ:
        return "", ""
    line = (f"interim {phase} read: floor={current_floor} "
           f"{row['failures']}/{row['n']} failed so far "
           f"(osc {row['oscillation_failures']}, acc "
           f"{row['accuracy_failures']}) -> {row['status']}")
    return f"{phase}:{current_floor}:{row['status']}", line


def tick() -> bool:
    """Runs one check: reports new milestones and an interim read.

    Returns:
        bool: True once the run has reached a final decision or aborted -
            the caller should stop polling.
    """
    if not os.path.exists(dd.FINDINGS_PATH):
        return False
    with open(dd.FINDINGS_PATH, encoding="utf-8") as handle:
        findings = json.load(handle)
    state = load_state()
    reported = set(state["reported_milestones"])

    verdicts = findings.get("verdicts", {})
    if "p1" in verdicts and "p1" not in reported:
        log(milestone_p1(verdicts["p1"]))
        reported.add("p1")
    for phase in ("p2a", "p2b"):
        if phase in verdicts and phase not in reported:
            log(milestone_floor(phase, verdicts[phase]))
            reported.add(phase)
    if "p3" in verdicts and "p3" not in reported:
        log(milestone_p3(verdicts["p3"]))
        reported.add("p3")

    if findings.get("decision") and "decision" not in reported:
        d = findings["decision"]
        log(f"MILESTONE - RUN COMPLETE: {d['headline']}")
        reported.add("decision")
    if findings.get("aborted") and "aborted" not in reported:
        log(f"MILESTONE - RUN ABORTED: {findings['aborted']}")
        reported.add("aborted")

    # The interim read, only for whichever phase is actually still
    # collecting data - reported only when the status itself changes
    # (e.g. FAILS -> MARGINAL, or a new floor starts), not on every trial's
    # incremental count. Reporting every tick made this unusable during a
    # long, steadily-failing floor - the operator's own complaint.
    key = line = ""
    if "p1" not in verdicts:
        key, line = interim_read_p1(findings)
    elif "p2a" not in verdicts and findings.get("trials", {}).get("p2a"):
        key, line = interim_read_p2(findings, "p2a")
    elif "p2b" not in verdicts and findings.get("trials", {}).get("p2b"):
        key, line = interim_read_p2(findings, "p2b")
    if line and key != state.get("last_interim_key"):
        log(line)
        state["last_interim_key"] = key

    state["reported_milestones"] = sorted(reported)
    save_state(state)
    return bool(findings.get("decision") or findings.get("aborted"))


def main() -> int:
    """Runs one tick and exits 0 once the run has reached a final state.

    Returns:
        int: 0 if the run is finished (decision or abort seen), 1 otherwise
            - lets a polling loop stop itself.
    """
    return 0 if tick() else 1


if __name__ == "__main__":
    raise SystemExit(main())
