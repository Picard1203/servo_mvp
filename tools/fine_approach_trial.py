"""D40c measurement tool: fine-approach accuracy, and a speed benchmark.

Board-testing tool for the D40c tuning campaign
(docs/backlog/D.md D40, D35). Measures only - it never writes a register or
changes a setting itself. Registers are changed via
POST /api/v1/servo/diagnostics/tuning_registers; speed/acceleration only
through python/.env plus a Python-only app restart (R9 removed per-move
speed as an operator control, and this tool does not reopen that). Keeping
control and measurement apart is what makes one script trustworthy across
the whole campaign.

Every commanded-speed value in speed-benchmark mode is a *label*, supplied
by the operator to match whatever DEFAULT_SPEED_DPS is actually configured
on the board for this run - the tool cannot read or set it itself, since it
is not exposed by the API. Run the tool once per candidate speed, after
setting DEFAULT_SPEED_DPS and restarting the app for that candidate.

Run examples:
    # Accuracy at three anchor points, N=5 each, unloaded
    python3 tools/fine_approach_trial.py accuracy --host 192.168.10.60 \\
        --targets -60,0,60 --repeats 5 --label baseline

    # Speed benchmark for one candidate GoalSpeed - 0/30/45/60/75/90 and
    # negatives, two repeats each, after setting DEFAULT_SPEED_DPS=6.0 and
    # restarting the app
    python3 tools/fine_approach_trial.py speed-benchmark \\
        --host 192.168.10.60 --commanded-speed-dps 6.0 --repeats 2 \\
        --label speed_sweep
"""

import argparse
import csv
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Optional

DEFAULT_STEP_DEG: float = 0.06
MOVE_SETTLE_TIMEOUT_SECONDS: float = 45.0

# A move at the fast end of the benchmark settles in 2-4s. Polling any
# slower during it yields only a handful of present-speed samples - too
# few for a real median. Sampling this tight while moving is what makes
# present_speed_median trustworthy instead of a shrug.
SPEED_SAMPLE_POLL_SECONDS: float = 0.15

# A high MinStartForce (or a stiff drivetrain generally) can make the
# servo take a long tail of small corrective moves to reach its final
# position, spaced arbitrarily far apart - each one dipping moving=True
# then False again. Accepting the first False, or even a short debounce
# on moving alone, is how a mid-hunt pause got mistaken for the finish
# twice on real hardware (MinStartForce 100, Session 21 - once at 0.05-0.07
# deg where the operator heard it correct much further, once again at 90
# deg where corrections were spaced further apart than a 1.0s debounce
# caught). The reported position itself, not just moving, must also stop
# changing for this long before a reading is trusted as final.
SETTLE_STABLE_SECONDS_REQUIRED: float = 2.0

# Two output_deg readings this close are the same position for settling
# purposes - smaller than the servo's own one-count resolution (0.06 deg),
# so it never mistakes real residual drift for read noise.
SETTLE_POSITION_EPSILON_DEG: float = 0.03

ARCHIVE_DIR: str = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "archive")

# 0/30/45/60/75/90 and their negatives - 0 appears once, matching the
# operator's own spec (Session 21).
SPEED_BENCHMARK_TARGETS_DEG: tuple[float, ...] = (
    0.0, 30.0, -30.0, 45.0, -45.0, 60.0, -60.0, 75.0, -75.0, 90.0, -90.0)

_ACCURACY_FIELDS = [
    "mode", "label", "loaded", "target_deg", "repeat", "measured_deg",
    "error_deg", "overshoot_deg", "overshoot_clamped", "wait_elapsed_s",
]

_SPEED_BENCHMARK_FIELDS = [
    "mode", "label", "loaded", "commanded_speed_dps", "target_deg",
    "repeat", "start_deg", "measured_deg", "commanded_distance_deg",
    "elapsed_s", "gross_real_dps", "present_speed_median_counts_s",
    "present_speed_sample_count",
]


def quantize_deg(deg: float, step: float = DEFAULT_STEP_DEG) -> float:
    """Snaps an angle to the nearest valid step multiple.

    Args:
        deg (float): Desired angle in output degrees.
        step (float): Configured step resolution in output degrees.

    Returns:
        float: Angle snapped to the step grid, rounded to 2 decimal places.
    """
    multiples = round(deg / step)
    return round(multiples * step, 2)


def _get(base_url: str, path: str) -> Optional[dict]:
    """Performs one GET request and decodes the JSON reply.

    Args:
        base_url (str): API base URL.
        path (str): Endpoint path relative to base_url.

    Returns:
        Optional[dict]: The decoded JSON body, or None on failure.
    """
    req = urllib.request.Request(
        f"{base_url}{path}", headers={"Connection": "keep-alive"})
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode("utf-8"))
        except Exception:
            if attempt == 0:
                time.sleep(0.25)
                continue
            return None
    return None


def _move(base_url: str, target_deg: float) -> bool:
    """Commands one move and reports whether the API accepted it.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.

    Returns:
        bool: True when the API returned success.
    """
    body = json.dumps({"target_deg": target_deg}).encode("utf-8")
    headers = {"Connection": "keep-alive", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{base_url}/servo/move", data=body,
                                 method="POST", headers=headers)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10):
                return True
        except urllib.error.HTTPError:
            return False
        except Exception:
            if attempt == 0:
                time.sleep(0.25)
                continue
            return False
    return False


def _wait_settle_sampling_speed(
        base_url: str,
        timeout: float = MOVE_SETTLE_TIMEOUT_SECONDS
        ) -> tuple[Optional[dict], list[int]]:
    """Polls state until motion stops, sampling present speed each tick.

    Sampling PRESENT_SPEED live throughout the move is what keeps this
    reading correct regardless of whether fine approach is on - unlike an
    elapsed-time estimate, it is not diluted by a second leg. A reading is
    only trusted as final once BOTH moving has read False AND output_deg
    has stopped changing, continuously, for SETTLE_STABLE_SECONDS_REQUIRED.
    Checking the position too (not just moving) catches a correction the
    moving flag itself blinks through between two polls.

    Args:
        base_url (str): API base URL.
        timeout (float): Longest time to wait, in seconds.

    Returns:
        tuple[Optional[dict], list[int]]: The last state read (or None if
            every read failed), and every present-speed sample taken while
            the servo reported itself moving.
    """
    deadline = time.monotonic() + timeout
    state = None
    samples: list[int] = []
    stable_since: Optional[float] = None
    stable_at_deg: Optional[float] = None
    while time.monotonic() < deadline:
        time.sleep(SPEED_SAMPLE_POLL_SECONDS)
        read = _get(base_url, "/servo/state")
        if read is None:
            continue
        state = read
        output_deg = read.get("output_deg")
        if read.get("moving") is True:
            stable_since = None
            stable_at_deg = None
            speed_reply = _get(base_url, "/servo/diagnostics/present_speed")
            if speed_reply is not None:
                value = speed_reply.get("present_speed_counts_s")
                if value is not None:
                    samples.append(value)
            continue
        now = time.monotonic()
        moved_since_last_check = (
            stable_at_deg is None or output_deg is None
            or abs(output_deg - stable_at_deg) > SETTLE_POSITION_EPSILON_DEG)
        if moved_since_last_check:
            stable_since = now
            stable_at_deg = output_deg
        elif now - stable_since >= SETTLE_STABLE_SECONDS_REQUIRED:
            return state, samples
    return state, samples


def _now_iso() -> str:
    """Returns the current UTC time in the events endpoint's own format.

    Matches EventService's own timespec="seconds" precision exactly - a
    finer-grained timestamp here would sort after a same-second server
    timestamp lexicographically (the fractional-seconds "." separator
    sorts after the timezone "+"), wrongly rejecting a genuinely new event
    as stale.

    Returns:
        str: ISO-8601 timestamp comparable, lexicographically, against the
            "timestamp" field the events endpoint returns.
    """
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _latest_event(base_url: str, event_name: str,
                  after_iso: Optional[str] = None) -> Optional[dict]:
    """Fetches the most recent event of a given name.

    Args:
        base_url (str): API base URL.
        event_name (str): Event name to match.
        after_iso (Optional[str]): When given, only a match strictly newer
            than this timestamp counts - a stale event from an earlier move
            is not this move's event.

    Returns:
        Optional[dict]: The event, or None if not found.
    """
    reply = _get(base_url, "/system/events?limit=50")
    if reply is None:
        return None
    for event in reply.get("events", []):
        if event.get("event") != event_name:
            continue
        if after_iso is not None and event.get("timestamp", "") < after_iso:
            continue
        return event
    return None


def _wait_for_event(base_url: str, event_name: str, after_iso: str,
                    timeout: float = 4.0,
                    poll_seconds: float = 0.3) -> Optional[dict]:
    """Polls for an event newer than a timestamp, tolerating its own delay.

    The fine-approach event is recorded by a background thread strictly
    after the servo reports itself settled - a single settle-then-read can
    lose the race and find nothing yet. Polling closes that window rather
    than trusting a single read to have caught it.

    Args:
        base_url (str): API base URL.
        event_name (str): Event name to match.
        after_iso (str): Only a match strictly newer than this counts.
        timeout (float): Longest time to wait, in seconds.
        poll_seconds (float): Delay between polls.

    Returns:
        Optional[dict]: The event, or None if it never appeared.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        event = _latest_event(base_url, event_name, after_iso=after_iso)
        if event is not None:
            return event
        time.sleep(poll_seconds)
    return None


def _median(values: list[int]) -> Optional[float]:
    """Returns the median of a list, or None if it is empty.

    Args:
        values (list[int]): Sample values.

    Returns:
        Optional[float]: The median, or None on an empty list.
    """
    if not values:
        return None
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return float(ordered[mid])
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _csv_path(mode: str, label: str) -> str:
    """Builds the shared, appended CSV path for one mode and label.

    Args:
        mode (str): "accuracy" or "speed_benchmark".
        label (str): Operator-supplied campaign label.

    Returns:
        str: Path under archive/, stable across repeated invocations so
            runs with the same label accumulate into one comparable file.
    """
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    return os.path.join(ARCHIVE_DIR, f"{mode}_{label}.csv")


def _append_csv(path: str, fields: list[str], rows: list[dict]) -> None:
    """Appends rows to a CSV, writing the header only for a new file.

    Args:
        path (str): Destination CSV path.
        fields (list[str]): Column order.
        rows (list[dict]): Rows to append.
    """
    write_header = not os.path.exists(path) or os.path.getsize(path) == 0
    with open(path, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def run_accuracy(host: str, port: int, targets: list[float], repeats: int,
                 label: str, loaded: bool) -> int:
    """Runs accuracy mode: repeated moves to each target, error recorded.

    Args:
        host (str): Board address.
        port (int): API port.
        targets (list[float]): Target output angles in degrees.
        repeats (int): Repeats per target.
        label (str): Campaign label, also the CSV file's identity.
        loaded (bool): Whether the rig is held under load for this run.

    Returns:
        int: 0 on completion.
    """
    base_url = f"http://{host}:{port}/api/v1"
    csv_path = _csv_path("accuracy", label)
    print(f"accuracy: targets={targets} repeats={repeats} loaded={loaded} "
          f"label={label} -> {csv_path}")
    rows: list[dict] = []
    for raw_target in targets:
        target = quantize_deg(raw_target)
        errors: list[float] = []
        for repeat in range(1, repeats + 1):
            issued_at = _now_iso()
            _move(base_url, target)
            state, _ = _wait_settle_sampling_speed(base_url)
            measured = state.get("output_deg") if state else None
            event = _wait_for_event(base_url, "servo.move.fine_approach",
                                    issued_at)
            data = event.get("data", {}) if event else {}
            error = (round(measured - target, 3)
                    if measured is not None else None)
            if error is not None:
                errors.append(error)
            rows.append({
                "mode": "accuracy", "label": label, "loaded": loaded,
                "target_deg": target, "repeat": repeat,
                "measured_deg": measured, "error_deg": error,
                "overshoot_deg": data.get("overshoot_deg"),
                "overshoot_clamped": data.get("overshoot_clamped"),
                "wait_elapsed_s": data.get("wait_elapsed_s"),
            })
            print(f"  target={target:>7} repeat={repeat} "
                 f"measured={measured} error={error}")
        if errors:
            mean_abs = sum(abs(e) for e in errors) / len(errors)
            print(f"  -> target={target:>7} mean|err|={mean_abs:.3f} "
                 f"min={min(errors):.3f} max={max(errors):.3f} "
                 f"n={len(errors)}")
        else:
            print(f"  -> target={target:>7} no valid readings")
    _append_csv(csv_path, _ACCURACY_FIELDS, rows)
    print(f"accuracy: done, {len(rows)} rows appended to {csv_path}")
    return 0


def run_speed_benchmark(host: str, port: int, commanded_speed_dps: float,
                        repeats: int, label: str, loaded: bool) -> int:
    """Runs speed-benchmark mode for one commanded-speed candidate.

    Args:
        host (str): Board address.
        port (int): API port.
        commanded_speed_dps (float): The DEFAULT_SPEED_DPS this run was
            taken at - a label, not something this tool sets.
        repeats (int): Repeats per target angle.
        label (str): Campaign label, also the CSV file's identity.
        loaded (bool): Whether the rig is held under load for this run.

    Returns:
        int: 0 on completion.
    """
    base_url = f"http://{host}:{port}/api/v1"
    csv_path = _csv_path("speed_benchmark", label)
    targets = [quantize_deg(t) for t in SPEED_BENCHMARK_TARGETS_DEG]
    print(f"speed-benchmark: commanded_speed_dps={commanded_speed_dps} "
          f"targets={targets} repeats={repeats} loaded={loaded} "
          f"label={label} -> {csv_path}")
    rows: list[dict] = []
    for target in targets:
        for repeat in range(1, repeats + 1):
            stage = 0.0 if target != 0.0 else 30.0
            _move(base_url, stage)
            _wait_settle_sampling_speed(base_url)
            start_state = _get(base_url, "/servo/state")
            start_deg = start_state.get("output_deg") if start_state else None
            commanded_distance = (abs(target - start_deg)
                                  if start_deg is not None else None)
            started_at = time.monotonic()
            _move(base_url, target)
            state, samples = _wait_settle_sampling_speed(base_url)
            elapsed_s = time.monotonic() - started_at
            measured = state.get("output_deg") if state else None
            gross_real_dps = (round(commanded_distance / elapsed_s, 3)
                              if commanded_distance and elapsed_s > 0
                              else None)
            median_speed = _median(samples)
            rows.append({
                "mode": "speed_benchmark", "label": label, "loaded": loaded,
                "commanded_speed_dps": commanded_speed_dps,
                "target_deg": target, "repeat": repeat,
                "start_deg": start_deg, "measured_deg": measured,
                "commanded_distance_deg": commanded_distance,
                "elapsed_s": round(elapsed_s, 3),
                "gross_real_dps": gross_real_dps,
                "present_speed_median_counts_s": median_speed,
                "present_speed_sample_count": len(samples),
            })
            print(f"  target={target:>7} repeat={repeat} "
                 f"elapsed={elapsed_s:.2f}s gross_real_dps={gross_real_dps} "
                 f"present_speed_median={median_speed} "
                 f"(n={len(samples)} samples)")
    _append_csv(csv_path, _SPEED_BENCHMARK_FIELDS, rows)
    print(f"speed-benchmark: done, {len(rows)} rows appended to {csv_path}")
    return 0


def _parse_targets(raw: str) -> list[float]:
    """Parses a comma-separated list of target angles.

    Args:
        raw (str): Comma-separated angles, e.g. "-60,0,60".

    Returns:
        list[float]: Parsed target angles.
    """
    return [float(part.strip()) for part in raw.split(",") if part.strip()]


def main() -> int:
    """Parses arguments and runs the requested trial mode."""
    parser = argparse.ArgumentParser(
        description="Measure fine-approach accuracy or benchmark commanded "
                    "vs. real servo speed. Measures only - never writes a "
                    "register or a setting.")
    parser.add_argument("--host", default="192.168.10.60",
                        help="board address serving the API")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--label", required=True,
                        help="campaign label; also the CSV file's identity "
                             "under archive/")
    parser.add_argument("--repeats", type=int, default=5,
                        help="repeats per target (accuracy default 5, "
                             "speed-benchmark typically 2)")
    parser.add_argument("--loaded", action="store_true",
                        help="mark this run as taken under hand-held load")

    subparsers = parser.add_subparsers(dest="mode", required=True)

    accuracy_parser = subparsers.add_parser(
        "accuracy", help="repeated moves to each target, error recorded")
    accuracy_parser.add_argument(
        "--targets", required=True,
        help="comma-separated target angles, e.g. -60,0,60")

    speed_parser = subparsers.add_parser(
        "speed-benchmark",
        help="0/30/45/60/75/90 and negatives at one commanded speed - run "
            "once per candidate DEFAULT_SPEED_DPS")
    speed_parser.add_argument(
        "--commanded-speed-dps", type=float, required=True,
        help="the DEFAULT_SPEED_DPS this run was actually taken at "
            "(label only - set it in .env and restart before running)")

    args = parser.parse_args()

    if args.mode == "accuracy":
        return run_accuracy(args.host, args.port,
                            _parse_targets(args.targets), args.repeats,
                            args.label, args.loaded)
    return run_speed_benchmark(args.host, args.port,
                               args.commanded_speed_dps, args.repeats,
                               args.label, args.loaded)


if __name__ == "__main__":
    raise SystemExit(main())
