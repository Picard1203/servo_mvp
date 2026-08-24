"""Reads the board's own account of a soak and states the verdict.

`synthetic_operator.py` reports what the API answered. This reports what the
board recorded while answering, which is where the failures that matter have
always shown up:

- **Sampler gaps.** The signature of the W5500 race was a gap of almost
  exactly 11 s - the servo_read timeout plus one sampler interval. Any gap in
  that band means it is back.
- **Impossible positions.** A stored count of 0 or below, once the mechanism
  has moved off the bottom, is a failed read that became a position.
- **Failed reads and sampler exceptions.** Both are logged now; neither was
  before.
- **MCU-side counters (backlog D3).** `write_lock_timeouts` is the D4 race
  signature from the sketch's own side: non-zero means `loop()` held the
  W5500 too long. `rejected_total`/`dropped_total` growth is R1's capacity
  ceiling and the diagnostic ring falling behind, respectively.
- **Growth rate.** Bytes per hour for the database and both logs, which is
  what a month-long test has to be budgeted against.

Pulls all three files over adb by default, because the database lives on the
board and a running app is writing to it.

    python3 tools/soak_report.py --since 2026-08-08T09:00
    python3 tools/soak_report.py --db ./servo_mvp.db --log ./servo_mvp.jsonl \\
        --mcu-log ./mcu.jsonl
"""

import argparse
import datetime
import json
import os
import sqlite3
import subprocess
import tempfile
from typing import Any, Optional

BOARD_APP_DIR: str = "/home/arduino/ArduinoApps/servo_mvp"

# A gap wider than this is worth naming. The sampler runs at 1 s, so anything
# past a couple of seconds means it did not get to run.
GAP_THRESHOLD_SECONDS: float = 2.0

# The stall signature: servo_read's 10 s timeout plus one sampler interval.
STALL_BAND_LOW_SECONDS: float = 9.0
STALL_BAND_HIGH_SECONDS: float = 13.0


def pull_from_board(name: str, destination: str) -> Optional[str]:
    """Copies one file off the board with adb.

    Args:
        name (str): File name inside the app directory.
        destination (str): Local directory to write into.

    Returns:
        Optional[str]: Local path, or None when the pull failed.
    """
    local_path = os.path.join(destination, name)
    result = subprocess.run(
        ["adb", "pull", f"{BOARD_APP_DIR}/{name}", local_path],
        capture_output=True, text=True)
    if result.returncode != 0:
        print(f"could not pull {name}: {result.stderr.strip()}")
        return None
    return local_path


def parse_since(text: Optional[str]) -> float:
    """Converts a since argument to a unix timestamp.

    Args:
        text (Optional[str]): ISO-8601 local time, or None for all history.

    Returns:
        float: Unix timestamp; 0.0 when no limit was given.
    """
    if text is None:
        return 0.0
    return datetime.datetime.fromisoformat(text).timestamp()


def _utc_cutoff(since: float) -> str:
    """Formats a unix timestamp as the board's own clock would (D30).

    Both JSONL logs are written in UTC (mcu_log.py uses time.gmtime(); the
    container's system clock is UTC regardless of the operator's own
    timezone). --since is typed in the operator's local time and converted
    to an absolute instant by parse_since() - this reformats that same
    instant back out in UTC so string comparison against the log's own
    timestamps lands on the instant actually meant, not one shifted by the
    local/UTC offset.

    Args:
        since (float): Unix timestamp, as returned by parse_since().

    Returns:
        str: ISO-8601 UTC timestamp, no offset suffix - same shape as the
        logs' own timestamp field.
    """
    return (datetime.datetime.fromtimestamp(since, tz=datetime.timezone.utc)
            .replace(tzinfo=None).isoformat())


def report_telemetry(db_path: str, since: float) -> dict[str, Any]:
    """Examines the telemetry table for gaps and impossible positions.

    Args:
        db_path (str): Path to the SQLite database.
        since (float): Only consider samples at or after this timestamp.

    Returns:
        dict[str, Any]: Findings, ready to print.
    """
    connection = sqlite3.connect(db_path)
    rows: list[tuple[int, float, int]] = []
    for row in connection.execute(
            "select id, timestamp, raw_counts from telemetry "
            "where timestamp >= ? order by id", (since,)):
        rows.append((row[0], row[1], row[2]))

    findings: dict[str, Any] = {
        "samples": len(rows),
        "gaps": [],
        "stall_band_gaps": 0,
        "impossible_positions": [],
        "hours": 0.0,
    }
    if len(rows) < 2:
        return findings

    findings["hours"] = round((rows[-1][1] - rows[0][1]) / 3600.0, 2)

    index = 1
    while index < len(rows):
        gap = rows[index][1] - rows[index - 1][1]
        if gap > GAP_THRESHOLD_SECONDS:
            moment = datetime.datetime.fromtimestamp(
                rows[index][1]).strftime("%H:%M:%S")
            findings["gaps"].append({"at": moment, "seconds": round(gap, 2)})
            if (gap >= STALL_BAND_LOW_SECONDS) and \
                    (gap <= STALL_BAND_HIGH_SECONDS):
                findings["stall_band_gaps"] += 1
        index += 1

    # A count at or below zero is only impossible once the mechanism has
    # moved off the bottom of its travel; before that, zero is a real
    # reading. Anchor on the first non-zero sample.
    first_moved: Optional[int] = None
    for row in rows:
        if (first_moved is None) and (row[2] > 0):
            first_moved = row[0]
    if first_moved is not None:
        for row in rows:
            if (row[0] > first_moved) and (row[2] <= 0):
                moment = datetime.datetime.fromtimestamp(
                    row[1]).strftime("%H:%M:%S")
                findings["impossible_positions"].append(
                    {"at": moment, "counts": row[2]})
    return findings


def report_log(log_path: str, since: float) -> dict[str, Any]:
    """Counts the events that matter in the log.

    Args:
        log_path (str): Path to the JSONL log.
        since (float): Only consider records at or after this timestamp.

    Returns:
        dict[str, Any]: Findings, ready to print.
    """
    cutoff = _utc_cutoff(since)
    findings: dict[str, Any] = {
        "records": 0,
        "read_failed": 0,
        "relay_churn": 0,
        "warnings": 0,
        "errors": [],
    }
    with open(log_path, "r", encoding="utf-8") as handle:
        for line in handle:
            record = _decode_record(line)
            if record is not None:
                _tally_record(record, cutoff, findings)
    return findings


def _decode_record(line: str) -> Optional[dict[str, Any]]:
    """Decodes one JSONL line.

    Args:
        line (str): Raw line from the log.

    Returns:
        Optional[dict[str, Any]]: The record, or None if it is malformed.
    """
    try:
        return json.loads(line)
    except ValueError:
        return None


def _tally_record(record: dict[str, Any], cutoff: str,
                  findings: dict[str, Any]) -> None:
    """Adds one record to the running findings.

    Args:
        record (dict[str, Any]): A decoded log record.
        cutoff (str): ISO timestamp before which records are ignored.
        findings (dict[str, Any]): Tally to update in place.

    Returns:
        None
    """
    if record.get("timestamp", "") < cutoff:
        return
    findings["records"] += 1
    event = record.get("metadata", {}).get("event", "")
    level = record.get("level", "")
    if event == "servo.read.failed":
        findings["read_failed"] += 1
    if event.startswith("relay.conn") is True:
        findings["relay_churn"] += 1
    if level == "WARNING":
        findings["warnings"] += 1
    if (level == "ERROR") or (level == "CRITICAL"):
        findings["errors"].append({
            "at": record.get("timestamp"),
            "message": record.get("message"),
            "exception": record.get("extra", {}).get("exception"),
            "type": record.get("extra", {}).get("exception_type"),
        })


def _mcu_log_unavailable() -> dict[str, Any]:
    """Findings shape for when mcu.jsonl could not be pulled (backlog D28).

    Returns:
        dict[str, Any]: Same keys as report_mcu_log, zeroed and flagged.
    """
    return {"available": False, "records": 0, "write_lock_timeouts": 0,
            "rejected": 0, "dropped": 0, "bus_stalls": 0, "warnings": 0,
            "errors": []}


def report_mcu_log(mcu_log_path: str, since: float) -> dict[str, Any]:
    """Counts the MCU-side diagnostic events that matter (backlog D3).

    Args:
        mcu_log_path (str): Path to the MCU-side JSONL log.
        since (float): Only consider records at or after this timestamp.

    Returns:
        dict[str, Any]: Findings, ready to print.
    """
    cutoff = _utc_cutoff(since)
    findings: dict[str, Any] = {
        "available": True,
        "records": 0,
        "write_lock_timeouts": 0,
        "rejected": 0,
        "dropped": 0,
        "bus_stalls": 0,
        "warnings": 0,
        "errors": [],
    }
    with open(mcu_log_path, "r", encoding="utf-8") as handle:
        for line in handle:
            record = _decode_record(line)
            if record is not None:
                _tally_mcu_record(record, cutoff, findings)
    return findings


def _tally_mcu_record(record: dict[str, Any], cutoff: str,
                      findings: dict[str, Any]) -> None:
    """Adds one MCU-side record to the running findings.

    Args:
        record (dict[str, Any]): A decoded log record.
        cutoff (str): ISO timestamp before which records are ignored.
        findings (dict[str, Any]): Tally to update in place.

    Returns:
        None
    """
    if record.get("timestamp", "") < cutoff:
        return
    findings["records"] += 1
    event = record.get("event", "")
    level = record.get("level", "")
    if event == "mcu.relay.write_lock_timeout":
        findings["write_lock_timeouts"] += 1
    if event == "mcu.relay.rejected":
        findings["rejected"] += 1
    if event == "mcu.servo.refresh_failed":
        # The sampler calls this once a second - the same signature as the
        # D4/D10 stalls, just observed from the MCU's own side.
        findings["bus_stalls"] += 1
    if level == "WARNING":
        findings["warnings"] += 1
    if level == "ERROR":
        findings["errors"].append({"at": record.get("timestamp"),
                                   "message": record.get("message"),
                                   "event": event})


def print_verdict(telemetry: dict[str, Any], log: dict[str, Any],
                  mcu_log: dict[str, Any], db_bytes: int, log_bytes: int,
                  mcu_log_bytes: int) -> int:
    """Prints the findings and returns an exit code.

    Args:
        telemetry (dict[str, Any]): Output of report_telemetry.
        log (dict[str, Any]): Output of report_log.
        db_bytes (int): Size of the database file.
        log_bytes (int): Size of the log file.

    Returns:
        int: 0 when nothing alarming was found, 1 otherwise.
    """
    hours = telemetry["hours"]
    print("---- board report ----")
    print(f"window             {hours} hour(s), "
          f"{telemetry['samples']} telemetry samples")
    print(f"sampler gaps > {GAP_THRESHOLD_SECONDS:g}s  "
          f"{len(telemetry['gaps'])}")
    print(f"  of those in the stall band ({STALL_BAND_LOW_SECONDS:g}-"
          f"{STALL_BAND_HIGH_SECONDS:g}s)  "
          f"{telemetry['stall_band_gaps']}")
    print(f"impossible positions {len(telemetry['impossible_positions'])}")
    print(f"failed reads logged  {log['read_failed']}")
    print(f"warnings             {log['warnings']}")
    print(f"errors               {len(log['errors'])}")
    print(f"relay churn lines    {log['relay_churn']}")
    print()
    if mcu_log["available"]:
        print(f"MCU write-lock timeouts (D4 signature)  "
              f"{mcu_log['write_lock_timeouts']}")
        print(f"MCU bus-refresh stalls                  "
              f"{mcu_log['bus_stalls']}")
        print(f"MCU connections rejected                "
              f"{mcu_log['rejected']}")
        print(f"MCU warnings / errors                   "
              f"{mcu_log['warnings']} / {len(mcu_log['errors'])}")
    else:
        print("MCU-side log         not present on the board (backlog D28) "
              "- write-lock/rejection counts not confirmed this run")

    if hours > 0.0:
        print()
        print("---- growth ----")
        print(f"database  {db_bytes / 1_048_576:.1f} MB now, "
              f"{db_bytes / 1_048_576 / hours:.2f} MB/hour "
              f"-> {db_bytes / 1_048_576 / hours * 24 * 30:.0f} MB/month")
        print(f"log       {log_bytes / 1_048_576:.1f} MB now, "
              f"{log_bytes / 1_048_576 / hours:.2f} MB/hour "
              f"-> {log_bytes / 1_048_576 / hours * 24 * 30:.0f} MB/month")
        if mcu_log["available"]:
            print(f"mcu log   {mcu_log_bytes / 1_048_576:.1f} MB now, "
                  f"{mcu_log_bytes / 1_048_576 / hours:.2f} MB/hour "
                  f"-> {mcu_log_bytes / 1_048_576 / hours * 24 * 30:.0f} "
                  f"MB/month")

    for gap in telemetry["gaps"]:
        print(f"  gap at {gap['at']}: {gap['seconds']}s")
    for bad in telemetry["impossible_positions"]:
        print(f"  impossible position at {bad['at']}: counts={bad['counts']}")
    for error in log["errors"]:
        print(f"  ERROR {error['at']} {error['message']} "
              f"[{error['type']}: {error['exception']}]")
    for error in mcu_log["errors"]:
        print(f"  MCU ERROR {error['at']} {error['message']} "
              f"[{error['event']}]")

    print()
    linux_side_clean = (telemetry["stall_band_gaps"] == 0) and \
        (len(telemetry["impossible_positions"]) == 0) and \
        (len(log["errors"]) == 0)
    mcu_side_clean = mcu_log["available"] and \
        (mcu_log["write_lock_timeouts"] == 0) and \
        (mcu_log["bus_stalls"] == 0) and \
        (len(mcu_log["errors"]) == 0)
    if linux_side_clean and mcu_side_clean:
        print("VERDICT: clean - no stall signature, no fabricated positions, "
              "no errors.")
        return 0
    if linux_side_clean and not mcu_log["available"]:
        print("VERDICT: clean on the Linux side, but the MCU side was never "
              "checked (D28) - do not report this as a full clean.")
        return 0
    print("VERDICT: something to look at - see the lines above.")
    return 1


def main() -> int:
    """Parses arguments and prints the report.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(
        description="Report what the board recorded during a soak.")
    parser.add_argument("--since", default=None,
                        help="ISO-8601 local time, e.g. 2026-08-08T09:00")
    parser.add_argument("--db", default=None,
                        help="local database path; pulled over adb if omitted")
    parser.add_argument("--log", default=None,
                        help="local log path; pulled over adb if omitted")
    parser.add_argument("--mcu-log", default=None,
                        help="local MCU-side log path (backlog D3); "
                             "pulled over adb if omitted")
    arguments = parser.parse_args()

    workspace = tempfile.mkdtemp(prefix="soak-")
    db_path = arguments.db
    if db_path is None:
        db_path = pull_from_board("servo_mvp.db", workspace)
    log_path = arguments.log
    if log_path is None:
        log_path = pull_from_board("servo_mvp.jsonl", workspace)
    mcu_log_path = arguments.mcu_log
    if mcu_log_path is None:
        mcu_log_path = pull_from_board("mcu.jsonl", workspace)
    if (db_path is None) or (log_path is None):
        return 2

    since = parse_since(arguments.since)
    telemetry = report_telemetry(db_path, since)
    log = report_log(log_path, since)
    if mcu_log_path is None:
        mcu_log = _mcu_log_unavailable()
        mcu_log_bytes = 0
    else:
        mcu_log = report_mcu_log(mcu_log_path, since)
        mcu_log_bytes = os.path.getsize(mcu_log_path)
    return print_verdict(telemetry, log, mcu_log, os.path.getsize(db_path),
                         os.path.getsize(log_path), mcu_log_bytes)


if __name__ == "__main__":
    raise SystemExit(main())
