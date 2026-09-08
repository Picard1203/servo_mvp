#!/usr/bin/env python3
"""Multi-angle validation sweep for D48.

Tests top candidate configurations from B7 and B8 against the baseline
across the full range of angles (-90, -60, -45, 0, +45, +60, +90 deg)
to verify that the fix is not localized to -60 deg and to measure steady-state
droop / holding current under maximal gravitational hang.
"""

import argparse
import json
import math
import os
import random
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import jitter_probe as jp
import resonance_campaign as rc

LABEL = "d48_multi_angle"
FINDINGS_PATH = os.path.join(jp.ARCHIVE_DIR, "d48_multi_angle_findings.json")

FAST_POLL_SECONDS = 0.010
MIN_FAST_HZ = 40.0
DEFAULT_ANCHOR = 0.0
WINDOW_SECONDS = 15.0

TEST_ANGLES = (-90.0, -60.0, -45.0, 0.0, 45.0, 60.0, 90.0)

CANDIDATES = {
    "msf85_dz1": {
        "description": "B7/B8 top pick: high holding torque (85) with 1-count deadzone",
        "registers": {"min_start_force": 85, "cw_dead_zone": 1, "ccw_dead_zone": 1},
    },
    "msf40_dz0": {
        "description": "B7 zero-deadzone pick: 100% clean settling with 0 deadband",
        "registers": {"min_start_force": 40, "cw_dead_zone": 0, "ccw_dead_zone": 0},
    },
    "baseline_msf150_dz0": {
        "description": "Session 26 baseline control chart",
        "registers": {"min_start_force": 150, "cw_dead_zone": 0, "ccw_dead_zone": 0},
    },
}

FALLBACK_BASELINE = {
    "position_p": 24, "position_d": 32, "position_i": 0,
    "min_start_force": 150, "cw_dead_zone": 0, "ccw_dead_zone": 0,
    "speed_p": 10, "speed_i": 200,
}


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def load_findings() -> dict:
    if not os.path.exists(FINDINGS_PATH):
        return {"trials": {}, "angles": list(TEST_ANGLES), "candidates": list(CANDIDATES.keys())}
    try:
        with open(FINDINGS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        log(f"findings unreadable ({exc!r}); starting fresh")
        return {"trials": {}, "angles": list(TEST_ANGLES), "candidates": list(CANDIDATES.keys())}


def save_findings(findings: dict) -> None:
    os.makedirs(jp.ARCHIVE_DIR, exist_ok=True)
    tmp = f"{FINDINGS_PATH}.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(findings, f, indent=2, default=str)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, FINDINGS_PATH)


def apply_config_resilient(base_url: str, config: dict, attempts: int = 3) -> None:
    last: Optional[Exception] = None
    for _ in range(attempts):
        try:
            rc.write_registers(base_url, **config)
            time.sleep(0.3)
            got = jp.get(base_url, "/servo/diagnostics/tuning_registers")
            mismatched = {k: (v, got.get(k)) for k, v in config.items() if got.get(k) != v}
            if mismatched:
                raise RuntimeError(f"readback mismatch: {mismatched}")
            return
        except Exception as exc:
            last = exc
            log(f"register write failed ({exc!r}); reconnecting")
            if not rc.reconnect(base_url):
                break
    raise RuntimeError(f"apply_config exhausted retries: {last!r}")


def probe_resilient(base_url: str, target_deg: float, tag: str, repeat: int,
                    attempts: int = 3) -> dict:
    rc.check_temperature_safety(base_url)
    rc.wait_for_cooldown(base_url)
    last: Optional[Exception] = None
    for _ in range(attempts):
        try:
            result = jp.probe(
                base_url, target_deg, LABEL, tag, repeat,
                poll_seconds=FAST_POLL_SECONDS, anchor_deg=DEFAULT_ANCHOR,
                window_seconds=WINDOW_SECONDS)
            return result
        except rc.TemperatureSafetyAbort:
            raise
        except Exception as exc:
            last = exc
            log(f"trial failed ({exc!r}); reconnecting")
            if not rc.reconnect(base_url):
                break
    raise RuntimeError(f"probe exhausted retries: {last!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--replicates", type=int, default=3)
    args = parser.parse_args()

    base_url = f"http://{args.host}:{args.port}/api/v1"

    findings = load_findings()
    baseline = findings.setdefault("baseline_registers", FALLBACK_BASELINE)
    findings["started_at"] = findings.get("started_at", time.strftime("%Y-%m-%dT%H:%M:%S"))

    log("=== D48 Multi-Angle Validation Sweep ===")
    log(f"Testing {len(TEST_ANGLES)} angles: {TEST_ANGLES}")
    log(f"Testing {len(CANDIDATES)} candidates: {list(CANDIDATES.keys())}")
    log(f"Replicates: {args.replicates} (Total trials: {len(TEST_ANGLES) * len(CANDIDATES) * args.replicates})")

    try:
        for rep in range(1, args.replicates + 1):
            log(f"--- Starting Replicate {rep}/{args.replicates} ---")
            conditions = [(angle, cand) for angle in TEST_ANGLES for cand in CANDIDATES]
            random.shuffle(conditions)

            for angle, cand in conditions:
                key = f"{cand}__{angle:+.0f}"
                block = findings["trials"].setdefault(key, [])
                if len(block) >= rep:
                    continue

                spec = CANDIDATES[cand]
                cfg = {**baseline, **spec["registers"]}
                apply_config_resilient(base_url, cfg)

                log(f"  [Rep {rep}] Testing {cand} at {angle:+.0f}°...")
                res = probe_resilient(base_url, angle, key, rep)

                block.append({
                    "replicate": rep,
                    "angle_deg": angle,
                    "candidate": cand,
                    "reversals": res["reversals"],
                    "swing_deg": res.get("swing_deg"),
                    "final_error_deg": res["final_error_deg"],
                    "current_mean_a": res["current_mean_a"],
                    "drive_duty": res.get("drive_duty"),
                    "temperature_c_mean": res.get("temperature_c_mean"),
                    "achieved_hz": res.get("achieved_hz"),
                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
                })
                save_findings(findings)
                log(f"    => rev={res['reversals']} swing={res.get('swing_deg')} "
                    f"err={res['final_error_deg']:.3f}° curr={res['current_mean_a']:.4f}A")

    except rc.TemperatureSafetyAbort as exc:
        log(f"TEMPERATURE ABORT: {exc}")
        return 2
    except Exception as exc:
        log(f"ABORTED: {exc!r}")
        return 1
    finally:
        try:
            rc.write_registers(base_url, **baseline)
            log(f"Registers restored to baseline: {baseline}")
        except Exception as exc:
            log(f"COULD NOT RESTORE REGISTERS: {exc!r}")
        findings["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        save_findings(findings)

    log("=== Multi-Angle Sweep Complete ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
