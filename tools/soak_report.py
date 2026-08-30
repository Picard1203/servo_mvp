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
- **Client correlation and R1 scorecard.** Cross-validates client-side
  `soak.json` reports with board logs and telemetry to evaluate the R1
  concurrent-operator capacity target.

Pulls all three files over adb by default, because the database lives on the
board and a running app is writing to it.

    python3 tools/soak_report.py --since 2026-08-08T09:00
    python3 tools/soak_report.py --db ./servo_mvp.db --log ./servo_mvp.jsonl \\
        --mcu-log ./mcu.jsonl --client-report ./run2_3op.json
"""

import argparse
import datetime
import json
import os
import sqlite3
import statistics
import subprocess
import tempfile
from typing import Any, Optional

BOARD_APP_DIR: str = "/home/arduino/ArduinoApps/servo_mvp"

# A gap wider than this is worth naming - past a couple of seconds means the
# sampler did not get to run, regardless of its configured interval.
GAP_THRESHOLD_SECONDS: float = 2.0

# The stall signature: servo_read's 10 s timeout, offset by one sampler
# interval either side.
SERVO_READ_TIMEOUT_SECONDS: float = 10.0


def stall_band(sampler_interval_seconds: float) -> tuple[float, float]:
    """Returns the (low, high) stall-band bounds for a given sampler interval.

    Args:
        sampler_interval_seconds (float): The sampler's configured interval.

    Returns:
        tuple[float, float]: A (low, high) tuple in seconds.
    """
    low = SERVO_READ_TIMEOUT_SECONDS - sampler_interval_seconds
    high = SERVO_READ_TIMEOUT_SECONDS + sampler_interval_seconds + 2.0
    return low, high


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
        str: ISO-8601 UTC timestamp, no offset suffix.
    """
    return (datetime.datetime.fromtimestamp(since, tz=datetime.timezone.utc)
            .replace(tzinfo=None).isoformat())


def report_telemetry(db_path: str, since: float,
                     sampler_interval_seconds: float) -> dict[str, Any]:
    """Examines the telemetry table for gaps, impossible positions, and anomalies.

    Args:
        db_path (str): Path to the SQLite database.
        since (float): Only consider samples at or after this timestamp.
        sampler_interval_seconds (float): The sampler interval the soak ran at.

    Returns:
        dict[str, Any]: Findings, ready to print.
    """
    stall_low, stall_high = stall_band(sampler_interval_seconds)
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

    # Query telemetry samples
    query = (
        "SELECT id, timestamp, raw_counts, voltage_v, current_a, "
        "temperature_c, torque_kgcm, overload, overcurrent, overheat "
        "FROM telemetry WHERE timestamp >= ? ORDER BY id"
    )
    rows: list[tuple] = []
    try:
        for row in cursor.execute(query, (since,)):
            rows.append(row)
    except sqlite3.OperationalError:
        # Fallback for older schemas
        for row in cursor.execute(
                "SELECT id, timestamp, raw_counts FROM telemetry "
                "WHERE timestamp >= ? ORDER BY id", (since,)):
            rows.append((row[0], row[1], row[2], None, None, None, None, 0, 0, 0))

    findings: dict[str, Any] = {
        "samples": len(rows),
        "gaps": [],
        "intervals": [],
        "stall_band_gaps": 0,
        "stall_band_low": stall_low,
        "stall_band_high": stall_high,
        "impossible_positions": [],
        "hours": 0.0,
        "cadence_median_s": 0.0,
        "cadence_p95_s": 0.0,
        "cadence_max_s": 0.0,
        "voltage_min": None,
        "voltage_max": None,
        "current_max": None,
        "temp_max": None,
        "torque_max": None,
        "voltage_sags": [],
        "overload_trips": 0,
    }
    if len(rows) < 2:
        return findings

    findings["hours"] = round((rows[-1][1] - rows[0][1]) / 3600.0, 2)

    intervals: list[float] = []
    voltages: list[float] = []
    currents: list[float] = []
    temps: list[float] = []
    torques: list[float] = []

    for index in range(1, len(rows)):
        prev_row = rows[index - 1]
        curr_row = rows[index]
        gap = curr_row[1] - prev_row[1]
        intervals.append(gap)
        if gap > GAP_THRESHOLD_SECONDS:
            moment = datetime.datetime.fromtimestamp(curr_row[1]).strftime("%H:%M:%S")
            findings["gaps"].append({"at": moment, "seconds": round(gap, 2)})
            if (gap >= stall_low) and (gap <= stall_high):
                findings["stall_band_gaps"] += 1

    if intervals:
        sorted_intervals = sorted(intervals)
        findings["cadence_median_s"] = round(statistics.median(sorted_intervals), 3)
        p95_idx = max(0, int(len(sorted_intervals) * 0.95) - 1)
        findings["cadence_p95_s"] = round(sorted_intervals[p95_idx], 3)
        findings["cadence_max_s"] = round(sorted_intervals[-1], 3)

    first_moved: Optional[int] = None
    for row in rows:
        r_id, r_ts, r_counts = row[0], row[1], row[2]
        r_volt, r_curr, r_temp, r_torq = row[3], row[4], row[5], row[6]
        r_overload = row[7]

        if (first_moved is None) and (r_counts > 0):
            first_moved = r_id

        if (first_moved is not None) and (r_id > first_moved) and (r_counts <= 0):
            moment = datetime.datetime.fromtimestamp(r_ts).strftime("%H:%M:%S")
            findings["impossible_positions"].append({"at": moment, "counts": r_counts})

        if r_volt is not None:
            voltages.append(r_volt)
            if r_volt < 4.5:
                moment = datetime.datetime.fromtimestamp(r_ts).strftime("%H:%M:%S")
                findings["voltage_sags"].append({"at": moment, "voltage": r_volt})
        if r_curr is not None:
            currents.append(r_curr)
        if r_temp is not None:
            temps.append(r_temp)
        if r_torq is not None:
            torques.append(r_torq)
        if r_overload:
            findings["overload_trips"] += 1

    if voltages:
        findings["voltage_min"] = round(min(voltages), 2)
        findings["voltage_max"] = round(max(voltages), 2)
    if currents:
        findings["current_max"] = round(max(currents), 2)
    if temps:
        findings["temp_max"] = round(max(temps), 1)
    if torques:
        findings["torque_max"] = round(max(torques), 1)

    return findings


def report_log(log_path: str, since: float) -> dict[str, Any]:
    """Counts the events that matter in the application log.

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
        "bridge_errors": 0,
        "move_rejected": 0,
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
    """Decodes one JSONL line."""
    try:
        return json.loads(line)
    except ValueError:
        return None


def _tally_record(record: dict[str, Any], cutoff: str,
                  findings: dict[str, Any]) -> None:
    """Adds one record to the running findings."""
    if record.get("timestamp", "") < cutoff:
        return
    findings["records"] += 1
    event = record.get("metadata", {}).get("event", "")
    level = record.get("level", "")
    if event == "servo.read.failed":
        findings["read_failed"] += 1
    if event.startswith("relay.conn") is True:
        findings["relay_churn"] += 1
    if event == "servo.bridge.error":
        findings["bridge_errors"] += 1
    if event == "servo.move.rejected":
        findings["move_rejected"] += 1
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
    """Findings shape for when mcu.jsonl could not be pulled."""
    return {"available": False, "records": 0, "write_lock_timeouts": 0,
            "rejected": 0, "dropped": 0, "bus_stalls": 0, "warnings": 0,
            "errors": []}


def report_mcu_log(mcu_log_path: str, since: float) -> dict[str, Any]:
    """Counts the MCU-side diagnostic events that matter.

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
    """Adds one MCU-side record to the running findings."""
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
        findings["bus_stalls"] += 1
    if level == "WARNING":
        findings["warnings"] += 1
    if level == "ERROR":
        findings["errors"].append({"at": record.get("timestamp"),
                                   "message": record.get("message"),
                                   "event": event})


def load_client_reports(report_paths: list[str]) -> Optional[dict[str, Any]]:
    """Aggregates metrics from one or more client report JSON files.

    Args:
        report_paths (list[str]): List of file paths to client reports.

    Returns:
        Optional[dict[str, Any]]: Aggregated metrics summary or None.
    """
    if not report_paths:
        return None

    combined = {
        "reports_loaded": len(report_paths),
        "total_operators": 0,
        "total_requests": 0,
        "total_failures": 0,
        "total_rejections": 0,
        "stream_frames": 0,
        "stream_opens": 0,
        "stream_reconnects": 0,
        "stream_failures": 0,
        "stream_gaps_over_2s": 0,
        "actions": {},
    }

    for path in report_paths:
        if not os.path.exists(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                rep = json.load(handle)
            combined["total_operators"] += rep.get("operators", 1)
            combined["total_requests"] += rep.get("requests", 0)
            combined["total_failures"] += rep.get("failures", 0)
            combined["total_rejections"] += rep.get("rejections", 0)

            stream = rep.get("stream", {})
            combined["stream_frames"] += stream.get("frames_total", 0)
            combined["stream_opens"] += stream.get("connection_opens", 0)
            combined["stream_reconnects"] += stream.get("reconnects", 0)
            combined["stream_failures"] += stream.get("failures", 0)
            combined["stream_gaps_over_2s"] += stream.get("gaps_over_2s", 0)

            for act, act_data in rep.get("actions", {}).items():
                if act not in combined["actions"]:
                    combined["actions"][act] = {"count": 0, "failures": 0,
                                               "rejections": 0}
                combined["actions"][act]["count"] += act_data.get("count", 0)
                combined["actions"][act]["failures"] += act_data.get("failures", 0)
                combined["actions"][act]["rejections"] += act_data.get("rejections", 0)
        except Exception as exc:
            print(f"warning: failed to read client report {path}: {exc}")

    return combined


def print_r1_scorecard(telemetry: dict[str, Any], log: dict[str, Any],
                       mcu_log: dict[str, Any],
                       client: Optional[dict[str, Any]]) -> bool:
    """Evaluates the soak against R1 and stability acceptance criteria.

    Args:
        telemetry (dict[str, Any]): Telemetry analysis findings.
        log (dict[str, Any]): Application log findings.
        mcu_log (dict[str, Any]): MCU log findings.
        client (Optional[dict[str, Any]]): Client metrics if provided.

    Returns:
        bool: True if all R1 criteria passed cleanly.
    """
    print("\n================ R1 CAPACITY & STABILITY SCORECARD ================")
    checks = []

    # 1. Stall band gaps (D4 signature)
    stall_pass = telemetry["stall_band_gaps"] == 0
    checks.append(("No W5500 stall-band gaps (10-12s)", stall_pass,
                   f"{telemetry['stall_band_gaps']} gaps detected"))

    # 2. Impossible positions (counts <= 0)
    pos_pass = len(telemetry["impossible_positions"]) == 0
    checks.append(("No impossible positions (counts <= 0)", pos_pass,
                   f"{len(telemetry['impossible_positions'])} invalid samples"))

    # 3. Application error log
    err_pass = len(log["errors"]) == 0
    checks.append(("No unhandled application errors", err_pass,
                   f"{len(log['errors'])} errors logged"))

    # 4. MCU write lock timeouts
    if mcu_log["available"]:
        mcu_pass = mcu_log["write_lock_timeouts"] == 0
        checks.append(("MCU write-lock timeouts == 0", mcu_pass,
                       f"{mcu_log['write_lock_timeouts']} timeouts"))
    else:
        checks.append(("MCU write-lock timeouts == 0", True,
                       "MCU log unavailable (skipped)"))

    # 5. Client metrics (if client report was ingested)
    client_all_pass = True
    if client is not None:
        fail_pass = client["total_failures"] == 0
        checks.append(("Client transport failures == 0", fail_pass,
                       f"{client['total_failures']} failures ({client['total_requests']} requests)"))

        stream_pass = (client["stream_failures"] == 0) and (client["stream_reconnects"] == 0)
        checks.append(("SSE stream connection 100% stable", stream_pass,
                       f"{client['stream_reconnects']} reconnects, {client['stream_failures']} drops"))

        client_all_pass = fail_pass and stream_pass

    all_passed = (stall_pass and pos_pass and err_pass and client_all_pass)

    for desc, passed, note in checks:
        mark = "[PASS]" if passed else "[FAIL]"
        print(f"  {mark:<7} {desc:<42} -> {note}")

    print("------------------------------------------------------------------")
    if all_passed:
        print("OVERALL VERDICT: ALL PASS — System satisfied capacity and stability goals.")
    else:
        print("OVERALL VERDICT: FAIL / ATTENTION REQUIRED — See failed items above.")
    print("==================================================================\n")
    return all_passed


def print_verdict(telemetry: dict[str, Any], log: dict[str, Any],
                  mcu_log: dict[str, Any], db_bytes: int, log_bytes: int,
                  mcu_log_bytes: int,
                  client: Optional[dict[str, Any]] = None) -> int:
    """Prints the findings and returns an exit code.

    Args:
        telemetry (dict[str, Any]): Telemetry analysis findings.
        log (dict[str, Any]): App log findings.
        mcu_log (dict[str, Any]): MCU log findings.
        db_bytes (int): Database size in bytes.
        log_bytes (int): App log size in bytes.
        mcu_log_bytes (int): MCU log size in bytes.
        client (Optional[dict[str, Any]]): Client summary findings.

    Returns:
        int: Process exit code.
    """
    hours = telemetry["hours"]
    print("---- board report ----")
    print(f"window             {hours} hour(s), {telemetry['samples']} telemetry samples")
    print(f"sampler cadence    median={telemetry['cadence_median_s']}s  "
          f"p95={telemetry['cadence_p95_s']}s  max={telemetry['cadence_max_s']}s")
    print(f"sampler gaps > 2s  {len(telemetry['gaps'])}")
    print(f"  of those in stall band ({telemetry['stall_band_low']:g}-"
          f"{telemetry['stall_band_high']:g}s)  {telemetry['stall_band_gaps']}")
    print(f"impossible positions {len(telemetry['impossible_positions'])}")
    print(f"failed reads logged  {log['read_failed']}")
    print(f"bridge errors logged {log['bridge_errors']}")
    print(f"move rejections      {log['move_rejected']}")
    print(f"warnings             {log['warnings']}")
    print(f"errors               {len(log['errors'])}")
    print(f"relay churn lines    {log['relay_churn']}")
    print()

    if telemetry["voltage_min"] is not None:
        print(f"voltage range      {telemetry['voltage_min']}V to {telemetry['voltage_max']}V "
              f"(sags < 4.5V: {len(telemetry['voltage_sags'])})")
    if telemetry["temp_max"] is not None:
        print(f"peak temp/torque   {telemetry['temp_max']} °C / {telemetry['torque_max']} kg.cm")

    print()
    if mcu_log["available"]:
        print(f"MCU write-lock timeouts (D4 signature)  {mcu_log['write_lock_timeouts']}")
        print(f"MCU bus-refresh stalls                  {mcu_log['bus_stalls']}")
        print(f"MCU connections rejected                {mcu_log['rejected']}")
        print(f"MCU warnings / errors                   {mcu_log['warnings']} / {len(mcu_log['errors'])}")
    else:
        print("MCU-side log         not present on the board (backlog D28)")

    if client is not None:
        print()
        print("---- client report summary ----")
        print(f"operators simulated  {client['total_operators']}")
        print(f"requests attempted   {client['total_requests']}")
        print(f"transport failures   {client['total_failures']}")
        print(f"deliberate refusals  {client['total_rejections']}")
        print(f"sse frames / gaps>2s {client['stream_frames']} / {client['stream_gaps_over_2s']}")
        print(f"sse reconnects       {client['stream_reconnects']}")

    if hours > 0.0:
        print()
        print("---- storage growth (T9 budget) ----")
        print(f"database  {db_bytes / 1_048_576:.1f} MB now, "
              f"{db_bytes / 1_048_576 / hours:.2f} MB/hour "
              f"-> {db_bytes / 1_048_576 / hours * 24 * 30:.0f} MB/month")
        print(f"log       {log_bytes / 1_048_576:.1f} MB now, "
              f"{log_bytes / 1_048_576 / hours:.2f} MB/hour "
              f"-> {log_bytes / 1_048_576 / hours * 24 * 30:.0f} MB/month")
        if mcu_log["available"]:
            print(f"mcu log   {mcu_log_bytes / 1_048_576:.1f} MB now, "
                  f"{mcu_log_bytes / 1_048_576 / hours:.2f} MB/hour "
                  f"-> {mcu_log_bytes / 1_048_576 / hours * 24 * 30:.0f} MB/month")

    for gap in telemetry["gaps"]:
        print(f"  gap at {gap['at']}: {gap['seconds']}s")
    for bad in telemetry["impossible_positions"]:
        print(f"  impossible position at {bad['at']}: counts={bad['counts']}")
    for error in log["errors"]:
        print(f"  ERROR {error['at']} {error['message']} [{error['type']}: {error['exception']}]")
    for error in mcu_log["errors"]:
        print(f"  MCU ERROR {error['at']} {error['message']} [{error['event']}]")

    scorecard_passed = print_r1_scorecard(telemetry, log, mcu_log, client)
    return 0 if scorecard_passed else 1


def main() -> int:
    """Parses CLI arguments and prints the soak evaluation."""
    parser = argparse.ArgumentParser(
        description="Report what the board recorded during a soak.")
    parser.add_argument("--since", default=None,
                        help="ISO-8601 local time, e.g. 2026-08-08T09:00")
    parser.add_argument("--db", default=None,
                        help="local database path; pulled over adb if omitted")
    parser.add_argument("--log", default=None,
                        help="local log path; pulled over adb if omitted")
    parser.add_argument("--mcu-log", default=None,
                        help="local MCU-side log path; pulled over adb if omitted")
    parser.add_argument("--client-report", action="append", default=[],
                        help="path to client JSON report(s) from synthetic_operator.py")
    parser.add_argument("--sampler-interval", type=float, default=0.5,
                        help="sampler_interval_seconds (default 0.5)")
    args = parser.parse_args()

    workspace = tempfile.mkdtemp(prefix="soak-")
    db_path = args.db
    if db_path is None:
        db_path = pull_from_board("servo_mvp.db", workspace)
    log_path = args.log
    if log_path is None:
        log_path = pull_from_board("servo_mvp.jsonl", workspace)
    mcu_log_path = args.mcu_log
    if mcu_log_path is None:
        mcu_log_path = pull_from_board("mcu.jsonl", workspace)

    if (db_path is None) or (log_path is None):
        return 2

    since = parse_since(args.since)
    telemetry = report_telemetry(db_path, since, args.sampler_interval)
    log = report_log(log_path, since)
    if mcu_log_path is None:
        mcu_log = _mcu_log_unavailable()
        mcu_log_bytes = 0
    else:
        mcu_log = report_mcu_log(mcu_log_path, since)
        mcu_log_bytes = os.path.getsize(mcu_log_path) if os.path.exists(mcu_log_path) else 0

    client_summary = load_client_reports(args.client_report)

    db_sz = os.path.getsize(db_path) if os.path.exists(db_path) else 0
    log_sz = os.path.getsize(log_path) if os.path.exists(log_path) else 0

    return print_verdict(telemetry, log, mcu_log, db_sz, log_sz, mcu_log_bytes,
                         client_summary)


if __name__ == "__main__":
    raise SystemExit(main())
