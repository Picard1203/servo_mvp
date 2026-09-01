"""Unit tests for tools/synthetic_operator.py."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import synthetic_operator  # noqa: E402


class TestQuantizeDeg:
    """Tests for quantize_deg() step quantization."""

    def test_exact_step_multiples_preserved(self) -> None:
        """Exact multiples of 0.06 deg should remain unchanged."""
        assert synthetic_operator.quantize_deg(0.0, 0.06) == 0.0
        assert synthetic_operator.quantize_deg(0.06, 0.06) == 0.06
        assert synthetic_operator.quantize_deg(-0.06, 0.06) == -0.06
        assert synthetic_operator.quantize_deg(23.4, 0.06) == 23.4
        assert synthetic_operator.quantize_deg(-45.0, 0.06) == -45.0

    def test_non_multiples_snapped_to_nearest_step(self) -> None:
        """Arbitrary floating point angles snap to nearest 0.06 grid."""
        # 0.05 is closer to 0.06 than 0.00
        assert synthetic_operator.quantize_deg(0.05, 0.06) == 0.06
        # 0.02 is closer to 0.00 than 0.06
        assert synthetic_operator.quantize_deg(0.02, 0.06) == 0.0
        # 23.42 should snap to 23.40 (390 * 0.06)
        assert synthetic_operator.quantize_deg(23.42, 0.06) == 23.4
        # -45.04 should snap to -45.06 (751 * -0.06)
        assert synthetic_operator.quantize_deg(-45.04, 0.06) == -45.06


class TestClassifySettleResult:
    """Tests for classify_settle_result() convergence classification."""

    def test_exact_match_converges(self) -> None:
        """A measured angle equal to the commanded one always converges."""
        assert synthetic_operator.classify_settle_result(
            90.0, 90.0, tolerance_deg=0.1) == "converged"

    def test_within_tolerance_converges(self) -> None:
        """A small deviation inside the stated tolerance still converges."""
        assert synthetic_operator.classify_settle_result(
            90.0, 90.05, tolerance_deg=0.1) == "converged"

    def test_beyond_tolerance_is_short(self) -> None:
        """The operator's own report: a real shortfall reads as short."""
        assert synthetic_operator.classify_settle_result(
            90.0, 89.0, tolerance_deg=0.1) == "short"

    def test_boundary_at_exactly_the_tolerance_converges(self) -> None:
        """The tolerance boundary itself counts as converged, not short."""
        assert synthetic_operator.classify_settle_result(
            90.0, 90.1, tolerance_deg=0.1) == "converged"


class TestFindMinimumEffectiveStep:
    """Tests for find_minimum_effective_step() threshold detection."""

    def test_first_moving_step_wins(self) -> None:
        """The smallest step that moved is returned, not the largest."""
        samples = [(0.06, False), (0.12, False), (0.30, True), (0.60, True)]
        assert synthetic_operator.find_minimum_effective_step(
            samples) == 0.30

    def test_smallest_step_already_moves(self) -> None:
        """No stiction at all: even the finest step produced movement."""
        samples = [(0.06, True), (0.12, True)]
        assert synthetic_operator.find_minimum_effective_step(
            samples) == 0.06

    def test_nothing_moved_returns_none(self) -> None:
        """Every sampled step failed to move: no threshold exists yet."""
        samples = [(0.06, False), (0.12, False), (3.00, False)]
        assert synthetic_operator.find_minimum_effective_step(
            samples) is None


class TestMetricsTally:
    """Tests for Metrics class request and stream tracking."""

    def test_request_metrics_and_rejection_reasons(self) -> None:
        """Requests, failures, and refusals categorized by reason."""
        m = synthetic_operator.Metrics()
        m.record_request_success("move", 0.050)
        m.record_request_success("move", 0.100)
        m.record_request_rejection("move", "locked")
        m.record_request_rejection("move", "locked")
        m.record_request_rejection("move", "moving")
        m.record_request_failure("move")

        summary = m.summary()
        assert summary["requests"] == 6
        assert summary["failures"] == 1
        assert summary["rejections"] == 3

        move_act = summary["actions"]["move"]
        assert move_act["count"] == 2
        assert move_act["median_s"] == 0.075
        assert move_act["failures"] == 1
        assert move_act["rejections"] == 3
        assert move_act["rejections_by_reason"] == {"locked": 2, "moving": 1}

    def test_stream_metrics_cadence_and_gaps(self) -> None:
        """Stream frame reception and inter-arrival jitter calculation."""
        m = synthetic_operator.Metrics()
        m.record_stream_open(is_reconnect=False)
        m.record_stream_frame("state", 0.50)
        m.record_stream_frame("state", 0.52)
        m.record_stream_frame("state", 2.10)  # gap > 2.0s
        m.record_stream_frame("positions", None)
        m.record_stream_failure()
        m.record_stream_open(is_reconnect=True)
        m.record_reading(False, None)

        summary = m.summary()
        stream = summary["stream"]
        assert stream["frames_total"] == 4
        assert stream["connection_opens"] == 2
        assert stream["reconnects"] == 1
        assert stream["failures"] == 1
        assert stream["gaps_over_2s"] == 1
        assert stream["cadence"]["median_s"] == 0.52
        assert stream["cadence"]["max_gap_s"] == 2.1
        assert summary["invalid_readings"] == 1
        assert summary["unknown_positions"] == 1
