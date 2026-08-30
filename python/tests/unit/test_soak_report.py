"""tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded,
plus tests for client report aggregation, telemetry anomaly analysis, and R1 scorecard.
"""

import json
import os
from pathlib import Path
import sqlite3
import sys
import time

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import soak_report  # noqa: E402


@pytest.fixture(autouse=True)
def _israel_time(monkeypatch):
    """Forces a non-UTC timezone (IDT, UTC+3 in August) for this module.

    Returns:
        None.
    """
    monkeypatch.setenv("TZ", "Asia/Jerusalem")
    time.tzset()
    yield
    time.tzset()


def _write_jsonl(path: Path, records: list) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


class TestUtcLocalCutoff:
    """A record just outside the local cutoff but inside the UTC one."""

    SINCE_LOCAL = "2026-08-08T09:00:00"
    RECORD_UTC_TIMESTAMP = "2026-08-08T07:00:00.000"

    def test_report_log_counts_a_record_after_the_true_utc_cutoff(
            self, tmp_path):
        since = soak_report.parse_since(self.SINCE_LOCAL)
        log_path = tmp_path / "app.jsonl"
        _write_jsonl(log_path, [
            {"timestamp": self.RECORD_UTC_TIMESTAMP, "level": "WARNING",
             "metadata": {"event": "relay.conn.open"}},
        ])
        findings = soak_report.report_log(str(log_path), since)
        assert findings["records"] == 1, (
            "a record 1 hour after the true UTC cutoff was dropped - "
            "the cutoff was computed in local time again (D30)")

    def test_report_mcu_log_counts_a_record_after_the_true_utc_cutoff(
            self, tmp_path):
        since = soak_report.parse_since(self.SINCE_LOCAL)
        mcu_log_path = tmp_path / "mcu.jsonl"
        _write_jsonl(mcu_log_path, [
            {"timestamp": self.RECORD_UTC_TIMESTAMP, "level": "INFO",
             "event": "mcu.relay.write_lock_timeout"},
        ])
        findings = soak_report.report_mcu_log(str(mcu_log_path), since)
        assert findings["records"] == 1, (
            "a record 1 hour after the true UTC cutoff was dropped - "
            "the cutoff was computed in local time again (D30)")

    def test_utc_cutoff_is_not_a_local_reformat(self):
        """Pins _utc_cutoff() itself: the helper both call sites share."""
        since = soak_report.parse_since(self.SINCE_LOCAL)
        assert soak_report._utc_cutoff(since) == "2026-08-08T06:00:00"


class TestClientReportAggregation:
    """Tests for load_client_reports()."""

    def test_aggregates_multiple_reports(self, tmp_path: Path) -> None:
        rep1 = tmp_path / "rep1.json"
        rep2 = tmp_path / "rep2.json"

        data1 = {
            "operators": 2,
            "requests": 50,
            "failures": 0,
            "rejections": 2,
            "stream": {"frames_total": 100, "connection_opens": 2,
                       "reconnects": 0, "failures": 0, "gaps_over_2s": 0},
            "actions": {"move": {"count": 20, "failures": 0, "rejections": 1}},
        }
        data2 = {
            "operators": 1,
            "requests": 30,
            "failures": 1,
            "rejections": 0,
            "stream": {"frames_total": 50, "connection_opens": 1,
                       "reconnects": 0, "failures": 0, "gaps_over_2s": 0},
            "actions": {"move": {"count": 10, "failures": 1, "rejections": 0}},
        }
        rep1.write_text(json.dumps(data1))
        rep2.write_text(json.dumps(data2))

        combined = soak_report.load_client_reports([str(rep1), str(rep2)])
        assert combined is not None
        assert combined["total_operators"] == 3
        assert combined["total_requests"] == 80
        assert combined["total_failures"] == 1
        assert combined["total_rejections"] == 2
        assert combined["stream_frames"] == 150
        assert combined["actions"]["move"]["count"] == 30
        assert combined["actions"]["move"]["failures"] == 1


class TestScorecardAndTelemetry:
    """Tests for print_r1_scorecard() and report_telemetry() anomaly detection."""

    def test_scorecard_passes_when_clean(self) -> None:
        telemetry = {"stall_band_gaps": 0, "impossible_positions": []}
        log = {"errors": []}
        mcu_log = {"available": True, "write_lock_timeouts": 0}
        client = {"total_failures": 0, "total_requests": 100,
                  "stream_failures": 0, "stream_reconnects": 0}

        passed = soak_report.print_r1_scorecard(telemetry, log, mcu_log, client)
        assert passed is True

    def test_scorecard_fails_on_stall_or_failures(self) -> None:
        telemetry = {"stall_band_gaps": 1, "impossible_positions": []}
        log = {"errors": []}
        mcu_log = {"available": True, "write_lock_timeouts": 0}
        client = {"total_failures": 2, "total_requests": 100,
                  "stream_failures": 1, "stream_reconnects": 1}

        passed = soak_report.print_r1_scorecard(telemetry, log, mcu_log, client)
        assert passed is False

    def test_report_telemetry_detects_sags_and_impossible_positions(self, tmp_path: Path) -> None:
        db_path = tmp_path / "test.db"
        con = sqlite3.connect(str(db_path))
        con.execute(
            "CREATE TABLE telemetry (id INTEGER PRIMARY KEY, timestamp REAL, "
            "raw_counts INTEGER, voltage_v REAL, current_a REAL, temperature_c REAL, "
            "torque_kgcm REAL, overload INTEGER, overcurrent INTEGER, overheat INTEGER)"
        )
        t0 = 1000.0
        # Row 1: baseline
        con.execute("INSERT INTO telemetry VALUES (1, ?, 2048, 12.0, 0.2, 35.0, 0.5, 0, 0, 0)", (t0,))
        # Row 2: sag
        con.execute("INSERT INTO telemetry VALUES (2, ?, 2100, 4.1, 0.8, 36.0, 1.0, 0, 0, 0)", (t0 + 0.5,))
        # Row 3: impossible position (counts <= 0 after moved)
        con.execute("INSERT INTO telemetry VALUES (3, ?, 0, 12.1, 0.2, 35.5, 0.5, 0, 0, 0)", (t0 + 1.0,))
        con.commit()
        con.close()

        findings = soak_report.report_telemetry(str(db_path), since=900.0, sampler_interval_seconds=0.5)
        assert findings["samples"] == 3
        assert len(findings["voltage_sags"]) == 1
        assert findings["voltage_sags"][0]["voltage"] == 4.1
        assert len(findings["impossible_positions"]) == 1
        assert findings["impossible_positions"][0]["counts"] == 0
        assert findings["cadence_median_s"] == 0.5
