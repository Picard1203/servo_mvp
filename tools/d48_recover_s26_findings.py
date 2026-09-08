#!/usr/bin/env python3
"""One-off recovery: rebuilds archive/d48_s26_findings.json from its own CSV.

Run once, 8 Sept 2026. `camp.preflight` (in tools/d48_s26_campaign.py) ends
with a `save_findings(findings)` call that resolves to *that module's own*
`save_findings`/`FINDINGS_PATH`, not the caller's - so when today's
unrelated D48 decisive run called `camp.preflight(base_url, findings)`
during its own startup, it silently overwrote this file with a stale
snapshot of the decisive run's own findings, destroying the archived B7/B8/
B9 confirmatory results from the session before.

The per-trial CSV (archive/jitter_trial_d48_s26b.csv) is append-only and
was never touched, so every trial - B7's 12-level dose response, B8's dead-
zone x floor factorial, B9's two-angle confirmatory run - is intact there.
This rebuilds the JSON from it, including the derived comparisons and
dose-response tables, using the campaign tool's own real analysis
functions rather than recomputing the logic by hand here.

    python3 tools/d48_recover_s26_findings.py
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import d48_s26_campaign as camp
import jitter_probe as jp

CSV_PATH = os.path.join(jp.ARCHIVE_DIR, "jitter_trial_d48_s26b.csv")

# Locked the same day (Session 26, before B9 ran), clamped to the tool's own
# ceilings (R_MAX_CEILING=5 already satisfied; C_MAX_CEILING_A=0.015 is
# lower than the raw locked 0.0221A, so the ceiling is what was actually in
# effect) - matches the r_max/c_max used for this session's own hand
# analysis of the same trials, done before this file was overwritten.
R_MAX = 3
C_MAX_A = camp.C_MAX_CEILING_A

# Registers as read live from the servo this session, before any of this
# tool's own writes - the real boot baseline.
BASELINE_REGISTERS = {
    "position_p": 24, "position_d": 32, "position_i": 0,
    "min_start_force": 150, "cw_dead_zone": 0, "ccw_dead_zone": 0,
    "speed_p": 10, "speed_i": 200,
}


def _phase_arm(tag: str) -> tuple[str, str]:
    """Splits a CSV tag back into (phase, arm), the way the tool wrote it.

    Args:
        tag (str): The "tag" column, e.g. "b9_m60__msf_45" or
            "b7__msf_baseline_150".

    Returns:
        tuple[str, str]: (phase, arm).
    """
    phase, arm = tag.split("__", 1)
    return phase, arm


def main() -> int:
    """Rebuilds every phase's trials and derived analysis, then saves.

    Returns:
        int: 0 on success, 1 if the CSV is missing.
    """
    if not os.path.exists(CSV_PATH):
        print(f"no CSV at {CSV_PATH}; nothing to recover")
        return 1

    trials: dict = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            phase, arm = _phase_arm(row["tag"])
            record = {
                "replicate": int(row["repeat"]),
                "reversals": int(row["reversals"]),
                "median_period_s": (float(row["median_period_s"])
                                    if row["median_period_s"] else None),
                "period_stdev_s": (float(row["period_stdev_s"])
                                   if row["period_stdev_s"] else None),
                "current_mean_a": float(row["current_mean_a"]),
                "current_peak_a": (float(row["current_peak_a"])
                                   if row["current_peak_a"] else None),
                "drive_duty": (float(row["drive_duty"])
                              if row["drive_duty"] else None),
                "current_on_target_a": (float(row["current_on_target_a"])
                                        if row["current_on_target_a"] else None),
                "swing_deg": (float(row["swing_deg"])
                             if row["swing_deg"] else None),
                "final_error_deg": float(row["final_error_deg"]),
                "settled_short": row["settled_short"] == "True",
                "achieved_hz": (float(row["achieved_hz"])
                               if row["achieved_hz"] else None),
                "temperature_c_mean": (float(row["temperature_c_mean"])
                                       if row["temperature_c_mean"] else None),
                "timestamp": row["timestamp"],
                "reconstructed_from_csv": True,
            }
            trials.setdefault(phase, {}).setdefault(arm, []).append(record)

    for phase, arms in sorted(trials.items()):
        print(f"{phase}: " + ", ".join(f"{arm}={len(recs)}"
                                       for arm, recs in sorted(arms.items())))

    findings = camp.load_findings()
    findings["trials"] = trials
    findings["comparisons"] = {}
    findings["dose_response"] = {}
    findings.pop("gates", None)
    findings["r_max"] = R_MAX
    findings["c_max"] = C_MAX_A
    findings["baseline_registers"] = BASELINE_REGISTERS
    findings.setdefault("seed", None)

    # Recompute every derived table with the tool's own real functions,
    # not by hand here - the same logic the original run used.
    if "b7" in trials:
        camp._record_arm_comparison(findings, "b7", "msf_baseline_150")
        camp._record_dose_response(findings, "b7", "min_start_force")
    if "b8" in trials:
        camp._record_arm_comparison(findings, "b8", "msf150_dz0")
    for phase in ("b9_m60", "b9_p45"):
        if phase in trials:
            camp._record_arm_comparison(findings, phase, "baseline_150")
            camp._record_dose_response(findings, phase, "min_start_force")

    camp.save_findings(findings)
    print(f"\nrestored to {camp.FINDINGS_PATH}")
    for phase in ("b7", "b8", "b9_m60", "b9_p45"):
        if phase in findings.get("comparisons", {}):
            print(f"\n{phase} comparisons:")
            for arm, stats in sorted(findings["comparisons"][phase].items()):
                print(f"  {arm}: {stats['oscillating']}/{stats['n']} "
                     f"oscillating, status={stats['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
