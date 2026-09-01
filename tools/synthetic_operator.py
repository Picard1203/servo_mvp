"""Synthetic operators that drive the running board like people would.

Written for the soak testing and capacity verification described in
`docs/BACKLOG.md` (Session 17, R1 concurrent-operator ceiling).

Each virtual operator maintains:
1. One persistent Server-Sent Events (SSE) stream (`GET /api/v1/stream`)
   receiving state, saved positions, and audit events.
2. Deliberate human-paced actions (moves, saved-position CRUD, motor isolation,
   lock toggling, diagnostic queries, and binary telemetry export) with
   randomized think times.

Supports configurable operator profiles:
- 'active': Drives the mechanism, manages saved positions, toggles lock/isolation.
- 'monitor': Passive screen left open, holding persistent SSE stream with
  occasional health checks (matching real operator usage in Q2).
- 'mixed': Operator 1 drives actively, remaining operators monitor passively.
- 'stress': Heavy burst load of moves, concurrent binary exports, and commands.

Run examples:
    # Pre-flight health and datum check
    python3 tools/synthetic_operator.py --host 192.168.10.60 --preflight

    # 10-minute 3-operator soak (R1 nominal target)
    python3 tools/synthetic_operator.py --host 192.168.10.60 --minutes 10 \\
        --operators 3 --profile mixed --report run2_3op.json

    # Settle-investigation protocol B (minimum effective step), under load
    python3 tools/synthetic_operator.py --host 192.168.10.60 \\
        --settle-probe --probe-phase b --probe-target 30.0 \\
        --probe-loaded --report probe_b_loaded.json
"""

import argparse
import http.client
import json
import random
import signal
import statistics
import threading
import time
import urllib.error
import urllib.request
from typing import Any, Optional

# One poll per second for motion settle polling
POLL_STATE_SECONDS: float = 1.0

# Human pauses between deliberate actions.
THINK_SECONDS_MIN: float = 3.0
THINK_SECONDS_MAX: float = 15.0

# Motion travel limits (degrees)
TARGET_DEG_MIN: float = -80.0
TARGET_DEG_MAX: float = 80.0
DEFAULT_STEP_DEG: float = 0.06

# Longest a move is waited on before giving up
MOVE_SETTLE_TIMEOUT_SECONDS: float = 45.0

# Default interval for status printing and JSON report rewrite
DEFAULT_CHECKPOINT_MINUTES: float = 5.0


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


def classify_settle_result(commanded_deg: float, measured_deg: float,
                           tolerance_deg: float) -> str:
    """Classifies whether a settled position reached its target.

    Args:
        commanded_deg (float): The angle that was commanded.
        measured_deg (float): The angle measured after settle.
        tolerance_deg (float): Acceptable deviation before calling it short.

    Returns:
        str: "converged" or "short".
    """
    if abs(commanded_deg - measured_deg) <= tolerance_deg:
        return "converged"
    return "short"


def find_minimum_effective_step(
        samples: list[tuple[float, bool]]) -> Optional[float]:
    """Finds the smallest commanded step that produced real movement.

    Args:
        samples (list[tuple[float, bool]]): Ascending (step_deg, moved) pairs.

    Returns:
        Optional[float]: The smallest step that moved, or None if none did.
    """
    for step_deg, moved in samples:
        if moved is True:
            return step_deg
    return None


class Metrics:
    """Thread-safe tally of everything the synthetic operators observed.

    Attributes:
        _lock (threading.Lock): Guards internal data structures.
        _latencies (dict[str, list[float]]): Seconds per REST request by action.
        _failures (dict[str, int]): Transport failures by action.
        _rejections (dict[str, dict[str, int]]): Refusals by action and reason.
        _requests (int): Total REST HTTP requests attempted.
        _stream_frames (dict[str, int]): Frames received by SSE event type.
        _stream_intervals (list[float]): Inter-arrival intervals for state frames.
        _stream_opens (int): Total SSE connections opened.
        _stream_reconnects (int): Total SSE reconnections after drops.
        _stream_failures (int): Total SSE transport failures.
        _invalid_readings (int): Replies carrying reading_valid false.
        _unknown_positions (int): Replies carrying a null output_deg.
        _first_invalid_at (Optional[float]): Unix timestamp of first invalid reading.
    """

    def __init__(self) -> None:
        """Initializes an empty metrics tally."""
        self._lock: threading.Lock = threading.Lock()
        self._latencies: dict[str, list[float]] = {}
        self._failures: dict[str, int] = {}
        self._rejections: dict[str, dict[str, int]] = {}
        self._requests: int = 0
        self._stream_frames: dict[str, int] = {}
        self._stream_intervals: list[float] = []
        self._stream_opens: int = 0
        self._stream_reconnects: int = 0
        self._stream_failures: int = 0
        self._invalid_readings: int = 0
        self._unknown_positions: int = 0
        self._first_invalid_at: Optional[float] = None

    def record_request_success(self, action: str, seconds: float) -> None:
        """Records one completed REST request.

        Args:
            action (str): Name of the action performed.
            seconds (float): Round-trip latency in seconds.
        """
        with self._lock:
            self._requests += 1
            if action not in self._latencies:
                self._latencies[action] = []
            self._latencies[action].append(seconds)

    def record_request_failure(self, action: str) -> None:
        """Records a request that failed to connect or completed with a 5xx error.

        Args:
            action (str): Name of the action performed.
        """
        with self._lock:
            self._requests += 1
            self._failures[action] = self._failures.get(action, 0) + 1

    def record_request_rejection(self, action: str, reason: str) -> None:
        """Records a deliberate 4xx refusal from the API with its reason.

        Args:
            action (str): Name of the action performed.
            reason (str): Decoded reason code or HTTP status string.
        """
        with self._lock:
            self._requests += 1
            if action not in self._rejections:
                self._rejections[action] = {}
            self._rejections[action][reason] = (
                self._rejections[action].get(reason, 0) + 1
            )

    def record_stream_open(self, is_reconnect: bool) -> None:
        """Records an SSE stream connection open.

        Args:
            is_reconnect (bool): True if this was a reconnection after a drop.
        """
        with self._lock:
            self._stream_opens += 1
            if is_reconnect:
                self._stream_reconnects += 1

    def record_stream_failure(self) -> None:
        """Records a disconnect or transport failure on an SSE stream."""
        with self._lock:
            self._stream_failures += 1

    def record_stream_frame(self, event: str, interval_s: Optional[float]) -> None:
        """Records reception of one SSE frame.

        Args:
            event (str): Event name (state, positions, events).
            interval_s (Optional[float]): Time elapsed since last state event.
        """
        with self._lock:
            self._stream_frames[event] = self._stream_frames.get(event, 0) + 1
            if (event == "state") and (interval_s is not None):
                self._stream_intervals.append(interval_s)

    def record_reading(self, reading_valid: bool,
                       output_deg: Optional[float]) -> None:
        """Records whether a state snapshot carried valid telemetry.

        Args:
            reading_valid (bool): Valid reading flag from server.
            output_deg (Optional[float]): Output angle or None if unknown.
        """
        with self._lock:
            if reading_valid is False:
                self._invalid_readings += 1
                if self._first_invalid_at is None:
                    self._first_invalid_at = time.time()
            if output_deg is None:
                self._unknown_positions += 1

    def summary(self) -> dict[str, Any]:
        """Builds a comprehensive summary dictionary.

        Returns:
            dict[str, Any]: Detailed metrics breakdown.
        """
        with self._lock:
            actions: dict[str, Any] = {}
            for action in sorted(self._latencies.keys()):
                samples = sorted(self._latencies[action])
                act_rejections = self._rejections.get(action, {})
                actions[action] = {
                    "count": len(samples),
                    "median_s": round(statistics.median(samples), 3) if samples else 0.0,
                    "p95_s": round(samples[int(len(samples) * 0.95) - 1], 3) if samples else 0.0,
                    "max_s": round(samples[-1], 3) if samples else 0.0,
                    "failures": self._failures.get(action, 0),
                    "rejections": sum(act_rejections.values()),
                    "rejections_by_reason": act_rejections,
                }

            all_actions = set(self._latencies.keys()) | set(self._failures.keys()) | set(self._rejections.keys())
            for action in sorted(all_actions):
                if action not in actions:
                    act_rejections = self._rejections.get(action, {})
                    actions[action] = {
                        "count": 0,
                        "median_s": 0.0,
                        "p95_s": 0.0,
                        "max_s": 0.0,
                        "failures": self._failures.get(action, 0),
                        "rejections": sum(act_rejections.values()),
                        "rejections_by_reason": act_rejections,
                    }

            total_failures = sum(self._failures.values())
            total_rejections = sum(
                sum(reasons.values()) for reasons in self._rejections.values()
            )

            stream_cadence = {"median_s": 0.0, "p95_s": 0.0, "max_gap_s": 0.0}
            gaps_over_2s = 0
            if self._stream_intervals:
                sorted_intervals = sorted(self._stream_intervals)
                stream_cadence["median_s"] = round(statistics.median(sorted_intervals), 3)
                p95_idx = max(0, int(len(sorted_intervals) * 0.95) - 1)
                stream_cadence["p95_s"] = round(sorted_intervals[p95_idx], 3)
                stream_cadence["max_gap_s"] = round(sorted_intervals[-1], 3)
                gaps_over_2s = sum(1 for iv in sorted_intervals if iv > 2.0)

            return {
                "requests": self._requests,
                "failures": total_failures,
                "rejections": total_rejections,
                "invalid_readings": self._invalid_readings,
                "unknown_positions": self._unknown_positions,
                "first_invalid_at": self._first_invalid_at,
                "stream": {
                    "frames_total": sum(self._stream_frames.values()),
                    "events": dict(self._stream_frames),
                    "connection_opens": self._stream_opens,
                    "reconnects": self._stream_reconnects,
                    "failures": self._stream_failures,
                    "cadence": stream_cadence,
                    "gaps_over_2s": gaps_over_2s,
                },
                "actions": actions,
            }


class SyntheticOperator:
    """One virtual operator running an SSE stream and deliberate HTTP actions.

    Attributes:
        _host (str): Target board IP or hostname.
        _port (int): Port for FastAPI service.
        _base_url (str): Base URL for API calls.
        _metrics (Metrics): Shared metrics accumulator.
        _name (str): Unique operator identifier.
        _profile (str): Action profile ('active', 'monitor', 'stress').
        _step_deg (float): Output angle step resolution.
        _random (random.Random): Independent RNG.
        _deadline (float): Monotonic deadline.
        _stop (threading.Event): Signal to terminate.
        _pos_counter (int): Counter for generating unique saved position names.
        _created_position_ids (list[int]): IDs of positions created by this operator.
    """

    def __init__(self, host: str, port: int, metrics: Metrics, name: str,
                 seed: int, deadline: float, profile: str = "active",
                 step_deg: float = DEFAULT_STEP_DEG) -> None:
        """Creates a synthetic operator.

        Args:
            host (str): Target host.
            port (int): Target port.
            metrics (Metrics): Shared metrics instance.
            name (str): Name label.
            seed (int): RNG seed.
            deadline (float): Monotonic stop time.
            profile (str): Operator profile.
            step_deg (float): Angle step resolution.
        """
        self._host: str = host
        self._port: int = port
        self._base_url: str = f"http://{host}:{port}/api/v1"
        self._metrics: Metrics = metrics
        self._name: str = name
        self._profile: str = profile
        self._step_deg: float = step_deg
        self._random: random.Random = random.Random(seed)
        self._deadline: float = deadline
        self._stop: threading.Event = threading.Event()
        self._pos_counter: int = 0
        self._created_position_ids: list[int] = []
        self._last_state_at: Optional[float] = None

    def stop(self) -> None:
        """Signals worker threads to stop."""
        self._stop.set()

    def _request(self, action: str, path: str, method: str = "GET",
                 payload: Optional[dict[str, Any]] = None,
                 drain_stream: bool = False) -> Optional[Any]:
        """Performs one REST HTTP call and updates metrics.

        Args:
            action (str): Metrics action label.
            path (str): Endpoint path relative to /api/v1.
            method (str): HTTP method.
            payload (Optional[dict[str, Any]]): JSON body for POST/PATCH/DELETE.
            drain_stream (bool): True to read raw stream without JSON decoding.

        Returns:
            Optional[Any]: Parsed JSON response or True on drained stream, None on error.
        """
        data: Optional[bytes] = None
        headers: dict[str, str] = {"Connection": "keep-alive"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        url = self._base_url + path
        request = urllib.request.Request(url, data=data, headers=headers,
                                         method=method)
        started = time.monotonic()
        for attempt in range(2):
            try:
                with urllib.request.urlopen(request, timeout=25) as response:
                    if drain_stream:
                        total_bytes = 0
                        while True:
                            chunk = response.read(65536)
                            if not chunk:
                                break
                            total_bytes += len(chunk)
                        self._metrics.record_request_success(action, time.monotonic() - started)
                        return total_bytes

                    body = response.read()
                    self._metrics.record_request_success(action, time.monotonic() - started)
                    if not body:
                        return {}
                    return json.loads(body.decode("utf-8"))
            except urllib.error.HTTPError as error:
                reason = str(error.code)
                try:
                    err_body = error.read().decode("utf-8")
                    err_json = json.loads(err_body)
                    if "reason" in err_json:
                        reason = str(err_json["reason"])
                    elif "detail" in err_json:
                        reason = str(err_json["detail"])
                except Exception:
                    pass

                if 400 <= error.code < 500:
                    self._metrics.record_request_rejection(action, reason)
                else:
                    self._metrics.record_request_failure(action)
                return None
            except Exception:
                if attempt == 0:
                    time.sleep(0.25)
                    continue
                self._metrics.record_request_failure(action)
                return None

    def stream_forever(self) -> None:
        """Reads the persistent SSE stream until deadline or stop."""
        is_reconnect = False
        while (time.monotonic() < self._deadline) and not self._stop.is_set():
            conn: Optional[http.client.HTTPConnection] = None
            try:
                conn = http.client.HTTPConnection(self._host, self._port, timeout=30)
                self._metrics.record_stream_open(is_reconnect)
                conn.request("GET", "/api/v1/stream",
                             headers={"Accept": "text/event-stream"})
                resp = conn.getresponse()
                if resp.status != 200:
                    raise http.client.HTTPException(f"HTTP {resp.status}")

                current_event: Optional[str] = None
                current_data: Optional[str] = None

                for raw_line in resp:
                    if self._stop.is_set() or (time.monotonic() >= self._deadline):
                        break
                    line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                    if line.startswith("event: "):
                        current_event = line[7:]
                    elif line.startswith("data: "):
                        current_data = line[6:]
                    elif line == "":
                        if current_event and current_data:
                            self._handle_sse_frame(current_event, current_data)
                        current_event = None
                        current_data = None
            except Exception:
                self._metrics.record_stream_failure()
                is_reconnect = True
                self._stop.wait(2.0)
            finally:
                if conn is not None:
                    try:
                        conn.close()
                    except Exception:
                        pass

    def _handle_sse_frame(self, event: str, data: str) -> None:
        """Decodes an SSE frame and records stream metrics.

        Args:
            event (str): Event name.
            data (str): JSON event payload string.
        """
        now = time.monotonic()
        delta_s: Optional[float] = None
        if event == "state":
            if self._last_state_at is not None:
                delta_s = now - self._last_state_at
            self._last_state_at = now

        self._metrics.record_stream_frame(event, delta_s)

        if event == "state":
            try:
                payload = json.loads(data)
                self._metrics.record_reading(
                    payload.get("reading_valid", True),
                    payload.get("output_deg"),
                )
            except json.JSONDecodeError:
                pass

    def act_forever(self) -> None:
        """Executes deliberate actions with think times."""
        while (time.monotonic() < self._deadline) and not self._stop.is_set():
            self._perform_one_action()
            think = self._random.uniform(THINK_SECONDS_MIN, THINK_SECONDS_MAX)
            time.sleep(min(think, max(0.0, self._deadline - time.monotonic())))

    def _perform_one_action(self) -> None:
        """Dispatches an action based on the operator's profile."""
        if self._profile == "monitor":
            if self._random.random() < 0.08:
                self._request("health", "/system/health")
            return

        if self._profile == "stress":
            roll = self._random.random()
            if roll < 0.40:
                self._move_somewhere()
            elif roll < 0.65:
                self._pull_export()
            elif roll < 0.85:
                self._act_saved_positions()
            else:
                self._read_diagnostics()
            return

        roll = self._random.random()
        if roll < 0.45:
            self._move_somewhere()
        elif roll < 0.65:
            self._act_saved_positions()
        elif roll < 0.75:
            self._toggle_lock()
        elif roll < 0.83:
            self._toggle_isolation()
        elif roll < 0.90:
            self._read_diagnostics()
        elif roll < 0.95:
            self._request("stop", "/servo/stop", method="POST", payload={})
        else:
            self._pull_export()

    def _move_somewhere(self) -> None:
        """Commands a motion to a quantized valid angle."""
        raw_deg = self._random.uniform(TARGET_DEG_MIN, TARGET_DEG_MAX)
        target = quantize_deg(raw_deg, self._step_deg)
        accepted = self._request("move", "/servo/move", method="POST",
                                 payload={"target_deg": target})
        if accepted is not None:
            self._wait_until_stopped()

    def _wait_until_stopped(self) -> None:
        """Polls until movement settles or timeout elapses."""
        limit = time.monotonic() + MOVE_SETTLE_TIMEOUT_SECONDS
        moving = True
        while (moving is True) and (time.monotonic() < limit) \
                and (time.monotonic() < self._deadline) and not self._stop.is_set():
            time.sleep(POLL_STATE_SECONDS)
            state = self._request("state_settle", "/servo/state")
            if state is None:
                moving = False
            else:
                moving = state.get("moving", False)

    def _act_saved_positions(self) -> None:
        """Exercises saved-position CRUD operations."""
        roll = self._random.random()
        if (roll < 0.40) or not self._created_position_ids:
            self._pos_counter += 1
            name = f"pos-{self._name[-1]}-{self._pos_counter}"
            deg = quantize_deg(self._random.uniform(TARGET_DEG_MIN, TARGET_DEG_MAX),
                               self._step_deg)
            created = self._request(
                "position_create", "/positions", method="POST",
                payload={"name": name, "description": "soak point", "target_deg": deg},
            )
            if created and isinstance(created, dict) and "id" in created:
                self._created_position_ids.append(created["id"])
                if len(self._created_position_ids) > 10:
                    self._created_position_ids.pop(0)
            return

        if roll < 0.75:
            pos_id = self._random.choice(self._created_position_ids)
            resp = self._request("position_go", f"/positions/{pos_id}/go", method="POST")
            if resp:
                self._wait_until_stopped()
            return

        if roll < 0.90:
            pos_id = self._random.choice(self._created_position_ids)
            pos_data = self._request("position_get", f"/positions/{pos_id}")
            if pos_data and isinstance(pos_data, dict) and "updated_at" in pos_data:
                deg = quantize_deg(self._random.uniform(TARGET_DEG_MIN, TARGET_DEG_MAX),
                                   self._step_deg)
                self._request(
                    "position_update", f"/positions/{pos_id}", method="PATCH",
                    payload={"name": f"upd-{pos_id}", "description": "updated soak point",
                             "target_deg": deg, "updated_at": pos_data["updated_at"]},
                )
            return

        pos_id = self._created_position_ids.pop(0)
        self._request("position_delete", f"/positions/{pos_id}", method="DELETE", payload={})

    def _toggle_lock(self) -> None:
        """Engages digital lock, waits briefly, and releases it."""
        self._request("lock", "/servo/lock", method="POST", payload={"locked": True})
        time.sleep(self._random.uniform(1.0, 3.0))
        self._request("lock", "/servo/lock", method="POST", payload={"locked": False})

    def _toggle_isolation(self) -> None:
        """Engages motor isolation, pauses, and restores torque."""
        self._request("isolate", "/servo/isolate", method="POST", payload={"isolated": True})
        time.sleep(self._random.uniform(1.0, 3.0))
        self._request("isolate", "/servo/isolate", method="POST", payload={"isolated": False})

    def _read_diagnostics(self) -> None:
        """Queries hardware diagnostic registers."""
        self._request("diag_torque", "/servo/diagnostics/torque_register")

    def _pull_export(self) -> None:
        """Streams binary telemetry export over the Bridge link."""
        finish = time.time()
        start = finish - 1800.0
        self._request("export_binary", f"/telemetry/binary?from={start}&to={finish}",
                      drain_stream=True)


class Checkpointer:
    """Periodically prints status and persists checkpoint reports."""

    def __init__(self, metrics: Metrics, report_path: Optional[str],
                 interval_seconds: float, started_at: float,
                 deadline: float) -> None:
        """Initializes checkpointer."""
        self._metrics = metrics
        self._report_path = report_path
        self._interval_seconds = interval_seconds
        self._started_at = started_at
        self._deadline = deadline
        self._stop = threading.Event()

    def run(self) -> None:
        """Executes the checkpoint loop until stopped."""
        while not self._stop.is_set():
            remaining = self._deadline - time.monotonic()
            if remaining <= 0:
                return
            if self._stop.wait(min(self._interval_seconds, remaining)):
                return
            self.write_once()

    def write_once(self) -> None:
        """Prints a live summary line and rewrites the report file."""
        summary = self._metrics.summary()
        elapsed_min = (time.time() - self._started_at) / 60.0
        stream = summary.get("stream", {})
        print(f"[{time.strftime('%H:%M:%S')}] checkpoint  "
              f"elapsed={elapsed_min:.1f}m  requests={summary['requests']}  "
              f"failures={summary['failures']}  "
              f"rejections={summary['rejections']}  "
              f"stream_frames={stream.get('frames_total', 0)}  "
              f"cadence_p95={stream.get('cadence', {}).get('p95_s', 0.0)}s")
        if self._report_path is not None:
            _write_report(self._report_path, summary)

    def stop(self) -> None:
        """Terminates the checkpoint loop."""
        self._stop.set()


def _write_report(report_path: str, summary: dict[str, Any]) -> None:
    """Writes the summary dictionary to a JSON file.

    Args:
        report_path (str): Destination file path.
        summary (dict[str, Any]): Data payload.
    """
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


def run_preflight(host: str, port: int) -> bool:
    """Queries board status and prints pre-flight diagnostics.

    Args:
        host (str): Board IP.
        port (int): API port.

    Returns:
        bool: True if board responded healthy with valid datum.
    """
    print(f"pre-flight: probing http://{host}:{port}...")
    base = f"http://{host}:{port}/api/v1"
    headers = {"Connection": "keep-alive"}
    try:
        req = urllib.request.Request(f"{base}/system/health", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            health = json.loads(r.read().decode("utf-8"))

        time.sleep(0.5)

        req = urllib.request.Request(f"{base}/servo/state", headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            state = json.loads(r.read().decode("utf-8"))

        print("---- pre-flight check ----")
        print(f"app status:        {health.get('status')} ({health.get('app_name')} v{health.get('version')})")
        print(f"servo reading:     {'VALID' if state.get('reading_valid') else 'INVALID'}")
        print(f"output angle:      {state.get('output_deg')} deg")
        print(f"reachable window:  {state.get('output_min_deg')} to {state.get('output_max_deg')} deg")
        print(f"position verified: {state.get('position_verified')}")
        print(f"isolated:          {state.get('isolated')}")
        print(f"locked:            {state.get('locked')}")
        print()
        if not state.get("reading_valid"):
            print("WARNING: Servo reading is marked INVALID. Verify servo connection and .env!")
            return False
        if not state.get("position_verified"):
            print("WARNING: Position reference is NOT verified. Needs calibration before negative travel!")
        print("PRE-FLIGHT: OK to proceed.")
        return True
    except Exception as exc:
        print(f"PRE-FLIGHT FAILED: could not reach board: {exc}")
        return False


# Settle-probe: default sweep of commanded steps for protocol B,
# smallest to largest.
SETTLE_PROBE_STEPS_DEG: tuple[float, ...] = (0.06, 0.12, 0.30, 0.60, 1.20, 3.00)

# Movement only counts as real once it clears sensor and rounding noise.
SETTLE_PROBE_NOISE_FLOOR_DEG: float = 0.03

# Repeats per direction in the repeatability protocol.
SETTLE_PROBE_REPEAT_COUNT: int = 3

# Protocol B2: target positions spread across the safe travel range, each
# far enough from +/-90 that staging and correction offsets stay in range.
SETTLE_PROBE_SURVEY_TARGETS_DEG: tuple[float, ...] = (-60.0, 0.0, 60.0)

# Realistic staging distance for a large move - matches how an operator
# actually drives the mechanism, not a sub-degree nudge.
SETTLE_PROBE_LARGE_MOVE_OFFSET_DEG: float = 35.0

# Re-command repeats: does pressing the identical target again ever
# self-correct, or is the shortfall consistently stuck.
SETTLE_PROBE_RECOMMAND_REPEAT_COUNT: int = 3

# Correction-offset sweep tried from a settled shortfall - starts at 0.30,
# since Protocol B already showed 0.06/0.12 unloaded never move it.
SETTLE_PROBE_CORRECTION_STEPS_DEG: tuple[float, ...] = (0.30, 0.60, 1.20, 3.00)

# The probe is a single serial client, never concurrent operators, so it can
# poll faster than POLL_STATE_SECONDS (tuned for the soak's shared-socket
# budget across several simultaneous operators) without hitting the same
# ceiling - used successfully across this session's probe and kick-test runs.
SETTLE_PROBE_POLL_SECONDS: float = 0.5


def _probe_get_state(base_url: str) -> Optional[dict[str, Any]]:
    """Reads the current servo state for the settle probe.

    Args:
        base_url (str): API base URL.

    Returns:
        Optional[dict[str, Any]]: The parsed state, or None on failure.
    """
    try:
        req = urllib.request.Request(f"{base_url}/servo/state",
                                     headers={"Connection": "keep-alive"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception:
        return None


def _probe_move(base_url: str, target_deg: float) -> tuple[bool, Optional[str]]:
    """Commands one move for the settle probe, retrying once on a
    transient connection failure (the relay path's own real ceiling,
    docs/OPEN_QUESTIONS.md Q2), the same tolerance _request() gives
    every other action in this file.

    Args:
        base_url (str): API base URL.
        target_deg (float): Target output angle in degrees.

    Returns:
        tuple[bool, Optional[str]]: Accepted flag and refusal reason.
    """
    body = json.dumps({"target_deg": target_deg}).encode("utf-8")
    headers = {"Connection": "keep-alive", "Content-Type": "application/json"}
    req = urllib.request.Request(f"{base_url}/servo/move", data=body,
                                 method="POST", headers=headers)
    for attempt in range(2):
        try:
            with urllib.request.urlopen(req, timeout=10):
                return True, None
        except urllib.error.HTTPError as error:
            reason = None
            try:
                err = json.loads(error.read().decode("utf-8"))
                reason = err.get("reason")
            except Exception:
                pass
            return False, reason
        except Exception:
            if attempt == 0:
                time.sleep(SETTLE_PROBE_POLL_SECONDS)
                continue
            return False, "unreachable"


def _probe_wait_settle(base_url: str,
                       timeout: float) -> Optional[dict[str, Any]]:
    """Polls state until motion stops or the timeout elapses.

    Paces reads at SETTLE_PROBE_POLL_SECONDS rather than tightly - a
    single failed read is retried rather than treated as settled.

    Args:
        base_url (str): API base URL.
        timeout (float): Longest time to wait, in seconds.

    Returns:
        Optional[dict[str, Any]]: The last state read, or None if every
            read failed.
    """
    deadline = time.monotonic() + timeout
    state = None
    while time.monotonic() < deadline:
        time.sleep(SETTLE_PROBE_POLL_SECONDS)
        read = _probe_get_state(base_url)
        if read is not None:
            state = read
            if state.get("moving") is not True:
                return state
    return state


def _run_settle_probe_repeatability(base_url: str, target_deg: float,
                                    approach_offset_deg: float) -> list[dict]:
    """Protocol A: approaches one target from below and from above.

    Args:
        base_url (str): API base URL.
        target_deg (float): Grid-aligned target angle.
        approach_offset_deg (float): Distance of the staging point either side.

    Returns:
        list[dict]: One record per approach.
    """
    records: list[dict] = []
    directions = (("from_below", target_deg - approach_offset_deg),
                 ("from_above", target_deg + approach_offset_deg))
    for repeat in range(SETTLE_PROBE_REPEAT_COUNT):
        for direction, stage_deg in directions:
            _probe_move(base_url, quantize_deg(stage_deg))
            _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
            accepted, reason = _probe_move(base_url, target_deg)
            state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
            measured = state.get("output_deg") if state else None
            delta = (round(measured - target_deg, 3)
                    if measured is not None else None)
            records.append({
                "repeat": repeat + 1, "direction": direction,
                "accepted": accepted, "reason": reason,
                "measured_deg": measured, "delta_deg": delta,
                "reading_valid": state.get("reading_valid") if state
                else None,
            })
            print(f"  [A] repeat {repeat + 1} {direction}: "
                 f"measured={measured} delta={delta}")
    return records


def _run_settle_probe_minimum_step(base_url: str, base_deg: float) -> dict:
    """Protocol B: finds the smallest step that reliably produces movement.

    Each step size is tried SETTLE_PROBE_REPEAT_COUNT times, re-settled to
    the same base position and re-confirmed before every trial - a single
    sample per step cannot tell a real threshold from a lucky trial, and
    step size is the only thing allowed to vary between trials.

    Args:
        base_url (str): API base URL.
        base_deg (float): Grid-aligned starting target.

    Returns:
        dict: Per-step trial results and the smallest step that moved on
            every trial.
    """
    records: list[dict] = []
    reliable: list[tuple[float, bool]] = []
    for step_deg in SETTLE_PROBE_STEPS_DEG:
        trials: list[dict] = []
        moved_count = 0
        for trial in range(SETTLE_PROBE_REPEAT_COUNT):
            _probe_move(base_url, base_deg)
            start_state = _probe_wait_settle(base_url,
                                             MOVE_SETTLE_TIMEOUT_SECONDS)
            start_deg = (start_state.get("output_deg") if start_state
                        else None)
            target = quantize_deg(base_deg + step_deg)
            accepted, reason = _probe_move(base_url, target)
            state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
            measured = state.get("output_deg") if state else None
            moved = (measured is not None and start_deg is not None
                    and abs(measured - start_deg) > SETTLE_PROBE_NOISE_FLOOR_DEG)
            if moved is True:
                moved_count += 1
            trials.append({"trial": trial + 1, "accepted": accepted,
                           "reason": reason, "start_deg": start_deg,
                           "measured_deg": measured, "moved": moved})
            print(f"  [B] step={step_deg} trial={trial + 1} moved={moved}")
        is_reliable = moved_count == SETTLE_PROBE_REPEAT_COUNT
        reliable.append((step_deg, is_reliable))
        records.append({"step_deg": step_deg, "moved_count": moved_count,
                        "repeat_count": SETTLE_PROBE_REPEAT_COUNT,
                        "reliable": is_reliable, "trials": trials})
    return {"steps": records,
           "minimum_reliable_step_deg": find_minimum_effective_step(reliable)}


def _run_settle_probe_large_move(base_url: str, target_deg: float) -> dict:
    """One target's survey: a realistic large approach, repeated
    re-commands of the identical target, then a repeated search for the
    smallest correction that reliably closes any gap.

    Args:
        base_url (str): API base URL.
        target_deg (float): Grid-aligned target angle for this trial.

    Returns:
        dict: The approach, the re-command repeats, and the correction
            search, all for this one target.
    """
    stage_offset = (-SETTLE_PROBE_LARGE_MOVE_OFFSET_DEG if target_deg >= 0.0
                    else SETTLE_PROBE_LARGE_MOVE_OFFSET_DEG)
    stage_deg = quantize_deg(target_deg + stage_offset)
    _probe_move(base_url, stage_deg)
    _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)

    approach_accepted, approach_reason = _probe_move(base_url, target_deg)
    approach_state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
    approach_measured = (approach_state.get("output_deg")
                        if approach_state else None)
    print(f"  [B2] target={target_deg} approach from {stage_deg}: "
         f"measured={approach_measured}")

    recommands = []
    for attempt in range(SETTLE_PROBE_RECOMMAND_REPEAT_COUNT):
        accepted, reason = _probe_move(base_url, target_deg)
        state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
        measured = state.get("output_deg") if state else None
        recommands.append({"attempt": attempt + 1, "accepted": accepted,
                           "reason": reason, "measured_deg": measured})
        print(f"  [B2] target={target_deg} re-command {attempt + 1}: "
             f"measured={measured}")

    corrections: list[dict] = []
    reliable: list[tuple[float, bool]] = []
    for step_deg in SETTLE_PROBE_CORRECTION_STEPS_DEG:
        trials: list[dict] = []
        moved_count = 0
        for trial in range(SETTLE_PROBE_REPEAT_COUNT):
            # Re-run the full staging approach, not a short hop back to
            # target_deg - a hop from wherever the previous trial's
            # correction left off does not reproduce the same starting
            # shortfall, which would leave step size no longer the only
            # variable between trials.
            _probe_move(base_url, stage_deg)
            _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
            _probe_move(base_url, target_deg)
            start_state = _probe_wait_settle(base_url,
                                             MOVE_SETTLE_TIMEOUT_SECONDS)
            start_deg = (start_state.get("output_deg") if start_state
                        else None)
            correction_target = quantize_deg(target_deg + step_deg)
            _probe_move(base_url, correction_target)
            state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
            measured = state.get("output_deg") if state else None
            moved = (measured is not None and start_deg is not None
                    and abs(measured - start_deg) > SETTLE_PROBE_NOISE_FLOOR_DEG)
            if moved is True:
                moved_count += 1
            trials.append({"trial": trial + 1, "start_deg": start_deg,
                           "measured_deg": measured, "moved": moved})
            print(f"  [B2] target={target_deg} correction={step_deg} "
                 f"trial={trial + 1} moved={moved}")
        is_reliable = moved_count == SETTLE_PROBE_REPEAT_COUNT
        reliable.append((step_deg, is_reliable))
        corrections.append({"step_deg": step_deg, "moved_count": moved_count,
                            "reliable": is_reliable, "trials": trials})

    return {
        "target_deg": target_deg, "stage_deg": stage_deg,
        "approach": {"accepted": approach_accepted,
                    "reason": approach_reason,
                    "measured_deg": approach_measured},
        "recommands": recommands,
        "corrections": corrections,
        "minimum_reliable_correction_deg":
            find_minimum_effective_step(reliable),
    }


def _run_settle_probe_survey(base_url: str) -> dict:
    """Protocol B2: the large-move survey across multiple target positions.

    Args:
        base_url (str): API base URL.

    Returns:
        dict: One result per surveyed target.
    """
    targets = []
    for target_deg in SETTLE_PROBE_SURVEY_TARGETS_DEG:
        targets.append(_run_settle_probe_large_move(base_url, target_deg))
    return {"targets": targets}


def _run_settle_probe_recommand(base_url: str, target_deg: float,
                                approach_offset_deg: float,
                                tolerance_deg: float) -> dict:
    """Protocol C: approach fresh, observe a shortfall, then re-command.

    Stages away from the target first and waits it out - re-reading a
    position the board already happened to be sitting at would only
    prove that a stale read doesn't change, not that a fresh approach
    settles short and a second press does not correct it.

    Args:
        base_url (str): API base URL.
        target_deg (float): Grid-aligned target angle.
        approach_offset_deg (float): Distance of the staging point.
        tolerance_deg (float): Deviation allowed before calling it short.

    Returns:
        dict: Both attempts' results and their classification.
    """
    _probe_move(base_url, quantize_deg(target_deg - approach_offset_deg))
    _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)

    attempts = []
    for attempt in range(2):
        accepted, reason = _probe_move(base_url, target_deg)
        state = _probe_wait_settle(base_url, MOVE_SETTLE_TIMEOUT_SECONDS)
        measured = state.get("output_deg") if state else None
        result = (classify_settle_result(target_deg, measured, tolerance_deg)
                  if measured is not None else "unknown")
        attempts.append({"attempt": attempt + 1, "accepted": accepted,
                         "reason": reason, "measured_deg": measured,
                         "result": result})
        print(f"  [C] attempt {attempt + 1}: accepted={accepted} "
             f"reason={reason} measured={measured} result={result}")
    return {"attempts": attempts}


def run_settle_probe(host: str, port: int, phase: str, target_deg: float,
                     loaded: bool, report_path: Optional[str]) -> int:
    """Runs one D40 settle-investigation protocol against the live board.

    Args:
        host (str): Board address.
        port (int): API port.
        phase (str): Protocol to run: 'a', 'b', or 'c'.
        target_deg (float): Grid-aligned base target for the protocol.
        loaded (bool): Whether the rig is held under load for this run.
        report_path (Optional[str]): Output report path.

    Returns:
        int: 0 on success, 1 if the board could not be reached.
    """
    base_url = f"http://{host}:{port}/api/v1"
    target_deg = quantize_deg(target_deg)
    print(f"settle-probe [{phase}]: target={target_deg} loaded={loaded} "
         f"against {host}:{port}")
    if _probe_get_state(base_url) is None:
        print(f"SETTLE-PROBE FAILED: could not reach board at {host}:{port}")
        return 1
    time.sleep(SETTLE_PROBE_POLL_SECONDS)

    if phase == "a":
        result = _run_settle_probe_repeatability(
            base_url, target_deg, approach_offset_deg=3.0)
    elif phase == "b":
        result = _run_settle_probe_minimum_step(base_url, target_deg)
    elif phase == "c":
        result = _run_settle_probe_recommand(
            base_url, target_deg, approach_offset_deg=3.0,
            tolerance_deg=SETTLE_PROBE_NOISE_FLOOR_DEG)
    else:
        result = _run_settle_probe_survey(base_url)

    summary = {"phase": phase, "target_deg": target_deg, "loaded": loaded,
              "started_at": time.strftime("%Y-%m-%d %H:%M:%S"),
              "result": result}
    if report_path is not None:
        _write_report(report_path, summary)
        print(f"settle-probe: report written to {report_path}")
    print("settle-probe: done.")
    return 0


def run_soak(host: str, port: int, minutes: float, operators: int,
             report_path: Optional[str], checkpoint_minutes: float,
             profile: str, step_deg: float) -> int:
    """Orchestrates synthetic operators during a soak test.

    Args:
        host (str): Board address.
        port (int): API port.
        minutes (float): Duration in minutes.
        operators (int): Number of virtual operators.
        report_path (Optional[str]): Output report path.
        checkpoint_minutes (float): Interval between status updates.
        profile (str): Load profile ('active', 'monitor', 'mixed', 'stress').
        step_deg (float): Output step resolution in degrees.

    Returns:
        int: 0 on success with 0 failures, 1 if failures occurred, 2 if interrupted.
    """
    metrics = Metrics()
    deadline = time.monotonic() + (minutes * 60.0)
    started_at = time.time()
    threads: list[threading.Thread] = []

    print(f"soak: {operators} operator(s) [profile={profile}] against {host}:{port} for {minutes:g}m")
    print(f"soak: started at {time.strftime('%H:%M:%S')}, "
          f"ends about {time.strftime('%H:%M:%S', time.localtime(started_at + minutes * 60.0))}")

    operator_instances: list[SyntheticOperator] = []
    for index in range(operators):
        if profile == "mixed":
            op_profile = "active" if index == 0 else "monitor"
        else:
            op_profile = profile

        op = SyntheticOperator(host, port, metrics, f"operator-{index + 1}",
                               seed=1000 + index, deadline=deadline,
                               profile=op_profile, step_deg=step_deg)
        operator_instances.append(op)
        for target in (op.stream_forever, op.act_forever):
            t = threading.Thread(target=target, daemon=True)
            threads.append(t)
            t.start()

    checkpointer: Optional[Checkpointer] = None
    if checkpoint_minutes > 0:
        checkpointer = Checkpointer(metrics, report_path, checkpoint_minutes * 60.0,
                                    started_at, deadline)
        threading.Thread(target=checkpointer.run, daemon=True).start()

    interrupted = False

    def _on_interrupt(_signum: int, _frame: Any) -> None:
        nonlocal interrupted
        interrupted = True

    previous_sigterm = signal.signal(signal.SIGTERM, _on_interrupt)
    try:
        for t in threads:
            while t.is_alive():
                t.join(timeout=1.0)
                if interrupted:
                    break
            if interrupted:
                break
    except KeyboardInterrupt:
        interrupted = True
    finally:
        signal.signal(signal.SIGTERM, previous_sigterm)
        if checkpointer is not None:
            checkpointer.stop()
        for op in operator_instances:
            op.stop()

    if interrupted:
        print("\nsoak: interrupted - writing gathered metrics...")

    summary = metrics.summary()
    summary["host"] = host
    summary["operators"] = operators
    summary["profile"] = profile
    summary["started_at"] = started_at
    summary["finished_at"] = time.time()
    summary["minutes"] = minutes
    summary["interrupted"] = interrupted

    print("\n---- soak report ----")
    print(f"requests:           {summary['requests']}")
    print(f"transport failures: {summary['failures']}")
    print(f"rejections (4xx):   {summary['rejections']}")
    print(f"invalid readings:   {summary['invalid_readings']}")
    print(f"unknown positions:  {summary['unknown_positions']}")

    stream = summary.get("stream", {})
    print(f"\n---- sse stream ----")
    print(f"frames received:    {stream.get('frames_total')}")
    print(f"connection opens:   {stream.get('connection_opens')}")
    print(f"reconnects:         {stream.get('reconnects')}")
    print(f"stream failures:    {stream.get('failures')}")
    cadence = stream.get("cadence", {})
    print(f"cadence median/p95: {cadence.get('median_s')}s / {cadence.get('p95_s')}s (max gap {cadence.get('max_gap_s')}s)")
    print(f"gaps > 2.0s:        {stream.get('gaps_over_2s')}")

    print("\n---- actions breakdown ----")
    for action, row in sorted(summary["actions"].items()):
        reasons_str = ""
        if row["rejections_by_reason"]:
            reasons_str = f" [{', '.join(f'{k}:{v}' for k, v in row['rejections_by_reason'].items())}]"
        print(f"  {action:<16} n={row['count']:<5} "
              f"median={row['median_s']:<6} p95={row['p95_s']:<6} max={row['max_s']:<6} "
              f"fail={row['failures']} refused={row['rejections']}{reasons_str}")

    if report_path is not None:
        _write_report(report_path, summary)
        print(f"\nreport written to {report_path}")

    if interrupted:
        return 2
    if summary["failures"] == 0:
        return 0
    return 1


def main() -> int:
    """Parses arguments and runs the soak."""
    parser = argparse.ArgumentParser(
        description="Drive the running board like real operators would.")
    parser.add_argument("--host", default="192.168.10.60",
                        help="board address serving the UI")
    parser.add_argument("--port", type=int, default=8000,
                        help="API port")
    parser.add_argument("--minutes", type=float, default=10.0,
                        help="how long to run in minutes")
    parser.add_argument("--operators", type=int, default=3,
                        help="number of virtual operators")
    parser.add_argument("--profile", choices=["mixed", "active", "monitor", "stress"],
                        default="mixed",
                        help="operator profile: mixed (1 active, rest monitor), "
                             "active, monitor, or stress")
    parser.add_argument("--step-deg", type=float, default=DEFAULT_STEP_DEG,
                        help="motion resolution step size (default 0.06)")
    parser.add_argument("--report", default=None,
                        help="path for the JSON report")
    parser.add_argument("--checkpoint-minutes", type=float,
                        default=DEFAULT_CHECKPOINT_MINUTES,
                        help="interval between status updates (0 to disable)")
    parser.add_argument("--preflight", action="store_true",
                        help="probe board health and datum without running soak")
    parser.add_argument("--settle-probe", action="store_true",
                        help="run one D40 settle-investigation protocol, "
                             "not the soak")
    parser.add_argument("--probe-phase", choices=["a", "b", "c", "d"],
                        default=None,
                        help="settle-probe protocol: a=repeatability, "
                             "b=minimum effective step, c=re-command, "
                             "d=large-move survey across multiple targets "
                             "(ignores --probe-target)")
    parser.add_argument("--probe-target", type=float, default=30.0,
                        help="grid-aligned base target for the settle probe")
    parser.add_argument("--probe-loaded", action="store_true",
                        help="mark this settle-probe run as taken under "
                             "hand-held load")
    args = parser.parse_args()

    if args.preflight:
        ok = run_preflight(args.host, args.port)
        return 0 if ok else 1

    if args.settle_probe:
        if args.probe_phase is None:
            parser.error("--settle-probe requires --probe-phase {a,b,c}")
        return run_settle_probe(args.host, args.port, args.probe_phase,
                                args.probe_target, args.probe_loaded,
                                args.report)

    return run_soak(args.host, args.port, args.minutes, args.operators,
                    args.report, args.checkpoint_minutes, args.profile,
                    args.step_deg)


if __name__ == "__main__":
    raise SystemExit(main())
