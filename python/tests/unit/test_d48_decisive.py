"""Unit tests for tools/d48_decisive.py's geometry and verdict logic (D48).

No hardware. What this guards is everything the run depends on being right
*before* several hours of rig time are spent on it: the anchor geometry that
forces an arrival direction, the round-trip against the rule the app itself
uses to pick that direction, and the branch verdicts that decide which
hypothesis the run pursues next.

The geometry is the load-bearing part. The whole design rests on being able
to force the final leg's arrival side from the host by choosing which side
the anchor sits on; if that mapping is inverted, every trial measures the
opposite of what it records and the run is worse than useless.
"""
import json
import sys
from pathlib import Path
from typing import Optional

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import d48_decisive as dd

STEP_DEG = 0.06


@pytest.fixture(autouse=True)
def _isolate_findings_path(tmp_path, monkeypatch):
    """Redirects every save_findings() call in this module to a temp file.

    `decide()`, `verdict_floors()` and `verdict_p1()` (outside dry_run) all
    call `save_findings(findings)`, which writes to the module-level
    `FINDINGS_PATH` regardless of what dict was passed in - not the
    argument the test constructed. A test calling any of them on a plain
    synthetic dict was silently overwriting the real, shared
    archive/d48_decisive_findings.json with test fixtures every time this
    file ran; that happened for real and destroyed a live hardware run's
    P1 results. Autouse, so a new test that calls a saving function later
    is protected without having to remember to add this itself.
    """
    monkeypatch.setattr(dd, "FINDINGS_PATH",
                        str(tmp_path / "test_d48_decisive_findings.json"))


def _trial(target_deg: float, arrival: str, first_error: float,
          oscillating: bool = False, floor: int = 45,
          max_abs_error: Optional[float] = None,
          current_mean_a: Optional[float] = None,
          c_max_used_a: Optional[float] = None) -> dict:
    """Builds one synthetic trial record shaped like run_trial writes.

    Args:
        target_deg (float): Scored target angle.
        arrival (str): Forced arrival direction.
        first_error (float): Signed error of the forced-approach landing.
        oscillating (bool): Whether the trial scored as oscillating.
        floor (int): Minimum-drive floor in force.
        max_abs_error (float): Worst landing error; defaults to first_error.
        current_mean_a (Optional[float]): Mean current, for the
            non-gating "strained" diagnostic.
        c_max_used_a (Optional[float]): Threshold that reading was
            compared against, for the same diagnostic.

    Returns:
        dict: A trial record.
    """
    worst = abs(first_error) if max_abs_error is None else max_abs_error
    accurate = worst <= dd.GATE_DEG
    return {
        "phase": "p1", "floor": floor, "target_deg": target_deg,
        "arrival": arrival, "first_error_deg": first_error,
        "max_abs_error_deg": worst, "oscillating": oscillating,
        "current_mean_a": current_mean_a, "c_max_used_a": c_max_used_a,
        "accurate": accurate, "passed": bool(accurate and not oscillating),
    }


def _findings(trials: list[dict], phase: str = "p1") -> dict:
    """Wraps trial records in a findings structure keyed the way the tool keys it.

    Args:
        trials (list[dict]): Trial records.
        phase (str): Phase key to file them under.

    Returns:
        dict: A findings dict.
    """
    blocks: dict = {}
    for trial in trials:
        tag = (f"{phase}__msf{trial['floor']}_{trial['arrival']}"
               f"_{trial['target_deg']:+.0f}")
        blocks.setdefault(tag, []).append(trial)
    return {"trials": {phase: blocks}, "verdicts": {}, "eeprom_writes": 0}


class TestQuantize:
    """Angles must land exactly on the grid the API will accept."""

    def test_snaps_to_the_nearest_grid_point(self):
        assert dd.quantize(-75.0) == -75.0
        assert dd.quantize(0.0) == 0.0
        # An off-grid angle moves by less than half a step, never further.
        assert abs(dd.quantize(-74.55) - (-74.55)) <= STEP_DEG / 2 + 1e-9

    def test_result_passes_the_api_step_check(self):
        # The backend refuses anything off the grid by more than 1e-6 of a
        # step, so a rounding scheme that drifts is a run that dies on a 422.
        for raw in (-89.97, -74.55, -60.02, -0.004, 12.3456, 89.999):
            multiples = dd.quantize(raw) / STEP_DEG
            assert abs(multiples - round(multiples)) < 1e-6


class TestAnchorGeometry:
    """The anchor side is what forces the arrival side."""

    def test_up_arrival_anchors_above_target(self):
        assert dd.anchor_for(-60.0, "up") > -60.0

    def test_down_arrival_anchors_below_target(self):
        assert dd.anchor_for(-60.0, "down") < -60.0

    def test_round_trip_matches_the_app_own_rule(self):
        # The invariant the entire run rests on: an anchor chosen to force
        # an arrival must actually produce that arrival under the rule
        # motion_service uses (overshoot beyond target, final leg returns).
        for target in (-90.0, -75.0, -60.0, -45.0, 0.0, 45.0, 60.0, 90.0):
            for arrival in ("up", "down"):
                anchor = dd.anchor_for(target, arrival)
                if anchor is None:
                    continue
                assert dd.natural_arrival(anchor, target) == arrival

    def test_unreachable_arrival_returns_none_at_the_travel_limits(self):
        # At +90 there is no room above to anchor, so arriving upward is
        # impossible; the cell must be skipped, not silently mis-run.
        assert dd.anchor_for(90.0, "up") is None
        assert dd.anchor_for(-90.0, "down") is None
        assert dd.anchor_for(90.0, "down") is not None
        assert dd.anchor_for(-90.0, "up") is not None

    def test_anchor_clears_the_overshoot_distance(self):
        # A separation smaller than the 1.5 deg overshoot would let the
        # overshoot cross the anchor and invert the arrival direction.
        for target in (-75.0, 0.0, 75.0):
            for arrival in ("up", "down"):
                anchor = dd.anchor_for(target, arrival)
                if anchor is not None:
                    assert abs(anchor - target) >= dd.MIN_APPROACH_DEG


class TestNaturalArrival:
    """Mirrors motion_service's own direction choice."""

    def test_target_above_start_arrives_downward(self):
        assert dd.natural_arrival(-90.0, -75.0) == "down"

    def test_target_below_start_arrives_upward(self):
        assert dd.natural_arrival(-74.55, -75.0) == "up"

    def test_no_op_move_has_no_arrival(self):
        assert dd.natural_arrival(-75.0, -75.0) is None
        assert dd.natural_arrival(None, -75.0) is None


class TestOscillationIsMovementOnly:
    """Oscillation is decided by reversals alone - the operator's own rule.

    Regression test for a live trial this run actually produced: floor 45,
    0 deg, arriving up - reversals=0, swing_deg=0.0, an identical landing
    on all four independent attempts, current 0.0177A against a 0.015A
    threshold. The shared campaign `is_oscillating` flagged it purely on
    current, mislabeling a servo stuck-but-static as "hunting". The
    operator's own call, watching the rig directly: as long as it does not
    move, it is not oscillating, no matter the current - even a correction
    attempt that fails to actually move the shaft is not oscillation, it is
    the minimum-drive floor being too low to break free. Current is no
    longer part of this decision at all; the accuracy check independently
    fails a trial that is stuck off-target regardless.
    """

    def test_static_trial_with_elevated_current_is_not_oscillating(self):
        trial = {"reversals": 0, "current_mean_a": 0.0177}
        assert dd.is_oscillating(trial, r_max=3, c_max=0.015) is False

    def test_high_current_never_triggers_it_on_its_own(self):
        # The operator's own explicit bar: not even 0.2A counts, as long as
        # nothing actually moved.
        trial = {"reversals": 0, "current_mean_a": 0.2}
        assert dd.is_oscillating(trial, r_max=3, c_max=0.015) is False

    def test_reversals_over_the_bar_is_oscillating_regardless_of_current(self):
        trial = {"reversals": 10, "current_mean_a": 0.0}
        assert dd.is_oscillating(trial, r_max=3, c_max=0.015) is True

    def test_reversals_at_or_under_the_bar_is_clean(self):
        trial = {"reversals": 3, "current_mean_a": 0.2}
        assert dd.is_oscillating(trial, r_max=3, c_max=0.015) is False

    def test_uncalibrated_threshold_falls_back_to_reversals_over_three(self):
        trial = {"reversals": 4, "current_mean_a": 0.0}
        assert dd.is_oscillating(trial, r_max=None, c_max=None) is True
        trial = {"reversals": 3, "current_mean_a": 999.0}
        assert dd.is_oscillating(trial, r_max=None, c_max=None) is False


class TestPerAngleCurrentThreshold:
    """`c_max_for` still matters for the non-gating "strained" diagnostic.

    Oscillation itself no longer reads current at all (see
    TestOscillationIsMovementOnly - the operator's own call). This
    threshold is what `score_floor`'s `passing_but_strained` count uses to
    flag an accurate, non-oscillating trial that is nonetheless drawing
    more current than simply holding station at that angle costs -
    informational only, never a failure.
    """

    def _findings_with_hold(self, hold_a: float) -> dict:
        return {"hold_reference": {"45": {"+75": hold_a}}}

    def test_quiet_angle_keeps_the_original_threshold(self):
        findings = self._findings_with_hold(0.0)
        assert dd.c_max_for(findings, 45, 75.0) == dd.C_MAX_FLOOR_A

    def test_unmeasured_angle_falls_back_to_the_original_threshold(self):
        assert dd.c_max_for({}, 45, -60.0) == dd.C_MAX_FLOOR_A

    def test_loaded_angle_raises_the_threshold_above_its_own_hold(self):
        findings = self._findings_with_hold(0.0173)
        assert dd.c_max_for(findings, 45, 75.0) > 0.0173

    def test_no_reversals_is_never_oscillating_however_high_the_current(self):
        # The exact trial that stopped an earlier run: no reversals, no
        # swing, no period, 0.0173A of pure holding current - and the
        # operator's explicit, unconditional rule since: current does not
        # decide oscillation at all, not even a much higher reading.
        findings = self._findings_with_hold(0.0150)
        c_max = dd.c_max_for(findings, 45, 75.0)
        for current in (0.0173, 0.082, 0.2):
            trial = {"reversals": 0, "current_mean_a": current}
            assert dd.is_oscillating(trial, dd.R_MAX, c_max) is False


class TestVerdictP1:
    """The branch decision: does arrival direction explain the miss?"""

    def test_clear_direction_effect_reads_dominant(self):
        # Mirrors the operator's own hand measurements: arriving upward
        # lands inside the gate, arriving downward misses by ~0.5 deg.
        trials = []
        for angle in (-75.0, -60.0, -30.0, 30.0, 60.0, 75.0):
            for _ in range(4):
                trials.append(_trial(angle, "up", 0.03))
                trials.append(_trial(angle, "down", 0.48))
        findings = _findings(trials)
        verdict = dd.verdict_p1(findings)
        assert verdict["effect"] == "DOMINANT"
        assert verdict["good_direction"] == "up"
        assert verdict["rule"] == "UNIVERSAL_UP"
        assert verdict["gate_reachable_open_loop"] is True

    def test_no_direction_effect_reads_none(self):
        trials = []
        for angle in (-75.0, -60.0, 60.0, 75.0):
            for _ in range(4):
                trials.append(_trial(angle, "up", 0.40))
                trials.append(_trial(angle, "down", 0.42))
        verdict = dd.verdict_p1(_findings(trials))
        assert verdict["effect"] == "NONE"
        assert verdict["gate_reachable_open_loop"] is False

    def test_direction_that_flips_with_angle_sign_is_reported(self):
        # A gravity-borne asymmetry would look exactly like this, and it
        # changes the fix from "always arrive up" to an angle-dependent rule.
        trials = []
        for angle in (-75.0, -60.0, -30.0):
            for _ in range(4):
                trials.append(_trial(angle, "up", 0.02))
                trials.append(_trial(angle, "down", 0.50))
        for angle in (30.0, 60.0, 75.0):
            for _ in range(4):
                trials.append(_trial(angle, "up", 0.50))
                trials.append(_trial(angle, "down", 0.02))
        verdict = dd.verdict_p1(_findings(trials))
        assert verdict["rule"] == "SIGN_DEPENDENT"

    def test_opposite_signed_effect_reads_sign_dominant_not_none(self):
        # Regression test for the bug this run actually hit: replays the
        # real P1 numbers from the 8 Sept run (per_sign inside-gate counts
        # 11/12 vs 0/12 negative, 6/12 vs 0/12 positive; pooled p=0.924). A
        # real, strong effect that flips sign averages to "no pooled
        # effect" - the branch decision must not read that as NONE and
        # send the run down the floor-search path with a direction that is
        # provably wrong for half the angles.
        trials = []
        neg_up = [0.03, 0.03, 0.03, 0.03, 0.05, 0.07, 0.13, 0.07, 0.08, 0.1,
                 0.04, 0.02]
        neg_down = [0.45, 0.51, 0.51, 0.33, 0.61, 0.61, 0.61, 0.67, 0.34,
                   0.4, 0.64, 0.4]
        pos_up = [0.55, 0.49, 0.55, 0.67, 0.51, 0.51, 0.51, 0.45, 0.52,
                 0.46, 0.46, 0.46]
        pos_down = [0.09, 0.09, 0.09, 0.09, 0.13, 0.13, 0.13, 0.25, 0.04,
                   0.14, 0.02, 0.14]
        for angle, value in zip([-75.0, -60.0, -30.0] * 4, neg_up, strict=True):
            trials.append(_trial(angle, "up", value))
        for angle, value in zip([-75.0, -60.0, -30.0] * 4, neg_down, strict=True):
            trials.append(_trial(angle, "down", value))
        for angle, value in zip([30.0, 60.0, 75.0] * 4, pos_up, strict=True):
            trials.append(_trial(angle, "up", value))
        for angle, value in zip([30.0, 60.0, 75.0] * 4, pos_down, strict=True):
            trials.append(_trial(angle, "down", value))

        verdict = dd.verdict_p1(_findings(trials))
        assert verdict["rule"] == "SIGN_DEPENDENT"
        assert verdict["effect"] == "SIGN_DOMINANT"
        assert verdict["per_sign"]["negative"]["better"] == "up"
        assert verdict["per_sign"]["positive"]["better"] == "down"
        assert verdict["per_sign"]["negative"]["dominant"] is True
        assert verdict["per_sign"]["positive"]["dominant"] is True
        assert verdict["gate_reachable_open_loop"] is True

    def test_dry_run_does_not_mutate_or_persist(self):
        # The provisional-read path a monitoring process uses must never
        # write into findings: this file is what a resumed run trusts, and
        # a premature or wrong verdict written to it would make a restart
        # skip trials it has not actually done.
        trials = [_trial(-60.0, "up", 0.02), _trial(-60.0, "down", 0.50)]
        findings = _findings(trials)
        before = json.loads(json.dumps(findings))
        dd.verdict_p1(findings, dry_run=True)
        assert findings == before
        assert "p1" not in findings["verdicts"]


class TestFloorVerdicts:
    """A floor ships only if every trial passed."""

    def test_clean_floor_passes_and_is_chosen(self):
        trials = [_trial(angle, "up", 0.02, floor=45)
                  for angle in (-90.0, -60.0, 0.0, 60.0, 90.0)
                  for _ in range(4)]
        findings = _findings(trials, phase="p2a")
        verdict = dd.verdict_floors(findings, "p2a", (45,))
        assert verdict["status"] == "FLOOR_FOUND"
        assert verdict["chosen_floor"] == 45

    def test_one_failure_is_marginal_not_a_pass(self):
        trials = [_trial(angle, "up", 0.02, floor=45)
                  for angle in (-90.0, -60.0, 0.0, 60.0)
                  for _ in range(4)]
        trials.append(_trial(-45.0, "up", 0.44, floor=45))
        findings = _findings(trials, phase="p2a")
        verdict = dd.verdict_floors(findings, "p2a", (45,))
        assert verdict["rows"][45]["status"] == "MARGINAL"
        assert verdict["status"] == "NO_VIABLE_FLOOR"

    def test_oscillating_trial_fails_the_floor_even_when_accurate(self):
        # The gate is a conjunction. An arm that lands perfectly while
        # hunting is not a pass - that is the whole point of this round.
        trials = [_trial(-60.0, "up", 0.01, oscillating=True, floor=70)
                  for _ in range(4)]
        findings = _findings(trials, phase="p2a")
        verdict = dd.verdict_floors(findings, "p2a", (70,))
        assert verdict["rows"][70]["oscillation_failures"] == 4
        assert verdict["status"] == "NO_VIABLE_FLOOR"

    def test_accurate_high_current_trial_passes_but_is_flagged_strained(self):
        # The operator's own rule: current alone never fails a trial. But
        # an accurate trial that is nonetheless straining should still be
        # visible in the writeup, not silently indistinguishable from one
        # that settled at near-zero current.
        trials = [_trial(0.0, "up", 0.02, floor=45,
                         current_mean_a=0.2, c_max_used_a=0.015)]
        findings = _findings(trials, phase="p2a")
        row = dd.score_floor(findings, "p2a", 45)
        assert row["status"] == "PASSES"
        assert row["passing_but_strained"] == 1
        assert row["strained_angles"] == [0.0]

    def test_highest_passing_floor_wins(self):
        trials = []
        for floor in (45, 55):
            trials += [_trial(angle, "up", 0.02, floor=floor)
                       for angle in (-60.0, 0.0, 60.0) for _ in range(4)]
        findings = _findings(trials, phase="p2a")
        verdict = dd.verdict_floors(findings, "p2a", (45, 55))
        assert verdict["chosen_floor"] == 55


class TestPhaseProbeGuardsMissingP1:
    """A post-hoc floor probe must not run without P1's direction rule."""

    def test_raises_without_a_p1_verdict(self):
        findings = {"verdicts": {}, "trials": {}}
        with pytest.raises(RuntimeError, match="no P1 verdict"):
            dd.phase_probe(None, findings, 65)


class TestDecision:
    """The run must end with a recommendation or a named blocker."""

    def test_floor_and_direction_produce_a_ship_decision(self):
        findings = {"trials": {}, "verdicts": {
            "p1": {"effect": "DOMINANT", "good_direction": "up",
                   "rule": "UNIVERSAL_UP"},
            "p2a": {"chosen_floor": 45, "status": "FLOOR_FOUND"},
            "p3": {"status": "CONVERGES"}}}
        decision = dd.decide(findings)
        assert decision["chosen_floor"] == 45
        assert "SHIP" in decision["headline"]

    def test_no_floor_but_converging_correction_names_software_as_the_fix(self):
        findings = {"trials": {}, "verdicts": {
            "p1": {"effect": "NONE", "good_direction": None,
                   "rule": "UNDETERMINED"},
            "p2b": {"chosen_floor": None, "status": "NO_VIABLE_FLOOR"},
            "p3": {"status": "CONVERGES"}}}
        decision = dd.decide(findings)
        assert decision["chosen_floor"] is None
        assert decision["software_correction"] == "required"
        assert "software" in decision["headline"]

    def test_nothing_passing_is_reported_as_no_decision(self):
        findings = {"trials": {}, "verdicts": {
            "p1": {"effect": "NONE"},
            "p2b": {"chosen_floor": None, "status": "NO_VIABLE_FLOOR"},
            "p3": {"status": "DOES_NOT_CONVERGE"}}}
        decision = dd.decide(findings)
        assert "NO DECISION" in decision["headline"]
