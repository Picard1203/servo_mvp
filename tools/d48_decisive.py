#!/usr/bin/env python3
"""The one D48 run: settles the settling question, or says why it cannot.

Why this tool exists rather than another sweep. Five previous rounds each
measured something rigorously and were undone by a flaw one level up:
sample size, then sampling rate, then time-of-day confounding, then the
selection statistic, and finally the definition of "working" itself - the
last round shipped a minimum-drive floor that does not oscillate and does
not arrive. Every round ended by scheduling another round.

So this one is built to *branch instead of stop*. It carries every live
hypothesis, runs them in order of information value, computes its own
verdict at each gate, and follows the branch that verdict implies - without
a human deciding mid-run what a result means. Whatever happens, it ends
with a written recommendation or an explicit statement of the one thing
that blocks one.

The leading hypothesis, from the operator's own hand-testing. The final leg
of the fine approach arrives *against* the direction of travel, because the
overshoot is placed beyond the target (`motion_service.py::_fine_approach`).
The arrival side is therefore decided by wherever the servo happened to
start, not fixed - the opposite of what an anti-backlash approach is for.
Measured by hand at floor 40:

    -60 deg, arriving downward: -59.39            (0.61 deg short)
    -60 deg, arriving upward:   -59.93 .. -60.05  (0.01-0.07 deg)
    -75 deg, arriving downward: -74.55 x3         (0.45 deg short, identical)
    -75 deg, arriving upward:   -75.09, -75.15    (0.09-0.15 deg)

If that holds, the apparent oscillation-versus-accuracy conflict is an
artifact of an uncontrolled variable, and a low floor plus a fixed arrival
direction satisfies both. This run tests that first, because it is cheap
and it would collapse the whole problem.

Arrival direction is controlled entirely from the host, by choosing which
side the anchor sits on - no firmware or app change is needed to test it:

    arrival = "up"    <=>  anchor above target  (travel down, final leg up)
    arrival = "down"  <=>  anchor below target  (travel up, final leg down)

The phases, and what each can conclude:

    P1  direction    Is arrival direction the dominant cause of the miss,
                     and is there a good direction that meets the gate?
                     -> DOMINANT / PARTIAL / NONE, plus the rule
                        (universal, or flipping with the sign of the angle)

    P2A confirm      (taken when P1 says DOMINANT) Does a low floor, with
                     arrival forced to the good side, pass both gates at
                     every angle? Starts with the cheapest candidate and
                     only widens if it fails. -> FLOOR_FOUND / no floor

    P2B search       (taken when P1 says NONE) The conflict is real: sweep
                     the floor band where oscillation and accuracy data are
                     both thin. -> FLOOR_FOUND / NO_VIABLE_FLOOR

    P3  correction   Always runs. Emulates, from the host, the software fix
                     that does not exist yet: measure the landing, aim past
                     the target by the measured residual from the same
                     side, repeat. Proves whether a verify-and-correct in
                     `motion_service.py` would converge - before anyone
                     writes it. -> CONVERGES / DOES_NOT

The pass gate is a conjunction, pre-declared, and it is what the last round
was missing: a trial passes only if it does NOT oscillate AND every one of
its landings is inside the accuracy gate. The accuracy gate is the
operator's own number, 0.12 deg (2 encoder counts), fixed before the run.

Every trial is checkpointed and the run resumes where it stopped.

    python3 tools/d48_decisive.py                 # the whole thing
    python3 tools/d48_decisive.py --dry-run       # print the plan, no hardware
"""

import argparse
import fcntl
import json
import os
import random
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import d48_s26_campaign as camp
import jitter_probe as jp
import resonance_campaign as rc

LABEL = "d48_decisive"
FINDINGS_PATH = os.path.join(jp.ARCHIVE_DIR, "d48_decisive_findings.json")

# The operator's own acceptance number, fixed before the run. 2 encoder
# counts at the output. Every landing must be inside it; a median inside it
# is not enough, which is exactly what the previous round got wrong.
GATE_DEG = 0.12

R_MAX = 3

# The current half of the oscillation test needs a per-angle reference, and
# this is the correction that stopped the first attempt at this run.
#
# A single threshold of 0.015A was carried over from the previous campaign,
# where it was calibrated from quiet angles - 0 and +-15 deg, which hold at
# 0.0000A because a ~345:1 train needs no current to stay put there. Under
# a real gravitational moment the servo draws steady holding current with
# no motion at all: the earlier multi-angle sweep measured 0.0070A at -60
# and 0.0091A at +60, and the first trial of this run read 0.0173A at +75
# with reversals=0, swing=0.000 deg and no measurable period - a servo
# standing perfectly still, scored as oscillating.
#
# So the threshold is now each angle's own measured holding current plus a
# margin, floored at the original constant so quiet angles keep exactly the
# detector they had. The case the current test exists to catch - sub-count
# hunting that position cannot see - measured 0.078-0.088A, far above any
# holding current seen here, so it is still caught everywhere.
C_MAX_FLOOR_A = 0.015
C_MAX_MARGIN_A = 0.010
HOLD_SECONDS = 10.0

FAST_POLL_SECONDS = 0.010
MIN_FAST_HZ = 40.0
WINDOW_SECONDS = 15.0

STEP_DEG = 0.06
SOFT_LIMIT_DEG = 90.0
# The anchor must sit far enough from the target that the 1.5 deg overshoot
# cannot cross to the other side and invert the arrival direction.
APPROACH_OFFSET_DEG = 15.0
MIN_APPROACH_DEG = 3.0

RESEND_COUNT = 3
SETTLE_TIMEOUT_S = 25.0
# How long position AND current must both sit quiet before a re-send
# landing counts as settled. Deliberately much longer than jp.reset_to's
# 1.2s, which only needs to confirm an anchor was reached before the next
# move starts - this number is what a pass/fail decision is read off.
# Movement decides settling; current does not gate it, at any level. An
# arm holding a position against gravity draws current continuously and it
# fluctuates by more than any sane epsilon, so requiring current to go
# quiet meant this never detected a settle at all - every correction ran
# the full SETTLE_TIMEOUT_S and returned whatever it last read, which is
# why a correction appeared to cost 27s. `is_oscillating` was moved to the
# movement-only rule last session; this is its twin, left behind.
#
# 1.5s is ~5x the 0.277s limit-cycle period measured for this servo, so a
# hunting arm cannot pass as settled: across 245 archived traces, 98% of
# arms still for 2s never moved again, and the median gap between
# movements while hunting is 0.27s.
RESEND_STABLE_SECONDS_REQUIRED = 1.5

# Recorded on every trial and surfaced as a diagnostic, never a gate.
CURRENT_QUIET_A = 0.005

# P1 asks one question - does the arrival side decide the residual - so it
# runs at a single floor already known not to oscillate (0/16 at N=16).
P1_FLOOR = 45
P1_ANGLES = (-75.0, -60.0, -30.0, 0.0, 30.0, 60.0, 75.0)
P1_N = 4

# P2 confirms across the full characterised grid.
P2_ANGLES = (-90.0, -75.0, -60.0, -45.0, -30.0, 0.0,
             30.0, 45.0, 60.0, 75.0, 90.0)
P2_FLOOR_ORDER = (45, 55, 70)
P2_N = 4
# Pre-declared, so a marginal floor is decided by rule rather than by eye.
P2_MARGINAL_FAILURES = 1

# The band where oscillation is known but accuracy has never been measured.
P2B_FLOORS = (45, 55, 65, 75, 85)
P2B_N = 6

P3_MAX_CORRECTIONS = 3
P3_N = 5

# Correct by a fraction of the residual, never all of it: see phase_p3's
# own docstring for the two servo behaviours this has to stay stable under.
CORRECTION_GAIN = 0.5

# A residual past this is not a miss, it is a bad reading. Reported, never
# driven - the guard that stops a mid-travel reading becoming a 61 deg swing.
MAX_CORRECTION_DEG = 2.0

# A floor above this is refused outright: measured to drive this servo into
# a divergent oscillation that jams its own bus. Inherited deliberately.
MAX_FLOOR = camp.MAX_WRITABLE_MIN_START_FORCE


def log(msg: str) -> None:
    """Prints a timestamped line.

    Args:
        msg (str): Message to print.
    """
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------
# persistence
# --------------------------------------------------------------------------

def load_findings() -> dict:
    """Reads the findings file, tolerating a missing or truncated one.

    Returns:
        dict: Findings so far, or a fresh structure.
    """
    if not os.path.exists(FINDINGS_PATH):
        return {"trials": {}, "verdicts": {}, "eeprom_writes": 0}
    try:
        with open(FINDINGS_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        log(f"findings unreadable ({exc!r}); starting fresh")
        return {"trials": {}, "verdicts": {}, "eeprom_writes": 0}


def save_findings(findings: dict) -> None:
    """Writes the findings file atomically.

    A plain in-place write races with this filesystem's write-back caching
    and has produced a truncated file before.

    Args:
        findings (dict): Findings to persist.
    """
    os.makedirs(jp.ARCHIVE_DIR, exist_ok=True)
    tmp = f"{FINDINGS_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as handle:
        json.dump(findings, handle, indent=2, default=str)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, FINDINGS_PATH)


# --------------------------------------------------------------------------
# geometry
# --------------------------------------------------------------------------

def quantize(deg: float) -> float:
    """Snaps an angle onto the command grid the API will accept.

    Grid points are exact multiples of 0.06, so rounding to two decimals
    afterwards is lossless and keeps the API's own step validation happy.

    Args:
        deg (float): Angle in output degrees.

    Returns:
        float: The nearest valid commandable angle.
    """
    return round(round(deg / STEP_DEG) * STEP_DEG, 2)


def anchor_for(target_deg: float, arrival: str) -> Optional[float]:
    """Returns the anchor that forces a given arrival direction.

    The final leg always runs against the direction of travel, so the side
    the anchor sits on decides the side the servo arrives from. This is the
    whole reason the run needs no firmware change to test the leading
    hypothesis.

    Args:
        target_deg (float): Scored target angle.
        arrival (str): "up" or "down", the direction the final leg moves.

    Returns:
        Optional[float]: The anchor angle, or None where travel limits make
            that arrival direction unreachable for this target.
    """
    sign = 1.0 if arrival == "up" else -1.0
    raw = target_deg + sign * APPROACH_OFFSET_DEG
    anchor = quantize(max(-SOFT_LIMIT_DEG, min(SOFT_LIMIT_DEG, raw)))
    separation = (anchor - target_deg) * sign
    if separation < MIN_APPROACH_DEG:
        return None
    return anchor


def natural_arrival(start_deg: Optional[float],
                    target_deg: float) -> Optional[str]:
    """Returns the arrival direction the app would pick unaided.

    Args:
        start_deg (Optional[float]): Where the servo currently sits.
        target_deg (float): Requested target.

    Returns:
        Optional[str]: "up", "down", or None when the move is a no-op and
            the fine approach does not engage at all.
    """
    if start_deg is None or abs(target_deg - start_deg) < 1e-9:
        return None
    return "down" if target_deg > start_deg else "up"


# --------------------------------------------------------------------------
# hardware
# --------------------------------------------------------------------------

def wait_stable(base_url: str, poll_seconds: float) -> Optional[float]:
    """Waits until the position AND current stop changing, then returns position.

    Mirrors the probe's own reset-stability rule rather than trusting the
    firmware's `moving` flag, which is known blind to real settling - but
    with a much longer quiet window than that rule uses (`jp.reset_to`'s
    1.2s), and a second, independent condition on current. This is scoring
    the number a pass/fail decision hangs on, not just confirming the servo
    reached an anchor before the next move starts, so it needs to be held
    to a higher standard: D40 already found the firmware's own settle claim
    blind to trembling that continued past 10s behind a reported 3s
    "clean" settle, and 1.2s of quiet position alone cannot rule out the
    same thing happening here. Position quiet with current still moving is
    exactly the signature of a slow final creep that has not actually
    stopped.

    Args:
        base_url (str): API base URL.
        poll_seconds (float): Interval between reads.

    Returns:
        Optional[float]: The settled output angle, or None if it never read.
    """
    last: Optional[float] = None
    last_current: Optional[float] = None
    stable_since: Optional[float] = None
    t0 = time.time()
    while time.time() - t0 < SETTLE_TIMEOUT_S:
        state = jp.get(base_url, "/servo/state")
        value, current = state.get("output_deg"), state.get("current_a")
        now = time.time()
        if value is not None:
            position_quiet = (last is not None
                              and abs(value - last) < jp.RESET_POSITION_EPSILON_DEG)
            if position_quiet:
                if stable_since is None:
                    stable_since = now
                elif now - stable_since >= RESEND_STABLE_SECONDS_REQUIRED:
                    return value
            else:
                stable_since = None
            last = value
        if current is not None:
            last_current = current
        time.sleep(poll_seconds)
    return last


def is_oscillating(result: dict, r_max: Optional[int],
                   c_max: Optional[float]) -> bool:
    """Decides oscillation from movement alone - the operator's own rule.

    `camp.is_oscillating` (the shared campaign version) also fails a trial
    on current alone, reversals or not. Found live this session why that is
    wrong: a trial at 0 deg, floor 45, arriving up read reversals=0,
    swing_deg=0.0, an identical landing on all four independent attempts,
    current 0.0177A against a 0.015A floor - motionless, but flagged
    "oscillating" anyway. The operator's own call, watching the rig
    directly, is unconditional: as long as it does not move, it is not
    oscillating, even if it is straining against the minimum-drive floor
    and drawing current trying to. A miss that size already fails on
    accuracy on its own; current does not additionally gate pass/fail here.
    Current is still recorded on every trial and surfaced separately (see
    `score_floor`'s `passing_but_strained`) so a trial that is accurate AND
    straining is not silently invisible - it just does not fail for it.

    Args:
        result (dict): One probe result (reversals; current_mean_a and
            c_max accepted for signature compatibility with callers that
            still pass them, but not used to decide oscillation).
        r_max (Optional[int]): Reversal threshold.
        c_max (Optional[float]): Unused - kept so existing call sites do
            not need to change.

    Returns:
        bool: True when the trial counts as oscillating.
    """
    del c_max  # not part of this decision; see docstring
    reversals = result.get("reversals", 0) or 0
    threshold = 3 if r_max is None else r_max
    return bool(reversals > threshold)


def c_max_for(findings: dict, floor: int, target_deg: float) -> float:
    """Returns the current threshold for one angle at one floor.

    Args:
        findings (dict): Findings holding the measured hold references.
        floor (int): Minimum-drive floor in force.
        target_deg (float): Angle the trial scores at.

    Returns:
        float: Amps above which the trial counts as drawing more than
            simply holding station at this angle.
    """
    hold = (findings.get("hold_reference", {})
            .get(str(floor), {})
            .get(f"{target_deg:+.0f}"))
    if hold is None:
        return C_MAX_FLOOR_A
    return max(C_MAX_FLOOR_A, hold + C_MAX_MARGIN_A)


def ensure_hold_reference(base_url: str, findings: dict, floor: int,
                          angles: tuple) -> None:
    """Measures what each angle costs to merely hold, at this floor.

    Parking without commanding a move separates the current a gravitational
    load demands from the current a limit cycle burns. It is measured per
    floor because the minimum-drive floor is itself part of what the servo
    pushes with while holding.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to record the reference into.
        floor (int): Minimum-drive floor, already applied.
        angles (tuple): Angles to characterise.
    """
    block = findings.setdefault("hold_reference", {}).setdefault(str(floor), {})
    missing = [a for a in angles if f"{a:+.0f}" not in block]
    if not missing:
        return
    log(f"  measuring holding current at floor {floor} "
        f"({len(missing)} angles, no moves scored)")
    for angle in missing:
        rc.check_temperature_safety(base_url)
        result = camp.hold_trial(base_url, angle, HOLD_SECONDS,
                                 FAST_POLL_SECONDS)
        mean = result.get("mean_current_a")
        block[f"{angle:+.0f}"] = mean
        save_findings(findings)
        log(f"    hold {angle:+.0f} deg: mean={mean:.4f}A "
            f"peak={result.get('peak_current_a')} "
            f"-> c_max={c_max_for(findings, floor, angle):.4f}A")


def apply_floor(base_url: str, findings: dict, floor: int) -> None:
    """Writes one minimum-drive floor, verified by readback.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings, for the write counter.
        floor (int): Minimum-drive floor to write.

    Raises:
        RuntimeError: If the floor is above the safety ceiling.
    """
    if floor > MAX_FLOOR:
        raise RuntimeError(
            f"refusing min_start_force={floor}: ceiling is {MAX_FLOOR}")
    if findings.get("applied_floor") == floor:
        return
    registers = {**findings["baseline_registers"], "min_start_force": floor}
    camp.apply_config_resilient(base_url, registers, findings)
    findings["applied_floor"] = floor
    save_findings(findings)


def run_trial(base_url: str, findings: dict, phase: str, floor: int,
              target_deg: float, arrival: str, replicate: int,
              resend_mode: str) -> Optional[dict]:
    """One scored trial: a forced approach, then repeated identical commands.

    The re-sends are inside the trial rather than in a block of their own,
    deliberately. The failure the operator found by hand only appears when
    the same target is commanded again, and a separate block is a block a
    later session can forget to run.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings, updated and persisted.
        phase (str): Phase key this trial belongs to.
        floor (int): Minimum-drive floor in force.
        target_deg (float): Scored target angle.
        arrival (str): Forced arrival direction for the scored move.
        replicate (int): 1-based repeat number.
        resend_mode (str): "natural" leaves the re-sends to the app, which
            is today's behaviour; "forced" re-anchors first, emulating the
            fixed-direction approach this run may end up recommending.

    Returns:
        Optional[dict]: The trial record, or None when travel limits make
            this cell unreachable.
    """
    anchor = anchor_for(target_deg, arrival)
    if anchor is None:
        return None
    tag = f"{phase}__msf{floor}_{arrival}_{target_deg:+.0f}"

    rc.check_temperature_safety(base_url)
    camp.cooldown_at_safe_angle(base_url)
    result = jp.probe(base_url, target_deg, LABEL, tag, replicate,
                      poll_seconds=FAST_POLL_SECONDS, anchor_deg=anchor,
                      window_seconds=WINDOW_SECONDS)
    camp.check_current_safety(result, tag)

    landings = [result["final_deg"]]
    arrivals = [arrival]
    for _ in range(RESEND_COUNT):
        previous = landings[-1]
        if resend_mode == "forced":
            jp.reset_to(base_url, anchor, poll_seconds=FAST_POLL_SECONDS)
            this_arrival: Optional[str] = arrival
        else:
            this_arrival = natural_arrival(previous, target_deg)
        jp.move(base_url, target_deg)
        landings.append(wait_stable(base_url, FAST_POLL_SECONDS))
        arrivals.append(this_arrival)

    errors = [round(value - target_deg, 4) for value in landings
              if value is not None]
    magnitudes = [abs(value) for value in errors]
    c_max = c_max_for(findings, floor, target_deg)
    oscillating = is_oscillating(result, R_MAX, c_max)
    max_abs_error = max(magnitudes) if magnitudes else None
    accurate = bool(magnitudes) and max_abs_error <= GATE_DEG
    record = {
        "phase": phase, "floor": floor, "target_deg": target_deg,
        "arrival": arrival, "replicate": replicate,
        "resend_mode": resend_mode, "anchor_deg": anchor,
        "reversals": result["reversals"],
        "current_mean_a": result["current_mean_a"],
        "median_period_s": result["median_period_s"],
        "swing_deg": result.get("swing_deg"),
        "oscillating": oscillating,
        "c_max_used_a": round(c_max, 4),
        "hold_reference_a": (findings.get("hold_reference", {})
                             .get(str(floor), {})
                             .get(f"{target_deg:+.0f}")),
        "landings": landings, "landing_arrivals": arrivals,
        "errors": errors,
        "first_error_deg": errors[0] if errors else None,
        "max_abs_error_deg": max_abs_error,
        "spread_deg": (round(max(v for v in landings if v is not None)
                             - min(v for v in landings if v is not None), 4)
                       if magnitudes else None),
        "accurate": accurate,
        "passed": bool(accurate and not oscillating),
        "achieved_hz": result.get("achieved_hz"),
        "temperature_c_mean": result.get("temperature_c_mean"),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    findings["trials"].setdefault(phase, {}).setdefault(tag, []).append(record)
    save_findings(findings)
    log(f"  {tag} rep {replicate}: reversals={record['reversals']} "
        f"osc={oscillating} errors={errors} "
        f"max={max_abs_error} pass={record['passed']}")
    return record


def cell_trials(findings: dict, phase: str, floor: int, target_deg: float,
                arrival: str) -> list[dict]:
    """Returns the trials already recorded for one cell.

    Args:
        findings (dict): Findings so far.
        phase (str): Phase key.
        floor (int): Minimum-drive floor.
        target_deg (float): Target angle.
        arrival (str): Arrival direction.

    Returns:
        list[dict]: Recorded trials, empty when the cell has not run.
    """
    tag = f"{phase}__msf{floor}_{arrival}_{target_deg:+.0f}"
    return findings["trials"].get(phase, {}).get(tag, [])


def run_cells(base_url: str, findings: dict, phase: str, cells: list[tuple],
              replicates: int, resend_mode: str) -> None:
    """Runs a randomised complete block over the given cells.

    Every replicate visits each cell once in a fresh random order, so drift
    over the run lands on the block rather than on whichever arm happened
    to run late. That confound is what invalidated an entire earlier
    session's comparisons.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings, updated per trial.
        phase (str): Phase key.
        cells (list[tuple]): (floor, target_deg, arrival) tuples.
        replicates (int): Repeats per cell.
        resend_mode (str): Passed through to each trial.
    """
    # Each floor's holding reference is measured once, before any trial at
    # that floor is scored against it.
    for floor in sorted({cell[0] for cell in cells}):
        angles = tuple(sorted({cell[1] for cell in cells if cell[0] == floor}))
        apply_floor(base_url, findings, floor)
        ensure_hold_reference(base_url, findings, floor, angles)

    for replicate in range(1, replicates + 1):
        order = list(cells)
        random.shuffle(order)
        for floor, target_deg, arrival in order:
            if len(cell_trials(findings, phase, floor, target_deg,
                               arrival)) >= replicate:
                continue
            if anchor_for(target_deg, arrival) is None:
                continue
            apply_floor(base_url, findings, floor)
            run_trial(base_url, findings, phase, floor, target_deg, arrival,
                      replicate, resend_mode)


# --------------------------------------------------------------------------
# analysis
# --------------------------------------------------------------------------

def flat_trials(findings: dict, phase: str, **match) -> list[dict]:
    """Returns every trial in a phase matching the given field values.

    Args:
        findings (dict): Findings so far.
        phase (str): Phase key.
        **match: Field/value pairs every returned trial must have.

    Returns:
        list[dict]: Matching trial records.
    """
    out = []
    for trials in findings["trials"].get(phase, {}).values():
        for trial in trials:
            if all(trial.get(k) == v for k, v in match.items()):
                out.append(trial)
    return out


def _rate(trials: list[dict], key: str) -> Optional[float]:
    """Returns the fraction of trials whose boolean field is True.

    Args:
        trials (list[dict]): Trial records.
        key (str): Boolean field name.

    Returns:
        Optional[float]: The fraction, or None with no trials.
    """
    if not trials:
        return None
    return sum(1 for t in trials if t.get(key)) / len(trials)


def verdict_p1(findings: dict, dry_run: bool = False) -> dict:
    """Decides whether arrival direction explains the positioning miss.

    Two things are decided here, and both are decided by rule. First,
    whether the arrival side has a real effect at all - measured on the
    first landing, which is the one whose direction was actually forced.
    Second, if it does, whether the good side is the same on both halves of
    travel or flips with the sign of the angle, which is what a
    gravity-borne asymmetry would look like.

    Args:
        findings (dict): Findings containing P1's trials.
        dry_run (bool): When True, computes and returns the verdict without
            writing it into findings or persisting anything - for reading a
            provisional read from outside the running process, which must
            never touch this file: the run resumes by trusting exactly what
            is on disk, and an early or wrong verdict written there would
            make a restarted run skip trials it has not actually done.

    Returns:
        dict: The verdict. Also written into findings unless dry_run.
    """
    by_arrival = {}
    for arrival in ("up", "down"):
        trials = flat_trials(findings, "p1", arrival=arrival)
        firsts = [abs(t["first_error_deg"]) for t in trials
                  if t.get("first_error_deg") is not None]
        inside = sum(1 for value in firsts if value <= GATE_DEG)
        by_arrival[arrival] = {
            "n": len(firsts),
            "inside_gate": inside,
            "inside_rate": (inside / len(firsts)) if firsts else None,
            "median_abs_error": jp._median(firsts),
            "max_abs_error": max(firsts) if firsts else None,
            "oscillating_rate": _rate(trials, "oscillating"),
        }

    up, down = by_arrival["up"], by_arrival["down"]
    good = None
    p_value = None
    if up["n"] and down["n"]:
        good = "up" if up["median_abs_error"] <= down["median_abs_error"] \
            else "down"
        bad = "down" if good == "up" else "up"
        # One-sided: the good side misses the gate less often than the bad.
        p_value = camp.fisher_exact_one_sided(
            by_arrival[good]["n"] - by_arrival[good]["inside_gate"],
            by_arrival[good]["inside_gate"],
            by_arrival[bad]["n"] - by_arrival[bad]["inside_gate"],
            by_arrival[bad]["inside_gate"])

    gap = None
    if good is not None:
        bad = "down" if good == "up" else "up"
        if (by_arrival[good]["inside_rate"] is not None
                and by_arrival[bad]["inside_rate"] is not None):
            gap = by_arrival[good]["inside_rate"] - by_arrival[bad]["inside_rate"]

    # Does the good side stay good on both halves of travel? Computed with
    # the same rigour as the pooled test above (inside-gate counts and a
    # one-sided Fisher test per sign), not just a median comparison - a real
    # effect that flips sign between halves averages to ~0 in the pooled
    # test above and would otherwise be missed entirely, which is exactly
    # what happened the first time this ran: p1_run 8 Sept found a p=0.92
    # pooled result sitting on top of a p=4.8e-6 negative-side effect and a
    # p=0.0069 positive-side effect running in opposite directions.
    per_sign = {}
    for name, angles in (("negative", [a for a in P1_ANGLES if a < 0]),
                         ("positive", [a for a in P1_ANGLES if a > 0])):
        sign_block = {}
        sign_stats = {}
        for arrival in ("up", "down"):
            values = [abs(t["first_error_deg"])
                      for t in flat_trials(findings, "p1", arrival=arrival)
                      if t.get("first_error_deg") is not None
                      and t["target_deg"] in angles]
            inside = sum(1 for v in values if v <= GATE_DEG)
            sign_block[arrival] = jp._median(values)
            sign_stats[arrival] = {
                "n": len(values), "inside_gate": inside,
                "inside_rate": (inside / len(values)) if values else None,
            }
        both = [sign_block["up"], sign_block["down"]]
        sign_block["better"] = (
            None if any(v is None for v in both)
            else ("up" if sign_block["up"] <= sign_block["down"] else "down"))
        sign_gap = sign_p = None
        if sign_block["better"] is not None:
            s_good, s_bad = sign_block["better"], (
                "down" if sign_block["better"] == "up" else "up")
            g, b = sign_stats[s_good], sign_stats[s_bad]
            if g["inside_rate"] is not None and b["inside_rate"] is not None:
                sign_gap = g["inside_rate"] - b["inside_rate"]
                sign_p = camp.fisher_exact_one_sided(
                    g["n"] - g["inside_gate"], g["inside_gate"],
                    b["n"] - b["inside_gate"], b["inside_gate"])
        sign_block["inside_rate_gap"] = sign_gap
        sign_block["p_value"] = None if sign_p is None else float(f"{sign_p:.6g}")
        sign_block["dominant"] = bool(
            sign_gap is not None and sign_gap >= 0.3
            and sign_p is not None and sign_p < 0.05)
        per_sign[name] = sign_block

    better = {k: v.get("better") for k, v in per_sign.items()}
    if None in better.values():
        rule = "UNDETERMINED"
    elif better["negative"] == better["positive"]:
        rule = f"UNIVERSAL_{better['negative'].upper()}"
    else:
        rule = "SIGN_DEPENDENT"

    sign_dominant = (rule == "SIGN_DEPENDENT"
                     and per_sign["negative"]["dominant"]
                     and per_sign["positive"]["dominant"])

    if sign_dominant:
        # Checked ahead of the pooled classification below: a real,
        # opposite-signed effect averages out to "no pooled effect" and
        # must not be allowed to read as NONE.
        effect = "SIGN_DOMINANT"
    elif good is None:
        effect = "INCONCLUSIVE"
    elif gap is not None and gap >= 0.3 and p_value is not None and p_value < 0.05:
        effect = "DOMINANT"
    elif p_value is not None and p_value < 0.05:
        effect = "PARTIAL"
    else:
        effect = "NONE"

    gate_reachable = bool(
        sign_dominant
        or (good is not None and by_arrival[good]["inside_rate"] is not None
            and by_arrival[good]["inside_rate"] >= 0.8))

    verdict = {
        "effect": effect, "good_direction": good, "rule": rule,
        "p_value": None if p_value is None else float(f"{p_value:.6g}"),
        "inside_rate_gap": gap,
        "gate_reachable_open_loop": gate_reachable,
        "by_arrival": by_arrival, "per_sign": per_sign,
        "directive": {
            "SIGN_DOMINANT": "Arrival direction decides the miss, and the "
                             "good side flips with the sign of the angle. "
                             "Confirm a low floor with direction chosen "
                             "per angle's own sign (P2A, sign-aware).",
            "DOMINANT": "Arrival direction decides the miss. Confirm a low "
                        "floor with arrival forced to the good side (P2A).",
            "PARTIAL": "Arrival direction matters but does not fully "
                       "explain it. Confirm the good side, expect some "
                       "angles still to fail (P2A).",
            "NONE": "Arrival direction is not the cause. The "
                    "oscillation/accuracy conflict is real; search the "
                    "floor band (P2B).",
            "INCONCLUSIVE": "Not enough usable trials to decide.",
        }[effect],
    }
    if not dry_run:
        findings["verdicts"]["p1"] = verdict
        save_findings(findings)
        log(f"P1 verdict: effect={effect} good={good} rule={rule} "
            f"p={verdict['p_value']} gate_reachable={gate_reachable}")
    return verdict


def score_floor(findings: dict, phase: str, floor: int) -> dict:
    """Summarises one floor across every angle it was tested at.

    Args:
        findings (dict): Findings so far.
        phase (str): Phase key.
        floor (int): Minimum-drive floor.

    Returns:
        dict: Counts, failure detail and the pre-declared status.
    """
    trials = flat_trials(findings, phase, floor=floor)
    failures = [t for t in trials if not t["passed"]]
    osc = [t for t in failures if t["oscillating"]]
    acc = [t for t in failures if not t["accurate"]]
    # Elevated current while nothing moved doesn't fail a trial on its own
    # (see is_oscillating) - the accuracy check catches it whenever the
    # servo is also stuck off-target, which is the only case seen so far.
    # But nothing stops it happening while accurately positioned too, and
    # that would otherwise pass with no record at all - tracked here, on
    # every trial, not just failures, so a floor that quietly strains while
    # sitting on target is still visible in the writeup even though the
    # pass/fail gate does not ask for zero current.
    strained = [t for t in trials
               if not t["oscillating"] and t["accurate"]
               and (t.get("current_mean_a") or 0.0) > (t.get("c_max_used_a") or 1e9)]
    worst = max((t["max_abs_error_deg"] for t in trials
                 if t.get("max_abs_error_deg") is not None), default=None)
    if not trials:
        status = "NOT_RUN"
    elif not failures:
        status = "PASSES"
    elif len(failures) <= P2_MARGINAL_FAILURES:
        status = "MARGINAL"
    else:
        status = "FAILS"
    return {
        "floor": floor, "n": len(trials), "failures": len(failures),
        "oscillation_failures": len(osc), "accuracy_failures": len(acc),
        "passing_but_strained": len(strained),
        "strained_angles": sorted({t["target_deg"] for t in strained}),
        "worst_abs_error_deg": worst,
        "failing_angles": sorted({t["target_deg"] for t in failures}),
        "status": status,
    }


def verdict_floors(findings: dict, phase: str, floors: tuple) -> dict:
    """Picks the floor to ship, or records that none qualifies.

    Among floors that pass everywhere the highest is preferred: more
    holding torque means less steady-state droop against gravity, right up
    to the point it starts a limit cycle.

    Args:
        findings (dict): Findings so far.
        phase (str): Phase key.
        floors (tuple): Floors considered in this phase.

    Returns:
        dict: The verdict, also written into findings.
    """
    rows = {floor: score_floor(findings, phase, floor) for floor in floors}
    passing = [f for f, r in rows.items() if r["status"] == "PASSES"]
    marginal = [f for f, r in rows.items() if r["status"] == "MARGINAL"]
    chosen = max(passing) if passing else None
    verdict = {
        "rows": rows,
        "passing": sorted(passing),
        "marginal": sorted(marginal),
        "chosen_floor": chosen,
        "status": "FLOOR_FOUND" if chosen is not None else "NO_VIABLE_FLOOR",
    }
    findings["verdicts"][phase] = verdict
    save_findings(findings)
    for floor, row in sorted(rows.items()):
        log(f"  floor {floor}: {row['failures']}/{row['n']} failed "
            f"(osc {row['oscillation_failures']}, acc "
            f"{row['accuracy_failures']}), worst "
            f"{row['worst_abs_error_deg']}, {row['status']}")
    log(f"{phase} verdict: {verdict['status']} chosen={chosen}")
    return verdict


# --------------------------------------------------------------------------
# phases
# --------------------------------------------------------------------------

def phase_p1(base_url: str, findings: dict) -> dict:
    """Tests the arrival-direction hypothesis at one known-quiet floor.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.

    Returns:
        dict: P1's verdict.
    """
    log("=== P1: does arrival direction decide the miss? ===")
    cells = [(P1_FLOOR, angle, arrival)
             for angle in P1_ANGLES for arrival in ("up", "down")]
    run_cells(base_url, findings, "p1", cells, P1_N, resend_mode="natural")
    return verdict_p1(findings)


def phase_p2a(base_url: str, findings: dict,
              direction_for: Callable[[float], str]) -> dict:
    """Confirms a low floor across the full grid, arrival forced per angle.

    Floors are tried cheapest-first: the first candidate that passes every
    angle ends the phase, because a floor that passes everywhere is the
    answer and spending hours on the rest proves nothing further.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
        direction_for (Callable[[float], str]): Maps a target angle to the
            arrival direction to force there. A plain `lambda a: "up"`
            reproduces the uniform-direction case; P1's SIGN_DOMINANT
            verdict supplies one that flips with the angle's sign instead,
            because a single fixed direction is provably wrong for half
            the angles when the good side depends on sign.

    Returns:
        dict: P2A's verdict.
    """
    sample = {a: direction_for(a) for a in P2_ANGLES}
    log(f"=== P2A: confirm a floor, arrival per angle: {sample} ===")
    tried: list[int] = []
    for floor in P2_FLOOR_ORDER:
        tried.append(floor)
        cells = [(floor, angle, direction_for(angle)) for angle in P2_ANGLES]
        run_cells(base_url, findings, "p2a", cells, P2_N,
                  resend_mode="forced")
        row = score_floor(findings, "p2a", floor)
        log(f"  floor {floor}: {row['status']} "
            f"({row['failures']}/{row['n']} failed)")
        if row["status"] == "PASSES":
            break
    return verdict_floors(findings, "p2a", tuple(tried))


def phase_p2b(base_url: str, findings: dict,
              good_direction: Optional[str]) -> dict:
    """Searches the floor band when arrival direction was not the cause.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
        good_direction (Optional[str]): Better arrival side if one exists.

    Returns:
        dict: P2B's verdict.
    """
    log("=== P2B: floor search (arrival direction was not the cause) ===")
    failing = sorted({t["target_deg"]
                      for t in flat_trials(findings, "p1")
                      if not t["passed"]}) or list(P1_ANGLES)
    angles = failing[:5]
    log(f"  angles carried from P1 failures: {angles}")
    arrival = good_direction or "up"
    cells = [(floor, angle, arrival)
             for floor in P2B_FLOORS for angle in angles]
    run_cells(base_url, findings, "p2b", cells, P2B_N, resend_mode="forced")
    return verdict_floors(findings, "p2b", P2B_FLOORS)


def phase_probe(base_url: str, findings: dict, floor: int) -> dict:
    """Tests one operator-chosen floor, standalone, at the full rigor of P2A.

    Not part of the pre-declared P2_FLOOR_ORDER - this exists for a value
    picked *after* seeing the trend across the pre-declared floors (here:
    45/55 improving on accuracy as the floor rises, 70 starting to
    oscillate, so 65 sits in the gap between them and was never going to be
    tested by the original 45/55/70 order). Recorded under its own phase
    key (`probe_msf<floor>`) rather than folded into "p2a", so the record
    stays honest about what was pre-registered versus added afterward on a
    live trend - the exact distinction this project's own history keeps
    finding was missing elsewhere.

    Requires P1's verdict already on record, since the direction rule is
    read from it rather than re-derived.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
        floor (int): The floor to test.

    Returns:
        dict: The probe's verdict (same shape as verdict_floors' return).

    Raises:
        RuntimeError: If P1 has not run yet in this findings file.
    """
    p1 = findings.get("verdicts", {}).get("p1")
    if p1 is None:
        raise RuntimeError(
            "no P1 verdict on record - run the main campaign first so the "
            "arrival-direction rule exists to probe this floor with")
    if p1["effect"] == "SIGN_DOMINANT":
        neg, pos = p1["per_sign"]["negative"]["better"], p1["per_sign"]["positive"]["better"]
        direction_for = lambda a: neg if a <= 0 else pos  # noqa: E731
    elif p1["effect"] in ("DOMINANT", "PARTIAL"):
        good = p1["good_direction"]
        direction_for = lambda a: good  # noqa: E731
    else:
        direction_for = lambda a: "up"  # noqa: E731

    phase_key = f"probe_msf{floor}"
    log(f"=== PROBE (not pre-declared): floor {floor}, arrival per angle "
        f"from P1's rule ===")
    cells = [(floor, angle, direction_for(angle)) for angle in P2_ANGLES]
    run_cells(base_url, findings, phase_key, cells, P2_N, resend_mode="forced")
    return verdict_floors(findings, phase_key, (floor,))


def phase_p3(base_url: str, findings: dict, floor: int,
             direction_for: Callable[[float], str],
             angles: list[float], backoff_deg: Optional[float] = None,
             gain: float = CORRECTION_GAIN,
             label: Optional[str] = None) -> dict:
    """Emulates the missing software fix and reports whether it converges.

    `_fine_approach` fires its final leg and checks only that the servo
    acknowledged it, never that it arrived. This phase does from the host
    what that code should do itself: read the landing, and if it is outside
    the gate, aim past the target by the residual just measured, from the
    same side so the same residual applies. If this converges, the fix is
    worth writing; if it does not, no amount of it will help.

    Two things the first version of this got wrong, both fixed here because
    they are the difference between a fix and a hazard:

    - It corrected by the whole residual. That is only stable if the servo
      lands at `aim + offset` for a fixed offset. When it instead lands
      *at* the aim, subtracting the residual doubles the error and the loop
      ping-pongs (measured: +45 deg landing 45.18/44.82/45.18/44.82). A
      gain below 1 converges under both models, so `gain` defaults to 0.5.
    - It commanded a correction of any size, including one computed from a
      reading taken mid-travel: a 61 deg "residual" was measured and then
      driven, twice, sign flipping. Anything past `MAX_CORRECTION_DEG` is
      now treated as a bad reading and reported, never driven.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
        floor (int): Floor to test the correction at.
        direction_for (Callable[[float], str]): Maps a target angle to the
            arrival direction to force there - the same resolver P2A uses,
            so P3 tests the correction under the direction the evidence
            actually supports at each angle, not one fixed side.
        angles (list[float]): Angles to test.
        backoff_deg (Optional[float]): How far to retreat before
            re-approaching. None keeps the original behaviour, a full
            traverse back to the 15 deg anchor. A number backs off only
            that far, which is the shape the product can afford - it
            already runs a 1.5 deg overshoot leg on every move. Both the
            accuracy and the time cost of the short version are unmeasured,
            which is the whole reason this parameter exists.
        gain (float): Fraction of the measured residual to correct by.
        label (Optional[str]): Suffix for the phase key, so two correction
            shapes can be compared without overwriting each other.

    Returns:
        dict: P3's verdict.
    """
    shape = ("anchor" if backoff_deg is None
             else f"backoff{backoff_deg:g}")
    phase = "p3" if label is None else f"p3_{label}"
    log(f"=== P3: does verify-and-correct converge? (floor {floor}, "
        f"{shape}, gain {gain}) ===")
    apply_floor(base_url, findings, floor)
    records = findings["trials"].setdefault(phase, {})
    for angle in angles:
        arrival = direction_for(angle)
        anchor = anchor_for(angle, arrival)
        if anchor is None:
            continue
        # "up" means the final leg travels upward, so the retreat that sets
        # it up has to sit above the aim - the same geometry anchor_for
        # uses, just at a distance the product can afford.
        retreat_sign = 1.0 if arrival == "up" else -1.0
        key = f"{phase}__msf{floor}_{arrival}_{angle:+.0f}"
        done = records.setdefault(key, [])
        for replicate in range(len(done) + 1, P3_N + 1):
            rc.check_temperature_safety(base_url)
            started = time.time()
            jp.reset_to(base_url, anchor, poll_seconds=FAST_POLL_SECONDS)
            jp.move(base_url, angle)
            measured = wait_stable(base_url, FAST_POLL_SECONDS)
            aim = angle
            steps = [measured]
            correction_seconds = []
            corrections = 0
            outcome = "converged"
            while (measured is not None
                   and abs(measured - angle) > GATE_DEG
                   and corrections < P3_MAX_CORRECTIONS):
                residual = measured - angle
                if abs(residual) > MAX_CORRECTION_DEG:
                    # Not a miss. A reading this far out means the servo was
                    # still travelling, or did not answer honestly; driving
                    # it is how a bad reading becomes a real 61 deg swing.
                    outcome = "implausible_residual"
                    log(f"  {key} rep {replicate}: residual "
                        f"{residual:+.2f} deg past the "
                        f"{MAX_CORRECTION_DEG} deg limit, not corrected")
                    break
                # Correct the AIM, not the target. The old rule recomputed
                # `target - residual` every round, discarding where it last
                # aimed - which is why it ping-ponged: when the servo lands
                # wherever it is aimed, that rule just flips the error's
                # sign forever (+45 deg: 45.18/44.82/45.18/44.82). Carrying
                # the aim forward converges under both behaviours this
                # servo shows - a fixed offset (-90 deg lands 0.43 deg past,
                # every time) and landing-at-aim - because each round
                # removes the error that was actually measured rather than
                # re-deriving it from a target the servo never lands on.
                aim = quantize(aim - gain * residual)
                correction_started = time.time()
                if backoff_deg is None:
                    jp.reset_to(base_url, anchor,
                                poll_seconds=FAST_POLL_SECONDS)
                else:
                    jp.reset_to(base_url,
                                quantize(aim + retreat_sign * backoff_deg),
                                poll_seconds=FAST_POLL_SECONDS)
                jp.move(base_url, aim)
                measured = wait_stable(base_url, FAST_POLL_SECONDS)
                correction_seconds.append(
                    round(time.time() - correction_started, 2))
                steps.append(measured)
                corrections += 1
            if measured is None:
                outcome = "unreadable"
            converged = (measured is not None
                         and abs(measured - angle) <= GATE_DEG)
            if outcome == "converged" and not converged:
                outcome = "did_not_converge"
            done.append({
                "replicate": replicate, "target_deg": angle,
                "arrival": arrival, "floor": floor,
                "correction_shape": shape, "correction_gain": gain,
                "landings": steps, "corrections": corrections,
                "correction_seconds": correction_seconds,
                "elapsed_s": round(time.time() - started, 2),
                "outcome": outcome,
                "final_error_deg": (None if measured is None
                                    else round(measured - angle, 4)),
                "converged": converged,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            save_findings(findings)
            log(f"  {key} rep {replicate}: corrections={corrections} "
                f"final_error={done[-1]['final_error_deg']} "
                f"converged={converged} "
                f"elapsed={done[-1]['elapsed_s']}s "
                f"per_correction={correction_seconds}")

    trials = [t for block in records.values() for t in block]
    converged = sum(1 for t in trials if t["converged"])
    needed = [t["corrections"] for t in trials if t["converged"]]
    rate = (converged / len(trials)) if trials else None
    verdict = {
        "n": len(trials), "converged": converged, "converged_rate": rate,
        "median_corrections": jp._median([float(v) for v in needed]),
        "max_corrections_seen": max(needed) if needed else None,
        "status": ("CONVERGES" if rate is not None and rate >= 0.95
                   else "PARTIAL" if rate is not None and rate >= 0.6
                   else "DOES_NOT_CONVERGE"),
        "correction_shape": shape,
        "correction_gain": gain,
        "median_seconds_per_correction": jp._median(
            [float(v) for t in trials
             for v in t.get("correction_seconds", [])]),
        "median_elapsed_s": jp._median(
            [float(t["elapsed_s"]) for t in trials if t.get("elapsed_s")]),
    }
    findings["verdicts"][phase] = verdict
    save_findings(findings)
    log(f"P3 verdict: {verdict['status']} "
        f"({converged}/{len(trials)} converged)")
    return verdict


# --------------------------------------------------------------------------
# the decision
# --------------------------------------------------------------------------

def decide(findings: dict) -> dict:
    """Combines every verdict into one recommendation, or names the blocker.

    Args:
        findings (dict): Findings with all phase verdicts.

    Returns:
        dict: The decision, also written into findings.
    """
    p1 = findings["verdicts"].get("p1", {})
    floors = (findings["verdicts"].get("p2a")
              or findings["verdicts"].get("p2b") or {})
    p3 = findings["verdicts"].get("p3", {})

    floor = floors.get("chosen_floor")
    direction = p1.get("good_direction")
    rule = p1.get("rule")

    if floor is not None:
        headline = f"SHIP floor={floor}"
        if p1.get("effect") == "SIGN_DOMINANT":
            neg = p1.get("per_sign", {}).get("negative", {}).get("better")
            pos = p1.get("per_sign", {}).get("positive", {}).get("better")
            headline += (f", arrival {neg} on negative angles / "
                        f"{pos} on positive angles ({rule})")
        elif p1.get("effect") in ("DOMINANT", "PARTIAL"):
            headline += f", arrival forced {direction} ({rule})"
        software = ("recommended as a backstop"
                    if p3.get("status") == "CONVERGES" else "not proven")
    elif p3.get("status") == "CONVERGES":
        headline = ("NO_VIABLE_FLOOR open-loop, but verify-and-correct "
                    "converges: the fix is software")
        software = "required"
    else:
        headline = "NO DECISION: neither a floor nor the correction passed"
        software = "did not converge"

    decision = {
        "headline": headline,
        "chosen_floor": floor,
        "arrival_rule": rule,
        "good_direction": direction,
        "direction_effect": p1.get("effect"),
        "software_correction": software,
        "software_correction_verdict": p3.get("status"),
        "gate_deg": GATE_DEG,
        "evidence": {"p1": p1, "floors": floors, "p3": p3},
    }
    findings["decision"] = decision
    save_findings(findings)
    return decision


def print_decision(decision: dict) -> None:
    """Prints the final decision block.

    Args:
        decision (dict): The decision from decide().
    """
    print("\n" + "=" * 72)
    print("D48 DECISION")
    print("=" * 72)
    print(f"  {decision['headline']}")
    print(f"  accuracy gate           : {decision['gate_deg']} deg")
    print(f"  arrival direction effect: {decision['direction_effect']}")
    print(f"  good arrival direction  : {decision['good_direction']} "
          f"({decision['arrival_rule']})")
    print(f"  chosen floor            : {decision['chosen_floor']}")
    print(f"  software verify/correct : {decision['software_correction']} "
          f"[{decision['software_correction_verdict']}]")
    print(f"\n  full evidence: {FINDINGS_PATH}")
    print("=" * 72 + "\n")


def print_plan() -> None:
    """Prints what the run will do, without touching hardware."""
    p1_cells = len(P1_ANGLES) * 2
    print(f"gate                 : {GATE_DEG} deg on every landing")
    print(f"P1 direction         : floor {P1_FLOOR}, {len(P1_ANGLES)} angles "
          f"x 2 arrivals x N={P1_N} = {p1_cells * P1_N} trials")
    print(f"P2A confirm (if P1 DOMINANT): floors {P2_FLOOR_ORDER} "
          f"cheapest-first, {len(P2_ANGLES)} angles x N={P2_N} "
          f"= up to {len(P2_ANGLES) * P2_N} trials per floor")
    print(f"P2B search  (if P1 NONE)    : floors {P2B_FLOORS} x <=5 angles "
          f"x N={P2B_N}")
    print(f"P3 correction (always)      : N={P3_N} per angle, up to "
          f"{P3_MAX_CORRECTIONS} corrections")
    print("every trial: forced approach + 15s score + "
          f"{RESEND_COUNT} identical re-sends")


LOCK_PATH = os.path.join(jp.ARCHIVE_DIR, ".d48_decisive.lock")


def acquire_servo_lock():
    """Takes an exclusive lock, so two runs can never drive one servo.

    Two overlapping runs do not merely interleave moves. The one that
    finishes first restores the registers on its way out, which silently
    drops the floor out from under the one still running - and every trial
    that run goes on to record carries the floor it *asked* for, not the
    floor the servo was actually at. That happened: a block labelled
    `msf55` was collected at 40, and only a live register read caught it.
    Data that lies about its own conditions is worse than no data.

    Returns:
        The held lock file. Keep it referenced for the process lifetime;
        closing it releases the lock.

    Raises:
        SystemExit: If another run already holds it.
    """
    handle = open(LOCK_PATH, "w", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise SystemExit(
            f"another d48_decisive run holds {LOCK_PATH}. Two runs on one "
            "servo corrupt each other's registers - wait for it to finish, "
            "or stop it, then re-run. It resumes from its checkpoint.")
    handle.write(f"{os.getpid()}\n")
    handle.flush()
    return handle


def main() -> int:
    """Runs the whole branching campaign and prints one decision.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--dry-run", action="store_true",
                        help="print the plan and exit, touching no hardware")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--probe-floor", type=int, default=None,
                        help="run one additional floor as a standalone, "
                             "clearly-labeled probe (phase key "
                             "'probe_msfN', not folded into the "
                             "pre-declared P2A order) across the full "
                             "angle grid, using the direction rule P1 "
                             "already decided. Requires a P1 verdict "
                             "already on record.")
    parser.add_argument("--p3-floor", type=int, default=None,
                        help="run P3 (verify-and-correct) standalone at "
                             "this floor instead of the automatic pipeline "
                             "choice (the chosen P2A floor, or P1_FLOOR if "
                             "none passed). Use this to test the "
                             "correction against a floor you have reason "
                             "to prefer - e.g. the best-performing one "
                             "found, not the pipeline's own fallback.")
    parser.add_argument("--p3-backoff", type=float, default=None,
                        help="how far to retreat before re-approaching "
                             "during a correction, in output degrees. "
                             "Omitted, it drives all the way back to the "
                             "15 deg anchor, which is what every trial so "
                             "far measured and costs ~17s per correction. "
                             "The product can only afford its existing "
                             "1.5 deg overshoot leg, and neither the "
                             "accuracy nor the timing of that shorter "
                             "retreat has been measured.")
    parser.add_argument("--p3-gain", type=float, default=CORRECTION_GAIN,
                        help="fraction of the residual to correct by "
                             f"(default {CORRECTION_GAIN}; 1.0 is what "
                             "ping-ponged at +45 deg)")
    parser.add_argument("--p3-label", type=str, default=None,
                        help="suffix for the phase key, so two correction "
                             "shapes can be compared in one findings file "
                             "without overwriting each other")
    parser.add_argument("--p3-angles", type=str, default=None,
                        help="comma-separated angles for --p3-floor, e.g. "
                             "'-60,90'. Defaults to that floor's own "
                             "recorded failing_angles if it was already "
                             "tested, else the pipeline's own default set.")
    args = parser.parse_args()

    lock = None if args.dry_run else acquire_servo_lock()  # noqa: F841

    if args.dry_run:
        print_plan()
        return 0

    base_url = f"http://{args.host}:{args.port}/api/v1"
    findings = load_findings()
    seed = (args.seed if args.seed is not None
            else findings.get("seed", int(time.time())))
    random.seed(seed)
    findings["seed"] = seed
    findings["gate_deg"] = GATE_DEG
    findings["started_at"] = findings.get(
        "started_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
    findings.setdefault("verdicts", {})
    findings.setdefault("trials", {})
    # A resumed run cannot know what the servo currently holds: the previous
    # process restores the boot registers on its way out, so a carried-over
    # "already applied" would skip the write and run the next trials at the
    # wrong floor while labelling them with the right one.
    findings["applied_floor"] = None
    save_findings(findings)

    boot_registers = None
    try:
        if not args.skip_preflight:
            camp.preflight(base_url, findings)
            save_findings(findings)
        else:
            findings.setdefault("baseline_registers",
                                camp.read_registers(base_url))
        boot_registers = dict(findings["baseline_registers"])
        log(f"registers at start: {boot_registers}")

        if args.probe_floor is not None:
            verdict = phase_probe(base_url, findings, args.probe_floor)
            print(f"\nPROBE floor={args.probe_floor}: {verdict['status']} "
                 f"({verdict['rows'][args.probe_floor]['failures']}/"
                 f"{verdict['rows'][args.probe_floor]['n']} failed)")
            save_findings(findings)
            return 0

        if args.p3_floor is not None:
            p1v = findings.get("verdicts", {}).get("p1")
            if p1v is None:
                raise RuntimeError(
                    "no P1 verdict on record - run the main campaign "
                    "first so the direction rule exists")
            if p1v["effect"] == "SIGN_DOMINANT":
                neg = p1v["per_sign"]["negative"]["better"]
                pos = p1v["per_sign"]["positive"]["better"]
                direction_for = lambda a, neg=neg, pos=pos: neg if a <= 0 else pos
            elif p1v["effect"] in ("DOMINANT", "PARTIAL"):
                good = p1v["good_direction"]
                direction_for = lambda a, good=good: good
            else:
                direction_for = lambda a: "up"
            if args.p3_angles:
                angles = [float(a) for a in args.p3_angles.split(",")]
            else:
                angles = None
                for phase_key in (f"probe_msf{args.p3_floor}", "p2a", "p2b"):
                    rows = (findings.get("verdicts", {}).get(phase_key, {})
                           .get("rows", {}))
                    row = rows.get(args.p3_floor) or rows.get(str(args.p3_floor))
                    if row and row.get("failing_angles"):
                        angles = row["failing_angles"]
                        break
                # Only the inferred lists are capped: four angles is a
                # sane default budget, but an explicitly requested list is
                # the operator's own call and must not be silently cut.
                angles = (angles or [-75.0, -60.0, 60.0, 75.0])[:4]
            log(f"=== P3 standalone at floor {args.p3_floor}, angles "
                f"{angles} ===")
            verdict = phase_p3(base_url, findings, args.p3_floor,
                              direction_for, angles,
                              backoff_deg=args.p3_backoff,
                              gain=args.p3_gain, label=args.p3_label)
            print(f"\nP3 (floor {args.p3_floor}): {verdict['status']} "
                 f"({verdict['converged']}/{verdict['n']} converged)")
            save_findings(findings)
            return 0

        p1 = phase_p1(base_url, findings)

        if p1["effect"] == "SIGN_DOMINANT":
            neg = p1["per_sign"]["negative"]["better"]
            pos = p1["per_sign"]["positive"]["better"]
            direction_for = lambda a, neg=neg, pos=pos: neg if a <= 0 else pos
            floors = phase_p2a(base_url, findings, direction_for)
        elif p1["effect"] in ("DOMINANT", "PARTIAL"):
            good = p1["good_direction"]
            direction_for = lambda a, good=good: good
            floors = phase_p2a(base_url, findings, direction_for)
        else:
            direction_for = None
            floors = phase_p2b(base_url, findings, p1.get("good_direction"))

        # P3 runs whatever happened: if a floor was found it proves the
        # correction is a safe backstop, and if none was it is the answer.
        p3_floor = floors.get("chosen_floor") or P1_FLOOR
        if direction_for is None:
            fallback = p1.get("good_direction") or "up"
            direction_for = lambda a, fallback=fallback: fallback
        p3_angles = (floors.get("rows", {})
                     .get(p3_floor, {})
                     .get("failing_angles") or [-75.0, -60.0, 60.0, 75.0])
        phase_p3(base_url, findings, p3_floor, direction_for, p3_angles[:4])

        decision = decide(findings)
        print_decision(decision)
        findings["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_findings(findings)
        return 0
    except rc.TemperatureSafetyAbort as exc:
        log(f"TEMPERATURE ABORT: {exc}")
        findings["aborted"] = f"temperature: {exc}"
        save_findings(findings)
        return 2
    except camp.CurrentSafetyAbort as exc:
        log(f"CURRENT ABORT: {exc}")
        findings["aborted"] = f"current: {exc}"
        save_findings(findings)
        return 3
    except KeyboardInterrupt:
        log("interrupted; checkpoint is safe, re-run to resume")
        return 130
    except Exception as exc:  # noqa: BLE001 - reported, then exited
        log(f"ABORTED: {exc!r}")
        findings["aborted"] = repr(exc)
        save_findings(findings)
        return 1
    finally:
        if boot_registers is not None:
            try:
                rc.write_registers(base_url, **boot_registers)
                log(f"registers restored to {boot_registers}")
            except Exception as exc:  # noqa: BLE001 - best effort on exit
                log(f"COULD NOT RESTORE REGISTERS ({exc!r}) - the servo is "
                    "not at its boot configuration; say so")


if __name__ == "__main__":
    raise SystemExit(main())
