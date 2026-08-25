"""tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded.

D30: both JSONL logs are written in UTC. report_log()/report_mcu_log() typed
--since in the operator's own local time, converted it to an absolute
instant correctly, then reformatted that instant back to a cutoff *string*
using a LOCAL reformat instead of a UTC one - so on a 3-hour-offset machine
(IDT), every real record from a soak sorted as "before the cutoff", and the
first report after a genuinely catastrophic run printed "VERDICT: clean."

This machine's own clock is UTC, so a test that does not force a non-UTC
timezone would pass even with the bug reinstated - local and UTC coincide
here. TZ is forced and time.tzset() called so the test actually exercises
the gap the bug lived in.
"""

import json
import os
import sys
import time
from pathlib import Path

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
    time.tzset()  # restore the system default after this module


def _write_jsonl(path: Path, records: list) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


class TestUtcLocalCutoff:
    """A record just outside the local cutoff but inside the UTC one."""

    # Local "since": 2026-08-08T09:00:00 IDT (UTC+3) == 2026-08-08T06:00:00Z.
    SINCE_LOCAL = "2026-08-08T09:00:00"
    # One hour after the true UTC cutoff - must be counted.
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
