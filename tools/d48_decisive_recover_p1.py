#!/usr/bin/env python3
"""One-off recovery: rebuilds P1's trial data from its CSV log.

Run once, 8 Sept 2026. `archive/d48_decisive_findings.json` was
accidentally overwritten by the test suite (see the autouse fixture added
to test_d48_decisive.py the same session) after P1's real 56 trials had
already completed on real hardware. The per-trial CSV
(archive/jitter_trial_d48_decisive.csv) is append-only and survived intact.

Only `first_error_deg`, `reversals` and `current_mean_a` from each trial's
first (forced-approach) landing are recoverable this way - the three
re-sends `run_trial` records afterward were never written to the CSV, only
to the now-lost JSON. `verdict_p1` uses only the first landing for its
statistics, so this reconstruction reproduces the real verdict exactly;
fields that need all four landings (`accurate`, `passed`, `spread_deg`) are
marked unknown rather than guessed.

    python3 tools/d48_decisive_recover_p1.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_decisive as dd
import jitter_probe as jp

CSV_PATH = os.path.join(jp.ARCHIVE_DIR, "jitter_trial_d48_decisive.csv")

# The real boot configuration, exactly as this run's own preflight read it
# at 11:46:38 and as a live readback confirmed again just now. min_start_
# force is 40, not the older campaigns' 150 - Config.h::kMinStartForce was
# changed earlier this session (before the sign-dependent finding reopened
# the question). Getting this wrong here would make the run's own
# exit-safety restore write the wrong boot value.
BASELINE_REGISTERS = {
    "position_p": 24, "position_d": 32, "position_i": 0,
    "min_start_force": 40, "cw_dead_zone": 0, "ccw_dead_zone": 0,
    "speed_p": 10, "speed_i": 200,
}


def main() -> int:
    """Rebuilds findings["trials"]["p1"], recomputes and prints the verdict.

    Returns:
        int: 0 on success, 1 if the CSV is missing.
    """
    if not os.path.exists(CSV_PATH):
        print(f"no CSV at {CSV_PATH}; nothing to recover")
        return 1

    trials: dict = {}
    timestamps = []
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if not row["tag"].startswith("p1__msf"):
                continue
            _, rest = row["tag"].split("__msf", 1)
            floor_str, arrival, angle_str = rest.split("_", 2)
            floor, target_deg = int(floor_str), float(angle_str)
            error = float(row["final_error_deg"])
            record = {
                "phase": "p1", "floor": floor, "target_deg": target_deg,
                "arrival": arrival, "replicate": int(row["repeat"]),
                "resend_mode": "natural", "anchor_deg": float(row["anchor_deg"]),
                "reversals": int(row["reversals"]),
                "current_mean_a": float(row["current_mean_a"]),
                "median_period_s": (float(row["median_period_s"])
                                    if row["median_period_s"] else None),
                "swing_deg": (float(row["swing_deg"])
                             if row["swing_deg"] else None),
                "oscillating": None,  # unrecoverable: per-angle hold
                                      # reference was in the lost JSON only,
                                      # and this field is informational -
                                      # verdict_p1 does not decide on it.
                "c_max_used_a": None,
                "hold_reference_a": None,
                "landings": [float(row["final_deg"])],
                "landing_arrivals": [arrival],
                "errors": [round(error, 4)],
                "first_error_deg": round(error, 4),
                "max_abs_error_deg": round(abs(error), 4),
                "spread_deg": None,  # needs all 4 landings; only 1 survived
                "accurate": None,
                "passed": None,
                "achieved_hz": (float(row["achieved_hz"])
                               if row["achieved_hz"] else None),
                "temperature_c_mean": (float(row["temperature_c_mean"])
                                       if row["temperature_c_mean"] else None),
                "timestamp": row["timestamp"],
                "reconstructed_from_csv": True,
            }
            tag = row["tag"]
            trials.setdefault(tag, []).append(record)
            timestamps.append(row["timestamp"])

    total = sum(len(v) for v in trials.values())
    print(f"recovered {total} P1 trials across {len(trials)} cells")
    for tag, recs in sorted(trials.items()):
        print(f"  {tag}: n={len(recs)}")

    findings = dd.load_findings()
    findings["trials"] = {"p1": trials}
    findings["verdicts"] = {}
    findings.pop("decision", None)
    findings.pop("aborted", None)
    findings["baseline_registers"] = BASELINE_REGISTERS
    findings["applied_floor"] = None
    findings["started_at"] = min(timestamps) if timestamps else None
    findings.setdefault("seed", None)
    dd.save_findings(findings)

    verdict = dd.verdict_p1(findings)
    print()
    print(f"recomputed P1 verdict: effect={verdict['effect']} "
         f"rule={verdict['rule']} p={verdict['p_value']}")
    print(f"per_sign: {verdict['per_sign']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
