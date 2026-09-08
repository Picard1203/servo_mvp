#!/usr/bin/env python3
"""Randomised-block settling-jitter campaign, driven end to end by the tool.

Why this exists rather than another sweep. The previous campaign ran each
configuration as one contiguous block, and re-analysis of its own archive
showed the machine's behaviour changes over hours: the same angle, anchor
and registers gave 33 reversals early in a session and 0 reversals hours
later. Any comparison whose arms ran at different times is confounded with
that drift, which is the simplest explanation for a run of results that
would not replicate.

So every comparison here is a randomised complete block design: one
"replicate" contains every arm exactly once, in a fresh random order, and
replicates repeat. Drift lands on the block, not on an arm. A baseline arm
rides along inside each comparison as a control chart, so drift is measured
rather than assumed away, and servo temperature is recorded per trial as a
covariate.

The other thing that changed: the previous campaign never passed a poll
interval to the probe, so every one of its trials silently used the 0.08s
default (~10Hz) no matter how carefully the fast USB path had been built.
Here the rate is explicit, verified against a floor before any trial runs,
and recorded per trial.

This tool is written to be run by an agent, not read and improvised on.
Every gate is computed here and written to the findings file as an explicit
verdict; nothing downstream requires the runner to judge a result.

    python3 tools/d48_s26_campaign.py --restart-app   # first run of the day
    python3 tools/d48_s26_campaign.py                 # all blocks in order
    python3 tools/d48_s26_campaign.py --only b5       # one block

Resuming needs no flag. Every trial is checkpointed as it completes, and a
re-run picks up at the first trial that has no result yet, so an interrupted
run costs only the trial that was in flight.
"""

import argparse
import json
import math
import os
import random
import sys
import time
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jitter_probe as jp
import resonance_campaign as rc

LABEL = "d48_s26b"
FINDINGS_PATH = os.path.join(jp.ARCHIVE_DIR, "d48_s26_findings.json")

# Poll intervals for the instrument arm. The fast one is what the mechanism
# read was taken at; the slow one is what the previous campaign used by
# accident, kept here as a real arm so the difference is measured, not argued.
FAST_POLL_SECONDS = 0.010
SLOW_POLL_SECONDS = 0.096
MIN_FAST_HZ = 40.0

CANDIDATE_ANGLES = (-60.0, -45.0, 45.0, 60.0)
QUIET_ANGLES = (0.0, -15.0, 15.0)
DEFAULT_ANCHOR = 0.0

# Factory-adjacent starting point, read from the servo at session start and
# restored on exit. These are only the fallback if the read fails.
FALLBACK_BASELINE = {
    "position_p": 24, "position_d": 32, "position_i": 0,
    "min_start_force": 150, "cw_dead_zone": 1, "ccw_dead_zone": 1,
    "speed_p": 10, "speed_i": 200,
}

SCREEN_N = 6
CONFIRM_N = 16
RESCREEN_N = 12
PROMOTE_AT_OR_BELOW = 1
DROP_AT_OR_ABOVE = 4
ACCEPT_BAR_FAILURES = 1
ACCEPT_BAR_N = 10

# A runaway guard, not a wear limit: these registers are rated
# far beyond anything a session can reach. It exists so a loop
# that rewrites needlessly is caught rather than left running.
EEPROM_WRITE_BUDGET = 5000

# Retreat here before cooling: measured holding current at 0 deg was
# ~0.0001A, against ~0.036A at the worst angle.
COOLDOWN_SAFE_ANGLE_DEG = 0.0

# Guards for the deliberately over-driven arms of the minimum-drive sweep.
# Normal oscillation sits at 0.03-0.08A mean, so these are several times
# anything measured so far, not a tight limit.
MAX_SAFE_MEAN_CURRENT_A = 0.35
MAX_SAFE_PEAK_CURRENT_A = 0.90

# The minimum-drive floor runs 0-1000 in the register, but this sweep only
# ever goes DOWNWARD from the established baseline. That is a safety
# invariant, not a preference.
#
# An earlier attempt included 300 and 500. At 500 the servo drove a 1-count
# error with half of full output through a ~345:1 reduction; the overshoot
# injected more energy per half-cycle than friction removed, so the
# oscillation diverged instead of settling, and the resulting current draw
# corrupted the serial bus. Every safety guard here reads the servo to
# decide - current, temperature, register readback - so a servo violent
# enough to jam its own bus defeats all of them at once, including the
# restore-on-exit that should have undone the damage. The value stayed in
# EEPROM through a power cut.
#
# Sweeping downward only makes a stranded value strictly safer than the
# baseline, so the worst case of a failed restore is a servo that pushes
# too gently rather than one that tears at the rig. The upward direction
# has already answered its question and does not need asking again.
MIN_START_FORCE_LEVELS = (0, 10, 20, 30, 40, 55, 70, 85, 100, 115, 130, 150)

# Hard ceiling enforced on every write, whatever a block asks for.
MAX_WRITABLE_MIN_START_FORCE = 150

# Ceilings on the calibrated outcome thresholds. See where they are applied.
R_MAX_CEILING = 5
C_MAX_CEILING_A = 0.015

# An angle is a usable test point only if it reproduces this often in
# screening. Declared before the run so the choice is not made by eye.
MIN_REPRODUCTION = 4


def log(msg: str) -> None:
    """Prints a timestamped line.

    Args:
        msg (str): Message to print.
    """
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# --------------------------------------------------------------------------
# findings persistence
# --------------------------------------------------------------------------

def load_findings() -> dict:
    """Reads the findings file, tolerating a missing or truncated one.

    Returns:
        dict: Findings so far, or a fresh dict.
    """
    if not os.path.exists(FINDINGS_PATH):
        return {"trials": {}, "gates": {}, "eeprom_writes": 0}
    try:
        with open(FINDINGS_PATH, encoding="utf-8") as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError) as exc:
        log(f"findings unreadable ({exc!r}); starting fresh")
        return {"trials": {}, "gates": {}, "eeprom_writes": 0}


def save_findings(findings: dict) -> None:
    """Writes the findings file atomically.

    A plain in-place write raced with this filesystem's write-back caching
    and produced a truncated file at least once, so the write goes to a
    temporary file, is flushed to disk, then renamed over the target.

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
# statistics
# --------------------------------------------------------------------------

def fisher_exact_one_sided(a: int, b: int, c: int, d: int) -> float:
    """One-sided Fisher exact p-value for a 2x2 table.

    Tests whether the first row has fewer "events" than the second, which
    is the direction every hypothesis here predicts (a fix reduces
    oscillation). Implemented directly so the tool needs no scientific
    Python stack on the board-facing workstation.

    Args:
        a (int): Events in group 1.
        b (int): Non-events in group 1.
        c (int): Events in group 2.
        d (int): Non-events in group 2.

    Returns:
        float: Probability of a table at least this extreme.
    """
    n = a + b + c + d
    row1, col1 = a + b, a + c

    def hypergeom(k: int) -> float:
        if k < 0 or k > row1 or (col1 - k) < 0 or (col1 - k) > (c + d):
            return 0.0
        return (math.comb(row1, k) * math.comb(n - row1, col1 - k)
                / math.comb(n, col1))

    return sum(hypergeom(k) for k in range(a + 1))


def summarise(trials: list[dict], r_max: Optional[int],
              c_max: Optional[float]) -> dict:
    """Reduces a list of trials to the numbers the gates read.

    Args:
        trials (list[dict]): Recorded trial results.
        r_max (Optional[int]): Reversal threshold, or None if uncalibrated.
        c_max (Optional[float]): Current threshold, or None if uncalibrated.

    Returns:
        dict: n, oscillating count and rate, and median period/current.
    """
    n = len(trials)
    osc = sum(1 for t in trials if is_oscillating(t, r_max, c_max))
    periods = [t["median_period_s"] for t in trials
               if t.get("median_period_s")]
    currents = [t.get("current_mean_a") or 0.0 for t in trials]
    temps = [t["temperature_c_mean"] for t in trials
             if t.get("temperature_c_mean") is not None]
    return {
        "n": n,
        "oscillating": osc,
        "rate": (osc / n) if n else None,
        "median_period_s": _median(periods),
        "period_stdev_s": _stdev(periods),
        "mean_current_a": (sum(currents) / n) if n else None,
        "mean_temperature_c": (sum(temps) / len(temps)) if temps else None,
    }


def _median(values: list[float]) -> Optional[float]:
    """Returns the median, or None for an empty list.

    Args:
        values (list[float]): Sample values.

    Returns:
        Optional[float]: Median, or None.
    """
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _stdev(values: list[float]) -> Optional[float]:
    """Returns the population standard deviation, or None for <2 values.

    Args:
        values (list[float]): Sample values.

    Returns:
        Optional[float]: Standard deviation, or None.
    """
    if len(values) < 2:
        return None
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / len(values))


def is_oscillating(trial: dict, r_max: Optional[int],
                   c_max: Optional[float]) -> bool:
    """Applies the pre-registered outcome definition to one trial.

    Current is the rate-robust half of this test: it is a mean over
    samples rather than an edge count, so it does not depend on how fast
    the trial was polled.

    Args:
        trial (dict): One recorded trial.
        r_max (Optional[int]): Reversal threshold.
        c_max (Optional[float]): Current threshold in amps.

    Returns:
        bool: True when the trial counts as oscillating.
    """
    if r_max is None or c_max is None:
        return bool(trial.get("reversals", 0) > 3)
    return (trial.get("reversals", 0) > r_max
            or (trial.get("current_mean_a") or 0.0) > c_max)


# --------------------------------------------------------------------------
# hardware interaction
# --------------------------------------------------------------------------

def read_registers(base_url: str) -> dict:
    """Reads every tuning register the API exposes.

    Args:
        base_url (str): API base URL.

    Returns:
        dict: Register values keyed by name.
    """
    return jp.get(base_url, "/servo/diagnostics/tuning_registers")


def apply_config(base_url: str, config: dict, findings: dict) -> None:
    """Writes a full register set and verifies it by readback.

    Every field is written on every application, including the ones that
    did not change. Holding the write ritual constant across arms means an
    arm differs only in the register *value* - otherwise the baseline arm
    would be the only one that never paid the cost of a write.

    Args:
        base_url (str): API base URL.
        config (dict): Register values to write.
        findings (dict): Findings, for the EEPROM write counter.

    Raises:
        RuntimeError: If the readback disagrees with what was written, or
            the write budget is exhausted.
    """
    floor = config.get("min_start_force")
    if floor is not None and floor > MAX_WRITABLE_MIN_START_FORCE:
        raise RuntimeError(
            f"refusing to write min_start_force={floor}: the ceiling is "
            f"{MAX_WRITABLE_MIN_START_FORCE}. Values above it have been "
            "measured to drive the servo into a divergent oscillation that "
            "jams the bus and defeats every read-based safety guard.")
    if findings.get("eeprom_writes", 0) + len(config) > EEPROM_WRITE_BUDGET:
        raise RuntimeError(
            f"EEPROM write budget {EEPROM_WRITE_BUDGET} exhausted; stopping "
            "rather than continuing to wear the register bank")
    rc.write_registers(base_url, **config)
    findings["eeprom_writes"] = findings.get("eeprom_writes", 0) + len(config)
    time.sleep(0.3)
    got = read_registers(base_url)
    mismatched = {k: (v, got.get(k)) for k, v in config.items()
                  if got.get(k) != v}
    if mismatched:
        raise RuntimeError(f"register readback mismatch: {mismatched}")


def apply_config_resilient(base_url: str, config: dict, findings: dict,
                           attempts: int = 3) -> None:
    """Applies a config, reconnecting once per failed attempt.

    Args:
        base_url (str): API base URL.
        config (dict): Register values to write.
        findings (dict): Findings, for the EEPROM write counter.
        attempts (int): How many times to try.

    Raises:
        RuntimeError: If every attempt fails.
    """
    last: Optional[Exception] = None
    for _ in range(attempts):
        try:
            apply_config(base_url, config, findings)
            return
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised
            last = exc
            log(f"register write failed ({exc!r}); reconnecting")
            if not rc.reconnect(base_url):
                break
    raise RuntimeError(f"apply_config exhausted retries: {last!r}")


def cooldown_at_safe_angle(base_url: str) -> None:
    """Retreats to a resting angle before waiting for the servo to cool.

    The shared cooldown waits wherever the servo happens to be, which during
    this investigation is the angle that is oscillating - and an oscillating
    servo draws current continuously, so it barely cools at all. Holding
    current at 0 deg measured ~0.0001A against ~0.036A at the worst angle, so
    retreating first is the difference between resting and simmering.

    Args:
        base_url (str): API base URL.
    """
    state = jp.get(base_url, "/servo/state")
    temp = state.get("temperature_c")
    if temp is None or temp < rc.COOLDOWN_TRIGGER_C:
        return
    log(f"temperature_c={temp}: retreating to {COOLDOWN_SAFE_ANGLE_DEG} deg "
        "before cooling, so the servo actually rests")
    try:
        jp.reset_to(base_url, COOLDOWN_SAFE_ANGLE_DEG,
                    poll_seconds=FAST_POLL_SECONDS)
    except Exception as exc:  # noqa: BLE001 - cooling still matters
        log(f"could not retreat ({exc!r}); cooling in place")
    rc.wait_for_cooldown(base_url)


def check_current_safety(result: dict, arm: str) -> None:
    """Aborts an over-driven configuration before it can cook the servo.

    Raising the minimum-drive floor deliberately makes the servo push harder
    whenever it is off target. That is the point of the sweep, but it also
    means a high arm can sit at a large continuous current, so this is a
    guard the earlier blocks never needed.

    Args:
        result (dict): One probe result.
        arm (str): Arm name, for the message.

    Raises:
        CurrentSafetyAbort: If the trial drew more than the safe mean.
    """
    mean = result.get("current_mean_a") or 0.0
    peak = result.get("current_peak_a") or 0.0
    if mean > MAX_SAFE_MEAN_CURRENT_A or peak > MAX_SAFE_PEAK_CURRENT_A:
        raise CurrentSafetyAbort(
            f"arm {arm} drew mean={mean:.3f}A peak={peak:.3f}A, above the "
            f"{MAX_SAFE_MEAN_CURRENT_A}/{MAX_SAFE_PEAK_CURRENT_A}A guard - "
            "stopping rather than driving the servo this hard unattended")


class CurrentSafetyAbort(Exception):
    """Raised when a configuration draws more current than is safe."""


def probe_resilient(base_url: str, target_deg: float, tag: str, repeat: int,
                    anchor_deg: float, poll_seconds: float,
                    window_seconds: float,
                    acceleration: Optional[int] = None,
                    attempts: int = 3) -> dict:
    """One scored trial, with the safety checks and a reconnect retry.

    Unlike the previous campaign's wrapper this passes the poll interval
    through, so the rate the caller asked for is the rate that is used.

    Args:
        base_url (str): API base URL.
        target_deg (float): Scored target angle.
        tag (str): Arm label recorded with the trial.
        repeat (int): 1-based repeat number.
        anchor_deg (float): Angle to reset to before the scored move.
        poll_seconds (float): Interval between reads.
        window_seconds (float): Observation window after the move.
        acceleration (Optional[int]): Per-move ramp, or None for default.
        attempts (int): How many times to try.

    Returns:
        dict: The probe result.

    Raises:
        RuntimeError: If every attempt fails.
    """
    rc.check_temperature_safety(base_url)
    cooldown_at_safe_angle(base_url)
    last: Optional[Exception] = None
    for _ in range(attempts):
        try:
            result = jp.probe(base_url, target_deg, LABEL, tag, repeat,
                              poll_seconds=poll_seconds, anchor_deg=anchor_deg,
                              window_seconds=window_seconds,
                              acceleration=acceleration)
            check_current_safety(result, tag)
            return result
        except (rc.TemperatureSafetyAbort, CurrentSafetyAbort):
            raise
        except Exception as exc:  # noqa: BLE001 - retried, then re-raised
            last = exc
            log(f"trial failed ({exc!r}); reconnecting")
            if not rc.reconnect(base_url):
                break
    raise RuntimeError(f"probe exhausted retries: {last!r}")


def hold_trial(base_url: str, angle_deg: float, seconds: float,
               poll_seconds: float) -> dict:
    """Parks at an angle and measures holding current without commanding a move.

    A gravity or load asymmetry shows up as a difference in the current the
    servo needs just to stay put. A drivetrain this heavily geared may need
    none at all, which is itself the answer.

    Args:
        base_url (str): API base URL.
        angle_deg (float): Angle to hold.
        seconds (float): How long to observe.
        poll_seconds (float): Interval between reads.

    Returns:
        dict: Mean/peak current, mean temperature and sample count.
    """
    rc.check_temperature_safety(base_url)
    jp.reset_to(base_url, angle_deg, poll_seconds=poll_seconds)
    currents: list[float] = []
    temps: list[float] = []
    t0 = time.time()
    while time.time() - t0 < seconds:
        state = jp.get(base_url, "/servo/state")
        if state.get("current_a") is not None:
            currents.append(state["current_a"])
        if state.get("temperature_c") is not None:
            temps.append(state["temperature_c"])
        time.sleep(poll_seconds)
    return {
        "angle_deg": angle_deg,
        "n": len(currents),
        "mean_current_a": (sum(currents) / len(currents)) if currents else None,
        "peak_current_a": max(currents) if currents else None,
        "mean_temperature_c": (sum(temps) / len(temps)) if temps else None,
    }


# --------------------------------------------------------------------------
# the randomised block runner
# --------------------------------------------------------------------------

def run_block(base_url: str, findings: dict, block_key: str,
              arms: dict, replicates: int, target_deg: float,
              anchor_deg: float = DEFAULT_ANCHOR,
              poll_seconds: float = FAST_POLL_SECONDS,
              window_seconds: float = jp.WINDOW_SECONDS,
              arm_filter: Optional[Callable[[dict, str], bool]] = None,
              ) -> dict:
    """Runs one randomised complete block design and checkpoints per trial.

    Each replicate runs every arm exactly once in a fresh random order, so
    any drift over the run is shared across arms instead of landing on
    whichever arm happened to run late.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings, updated and persisted per trial.
        block_key (str): Key under findings["trials"] for this block.
        arms (dict): Arm name to spec. A spec may carry "registers" (a dict
            written before the trial), "acceleration", "poll_seconds" and
            "target_deg" overrides.
        replicates (int): How many times to run every arm.
        target_deg (float): Default scored target angle.
        anchor_deg (float): Angle to reset to before each scored move.
        poll_seconds (float): Default poll interval.
        window_seconds (float): Observation window.
        arm_filter (Optional[Callable]): Called before each replicate with
            the block so far and an arm name; returning False retires that
            arm for the rest of the block. Retiring settled arms is what
            lets a promoted arm reach a confirmatory sample size without
            spending trials on arms already known to be futile.

    Returns:
        dict: The block's trials keyed by arm name.
    """
    block = findings["trials"].setdefault(block_key, {})
    for arm in arms:
        block.setdefault(arm, [])

    for replicate in range(1, replicates + 1):
        order = [a for a in arms
                 if arm_filter is None or arm_filter(block, a)]
        if not order:
            log(f"  every arm in {block_key} retired; block complete")
            break
        random.shuffle(order)
        for arm in order:
            if len(block[arm]) >= replicate:
                continue        # already recorded before a stop; resume past it
            spec = arms[arm]
            if spec.get("registers"):
                apply_config_resilient(base_url, spec["registers"], findings)
            result = probe_resilient(
                base_url,
                spec.get("target_deg", target_deg),
                f"{block_key}__{arm}",
                replicate,
                spec.get("anchor_deg", anchor_deg),
                spec.get("poll_seconds", poll_seconds),
                spec.get("window_seconds", window_seconds),
                acceleration=spec.get("acceleration"))
            achieved = result.get("achieved_hz", 0.0)
            if spec.get("poll_seconds", poll_seconds) <= FAST_POLL_SECONDS \
                    and achieved < MIN_FAST_HZ:
                raise RuntimeError(
                    f"fast path degraded: {achieved:.1f}Hz below the "
                    f"{MIN_FAST_HZ}Hz floor. Rebuild the USB bridge before "
                    "continuing; do not let trials run at the slow rate.")
            block[arm].append({
                "replicate": replicate,
                "reversals": result["reversals"],
                "median_period_s": result["median_period_s"],
                "period_stdev_s": result["period_stdev_s"],
                "current_mean_a": result["current_mean_a"],
                "current_peak_a": result.get("current_peak_a"),
                "drive_duty": result.get("drive_duty"),
                "current_on_target_a": result.get("current_on_target_a"),
                "swing_deg": result.get("swing_deg"),
                "final_error_deg": result["final_error_deg"],
                "settled_short": result["settled_short"],
                "achieved_hz": achieved,
                "temperature_c_mean": result.get("temperature_c_mean"),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                # Only where a block needs to re-score the same trace over a
                # different window; a full trace per trial would bloat the
                # findings file for no gain elsewhere.
                **({"trace": result.get("trace")}
                   if spec.get("keep_trace") else {}),
            })
            save_findings(findings)
            log(f"  {block_key}/{arm} rep {replicate}: "
                f"reversals={result['reversals']} "
                f"current={result['current_mean_a']} "
                f"period={result['median_period_s']} "
                f"{achieved:.0f}Hz")
    return block


def screening_arm_filter(r_max: Optional[int], c_max: Optional[float],
                         baseline_arm: str
                         ) -> Callable[[dict, str], bool]:
    """Builds the pre-declared promote / drop / re-screen rule.

    Applied per arm, before each replicate:
      - the in-block baseline always keeps running, so the control chart
        spans the whole block;
      - below the screening size, everything runs;
      - an arm that oscillated on nearly every screening trial is futile
        and retires - there is nothing to confirm;
      - an arm that looks like a fix is promoted and runs to a
        confirmatory sample size;
      - anything in between gets one more screening round, then is judged
        on the same rule rather than by eye.

    Args:
        r_max (Optional[int]): Reversal threshold.
        c_max (Optional[float]): Current threshold.
        baseline_arm (str): Arm that must never retire.

    Returns:
        Callable: Arm filter usable by run_block.
    """
    def keep(block: dict, arm: str) -> bool:
        trials = block.get(arm, [])
        done = len(trials)
        if arm == baseline_arm:
            return done < CONFIRM_N
        if done < SCREEN_N:
            return True
        osc = summarise(trials[:SCREEN_N], r_max, c_max)["oscillating"]
        if osc >= DROP_AT_OR_ABOVE:
            return False                      # futile
        if osc <= PROMOTE_AT_OR_BELOW:
            return done < CONFIRM_N           # promoted, confirm it
        return done < RESCREEN_N              # ambiguous, one more round
    return keep


# --------------------------------------------------------------------------
# blocks
# --------------------------------------------------------------------------

def preflight(base_url: str, findings: dict) -> None:
    """Verifies the path, the firmware and the starting registers.

    The velocity-loop fields only exist if the sketch on the board carries
    them, so this doubles as an end-to-end check that the board is running
    the current firmware rather than a stale build.

    Records into `findings` but deliberately does not persist it: this
    module's own path is the wrong destination for a caller that keeps its
    findings somewhere else, and writing it there once destroyed a whole
    day of results. The caller saves, to whichever path it owns.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to record the baseline into.

    Raises:
        RuntimeError: If the firmware or the fast path is not usable.
    """
    log("=== preflight ===")
    registers = read_registers(base_url)
    if registers.get("speed_p") is None or registers.get("speed_i") is None:
        raise RuntimeError(
            "the board does not report speed_p/speed_i. The sketch is stale: "
            "restart the app so it recompiles, then re-run. Do not continue.")
    log(f"registers at start: {registers}")
    # A partial read would otherwise become a partial restore set on exit,
    # silently leaving the servo somewhere other than where it started.
    baseline = dict(FALLBACK_BASELINE)
    baseline.update({k: v for k, v in registers.items()
                     if k in FALLBACK_BASELINE and v is not None})
    missing = [k for k in FALLBACK_BASELINE if registers.get(k) is None]
    if missing:
        log(f"WARNING: could not read {missing}; using documented defaults "
            "for those. Say so in the handback.")
        findings["baseline_read_gaps"] = missing
    findings.setdefault("baseline_registers", baseline)

    achieved = measure_rate(base_url)
    log(f"achieved {achieved:.1f}Hz on /servo/state")
    if achieved < MIN_FAST_HZ:
        log("below the floor; rebuilding the USB bridge and retrying once")
        try:
            rc.ensure_socat(rc.get_container_ip())
        except Exception as exc:  # noqa: BLE001 - reported below
            log(f"bridge rebuild failed: {exc!r}")
        achieved = measure_rate(base_url)
        log(f"after rebuild: {achieved:.1f}Hz")
    findings["preflight_hz"] = round(achieved, 1)
    if achieved < MIN_FAST_HZ:
        raise RuntimeError(
            f"only {achieved:.1f}Hz, below the {MIN_FAST_HZ}Hz floor, and "
            "rebuilding the bridge did not fix it. Stop and report. A silent "
            "fall back to the slow path is the exact defect this campaign "
            "exists to avoid, so the run must not continue.")


def measure_rate(base_url: str, samples: int = 50) -> float:
    """Measures the achievable read rate on the state endpoint.

    Args:
        base_url (str): API base URL.
        samples (int): How many reads to time.

    Returns:
        float: Reads per second.
    """
    t0 = time.time()
    for _ in range(samples):
        jp.get(base_url, "/servo/state")
    elapsed = time.time() - t0
    return samples / elapsed if elapsed > 0 else 0.0


def block_b0(base_url: str, findings: dict) -> None:
    """Picks today's test angle, calibrates thresholds and tests poll rate.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B0: target selection, threshold calibration, instrument ===")
    baseline = findings["baseline_registers"]

    arms = {}
    for angle in CANDIDATE_ANGLES:
        for rate, name in ((FAST_POLL_SECONDS, "fast"),
                           (SLOW_POLL_SECONDS, "slow")):
            arms[f"{angle:+.0f}_{name}"] = {
                "target_deg": angle, "poll_seconds": rate,
            }
    # No arm here varies a register, so the register set is applied once for
    # the whole block rather than rewritten before every trial.
    apply_config_resilient(base_url, baseline, findings)
    block = run_block(base_url, findings, "b0", arms, replicates=4,
                      target_deg=CANDIDATE_ANGLES[0])

    quiet_arms = {f"quiet_{a:+.0f}": {"target_deg": a} for a in QUIET_ANGLES}
    quiet = run_block(base_url, findings, "b0_quiet", quiet_arms,
                      replicates=3, target_deg=QUIET_ANGLES[0])

    quiet_trials = [t for trials in quiet.values() for t in trials]
    r_max = max((t["reversals"] for t in quiet_trials), default=3)
    worst_quiet_current = max(
        ((t["current_mean_a"] or 0.0) for t in quiet_trials), default=0.0)
    c_max = max(0.010, worst_quiet_current * 1.5)
    # A purely empirical floor trusts the quiet angles to be quiet, and in
    # the first run one of them was not: it oscillated during calibration
    # and dragged the thresholds up to 20 reversals and 0.053A, lenient
    # enough to score a plainly oscillating trial as clean. The measured
    # populations are far apart - settled trials read 0.000A and 0.000 deg
    # of swing, oscillating ones 0.03A and up - so a ceiling costs no real
    # discrimination and stops one bad calibration angle from silently
    # widening the bar.
    r_max, c_max = min(r_max, R_MAX_CEILING), min(c_max, C_MAX_CEILING_A)
    findings["r_max"] = r_max
    findings["c_max"] = round(c_max, 4)
    log(f"thresholds locked from quiet angles: R_max={r_max} "
        f"C_max={c_max:.4f}A")

    per_angle = {}
    for angle in CANDIDATE_ANGLES:
        trials = (block[f"{angle:+.0f}_fast"] + block[f"{angle:+.0f}_slow"])
        per_angle[f"{angle:+.0f}"] = summarise(trials, r_max, c_max)
    findings["b0_per_angle"] = per_angle

    best = max(per_angle.items(), key=lambda kv: kv[1]["oscillating"])
    if best[1]["oscillating"] < MIN_REPRODUCTION:
        findings["gates"]["target_angle"] = {
            "verdict": "NO_REPRODUCTION",
            "evidence": per_angle,
            "directive": (
                "No candidate angle reproduced often enough. Do not proceed "
                "to register blocks. Run --only b0_wide, and if that also "
                "finds nothing, stop and hand back: the fault is "
                "state-dependent and register hunting cannot be interpreted."),
        }
        save_findings(findings)
        return
    findings["test_angle"] = float(best[0])
    findings["gates"]["target_angle"] = {
        "verdict": "SELECTED", "angle": float(best[0]), "evidence": per_angle}

    fast = [t for a in CANDIDATE_ANGLES for t in block[f"{a:+.0f}_fast"]]
    slow = [t for a in CANDIDATE_ANGLES for t in block[f"{a:+.0f}_slow"]]
    fs, ss = summarise(fast, r_max, c_max), summarise(slow, r_max, c_max)
    p = fisher_exact_one_sided(
        ss["oscillating"], ss["n"] - ss["oscillating"],
        fs["oscillating"], fs["n"] - fs["oscillating"])
    if ss["rate"] is not None and ss["rate"] <= 0.15 and fs["rate"] >= 0.6:
        verdict, directive = "FAIL", (
            "Oscillation is largely absent when not polling fast. Our own "
            "instrument is implicated. Stop after B1 and B2 and hand back; "
            "do NOT run the register blocks.")
    elif p < 0.05:
        verdict, directive = "PARTIAL", (
            "Poll rate shifts severity but oscillation occurs at both rates. "
            "Proceed at the fast rate; report the rate with every result.")
    else:
        verdict, directive = "PASS", (
            "No poll-rate effect. Proceed at the fast rate.")
    findings["gates"]["g1"] = {
        "verdict": verdict, "p_one_sided": round(p, 4),
        "fast": fs, "slow": ss, "directive": directive}
    log(f"G1 {verdict} (p={p:.4f}) fast_rate={fs['rate']} slow_rate={ss['rate']}")
    save_findings(findings)


def block_b1(base_url: str, findings: dict) -> None:
    """Tests whether the oscillation persists or decays over a long window.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B1: persistence over a 60s window ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    arms = {"persistence": {"window_seconds": 60.0, "keep_trace": True}}
    apply_config_resilient(base_url, findings["baseline_registers"], findings)
    block = run_block(base_url, findings, "b1", arms, replicates=5,
                      target_deg=angle, window_seconds=60.0)

    # The default scoring window is 5-15s, so scoring a 60s trace with it
    # would report the same early slice as every other trial and could only
    # ever say "persists". The comparison has to be early slice against late
    # slice of the same trace.
    pairs = findings.setdefault("b1_early_vs_late", [])
    if not pairs:
        for entry in block["persistence"]:
            trace = entry.get("trace")
            if not trace:
                continue
            early = jp.score_trial(trace, angle, 5.0, 15.0)
            late = jp.score_trial(trace, angle, 45.0, 60.0)
            pairs.append({
                "early_reversals": early["reversals"],
                "late_reversals": late["reversals"],
                "early_current_a": early["current_mean_a"],
                "late_current_a": late["current_mean_a"],
            })
        save_findings(findings)

    if not pairs:
        findings["gates"]["g2"] = {
            "verdict": "INCONCLUSIVE",
            "directive": "No 60s traces were captured; persistence untested.",
        }
    else:
        # Sustained means the late slice is still oscillating at a
        # comparable rate; decay means it has largely stopped by then.
        sustained = sum(
            1 for p in pairs
            if p["late_reversals"] >= 0.5 * max(p["early_reversals"], 1))
        decayed = len(pairs) - sustained
        findings["gates"]["g2"] = {
            "verdict": "PERSISTS" if sustained > decayed else "DECAYS",
            "evidence": {"pairs": pairs, "sustained": sustained,
                         "decayed": decayed},
            "directive": (
                "Self-sustaining: register and loop-gain work is the right "
                "remedy class."
                if sustained > decayed else
                "Decays: residual-energy remedies (a dwell before the final "
                "leg) become primary and register tuning secondary. Report "
                "this prominently - it changes the remedy class."),
        }
    log(f"G2 {findings['gates']['g2']['verdict']}")
    save_findings(findings)


def block_b2(base_url: str, findings: dict) -> None:
    """Measures holding current at rest, to test the load-asymmetry story.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B2: holding current at rest ===")
    holds = findings.setdefault("b2_holds", {})
    for angle in (0.0, -45.0, 45.0, -60.0, 60.0):
        key = f"{angle:+.0f}"
        for repeat in range(len(holds.get(key, [])), 3):
            result = hold_trial(base_url, angle, 20.0, FAST_POLL_SECONDS)
            holds.setdefault(key, []).append(result)
            save_findings(findings)
            log(f"  hold {key} rep {repeat + 1}: "
                f"mean_current={result['mean_current_a']}")
    means = {k: _median([h["mean_current_a"] or 0.0 for h in v])
             for k, v in holds.items()}
    pos = max(means.get("+60", 0.0), means.get("+45", 0.0))
    neg = max(means.get("-60", 0.0), means.get("-45", 0.0))
    asymmetric = abs(pos - neg) > 0.010
    findings["gates"]["h3"] = {
        "verdict": "ASYMMETRIC" if asymmetric else "SYMMETRIC",
        "evidence": means,
        "directive": (
            "Holding current differs by side: a gravity or load asymmetry is "
            "live. Keep the mechanical branch open."
            if asymmetric else
            "Holding current is symmetric and near zero. The gravity/load "
            "asymmetry explanation is not supported; the mechanical branch "
            "(re-datum, rig inversion, belt re-tension) can be dropped."),
    }
    log(f"H3 {findings['gates']['h3']['verdict']}: {means}")
    save_findings(findings)


def block_b3(base_url: str, findings: dict) -> None:
    """Acceleration ramp, predicted to do nothing. Costs no EEPROM writes.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B3: acceleration ramp ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    baseline = findings["baseline_registers"]
    apply_config_resilient(base_url, baseline, findings)
    arms = {"accel_default": {}}
    for value in (0, 10, 30, 100):
        arms[f"accel_{value}"] = {"acceleration": value}
    run_block(base_url, findings, "b3", arms, replicates=CONFIRM_N,
              target_deg=angle,
              arm_filter=screening_arm_filter(
                  findings.get("r_max"), findings.get("c_max"),
                  "accel_default"))
    _record_arm_comparison(findings, "b3", "accel_default")


def block_b4(base_url: str, findings: dict) -> None:
    """Position-loop P, which one competing diagnosis says sets the period.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B4: position-loop P ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    baseline = findings["baseline_registers"]
    arms = {"p_baseline": {"registers": baseline}}
    for value in (32, 16, 12):
        arms[f"p_{value}"] = {"registers": {**baseline, "position_p": value}}
    run_block(base_url, findings, "b4", arms, replicates=CONFIRM_N,
              target_deg=angle,
              arm_filter=screening_arm_filter(
                  findings.get("r_max"), findings.get("c_max"),
                  "p_baseline"))
    _record_arm_comparison(findings, "b4", "p_baseline")


def block_b5(base_url: str, findings: dict) -> None:
    """Velocity-loop integrator - the lever both research passes ranked first.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B5: velocity-loop I ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    if findings["gates"].get("g1", {}).get("verdict") == "FAIL":
        log("  G1 FAILed; the register programme is deferred. Skipping.")
        return
    baseline = findings["baseline_registers"]
    arms = {"i_baseline": {"registers": baseline}}
    for value in (100, 50, 25, 0):
        arms[f"i_{value}"] = {"registers": {**baseline, "speed_i": value}}
    run_block(base_url, findings, "b5", arms, replicates=CONFIRM_N,
              target_deg=angle,
              arm_filter=screening_arm_filter(
                  findings.get("r_max"), findings.get("c_max"),
                  "i_baseline"))
    _record_arm_comparison(findings, "b5", "i_baseline")


def block_b6(base_url: str, findings: dict) -> None:
    """Velocity-loop P.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B6: velocity-loop P ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    if findings["gates"].get("g1", {}).get("verdict") == "FAIL":
        log("  G1 FAILed; the register programme is deferred. Skipping.")
        return
    baseline = findings["baseline_registers"]
    arms = {"sp_baseline": {"registers": baseline}}
    for value in (20, 40):
        arms[f"sp_{value}"] = {"registers": {**baseline, "speed_p": value}}
    run_block(base_url, findings, "b6", arms, replicates=CONFIRM_N,
              target_deg=angle,
              arm_filter=screening_arm_filter(
                  findings.get("r_max"), findings.get("c_max"),
                  "sp_baseline"))
    _record_arm_comparison(findings, "b6", "sp_baseline")


def _record_arm_comparison(findings: dict, block_key: str,
                           baseline_arm: str) -> None:
    """Scores every arm against its in-block baseline and writes directives.

    The period comparison is the mechanism test and the proportion test is
    the fix test. They are reported separately because they answer different
    questions and need very different sample sizes.

    Args:
        findings (dict): Findings to update.
        block_key (str): Block whose arms to compare.
        baseline_arm (str): Name of the in-block control arm.
    """
    r_max, c_max = findings.get("r_max"), findings.get("c_max")
    block = findings["trials"].get(block_key, {})
    if baseline_arm not in block:
        return
    base = summarise(block[baseline_arm], r_max, c_max)
    results = {}
    for arm, trials in block.items():
        stats = summarise(trials, r_max, c_max)
        p = fisher_exact_one_sided(
            stats["oscillating"], stats["n"] - stats["oscillating"],
            base["oscillating"], base["n"] - base["oscillating"])
        period_shift = None
        if stats["median_period_s"] and base["median_period_s"]:
            period_shift = round(
                (stats["median_period_s"] - base["median_period_s"])
                / base["median_period_s"], 4)
        if arm == baseline_arm:
            status = "BASELINE"
        elif stats["n"] >= ACCEPT_BAR_N and \
                stats["oscillating"] <= ACCEPT_BAR_FAILURES:
            status = "MEETS_ACCEPTANCE_BAR"
        elif p < 0.05:
            status = "BETTER_THAN_BASELINE"
        elif stats["oscillating"] >= DROP_AT_OR_ABOVE:
            status = "FUTILE"
        else:
            status = "UNDECIDED"
        results[arm] = {**stats, "p_vs_baseline": float(f"{p:.6g}"),
                        "period_shift_vs_baseline": period_shift,
                        "status": status}
    findings.setdefault("comparisons", {})[block_key] = results
    save_findings(findings)
    for arm, stats in sorted(results.items()):
        log(f"  {arm}: {stats['oscillating']}/{stats['n']} oscillating, "
            f"period_shift={stats['period_shift_vs_baseline']}, "
            f"{stats['status']}")


def block_b7(base_url: str, findings: dict) -> None:
    """Minimum-drive floor, swept as a dose-response in both directions.

    Every gain the earlier blocks touched left the period, the drive current
    and the swing unchanged, which is what a loop whose output is dominated
    by a fixed minimum drive looks like: the proportional terms cannot matter
    while a floor is doing the pushing. That floor is `min_start_force`, held
    at 150 of a possible 1000 through every block so far and never varied.

    Sweeping below *and* above the current value is the point. A fix that
    only ever gets tested downward cannot distinguish "this lever is the
    cause" from "any change helps"; a monotonic relationship across the whole
    range can. The prediction is directional and specific: swing, drive duty
    and on-target current all rise with the floor, and fall away as it
    approaches zero.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B7: minimum-drive floor dose-response ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    baseline = findings["baseline_registers"]
    arms = {"msf_baseline_150": {"registers": baseline}}
    for value in MIN_START_FORCE_LEVELS:
        if value == baseline.get("min_start_force"):
            continue
        arms[f"msf_{value}"] = {
            "registers": {**baseline, "min_start_force": value}}
    run_block(base_url, findings, "b7", arms, replicates=SCREEN_N,
              target_deg=angle)
    _record_arm_comparison(findings, "b7", "msf_baseline_150")
    _record_dose_response(findings, "b7", "min_start_force")


def block_b8(base_url: str, findings: dict) -> None:
    """Dead zone crossed with the minimum-drive floor.

    The dead zone is currently 0, so a single count of error is enough to
    trigger the floor. Widening it should stop small errors from triggering
    anything at all - the same suppression from the other side of the same
    mechanism. The two have never been varied together.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B8: dead zone x minimum-drive floor ===")
    angle = findings.get("test_angle")
    if angle is None:
        log("  no test angle selected; skipping")
        return
    baseline = findings["baseline_registers"]
    best = findings.get("b7_best_min_start_force",
                        baseline.get("min_start_force"))
    arms = {}
    for msf in sorted({baseline.get("min_start_force"), best}):
        for dz in (0, 1, 2):
            arms[f"msf{msf}_dz{dz}"] = {"registers": {
                **baseline, "min_start_force": msf,
                "cw_dead_zone": dz, "ccw_dead_zone": dz}}
    run_block(base_url, findings, "b8", arms, replicates=SCREEN_N,
              target_deg=angle)
    control = f"msf{baseline.get('min_start_force')}_dz0"
    if control in arms:
        _record_arm_comparison(findings, "b8", control)


def _record_dose_response(findings: dict, block_key: str,
                          register: str) -> None:
    """Reports how the physical measures track a swept register value.

    "Settled" is decided by the same pass/fail proportion the rest of the
    tool uses (the Fisher-exact status `_record_arm_comparison` already
    wrote for this block, one arm at a time), not by a median swing. A
    median hides a coin flip: `min_start_force=85` read 3 clean / 3
    oscillating at N=6 in Session 26 and still passed the old median-based
    bar, then failed 4/6 when B8 re-tested it alone (see D48's own entry).
    Call `_record_arm_comparison` on this block before calling this.

    Args:
        findings (dict): Findings to update.
        block_key (str): Block to summarise.
        register (str): Register name, for the report.
    """
    block = findings["trials"].get(block_key, {})
    comparisons = findings.get("comparisons", {}).get(block_key, {})
    rows = {}
    for arm, trials in block.items():
        value = int(arm.rsplit("_", 1)[-1]) if arm.rsplit(
            "_", 1)[-1].isdigit() else None
        swings = [t["swing_deg"] for t in trials
                  if t.get("swing_deg") is not None]
        duties = [t["drive_duty"] for t in trials
                  if t.get("drive_duty") is not None]
        on_target = [t["current_on_target_a"] for t in trials
                     if t.get("current_on_target_a") is not None]
        errors = [abs(t["final_error_deg"]) for t in trials
                  if t.get("final_error_deg") is not None]
        stats = comparisons.get(arm, {})
        rows[arm] = {
            "value": value,
            "status": stats.get("status"),
            "oscillating": stats.get("oscillating"),
            "n": stats.get("n", len(trials)),
            "median_swing_deg": _median(swings),
            "median_drive_duty": _median(duties),
            "median_current_on_target_a": _median(on_target),
            "median_abs_final_error_deg": _median(errors),
        }
    findings.setdefault("dose_response", {})[block_key] = {
        "register": register, "rows": rows}

    ordered = [r for r in rows.values() if r["value"] is not None]
    ordered.sort(key=lambda r: r["value"])
    # Accuracy is the point, not just avoiding oscillation: among the values
    # that pass, the highest one holds the most torque against gravity and
    # so gives the smallest steady-state error. Picking the lowest safe value
    # instead would pass the same oscillation test while accepting more droop
    # for no reason.
    settled = [r for r in ordered
              if r["status"] in ("MEETS_ACCEPTANCE_BAR", "BETTER_THAN_BASELINE")]
    best = max(settled, key=lambda r: r["value"], default=None)
    if best is not None:
        findings[f"{block_key}_best_min_start_force"] = best["value"]
    save_findings(findings)
    log(f"  dose-response for {register} "
        f"(best = highest value passing on proportion, for accuracy):")
    log(f"    {'value':>6s} {'status':>20s} {'osc/n':>7s} {'swing_deg':>10s} "
        f"{'drive_duty':>11s} {'on_target_A':>12s} {'abs_err_deg':>12s}")
    for row in ordered:
        osc_n = (f"{row['oscillating']}/{row['n']}"
                if row["oscillating"] is not None else "-")
        log(f"    {row['value']:6d} {row['status'] or '-':>20s} "
            f"{osc_n:>7s} "
            f"{row['median_swing_deg'] or 0:10.3f} "
            f"{row['median_drive_duty'] or 0:11.2%} "
            f"{row['median_current_on_target_a'] or 0:12.4f} "
            f"{row['median_abs_final_error_deg'] or 0:12.3f}")


def block_b9(base_url: str, findings: dict) -> None:
    """Confirmatory re-test of B7's fine-bracket candidates, at real N.

    B7/B8 (and the fine-bracket sweep before this tool existed) screened at
    N=6 or fewer and picked a "best" `min_start_force` by median swing - the
    bug `_record_dose_response` no longer has. Nothing has actually run at
    the pre-registered confirmatory N (10-16) with a real pass/fail bar. The
    fine-bracket sweep favoured 40 and 45; both go head-to-head against the
    150 baseline here, at -60 deg (the angle every lever tried in Session 25
    and 26 failed to move at all) and +45 deg (one of the angles the 7-angle
    validation sweep found the baseline also fails), using the same
    sequential promote/drop/re-screen rule the gain-register blocks use so a
    clearly futile or clearly passing arm does not spend the full N.

    Args:
        base_url (str): API base URL.
        findings (dict): Findings to update.
    """
    log("=== B9: minimum-drive floor, confirmatory ===")
    baseline = findings["baseline_registers"]
    arms = {
        "baseline_150": {"registers": baseline},
        "msf_40": {"registers": {**baseline, "min_start_force": 40}},
        "msf_45": {"registers": {**baseline, "min_start_force": 45}},
    }
    for angle, suffix in ((-60.0, "m60"), (45.0, "p45")):
        block_key = f"b9_{suffix}"
        run_block(base_url, findings, block_key, arms, replicates=CONFIRM_N,
                  target_deg=angle,
                  arm_filter=screening_arm_filter(
                      findings.get("r_max"), findings.get("c_max"),
                      "baseline_150"))
        _record_arm_comparison(findings, block_key, "baseline_150")
        _record_dose_response(findings, block_key, "min_start_force")


BLOCKS = {"b0": block_b0, "b1": block_b1, "b2": block_b2,
          "b3": block_b3, "b4": block_b4, "b5": block_b5, "b6": block_b6,
          "b7": block_b7, "b8": block_b8, "b9": block_b9}


def main() -> int:
    """Parses arguments and runs the requested blocks in order.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--only", help="run just these blocks, comma separated")
    parser.add_argument("--seed", type=int, default=None,
                        help="fix the randomisation seed for reproducibility")
    parser.add_argument("--skip-preflight", action="store_true")
    parser.add_argument("--restart-app", action="store_true",
                        help="restart the board app first, which recompiles "
                             "the sketch; needed once after firmware changes")
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}/api/v1"
    if args.restart_app:
        log("restarting the board app so the sketch recompiles")
        rc.restart_app_and_wait(base_url)

    # Load before seeding: a resumed run must continue from the seed the run
    # started with, not draw a fresh one and then report the original.
    findings = load_findings()
    # Apply the threshold ceilings to anything carried over from an earlier
    # run too, not just to a fresh calibration - the first run's thresholds
    # were set by a "quiet" angle that was in fact oscillating.
    for key, ceiling in (("r_max", R_MAX_CEILING), ("c_max", C_MAX_CEILING_A)):
        if findings.get(key) is not None and findings[key] > ceiling:
            log(f"clamping carried-over {key} {findings[key]} -> {ceiling}")
            findings.setdefault("threshold_clamped", {})[key] = findings[key]
            findings[key] = ceiling
    seed = (args.seed if args.seed is not None
            else findings.get("seed", int(time.time())))
    random.seed(seed)
    findings["seed"] = seed
    findings["started_at"] = findings.get(
        "started_at", time.strftime("%Y-%m-%dT%H:%M:%S"))

    # Ordered by information value, not by block number: G1 needs only B0,
    # B1 and B2 are minutes, and B5 is the lever both research passes ranked
    # first. B3 is a predicted-null control and so is the cheapest to lose
    # if the session runs short.
    requested = (args.only.split(",") if args.only
                 else ["b7", "b8"])

    try:
        if not args.skip_preflight:
            preflight(base_url, findings)
            save_findings(findings)
        for name in requested:
            block = BLOCKS.get(name.strip())
            if block is None:
                log(f"unknown block {name!r}; skipping")
                continue
            block(base_url, findings)
    except rc.TemperatureSafetyAbort as exc:
        log(f"TEMPERATURE ABORT: {exc}")
        findings["aborted"] = f"temperature: {exc}"
        save_findings(findings)
        return 2
    except CurrentSafetyAbort as exc:
        log(f"CURRENT ABORT: {exc}")
        findings["aborted"] = f"current: {exc}"
        save_findings(findings)
        return 3
    except Exception as exc:  # noqa: BLE001 - reported, then exited
        log(f"ABORTED: {exc!r}")
        findings["aborted"] = repr(exc)
        save_findings(findings)
        return 1
    finally:
        baseline = findings.get("baseline_registers")
        if baseline:
            try:
                rc.write_registers(base_url, **baseline)
                log(f"registers restored to {baseline}")
            except Exception as exc:  # noqa: BLE001 - best effort on exit
                log(f"COULD NOT RESTORE REGISTERS ({exc!r}) - "
                    "say so in the handback; the servo is not at baseline")
        findings["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_findings(findings)
        log(f"findings written to {FINDINGS_PATH}")

    log("=== gate verdicts ===")
    for name, gate in findings.get("gates", {}).items():
        log(f"  {name}: {gate.get('verdict')} - {gate.get('directive', '')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
