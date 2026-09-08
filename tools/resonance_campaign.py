"""D48 Session 25: full unattended diagnosis + fix campaign.

Runs on top of tools/jitter_probe.py's measurement primitive (imported, not
duplicated). Session 24 characterised 11 angles at N=3 each and found the
result unreliable (Session 25 re-check: +45deg called "clean" at N=3 failed
8/10 at N=10). This script re-runs the full diagnosis at real statistical
power, then tests candidate fixes for the confirmed mechanism (M1:
quantisation-boundary loop hunting - Step 3, N=3 at +30deg, consistent
~0.267s reversal period, modest oscillating current) at a pre-registered
pass bar, then confirms and writes the winner.

Never call this unattended without reading its PHASE PLAN below first - it
drives real hardware for roughly 75-90 minutes and writes live tuning
registers and .env files, always restoring the documented baseline
(P=24 D=32 dead zone 0/0, FINE_APPROACH_FINAL_*=None, DEFAULT_SPEED_DPS=30)
if no configuration beats it.

Usage:
    python3 tools/resonance_campaign.py --host 127.0.0.1 --port 8001
"""
import argparse
import json
import math
import os
import subprocess
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jitter_probe as jp  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(REPO_ROOT, "python", ".env")
ENV_BOARD_PATH = os.path.join(REPO_ROOT, "python", ".env.board")
FINDINGS_PATH = os.path.join(jp.ARCHIVE_DIR, "d48_campaign_findings.json")

BASELINE_REGISTERS = {"position_p": 24, "position_d": 32}
SURVEY_ANGLES = [-90, -60, -45, -30, -15, 0, 15, 30, 45, 60, 90]
CLEAN_MAX_FAILURES = 1     # of 10: an angle with <=1 failure is "confirmed clean"
BAD_MIN_FAILURES = 3       # of 10: an angle with >=3 failures is "confirmed bad"

PASS_BAR_N = 10
PASS_BAR_MAX_FAILURES = 1  # pre-registered: pass if <=1 failure of 10


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def write_registers(base_url: str, **kwargs) -> dict:
    import urllib.request
    req = urllib.request.Request(
        f"{base_url}/servo/diagnostics/tuning_registers",
        data=json.dumps(kwargs).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def read_registers(base_url: str) -> dict:
    return jp.get(base_url, "/servo/diagnostics/tuning_registers")


def apply_registers(base_url: str, position_p: int, position_d: int) -> None:
    """Writes P/D and confirms by readback; raises if the board disagrees."""
    write_registers(base_url, position_p=position_p, position_d=position_d)
    time.sleep(0.3)
    got = read_registers(base_url)
    if got["position_p"] != position_p or got["position_d"] != position_d:
        raise RuntimeError(
            f"register readback mismatch: wrote P={position_p} D={position_d}, "
            f"read back {got}")


def apply_deadzone(base_url: str, cw: int, ccw: int) -> None:
    """Writes the CW/CCW dead-zone registers and confirms by readback.

    Deliberately kept separate from apply_registers (P/D) - dead zone was
    set to 0/0 on purpose (D40) to preserve accuracy, so every caller of
    this should know explicitly that it is touching that specific,
    consciously-made tradeoff, not folding it into the general register path.
    """
    write_registers(base_url, cw_dead_zone=cw, ccw_dead_zone=ccw)
    time.sleep(0.3)
    got = read_registers(base_url)
    if got["cw_dead_zone"] != cw or got["ccw_dead_zone"] != ccw:
        raise RuntimeError(
            f"dead-zone readback mismatch: wrote cw={cw} ccw={ccw}, "
            f"read back {got}")


def apply_deadzone_resilient(base_url: str, cw: int, ccw: int,
                              max_retries: int = 3) -> None:
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            apply_deadzone(base_url, cw, ccw)
            return
        except Exception as exc:
            last_exc = exc
            log(f"dead-zone write failed ({exc!r}), attempting reconnect before retry")
            if not reconnect(base_url):
                break
    raise RuntimeError(f"apply_deadzone_resilient exhausted retries: {last_exc!r}")


def outcome_fails(result: dict, r_max: int, c_max: float) -> bool:
    """Applies the pre-registered 3-condition FAIL rule."""
    if result["reversals"] > r_max:
        return True
    if result["settled_short"]:
        return True
    if result["current_mean_a"] is not None and result["current_mean_a"] > c_max:
        return True
    return False


OUTPUT_STEP_DEG = 0.06


def round_to_step(v: float, step: float = OUTPUT_STEP_DEG) -> float:
    """Snaps to the nearest valid commandable angle.

    The API rejects any target_deg that isn't a clean multiple of
    OUTPUT_STEP_DEG (python/app/services/motion_service.py's StepError) -
    an arithmetic offset like angle-5 lands on an arbitrary float, not
    necessarily a valid step, and gets refused with a 422.
    """
    return round(round(v / step) * step, 6)


def clamp(v: float, lo: float = -90.0, hi: float = 90.0) -> float:
    return round_to_step(max(lo, min(hi, v)))


def checkpoint(findings: dict) -> None:
    """Writes the findings dict to disk now, so a later crash loses nothing
    already recorded - the campaign's first real run (Session 25) lost all of
    Phase A's in-progress work to a physical bump that dropped the USB link.

    Writes to a temp file, fsyncs, then atomically renames over the real
    path - the working copy here is a CIFS mount with documented write-back
    caching quirks (this project's own CLAUDE.md flags it as suspect for
    file writes generally), and a plain in-place write already produced one
    silently truncated checkpoint this session (a reconstructed Phase A/A2
    result was found empty moments after being written and verified).
    """
    os.makedirs(jp.ARCHIVE_DIR, exist_ok=True)
    tmp_path = FINDINGS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp_path, FINDINGS_PATH)


def load_checkpoint(path: str) -> dict:
    """Loads a prior findings JSON to resume from, or {} if none/unreadable.

    A second run overwriting this same path without first loading it would
    silently destroy the first run's results - happened once already
    (Session 25: a restart clobbered a crashed run's already-valid Phase A
    classification before it was recovered from conversation history).
    """
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log(f"Could not read checkpoint {path} ({exc!r}), starting fresh")
        return {}


PHASE_KEYS = ("clean_angles", "bad_angles", "r_max", "c_max",
              "primary_test_angle", "phase_a2", "phase_b_registers",
              "phase_b_factorial", "best_registers", "phase_final_leg",
              "phase_speed", "phase_regression")


def has_phase(findings: dict, key: str) -> bool:
    return key in findings and findings[key] is not None


def reconnect(base_url: str, max_attempts: int = 5) -> bool:
    """Re-establishes the USB bridge path after a dropped connection.

    Checks whether the app container is still running (restarting it if not
    - a physical bump can kill the container outright, not just the link),
    re-detects its bridge IP, restarts the socat TCP bridge if needed, and
    re-does the adb forward. Returns True once /servo/state answers again.
    """
    for attempt in range(1, max_attempts + 1):
        log(f"reconnect attempt {attempt}/{max_attempts}...")
        if attempt == 1:
            # Cheap first: most failures are one transient blip, not a dead
            # bridge - rebuilding socat unconditionally on every single one
            # is itself what caused a duplicate-listener race this session.
            try:
                jp.get(base_url, "/servo/state")
                log("reconnect succeeded (bridge was fine, no rebuild needed)")
                return True
            except Exception:
                pass
        try:
            status = subprocess.run(
                ["adb", "shell",
                 "docker inspect servo_mvp-main-1 --format '{{.State.Running}}'"],
                capture_output=True, text=True, timeout=20).stdout.strip()
            if status != "true":
                log("container not running - restarting app")
                subprocess.run(["adb", "shell", "arduino-app-cli", "app",
                                 "start", "user:servo_mvp"],
                                capture_output=True, timeout=120)
                time.sleep(3.0)
            ip = get_container_ip()
            ensure_socat(ip)
            subprocess.run(["adb", "forward", "tcp:8001", "tcp:8000"],
                            capture_output=True, timeout=20)
            time.sleep(1.5)
            jp.get(base_url, "/servo/state")
            log("reconnect succeeded")
            return True
        except Exception as exc:
            log(f"reconnect attempt {attempt} failed: {exc!r}")
            time.sleep(3.0)
    log("reconnect exhausted all attempts")
    return False


class TemperatureSafetyAbort(Exception):
    """Raised when the servo's own temperature reading looks anomalous.

    Session 25 had a real overheating incident (a shorted Ethernet shield,
    unrelated to the servo bus, discovered by touch and burn - nothing in
    this system has a sensor for that chip). This check cannot catch that
    class of fault; it exists as the one piece of actual sensor data this
    system does have (the servo's own temperature register), so a genuine
    anomaly there at least stops the run instead of continuing blind.
    """


# 30-36 C was the stable reading for the servo across all of Session 25's
# work, including sustained M1-jitter conditions. This gives a wide margin
# above that baseline while stopping well short of the servo's own published
# thermal limits - a trip here means something is genuinely unusual.
MAX_SAFE_TEMPERATURE_C = 50.0


def check_temperature_safety(base_url: str) -> None:
    state = jp.get(base_url, "/servo/state")
    temp = state.get("temperature_c")
    if temp is not None and temp > MAX_SAFE_TEMPERATURE_C:
        raise TemperatureSafetyAbort(
            f"servo temperature_c={temp} exceeds {MAX_SAFE_TEMPERATURE_C} - "
            "aborting rather than continuing blind")


# Below this, pause and wait rather than pushing on - a session-25 run hit
# 55C (hard abort is 50C) during a block of full-travel moves; sustained
# jitter draws continuous small current even while "settled", so the servo
# does not necessarily rest between trials the way a clean move-and-stop
# cycle would.
COOLDOWN_TRIGGER_C = 45.0
COOLDOWN_RESUME_C = 40.0
COOLDOWN_POLL_SECONDS = 15.0
COOLDOWN_MAX_WAIT_SECONDS = 300.0


def wait_for_cooldown(base_url: str) -> None:
    """Pauses trials if temperature is elevated but not yet abort-worthy.

    Checked once per trial (cheap - one GET). Below COOLDOWN_TRIGGER_C this
    is a no-op. Between the trigger and the hard abort threshold, waits for
    it to drop back to COOLDOWN_RESUME_C before letting the next trial
    start, instead of either pushing on or hard-aborting. Gives up and
    proceeds (loudly) after COOLDOWN_MAX_WAIT_SECONDS - a genuinely stuck
    high temperature should hit the real safety abort on the next reading,
    not hang here forever.
    """
    state = jp.get(base_url, "/servo/state")
    temp = state.get("temperature_c")
    if temp is None or temp < COOLDOWN_TRIGGER_C:
        return
    log(f"temperature_c={temp} above cooldown trigger {COOLDOWN_TRIGGER_C} - "
        f"pausing until it drops to {COOLDOWN_RESUME_C}")
    waited = 0.0
    while waited < COOLDOWN_MAX_WAIT_SECONDS:
        time.sleep(COOLDOWN_POLL_SECONDS)
        waited += COOLDOWN_POLL_SECONDS
        state = jp.get(base_url, "/servo/state")
        temp = state.get("temperature_c")
        log(f"  cooling: temperature_c={temp} ({waited:.0f}s waited)")
        if temp is not None and temp <= COOLDOWN_RESUME_C:
            log("cooled below resume threshold, continuing")
            return
    log(f"WARNING: still above {COOLDOWN_RESUME_C} after "
        f"{COOLDOWN_MAX_WAIT_SECONDS}s - proceeding anyway, the hard "
        f"{MAX_SAFE_TEMPERATURE_C} abort remains the real backstop")


def probe_resilient(base_url: str, target_deg: float, label: str, tag: str,
                     repeat: int, anchor_deg: float = 0.0,
                     max_retries: int = 3) -> dict:
    """jp.probe() with reconnect-and-retry on a dropped connection.

    Checks the temperature safety cutoff first and lets that exception
    propagate immediately - a real thermal anomaly should stop the campaign
    outright, not get treated as a transient connection blip to retry past.
    Then a softer cooldown pause if elevated but not yet abort-worthy -
    applies to every trial in the campaign since this is the one place
    every trial passes through.
    """
    check_temperature_safety(base_url)
    wait_for_cooldown(base_url)
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return jp.probe(base_url, target_deg, label, tag, repeat,
                             anchor_deg=anchor_deg)
        except TemperatureSafetyAbort:
            raise
        except Exception as exc:
            last_exc = exc
            log(f"trial failed ({exc!r}), attempting reconnect before retry")
            if not reconnect(base_url):
                break
    raise RuntimeError(f"probe_resilient exhausted retries: {last_exc!r}")


def apply_registers_resilient(base_url: str, position_p: int, position_d: int,
                               max_retries: int = 3) -> None:
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            apply_registers(base_url, position_p, position_d)
            return
        except Exception as exc:
            last_exc = exc
            log(f"register write failed ({exc!r}), attempting reconnect before retry")
            if not reconnect(base_url):
                break
    raise RuntimeError(f"apply_registers_resilient exhausted retries: {last_exc!r}")


def get_container_ip() -> str:
    out = subprocess.run(
        ["adb", "shell",
         "docker inspect servo_mvp-main-1 --format "
         "'{{.NetworkSettings.Networks.servo_mvp_default.IPAddress}}'"],
        capture_output=True, text=True, timeout=20)
    return out.stdout.strip()


def ensure_socat(container_ip: str) -> None:
    """Rebuilds the TCP-LISTEN:8000 bridge, verifying the old one is truly
    dead first.

    A plain `pkill` (SIGTERM) plus a fixed 0.5s sleep raced with a slow
    exit at least once this session - two socat processes both ended up
    listening on :8000 at the same time, which produces exactly the
    intermittent, random-looking timeouts this function exists to fix.
    SIGKILL plus polling pgrep until it is actually gone closes that race.
    """
    subprocess.run(["adb", "shell", "pkill -9 -f 'socat TCP-LISTEN:8000'"],
                    capture_output=True, timeout=20)
    for _ in range(10):
        remaining = subprocess.run(
            ["adb", "shell", "pgrep -f 'socat TCP-LISTEN:8000'"],
            capture_output=True, text=True, timeout=20).stdout.strip()
        if not remaining:
            break
        time.sleep(0.3)
    subprocess.run(
        ["adb", "shell",
         f"nohup socat TCP-LISTEN:8000,fork,reuseaddr TCP:{container_ip}:8000 "
         ">/tmp/socat_8000.log 2>&1 & disown"],
        capture_output=True, timeout=20)
    time.sleep(1.0)


def restart_app_and_wait(base_url: str, timeout_s: float = 150.0) -> None:
    """Restarts the app (to pick up an .env change) and waits until it answers.

    The container may get a new bridge IP on recreation - re-detects it and
    restarts the socat bridge if so. Re-checks the container/bridge partway
    through the wait rather than only once up front - one restart this
    session never came back within the original 90s single-shot version,
    and a stale IP or a socat that needed re-establishing mid-boot is a
    plausible reason a single attempt at t=0 wouldn't catch.
    """
    log("restarting app to pick up .env change...")
    subprocess.run(["adb", "shell", "arduino-app-cli", "app", "restart",
                     "user:servo_mvp"], capture_output=True, timeout=120)
    time.sleep(3.0)
    ip = get_container_ip()
    ensure_socat(ip)
    subprocess.run(["adb", "forward", "tcp:8001", "tcp:8000"],
                    capture_output=True, timeout=20)

    t0 = time.time()
    last_check = t0
    while time.time() - t0 < timeout_s:
        try:
            jp.get(base_url, "/servo/state")
            log(f"app answering again after restart ({time.time() - t0:.1f}s)")
            return
        except Exception:
            if time.time() - last_check > 30.0:
                # "app restart" stopped the app but never actually started
                # it back up at least once this session - app list showed
                # "stopped", not a network issue at all, and re-bridging
                # alone just spun forever against nothing to bridge to.
                # Check which case this is and act accordingly.
                status = subprocess.run(
                    ["adb", "shell",
                     "docker inspect servo_mvp-main-1 --format '{{.State.Running}}'"],
                    capture_output=True, text=True, timeout=20).stdout.strip()
                if status != "true":
                    log("still not answering after 30s - container is not "
                        "running at all, re-issuing app start")
                    subprocess.run(["adb", "shell", "arduino-app-cli", "app",
                                     "start", "user:servo_mvp"],
                                    capture_output=True, timeout=120)
                    time.sleep(3.0)
                else:
                    log("still not answering after 30s - container is up, "
                        "re-detecting IP and rebuilding the bridge in case "
                        "it changed mid-boot")
                try:
                    ip = get_container_ip()
                    ensure_socat(ip)
                    subprocess.run(["adb", "forward", "tcp:8001", "tcp:8000"],
                                    capture_output=True, timeout=20)
                except Exception as exc:
                    log(f"re-bridge attempt failed: {exc!r}")
                last_check = time.time()
            time.sleep(1.0)
    raise RuntimeError("app did not answer within timeout after restart")


def set_env_value(path: str, key: str, value: Optional[str]) -> None:
    """Sets or removes a KEY=value line in an .env-style file.

    Writes via a temp file + atomic rename, same as checkpoint() - a plain
    in-place write hit a PermissionError on this CIFS mount mid-campaign,
    the same class of write flakiness that once silently truncated the
    JSON checkpoint. Retries a few times since a transient CIFS write lock
    is plausible here, matching how registers/state calls already retry.
    """
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    out = []
    found = False
    for line in lines:
        if line.strip().startswith(f"{key}="):
            found = True
            if value is not None:
                out.append(f"{key}={value}\n")
        else:
            out.append(line)
    if value is not None and not found:
        out.append(f"{key}={value}\n")

    tmp_path = path + ".tmp"
    last_exc: Optional[Exception] = None
    for attempt in range(5):
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                f.writelines(out)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, path)
            return
        except Exception as exc:
            last_exc = exc
            log(f"set_env_value write failed ({exc!r}), retrying ({attempt + 1}/5)")
            time.sleep(2.0)
    raise RuntimeError(f"set_env_value exhausted retries writing {path}: {last_exc!r}")


def run_n(base_url: str, target: float, anchor: float, n: int, label: str,
          tag: str, r_max: Optional[int] = None,
          c_max: Optional[float] = None, findings: Optional[dict] = None,
          raw_key: Optional[str] = None) -> dict:
    """Runs n trials at one (anchor, target), returns a summary dict.

    If r_max/c_max are given, also computes pass/fail counts against them.
    If findings+raw_key are given, checkpoints after every single trial and
    resumes any already-recorded ones under findings[raw_key][tag] - a crash
    mid-block then only costs the one trial in flight, not the whole block
    (Session 25 lost a fully-completed angle's data to phase-level-only
    checkpointing before this was added).
    """
    trials: list = []
    if findings is not None and raw_key is not None:
        raw = findings.setdefault(raw_key, {})
        trials = list(raw.get(tag, []))
    start = len(trials)
    if start:
        log(f"  {tag}: resuming at trial {start + 1}/{n} "
            f"({start} already recorded)")
    for i in range(start + 1, n + 1):
        r = probe_resilient(base_url, target, label, tag, i, anchor_deg=anchor)
        trials.append({"reversals": r["reversals"],
                        "settled_short": r["settled_short"],
                        "current_mean_a": r["current_mean_a"],
                        "final_error_deg": r.get("final_error_deg")})
        if findings is not None and raw_key is not None:
            findings[raw_key][tag] = trials
            checkpoint(findings)
    results = trials[:n]
    failures = None
    if r_max is not None and c_max is not None:
        failures = sum(1 for r in results if outcome_fails(r, r_max, c_max))
    reversals = [r["reversals"] for r in results]
    currents = [r["current_mean_a"] or 0.0 for r in results]
    return {
        "label": label, "tag": tag, "anchor": anchor, "target": target, "n": n,
        "failures": failures,
        "reversal_counts": reversals,
        "max_reversals": max(reversals) if reversals else None,
        "max_current_mean_a": max(currents) if currents else None,
        "mean_current_mean_a": sum(currents) / len(currents) if currents else None,
    }


def phase_a_survey(base_url: str, findings: dict) -> dict:
    log("=== Phase A: 11-angle re-survey, N=10, current registers/env ===")
    per_angle = findings.setdefault("phase_a_survey", {})
    for angle in SURVEY_ANGLES:
        anchor = 0.0 if angle != 0 else 45.0
        summary = run_n(base_url, float(angle), anchor, PASS_BAR_N,
                         "d48_phaseA_survey", f"baseline_survey_{angle}",
                         findings=findings, raw_key="phase_a_survey_raw")
        n_bad = sum(1 for r in summary["reversal_counts"] if r >= 3)
        summary["n_bad_by_reversal_count"] = n_bad
        per_angle[angle] = summary
        log(f"  angle={angle:+4.0f}  reversals={summary['reversal_counts']}  "
            f"bad={n_bad}/{PASS_BAR_N}")
        checkpoint(findings)
    return per_angle


def classify_angles(per_angle: dict) -> tuple[list, list]:
    clean, bad = [], []
    for angle, s in per_angle.items():
        if s["n_bad_by_reversal_count"] <= CLEAN_MAX_FAILURES:
            clean.append(angle)
        elif s["n_bad_by_reversal_count"] >= BAD_MIN_FAILURES:
            bad.append(angle)
    return clean, bad


def lock_noise_floor(per_angle: dict, clean_angles: list) -> tuple[int, float]:
    max_rev = 0
    max_cur = 0.0
    for angle in clean_angles:
        s = per_angle[angle]
        max_rev = max(max_rev, s["max_reversals"] or 0)
        max_cur = max(max_cur, s["max_current_mean_a"] or 0.0)
    r_max = max_rev + 1
    c_max = max_cur + 0.02  # margin, degrees of freedom for genuine noise
    log(f"Locked noise floor from {len(clean_angles)} clean angle(s) "
        f"{clean_angles}: R_max={r_max}  C_max={c_max:.4f}")
    return r_max, c_max


def phase_a2_direction_and_size(base_url: str, worst_angles: list,
                                 findings: dict) -> dict:
    log(f"=== Phase A2: approach direction + move size at {worst_angles} ===")
    out = findings.setdefault("phase_a2", {})
    for angle in worst_angles:
        key = str(angle)
        if key in out:
            log(f"  {angle:+.0f}: already fully recorded, reusing")
            continue
        sign = 1.0 if angle >= 0 else -1.0
        anchor_near = clamp(angle - sign * 30)
        anchor_far = clamp(angle + sign * 30)
        anchor_small = clamp(angle - sign * 5)
        anchor_full = clamp(-90.0 if angle >= 0 else 90.0)

        d1 = run_n(base_url, float(angle), anchor_near, 5,
                   "d48_phaseA2_direction", f"dir_near_{angle}",
                   findings=findings, raw_key="phase_a2_raw")
        d2 = run_n(base_url, float(angle), anchor_far, 5,
                   "d48_phaseA2_direction", f"dir_far_{angle}",
                   findings=findings, raw_key="phase_a2_raw")
        s1 = run_n(base_url, float(angle), anchor_small, 5,
                   "d48_phaseA2_movesize", f"small_{angle}",
                   findings=findings, raw_key="phase_a2_raw")
        s2 = run_n(base_url, float(angle), anchor_full, 5,
                   "d48_phaseA2_movesize", f"full_{angle}",
                   findings=findings, raw_key="phase_a2_raw")
        out[key] = {"dir_near": d1, "dir_far": d2,
                     "move_small": s1, "move_full": s2}
        log(f"  {angle:+.0f}: dir_near={d1['reversal_counts']} "
            f"dir_far={d2['reversal_counts']} small={s1['reversal_counts']} "
            f"full={s2['reversal_counts']}")
        checkpoint(findings)
    return out


def phase_b_registers(base_url: str, test_angle: float, anchor: float,
                       r_max: int, c_max: float, findings: dict) -> dict:
    log(f"=== Phase B: register campaign at {test_angle:+.0f} deg "
        f"(anchor {anchor:+.0f}), N={PASS_BAR_N}/config, randomized order ===")
    # Revised from an earlier "raise D" sweep (40/48/56/64) that had no
    # grounding beyond generic textbook damping intuition. Web research
    # found: (1) LeRobot's own configure() template for this exact chip
    # leaves D at the factory default 32 and only lowers P, to the same
    # 10-16 range already used for this project's own P reduction, (2) no
    # community source anywhere recommends raising D on this servo, one
    # LeRobot doc page showed a real unit at D=8 (lower, not higher).
    # (3) the confirmed hunting mechanism is a quantisation-boundary
    # effect - raising D computes a derivative off a coarse, noisy
    # position signal, plausibly amplifying exactly the noise that drives
    # the hunting rather than damping it. Testing lower D instead, plus a
    # third P step, same total trial budget.
    configs = {
        "baseline_P24_D32": {"position_p": 24, "position_d": 32},
        "P20": {"position_p": 20, "position_d": 32},
        "P16": {"position_p": 16, "position_d": 32},
        "P12": {"position_p": 12, "position_d": 32},
        "D24": {"position_p": 24, "position_d": 24},
        "D16": {"position_p": 24, "position_d": 16},
        "D8": {"position_p": 24, "position_d": 8},
    }
    import random
    raw = findings.setdefault("phase_b_registers_raw", {})
    per_trial: dict = {name: list(raw.get(name, [])) for name in configs}
    order = []
    for name in configs:
        need = PASS_BAR_N - len(per_trial[name])
        if need > 0:
            order += [name] * need
    already = sum(len(t) for t in per_trial.values())
    if already:
        log(f"  resuming Phase B: {already}/{len(configs) * PASS_BAR_N} "
            f"trials already recorded, {len(order)} remain")
    random.shuffle(order)

    counters = {name: len(per_trial[name]) for name in configs}
    for i, name in enumerate(order, 1):
        counters[name] += 1
        cfg = configs[name]
        apply_registers_resilient(base_url, cfg["position_p"], cfg["position_d"])
        r = probe_resilient(base_url, test_angle, "d48_phaseB_registers", name,
                     counters[name], anchor_deg=anchor)
        per_trial[name].append({"reversals": r["reversals"],
                                  "settled_short": r["settled_short"],
                                  "current_mean_a": r["current_mean_a"],
                                  "final_error_deg": r.get("final_error_deg")})
        raw[name] = per_trial[name]
        findings["phase_b_progress"] = f"{i}/{len(order)} remaining"
        checkpoint(findings)

    results = {}
    for name, trials in per_trial.items():
        failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
        results[name] = {
            "config": configs[name], "n": len(trials), "failures": failures,
            "passes": failures <= PASS_BAR_MAX_FAILURES,
            "reversal_counts": [r["reversals"] for r in trials],
            "mean_current_a": sum((r["current_mean_a"] or 0) for r in trials) / len(trials),
        }
        log(f"  {name}: {results[name]['failures']}/{len(trials)} failures "
            f"{'PASS' if results[name]['passes'] else 'fail'} "
            f"reversals={results[name]['reversal_counts']}")

    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                     BASELINE_REGISTERS["position_d"])
    return results


def phase_staging_confirm(base_url: str, angles: list, r_max: int,
                           c_max: float, findings: dict) -> dict:
    """Confirms, at real power (N=10), Phase A2's own N=5 screen: does a
    short (~5deg) final approach avoid the jitter, under baseline registers?

    Phase A2 found +60deg clean (0/5) with a short approach but -60deg
    still 3/5 bad even with one - this re-runs both at N=10 to see if that
    holds up, before spending any more attended time on register tuning.
    No register changes here at all - this isolates the procedural/
    approach-dynamics lever on its own.
    """
    log(f"=== Staging confirm: short (~5deg) final approach at {angles}, "
        f"N=10, baseline registers ===")
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                               BASELINE_REGISTERS["position_d"])
    out = {}
    for angle in angles:
        sign = 1.0 if angle >= 0 else -1.0
        anchor_small = clamp(angle - sign * 5)
        s = run_n(base_url, angle, anchor_small, PASS_BAR_N,
                  "d48_staging_confirm", f"staging_{angle}",
                  r_max=r_max, c_max=c_max, findings=findings,
                  raw_key="phase_staging_raw")
        out[angle] = s
        log(f"  {angle:+.0f} (short approach from {anchor_small:+.2f}): "
            f"failures={s['failures']}/{PASS_BAR_N} "
            f"reversals={s['reversal_counts']}")
    return out


def phase_d_bracket(base_url: str, test_angle: float, anchor: float,
                     r_max: int, c_max: float, findings: dict,
                     bracket_n: int = 8) -> dict:
    """Localizes the interior optimum found in Phase B's coarse sweep.

    Phase B found D non-monotonic: D32(baseline)=7/10 fail, D24=5/10,
    D16=2/10 (best), D8=9/10 (worse than baseline) - lower is not always
    better, there's a real dip near D16 that the coarse grid did not
    resolve (D16 vs D24 was not statistically distinguishable, p=0.35).
    Brackets it with 3 new points at a smaller N (attended-time is now the
    scarce resource, not hardware time) rather than a full N=10 re-sweep.
    D16/D24/baseline are not re-run - already have that data.
    """
    log(f"=== D-bracket: localizing the optimum near D16, N={bracket_n}/point ===")
    configs = {
        "D14": {"position_p": 24, "position_d": 14},
        "D18": {"position_p": 24, "position_d": 18},
        "D20": {"position_p": 24, "position_d": 20},
    }
    import random
    raw = findings.setdefault("phase_d_bracket_raw", {})
    per_trial = {name: list(raw.get(name, [])) for name in configs}
    order = []
    for name in configs:
        need = bracket_n - len(per_trial[name])
        if need > 0:
            order += [name] * need
    random.shuffle(order)
    counters = {name: len(per_trial[name]) for name in configs}
    for name in order:
        counters[name] += 1
        cfg = configs[name]
        apply_registers_resilient(base_url, cfg["position_p"], cfg["position_d"])
        r = probe_resilient(base_url, test_angle, "d48_d_bracket", name,
                             counters[name], anchor_deg=anchor)
        per_trial[name].append({"reversals": r["reversals"],
                                  "settled_short": r["settled_short"],
                                  "current_mean_a": r["current_mean_a"],
                                  "final_error_deg": r.get("final_error_deg")})
        raw[name] = per_trial[name]
        checkpoint(findings)

    results = {}
    for name, trials in per_trial.items():
        failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
        results[name] = {
            "config": configs[name], "n": len(trials), "failures": failures,
            "passes": failures <= 1,
            "reversal_counts": [r["reversals"] for r in trials],
        }
        log(f"  {name}: {results[name]['failures']}/{len(trials)} failures "
            f"{'PASS' if results[name]['passes'] else 'fail'} "
            f"reversals={results[name]['reversal_counts']}")
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                               BASELINE_REGISTERS["position_d"])
    return results


def phase_d_p_combo(base_url: str, test_angle: float, anchor: float,
                     d_config: dict, r_max: int, c_max: float,
                     findings: dict, n: int = 8) -> dict:
    """Tests the two strongest individual levers together: the best D found
    (from Phase B or the bracket) combined with P16 (Phase B's best P,
    5/10 - never tried alongside a D change). Worth one direct test even
    though neither passed the strict bar alone - D16 vs baseline was only
    suggestive (p=0.070), not conclusive; combining may cross the bar.
    """
    combo = {"position_p": 16, "position_d": d_config["position_d"]}
    log(f"=== D+P combo: {combo} at {test_angle:+.0f}, N={n} ===")
    apply_registers_resilient(base_url, combo["position_p"], combo["position_d"])
    tag = f"combo_P16_D{combo['position_d']}"
    trials = run_n_checkpointed(
        n, findings, "phase_d_p_combo_raw", tag,
        lambda i: probe_resilient(base_url, test_angle, "d48_d_p_combo",
                                    tag, i, anchor_deg=anchor))
    failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                               BASELINE_REGISTERS["position_d"])
    result = {"config": combo, "n": n, "failures": failures,
              "passes": failures <= 1,
              "reversal_counts": [r["reversals"] for r in trials]}
    log(f"  combo: {failures}/{n} failures {'PASS' if result['passes'] else 'fail'}")
    return result


def run_n_checkpointed(n: int, findings: dict, raw_key: str, tag: str,
                        trial_fn) -> list:
    """Generic per-trial resume+checkpoint wrapper for any trial shape.

    trial_fn(i) must return a probe-result-shaped dict (reversals,
    settled_short, current_mean_a). Used by the phases below whose trial
    loops don't go through run_n directly (a single named block, or a
    custom move like phase_speed's speed override).
    """
    raw = findings.setdefault(raw_key, {})
    trials = list(raw.get(tag, []))
    start = len(trials)
    if start:
        log(f"  {tag}: resuming at trial {start + 1}/{n} "
            f"({start} already recorded)")
    for i in range(start + 1, n + 1):
        r = trial_fn(i)
        trials.append({"reversals": r["reversals"],
                        "settled_short": r["settled_short"],
                        "current_mean_a": r["current_mean_a"],
                        "final_error_deg": r.get("final_error_deg")})
        raw[tag] = trials
        checkpoint(findings)
    return trials[:n]


def phase_b_factorial(base_url: str, test_angle: float, anchor: float,
                       best_d: dict, best_p: dict, r_max: int,
                       c_max: float, findings: dict) -> dict:
    combo = {"position_p": best_p["position_p"], "position_d": best_d["position_d"]}
    log(f"=== Factorial: combining {combo} at {test_angle:+.0f}, N=8 ===")
    apply_registers_resilient(base_url, combo["position_p"], combo["position_d"])
    tag = f"combo_P{combo['position_p']}_D{combo['position_d']}"
    trials = run_n_checkpointed(
        8, findings, "phase_b_factorial_raw", tag,
        lambda i: probe_resilient(base_url, test_angle, "d48_phaseB_factorial",
                                    tag, i, anchor_deg=anchor))
    failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                     BASELINE_REGISTERS["position_d"])
    result = {"config": combo, "n": 8, "failures": failures,
              "passes": failures <= 1,
              "reversal_counts": [r["reversals"] for r in trials]}
    log(f"  combo: {failures}/8 failures {'PASS' if result['passes'] else 'fail'}")
    return result


def phase_final_leg(base_url: str, test_angle: float, anchor: float,
                     winning_regs: dict, r_max: int, c_max: float,
                     findings: dict) -> dict:
    """Tests the fine-approach final leg's own dynamics, independent of the
    register story (which the D-bracket showed was likely noise - this runs
    against plain baseline registers, not whatever "won" Phase B).

    The mechanism read from motion_service.py: the final leg only starts
    once the servo's own `moving` flag says the overshoot leg has stopped -
    but that flag is exactly the signal known to be blind to real settling
    (the reason jitter_probe exists at all). A big preceding overshoot leg
    could leave real residual energy in the rig that the firmware already
    considers "stopped" - so softening the final leg's own speed/
    acceleration, or shrinking the overshoot distance itself (flagged
    independently by the original research as a possible excitation event),
    are both worth testing regardless of the overall move's size.
    """
    log("=== Fine-approach final-leg test: speed, acceleration, and "
        "overshoot distance, N=8/arm, baseline registers ===")
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                               BASELINE_REGISTERS["position_d"])

    def run_arm(tag: str) -> list:
        return run_n_checkpointed(
            8, findings, "phase_final_leg_raw", tag,
            lambda i: probe_resilient(base_url, test_angle, "d48_final_leg",
                                        tag, i, anchor_deg=anchor))

    arms = {
        "unsoftened": {},
        "softened_moderate": {"FINE_APPROACH_FINAL_SPEED_DPS": "10.0",
                               "FINE_APPROACH_FINAL_ACCELERATION": "20"},
        "softened_aggressive": {"FINE_APPROACH_FINAL_SPEED_DPS": "5.0",
                                 "FINE_APPROACH_FINAL_ACCELERATION": "10"},
        "reduced_overshoot": {"FINE_APPROACH_OVERSHOOT_DEG": "0.5"},
    }
    all_keys = {"FINE_APPROACH_FINAL_SPEED_DPS", "FINE_APPROACH_FINAL_ACCELERATION",
                "FINE_APPROACH_OVERSHOOT_DEG"}

    results = {}
    for tag, env_overrides in arms.items():
        already = len(findings.get("phase_final_leg_raw", {}).get(tag, []))
        if already < 8:
            for key in all_keys:
                value = env_overrides.get(key)
                set_env_value(ENV_PATH, key, value)
                set_env_value(ENV_BOARD_PATH, key, value)
            restart_app_and_wait(base_url)
            apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                                       BASELINE_REGISTERS["position_d"])
        trials = run_arm(tag)
        failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
        results[tag] = {"failures": failures, "n": 8, "passes": failures <= 1,
                         "reversal_counts": [r["reversals"] for r in trials]}
        log(f"  {tag} ({env_overrides or 'defaults'}): {failures}/8 failures "
            f"{'PASS' if failures <= 1 else 'fail'} "
            f"reversals={results[tag]['reversal_counts']}")

    for key in all_keys:
        set_env_value(ENV_PATH, key, None)
        set_env_value(ENV_BOARD_PATH, key, None)
    restart_app_and_wait(base_url)
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                     BASELINE_REGISTERS["position_d"])

    return results


def phase_speed(base_url: str, test_angle: float, anchor: float,
                 winning_regs: dict, r_max: int, c_max: float,
                 findings: dict) -> dict:
    log("=== Approach speed test, N=8/arm (30 dps vs 15 dps) ===")
    apply_registers_resilient(base_url, winning_regs["position_p"], winning_regs["position_d"])

    def probe_at_speed(speed_dps: float, tag: str, i: int) -> dict:
        check_temperature_safety(base_url)
        wait_for_cooldown(base_url)
        jp.reset_to(base_url, anchor)
        issued = time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime())
        t0 = time.time()
        import urllib.request
        req = urllib.request.Request(
            f"{base_url}/servo/move",
            data=json.dumps({"target_deg": test_angle,
                              "speed_dps": speed_dps}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=5) as r:
                    r.read()
                break
            except Exception as exc:
                if attempt == 2 or not reconnect(base_url):
                    raise
        trace = []
        while time.time() - t0 < jp.WINDOW_SECONDS:
            d = jp.get(base_url, "/servo/state")
            trace.append((time.time() - t0, d["output_deg"], d["current_a"]))
        result = jp.score_trial(trace, test_angle)
        trial_id = f"d48_speed_{tag}_{i}_{issued}"
        jp._append_csv(jp._csv_path("jitter_trace", "d48_speed"),
                        ["trial_id", "elapsed_s", "output_deg", "current_a"],
                        [{"trial_id": trial_id, "elapsed_s": e, "output_deg": v,
                          "current_a": c} for e, v, c in trace])
        return result

    trials_fast = run_n_checkpointed(
        8, findings, "phase_speed_raw", "speed_30",
        lambda i: probe_at_speed(30.0, "speed30", i))
    fail_fast = sum(1 for r in trials_fast if outcome_fails(r, r_max, c_max))
    log(f"  30 dps: {fail_fast}/8 failures reversals="
        f"{[r['reversals'] for r in trials_fast]}")

    trials_slow = run_n_checkpointed(
        8, findings, "phase_speed_raw", "speed_15",
        lambda i: probe_at_speed(15.0, "speed15", i))
    fail_slow = sum(1 for r in trials_slow if outcome_fails(r, r_max, c_max))
    log(f"  15 dps: {fail_slow}/8 failures reversals="
        f"{[r['reversals'] for r in trials_slow]}")

    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                     BASELINE_REGISTERS["position_d"])
    return {
        "speed_30": {"failures": fail_fast, "n": 8,
                      "reversal_counts": [r["reversals"] for r in trials_fast]},
        "speed_15": {"failures": fail_slow, "n": 8,
                      "reversal_counts": [r["reversals"] for r in trials_slow],
                      "passes": fail_slow <= 1},
    }


def phase_deadzone(base_url: str, angles: list, r_max: int, c_max: float,
                    findings: dict) -> dict:
    """Tests dead-zone 1 vs 2 counts (0.06/0.12 deg) at both bad angles,
    baseline P/D registers, N=10 each - the deliberately-deprioritized
    last-resort lever (D40 set it to 0/0 on purpose to protect accuracy),
    reached only after register tuning, move-staging, and every fine-
    approach final-leg/overshoot variant all failed to produce anything
    reproducible today.

    Reports accuracy cost (final_error_deg) explicitly alongside the pass/
    fail count for every trial - that tradeoff is the whole reason this was
    avoided until now, so it must be visible in the result, not just the
    jitter outcome.
    """
    log(f"=== Dead-zone test: 1 vs 2 counts at {angles}, N=10, baseline "
        f"P/D registers ===")
    apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                               BASELINE_REGISTERS["position_d"])
    results = {}
    for dz in (1, 2):
        apply_deadzone_resilient(base_url, dz, dz)
        for angle in angles:
            anchor = 0.0 if angle != 0 else 45.0
            tag = f"dz{dz}_{angle}"
            trials = run_n_checkpointed(
                PASS_BAR_N, findings, "phase_deadzone_raw", tag,
                lambda i, a=angle, an=anchor: probe_resilient(
                    base_url, a, "d48_deadzone", tag, i, anchor_deg=an))
            failures = sum(1 for r in trials if outcome_fails(r, r_max, c_max))
            errors = [abs(r.get("final_error_deg") or 0.0) for r in trials]
            mean_abs_error = sum(errors) / len(errors) if errors else None
            max_abs_error = max(errors) if errors else None
            results[tag] = {
                "dead_zone": dz, "angle": angle, "n": PASS_BAR_N,
                "failures": failures, "passes": failures <= PASS_BAR_MAX_FAILURES,
                "reversal_counts": [r["reversals"] for r in trials],
                "mean_abs_final_error_deg": mean_abs_error,
                "max_abs_final_error_deg": max_abs_error,
            }
            log(f"  dead_zone={dz} angle={angle:+.0f}: "
                f"{failures}/{PASS_BAR_N} failures "
                f"{'PASS' if results[tag]['passes'] else 'fail'} "
                f"reversals={results[tag]['reversal_counts']} "
                f"mean_abs_error={mean_abs_error:.3f}deg "
                f"max_abs_error={max_abs_error:.3f}deg")
    apply_deadzone_resilient(base_url, 0, 0)
    log("Dead zone reverted to 0/0 (the deliberate accuracy-preserving default)")
    return results


def phase_regression(base_url: str, winning_regs: dict, r_max: int,
                      c_max: float, second_bad_angle: Optional[float],
                      findings: dict) -> dict:
    log(f"=== Regression check under winning config {winning_regs} ===")
    apply_registers_resilient(base_url, winning_regs["position_p"], winning_regs["position_d"])
    out = {}
    for angle in [0.0, -60.0, 60.0, -90.0, 90.0]:
        anchor = 0.0 if angle != 0 else 45.0
        s = run_n(base_url, angle, anchor, 5, "d48_regression",
                  f"post_fix_{angle}", r_max=r_max, c_max=c_max,
                  findings=findings, raw_key="phase_regression_raw")
        out[angle] = s
        log(f"  {angle:+.0f}: failures={s['failures']}/5 "
            f"reversals={s['reversal_counts']}")
    if second_bad_angle is not None:
        s = run_n(base_url, second_bad_angle, 0.0, PASS_BAR_N,
                  "d48_regression", f"post_fix_second_bad_{second_bad_angle}",
                  r_max=r_max, c_max=c_max, findings=findings,
                  raw_key="phase_regression_raw")
        out[second_bad_angle] = s
        log(f"  {second_bad_angle:+.0f} (2nd bad pt): failures="
            f"{s['failures']}/{PASS_BAR_N} reversals={s['reversal_counts']}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--resume-from", default=FINDINGS_PATH,
                        help="findings JSON to resume from - any phase "
                             "already recorded there is reused, not re-run. "
                             "Defaults to the standard checkpoint path.")
    parser.add_argument("--fresh", action="store_true",
                        help="ignore any existing checkpoint, start clean")
    args = parser.parse_args()
    base_url = f"http://{args.host}:{args.port}/api/v1"

    findings: dict = {} if args.fresh else load_checkpoint(args.resume_from)
    if findings:
        done = [k for k in PHASE_KEYS if has_phase(findings, k)]
        log(f"Resuming from {args.resume_from} - already have: {done}")
    findings.setdefault("started", time.strftime("%Y-%m-%dT%H:%M:%S"))

    try:
        log(f"Confirming baseline registers via readback: {read_registers(base_url)}")

        if all(has_phase(findings, k) for k in
               ("clean_angles", "bad_angles", "r_max", "c_max",
                "primary_test_angle")):
            clean = findings["clean_angles"]
            bad = findings["bad_angles"]
            r_max = findings["r_max"]
            c_max = findings["c_max"]
            test_angle = findings["primary_test_angle"]
            second_bad = findings.get("secondary_bad_angle")
            log(f"Reusing Phase A result: clean={clean} bad={bad} "
                f"R_max={r_max} C_max={c_max} test_angle={test_angle} "
                f"second_bad={second_bad}")
        else:
            per_angle = phase_a_survey(base_url, findings)
            clean, bad = classify_angles(per_angle)
            log(f"Classified: clean={clean}  bad={bad}  "
                f"ambiguous={[a for a in SURVEY_ANGLES if a not in clean and a not in bad]}")
            findings["clean_angles"] = clean
            findings["bad_angles"] = bad

            r_max, c_max = lock_noise_floor(per_angle, clean if clean else [0])
            findings["r_max"] = r_max
            findings["c_max"] = c_max

            worst_sorted = sorted(bad, key=lambda a: -per_angle[a]["n_bad_by_reversal_count"])
            if not worst_sorted:
                worst_sorted = sorted(
                    SURVEY_ANGLES,
                    key=lambda a: -per_angle[a]["n_bad_by_reversal_count"])[:2]
            test_angle = float(worst_sorted[0])
            second_bad = float(worst_sorted[1]) if len(worst_sorted) > 1 else None
            log(f"Primary test point: {test_angle:+.0f}  secondary bad point: {second_bad}")
            findings["primary_test_angle"] = test_angle
            findings["secondary_bad_angle"] = second_bad
            checkpoint(findings)

        worst_top2 = [test_angle] + ([second_bad] if second_bad is not None else [])

        # phase_a2_direction_and_size manages its own per-angle resume/
        # checkpoint internally (findings["phase_a2"]), so it's always
        # called - it no-ops quickly for any angle already fully recorded.
        phase_a2_direction_and_size(base_url, worst_top2, findings)

        anchor_for_test = 0.0 if test_angle != 0 else 45.0

        if not has_phase(findings, "phase_b_registers"):
            b_results = phase_b_registers(base_url, test_angle, anchor_for_test,
                                           r_max, c_max, findings)
            findings["phase_b_registers"] = b_results
            checkpoint(findings)
        else:
            b_results = findings["phase_b_registers"]
            log("Reusing Phase B register campaign (already recorded)")

        passing = {n: r for n, r in b_results.items() if r["passes"]
                   and n != "baseline_P24_D32"}
        d_winners = {n: r for n, r in passing.items() if "D" in n and "P" not in n}
        p_winners = {n: r for n, r in passing.items() if n.startswith("P")}

        best_full_config = dict(BASELINE_REGISTERS)
        best_source = "baseline (nothing passed)"
        if passing:
            best_name = min(passing, key=lambda n: (
                passing[n]["failures"], passing[n]["mean_current_a"]))
            best_full_config = passing[best_name]["config"]
            best_source = best_name

        if d_winners and p_winners and not has_phase(findings, "phase_b_factorial"):
            best_d = min(d_winners.values(), key=lambda r: r["failures"])
            best_p = min(p_winners.values(), key=lambda r: r["failures"])
            factorial = phase_b_factorial(base_url, test_angle, anchor_for_test,
                                           best_d["config"], best_p["config"],
                                           r_max, c_max, findings)
            findings["phase_b_factorial"] = factorial
            checkpoint(findings)
        if has_phase(findings, "phase_b_factorial") and findings["phase_b_factorial"]["passes"]:
            best_full_config = findings["phase_b_factorial"]["config"]
            best_source = "factorial combo"

        findings["best_registers"] = best_full_config
        findings["best_source"] = best_source
        log(f"Best register configuration so far: {best_full_config} "
            f"(source: {best_source})")
        checkpoint(findings)

        # Follow-up phases added after reviewing Phase B's full result: the
        # D gain response was non-monotonic (D=16 best at 2/10 failures,
        # but D=8 worse than the factory baseline at 9/10 - lower is not
        # simply better), nothing passed the strict bar, and Phase A2
        # already hinted a short final approach alone might matter more
        # than register tuning. These localize the real optimum and test
        # the two strongest levers together, at smaller per-arm N since
        # attended time is now the scarce resource.
        if not has_phase(findings, "phase_staging_confirm"):
            findings["phase_staging_confirm"] = phase_staging_confirm(
                base_url, [test_angle, second_bad] if second_bad is not None
                else [test_angle], r_max, c_max, findings)
            checkpoint(findings)
        else:
            log("Reusing staging-confirm phase (already recorded)")

        if not has_phase(findings, "phase_d_bracket"):
            findings["phase_d_bracket"] = phase_d_bracket(
                base_url, test_angle, anchor_for_test, r_max, c_max, findings)
            checkpoint(findings)
        else:
            log("Reusing D-bracket phase (already recorded)")

        # Best D candidate across the coarse sweep (D at 16/24/32-baseline;
        # D=8 excluded, already shown worse than the factory baseline) and
        # the new bracket.
        d_candidates = {n: r for n, r in b_results.items()
                         if n.startswith("D") and n != "D8"}
        d_candidates.update(findings["phase_d_bracket"])
        best_d_name = min(d_candidates, key=lambda n: d_candidates[n]["failures"])
        best_d_config = d_candidates[best_d_name]["config"]
        log(f"Best D candidate after bracket: {best_d_name} "
            f"({d_candidates[best_d_name]['failures']} failures)")

        if not has_phase(findings, "phase_d_p_combo"):
            findings["phase_d_p_combo"] = phase_d_p_combo(
                base_url, test_angle, anchor_for_test, best_d_config,
                r_max, c_max, findings)
            checkpoint(findings)
        else:
            log("Reusing D+P combo phase (already recorded)")

        # Re-pick the overall best registers now that the bracket/combo
        # results are in - prefer anything that actually passes, else fall
        # back to whichever has fewest failures so final-leg/speed test on
        # top of the least-bad config rather than reverting to baseline.
        all_candidates = dict(b_results)
        all_candidates.update(findings["phase_d_bracket"])
        all_candidates["combo"] = findings["phase_d_p_combo"]
        passing_now = {n: r for n, r in all_candidates.items() if r.get("passes")}
        if passing_now:
            winner = min(passing_now, key=lambda n: passing_now[n]["failures"])
            best_full_config = passing_now[winner]["config"]
            best_source = winner
        else:
            winner = min(all_candidates, key=lambda n: all_candidates[n]["failures"])
            best_full_config = all_candidates[winner]["config"]
            best_source = f"{winner} (least-bad, none passed the strict bar)"
        findings["best_registers"] = best_full_config
        findings["best_source"] = best_source
        log(f"Best register configuration after refinement: {best_full_config} "
            f"(source: {best_source})")
        checkpoint(findings)

        if not has_phase(findings, "phase_final_leg"):
            findings["phase_final_leg"] = phase_final_leg(
                base_url, test_angle, anchor_for_test, best_full_config, r_max, c_max,
                findings)
            checkpoint(findings)
        else:
            log("Reusing final-leg phase (already recorded)")

        if not has_phase(findings, "phase_speed"):
            findings["phase_speed"] = phase_speed(
                base_url, test_angle, anchor_for_test, best_full_config, r_max, c_max,
                findings)
            checkpoint(findings)
        else:
            log("Reusing speed phase (already recorded)")

        # Last-resort lever, reached only because register tuning, move-
        # staging, and every fine-approach final-leg/overshoot variant
        # tested today all failed to produce anything reproducible.
        # Deliberately run at plain baseline P/D, isolated from the
        # likely-noise best-D-gain result from the bracket, and always
        # reverted to 0/0 afterward - the operator's own deliberate
        # accuracy-preserving default.
        deadzone_angles = [test_angle] + ([second_bad] if second_bad is not None else [])
        if not has_phase(findings, "phase_deadzone"):
            findings["phase_deadzone"] = phase_deadzone(
                base_url, deadzone_angles, r_max, c_max, findings)
            checkpoint(findings)
        else:
            log("Reusing dead-zone phase (already recorded)")

        if not has_phase(findings, "phase_regression"):
            findings["phase_regression"] = phase_regression(
                base_url, best_full_config, r_max, c_max, second_bad, findings)
            checkpoint(findings)
        else:
            log("Reusing regression phase (already recorded)")

        reg_failures = sum(
            s["failures"] for s in findings["phase_regression"].values())
        findings["regression_clean"] = reg_failures == 0
        deadzone_passing = {k: v for k, v in findings["phase_deadzone"].items()
                             if v["passes"]}
        findings["overall_conclusion"] = (
            "candidate registers pass primary bar and regression check"
            if (best_source != "baseline (nothing passed)" and reg_failures == 0)
            else "dead-zone passes at some angle(s) - see accuracy cost before adopting"
            if deadzone_passing
            else "no configuration (registers, staging, final-leg, dead-zone) "
                 "reliably beats baseline - see phase data, mechanism (M1) stands"
        )

        apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                         BASELINE_REGISTERS["position_d"])
        log("Restored baseline registers (P=24 D=32) pending the operator's "
            "review of findings before anything is written permanently.")

    except TemperatureSafetyAbort as exc:
        findings["error"] = repr(exc)
        findings["safety_abort"] = True
        log(f"SAFETY ABORT - TEMPERATURE ANOMALY: {exc!r}")
        try:
            apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                             BASELINE_REGISTERS["position_d"])
        except Exception:
            log("WARNING: could not confirm baseline registers restored after safety abort")
        checkpoint(findings)
        return 2
    except Exception as exc:
        findings["error"] = repr(exc)
        log(f"CAMPAIGN FAILED: {exc!r}")
        try:
            apply_registers_resilient(base_url, BASELINE_REGISTERS["position_p"],
                             BASELINE_REGISTERS["position_d"])
        except Exception:
            log("WARNING: could not confirm baseline registers restored after failure")
        os.makedirs(jp.ARCHIVE_DIR, exist_ok=True)
        with open(FINDINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(findings, f, indent=2, default=str)
        return 1

    findings["finished"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    os.makedirs(jp.ARCHIVE_DIR, exist_ok=True)
    with open(FINDINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, default=str)
    log(f"Findings written to {FINDINGS_PATH}")
    log(f"CONCLUSION: {findings['overall_conclusion']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
