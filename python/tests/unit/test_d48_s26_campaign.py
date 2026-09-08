"""Unit tests for tools/d48_s26_campaign.py's statistics and selection logic (D48).

No hardware, no network - `run_block`/`probe_resilient` talk to a live board
and are out of scope here. What this guards is the pure, hardware-free layer
underneath them: the Fisher-exact comparison, the oscillation call, the
promote/drop/re-screen filter, and above all `_record_dose_response`'s "best"
picker - the exact function Session 26 found picking a coin-flip arm
(`min_start_force=85`, 3 clean / 3 oscillating of 6) because it judged by
median swing instead of the pass/fail proportion. That is the regression this
file exists to catch.
"""
import inspect
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import d48_s26_campaign as camp


@pytest.fixture(autouse=True)
def _isolate_findings_path(tmp_path, monkeypatch):
    """Redirects every save_findings() call in this module to a temp file.

    `_record_arm_comparison` and `_record_dose_response` - the two
    functions most of this file exercises - call `save_findings(findings)`
    unconditionally, and that writes to the module-level `FINDINGS_PATH`,
    not to the synthetic dict the test built. Without this, running the
    tests overwrites the real, shared archive/d48_s26_findings.json with
    fixtures. The sibling suite for `d48_decisive.py` carries the same
    guard, for the same reason, after that exact accident destroyed a live
    run's results. Autouse, so a test added later is covered without
    having to remember it.
    """
    monkeypatch.setattr(camp, "FINDINGS_PATH",
                        str(tmp_path / "test_d48_s26_findings.json"))


def _trial(reversals: int, current_mean_a: float = 0.0,
          swing_deg: float = 0.0, final_error_deg: float = 0.0,
          drive_duty: float = 0.0, current_on_target_a: float = 0.0) -> dict:
    """Builds one synthetic trial record with the fields the tool reads.

    Args:
        reversals (int): Reversal count.
        current_mean_a (float): Mean current in the score window.
        swing_deg (float): Post-move swing.
        final_error_deg (float): Signed final positioning error.
        drive_duty (float): Fraction of the window spent driving.
        current_on_target_a (float): Current once settled.

    Returns:
        dict: A trial record shaped like `run_block` writes.
    """
    return {
        "reversals": reversals, "current_mean_a": current_mean_a,
        "swing_deg": swing_deg, "final_error_deg": final_error_deg,
        "drive_duty": drive_duty, "current_on_target_a": current_on_target_a,
        "median_period_s": None,
    }


class TestIsOscillating:
    """The pre-registered oscillation call: reversals or current over bar."""

    def test_clean_trial_is_not_oscillating(self):
        assert not camp.is_oscillating(_trial(0, 0.0), r_max=3, c_max=0.02)

    def test_reversals_over_bar_is_oscillating(self):
        assert camp.is_oscillating(_trial(4, 0.0), r_max=3, c_max=0.02)

    def test_current_over_bar_is_oscillating_even_with_no_reversals(self):
        # Correction that never crosses a full encoder count is invisible to
        # reversal counting but still shows up as elevated current - the
        # reason this is an "or", not just a reversal check.
        assert camp.is_oscillating(_trial(0, 0.03), r_max=3, c_max=0.02)

    def test_uncalibrated_thresholds_fall_back_to_reversals_over_three(self):
        assert not camp.is_oscillating(_trial(3, 999.0), r_max=None, c_max=None)
        assert camp.is_oscillating(_trial(4, 0.0), r_max=None, c_max=None)


class TestSummarise:
    """Reduces a trial list to n, oscillating count, and medians."""

    def test_counts_and_rate(self):
        trials = [_trial(0), _trial(0), _trial(10, 0.05)]
        stats = camp.summarise(trials, r_max=3, c_max=0.02)
        assert stats["n"] == 3
        assert stats["oscillating"] == 1
        assert stats["rate"] == 1 / 3

    def test_empty_trials_do_not_divide_by_zero(self):
        stats = camp.summarise([], r_max=3, c_max=0.02)
        assert stats["n"] == 0
        assert stats["rate"] is None


class TestFisherExactOneSided:
    """One-sided hypergeometric p-value for the arm-vs-baseline comparison."""

    def test_maximally_extreme_table_is_near_zero(self):
        # 0/10 oscillating in the arm vs 10/10 in the baseline: the most
        # extreme table these margins allow.
        p = camp.fisher_exact_one_sided(0, 10, 10, 0)
        assert p < 1e-4

    def test_identical_rates_are_not_significant(self):
        # Same 5/10 oscillation rate in both groups: no evidence of a
        # difference, so this must not read as a passing arm.
        p = camp.fisher_exact_one_sided(5, 5, 5, 5)
        assert p > 0.3


class TestScreeningArmFilter:
    """The pre-declared promote / drop / re-screen rule."""

    def test_baseline_always_kept_up_to_confirm_n(self):
        keep = camp.screening_arm_filter(r_max=3, c_max=0.02, baseline_arm="base")
        block = {"base": [_trial(0)] * (camp.CONFIRM_N - 1)}
        assert keep(block, "base") is True
        block["base"].append(_trial(0))
        assert keep(block, "base") is False

    def test_arm_below_screen_size_always_runs(self):
        keep = camp.screening_arm_filter(r_max=3, c_max=0.02, baseline_arm="base")
        block = {"arm": [_trial(0)] * (camp.SCREEN_N - 1)}
        assert keep(block, "arm") is True

    def test_futile_arm_drops_at_screen_size(self):
        keep = camp.screening_arm_filter(r_max=3, c_max=0.02, baseline_arm="base")
        block = {"arm": [_trial(10, 0.05)] * camp.SCREEN_N}
        assert keep(block, "arm") is False

    def test_clean_arm_promotes_to_confirm_n(self):
        keep = camp.screening_arm_filter(r_max=3, c_max=0.02, baseline_arm="base")
        block = {"arm": [_trial(0)] * camp.SCREEN_N}
        assert keep(block, "arm") is True
        block["arm"] = [_trial(0)] * camp.CONFIRM_N
        assert keep(block, "arm") is False


class TestRecordDoseResponsePicksByProportionNotMedian:
    """Regression test for the exact bug D48's own entry found in Session 26.

    `_record_arm_comparison` must run first - it is what writes the
    `status` this function now reads, mirroring how `block_b7` calls them
    in sequence.
    """

    def _findings(self) -> dict:
        return {"trials": {}, "gates": {}, "eeprom_writes": 0,
               "r_max": 3, "c_max": 0.02}

    def test_coinflip_arm_is_not_picked_over_a_clean_higher_arm(self):
        findings = self._findings()
        block = findings["trials"].setdefault("b7", {})
        # Baseline: mostly oscillating, matches Session 26's msf_150.
        block["msf_baseline_150"] = [_trial(20, 0.05, swing_deg=0.3)] * 6
        # msf_85: 3 clean / 3 oscillating - low median swing (a coin flip
        # reads as "settled" under the old median-based picker), but this
        # is exactly the arm that must NOT win.
        block["msf_85"] = ([_trial(0, 0.0, swing_deg=0.0)] * 3
                           + [_trial(27, 0.05, swing_deg=0.3)] * 3)
        # msf_45: genuinely clean across all 6 - the real candidate.
        block["msf_45"] = [_trial(0, 0.0, swing_deg=0.0)] * 6

        camp._record_arm_comparison(findings, "b7", "msf_baseline_150")
        camp._record_dose_response(findings, "b7", "min_start_force")

        assert findings["b7_best_min_start_force"] == 45
        rows = findings["dose_response"]["b7"]["rows"]
        assert rows["msf_85"]["status"] not in (
            "MEETS_ACCEPTANCE_BAR", "BETTER_THAN_BASELINE")

    def test_no_arm_passes_leaves_best_unset(self):
        findings = self._findings()
        block = findings["trials"].setdefault("b7", {})
        block["msf_baseline_150"] = [_trial(20, 0.05)] * 6
        block["msf_10"] = [_trial(18, 0.04)] * 6

        camp._record_arm_comparison(findings, "b7", "msf_baseline_150")
        camp._record_dose_response(findings, "b7", "min_start_force")

        assert "b7_best_min_start_force" not in findings


class TestBlockB9Registered:
    """B9 (the confirmatory re-test) is wired into the block table."""

    def test_b9_is_registered(self):
        assert camp.BLOCKS["b9"] is camp.block_b9

    def test_b9_does_not_depend_on_a_selected_test_angle(self):
        # Unlike b3-b8, b9 names its own two angles (-60/+45) rather than
        # reading findings["test_angle"] from B0 - it must not silently
        # no-op the way those blocks do when that key is absent.
        source = inspect.getsource(camp.block_b9)
        assert 'findings.get("test_angle")' not in source
        assert "-60.0" in source and "45.0" in source


class TestPreflightDoesNotPersist:
    """`preflight` records into the caller's dict but must not write it out.

    It writes into whatever findings dict it is handed, and this module's
    own findings path is the wrong destination whenever the caller keeps
    its results somewhere else. `d48_decisive.py` calls it with the
    decisive run's dict; the save inside it silently overwrote a whole
    day of campaign results with an unrelated run's snapshot. The caller
    owns persistence now.
    """

    def test_preflight_does_not_call_save_findings(self, monkeypatch):
        saved = []
        monkeypatch.setattr(camp, "save_findings",
                            lambda findings: saved.append(findings))
        monkeypatch.setattr(camp, "read_registers", lambda base_url: {
            "position_p": 24, "position_d": 32, "position_i": 0,
            "min_start_force": 40, "cw_dead_zone": 0, "ccw_dead_zone": 0,
            "speed_p": 10, "speed_i": 200})
        monkeypatch.setattr(camp, "measure_rate",
                            lambda base_url: float(camp.MIN_FAST_HZ) + 10.0)
        findings: dict = {}

        camp.preflight("http://board.invalid", findings)

        assert saved == []
        assert findings["preflight_hz"] == camp.MIN_FAST_HZ + 10.0

    def test_preflight_source_has_no_save_call(self):
        # The dict it is handed may belong to another tool entirely, so the
        # guarantee has to hold for every path through the function, not
        # only the one the test above exercises.
        assert "save_findings" not in inspect.getsource(camp.preflight)
