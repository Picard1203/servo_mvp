"""Unit tests for tools/jitter_probe.py's scoring logic (D48).

Synthetic traces only - the crux of the whole experiment is that the metric
scores correctly, and no hardware can confirm that, only known-answer traces
can. Guards two faults found reading the previous version of this tool:
reversal counting had no way to separate real jitter from readout noise
(both are the same 1-count amplitude here), and a move settling short of
target used to score as a silent perfect pass.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import jitter_probe

COUNT_DEG = 0.06
TARGET_DEG = -60.0


def _trace(samples: list[tuple[float, float, float]]) -> list[tuple[float, float, float]]:
    """Builds a (elapsed_s, output_deg, current_a) trace from short samples.

    Args:
        samples (list[tuple[float, float, float]]): elapsed_s, output_deg, current_a.

    Returns:
        list[tuple[float, float, float]]: The same trace, typed for score_trial.
    """
    return list(samples)


class TestCleanSettle:
    """A move that reaches target and stays there registers no failure."""

    def test_zero_reversals(self):
        trace = _trace([
            (0.0, -55.0, 0.4), (1.0, -59.0, 0.3), (2.0, -60.0, 0.1),
            (5.0, -60.0, 0.05), (8.0, -60.0, 0.05), (12.0, -60.0, 0.05),
            (15.0, -60.0, 0.05),
        ])
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["reversals"] == 0
        assert result["settled_short"] is False
        assert result["final_error_deg"] == 0.0


class TestSustainedJitter:
    """A regular back-and-forth alternation inside the score window is caught."""

    def test_periodic_alternation_is_counted_with_its_period(self):
        # Alternates every 0.5s starting at t=5.0, one count (0.06 deg) each way.
        trace = [(0.0, -55.0, 0.4), (2.0, -60.0, 0.1)]
        t = 5.0
        val = TARGET_DEG
        up = True
        while t <= 15.0:
            val = TARGET_DEG + COUNT_DEG if up else TARGET_DEG
            trace.append((t, val, 0.3))
            up = not up
            t += 0.5
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["reversals"] >= 8
        assert result["median_period_s"] is not None
        assert abs(result["median_period_s"] - 0.5) < 0.05
        assert result["period_stdev_s"] < 0.05  # regular -> low spread

    def test_reversals_before_score_window_are_not_counted(self):
        # Fine-approach overshoot-then-return happens before t=5.0 and must
        # not be mistaken for sustained trembling.
        trace = [
            (0.0, -55.0, 0.4), (1.0, -61.5, 0.5), (2.0, -60.0, 0.1),
            (5.0, -60.0, 0.05), (8.0, -60.0, 0.05), (15.0, -60.0, 0.05),
        ]
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["reversals"] == 0

    def test_irregular_flicker_has_higher_period_spread_than_regular_jitter(self):
        # Same amplitude (1 count) as the periodic case, but at irregular
        # intervals - this is the case an amplitude-only filter cannot see,
        # since real jitter and this flicker are the same size.
        trace = [(0.0, -55.0, 0.4), (2.0, -60.0, 0.1)]
        times = [5.1, 5.4, 7.9, 8.0, 8.05, 11.0, 14.9]
        up = True
        for t in times:
            val = TARGET_DEG + COUNT_DEG if up else TARGET_DEG
            trace.append((t, val, 0.05))
            up = not up
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["reversals"] >= 4
        assert result["period_stdev_s"] > 0.5


class TestSettledShort:
    """The false-negative D48 exists to close: not reaching target must FAIL."""

    def test_settling_short_of_target_is_a_failure_not_a_clean_pass(self):
        trace = [
            (0.0, -30.0, 0.4), (2.0, -55.0, 0.2),
            (5.0, -56.0, 0.05), (8.0, -56.0, 0.05), (15.0, -56.0, 0.05),
        ]
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["settled_short"] is True
        assert result["final_error_deg"] == 4.0
        # The old bug: this used to report reversals=0, swing=0.0 here,
        # which is indistinguishable from a perfect settle.
        assert result["reversals"] == 0
        assert result["final_deg"] == -56.0

    def test_settling_short_with_a_stable_final_reading_still_fails(self):
        # Guards against re-deriving "settled short" from swing alone -
        # a short settle can itself be perfectly steady.
        trace = [(t, -57.5, 0.05) for t in (0.0, 5.0, 10.0, 15.0)]
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["settled_short"] is True
        assert result["reversals"] == 0


class TestEmptyTrace:
    """An empty trace (network failure mid-probe) reports None, not a crash."""

    def test_empty_trace(self):
        result = jitter_probe.score_trial([], TARGET_DEG)
        assert result["final_deg"] is None
        assert result["settled_short"] is None
        assert result["reversals"] == 0


class TestCurrentStats:
    """Current is summarised over the score window only, for the mechanism read."""

    def test_current_stats_exclude_samples_outside_the_score_window(self):
        trace = [
            (0.0, -55.0, 5.0),  # huge current during the approach - excluded
            (2.0, -60.0, 5.0),  # still before the window - excluded
            (6.0, -60.0, 0.2), (10.0, -60.0, 0.4), (14.0, -60.0, 0.2),
        ]
        result = jitter_probe.score_trial(trace, TARGET_DEG)
        assert result["current_peak_a"] == 0.4
        assert abs(result["current_mean_a"] - 0.2667) < 0.001


class TestResetPositionEpsilonRenamed:
    """RESET_STABLE_SECONDS was a degree threshold, not a duration - renamed."""

    def test_old_misleading_name_is_gone(self):
        assert not hasattr(jitter_probe, "RESET_STABLE_SECONDS")

    def test_renamed_constant_is_a_degree_epsilon(self):
        assert jitter_probe.RESET_POSITION_EPSILON_DEG < 1.0

    def test_reset_stability_is_time_based(self):
        assert jitter_probe.RESET_STABLE_SECONDS_REQUIRED > 0
