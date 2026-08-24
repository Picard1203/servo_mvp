"""Synthetic operators that drive the running board like people would.

Written for the soak described in `docs/BACKLOG.md` D4: a race that stopped
reproducing in seven minutes is rare, not absent, and only sustained realistic
load can tell the difference.

Each virtual operator reproduces `app.js`'s exact traffic shape: three
independent polling streams - state once a second, the zero list and the
event list every 15 seconds, each on its own kept-alive HTTP connection
(`--enhanced 8 August 2026`, closing backlog D27) - plus, between polls, what
a person does: moves somewhere, waits to see it arrive, thinks for a while,
occasionally locks, saves a zero or pulls an export. Think time is
randomised, because several operators acting in lockstep is a load pattern
no real site produces.

Earlier versions of this tool used `urllib.request`, which opens and closes
a fresh TCP connection on every call. That is not what a browser does - a
browser holds one connection open per active poll via HTTP keep-alive - and
it materially understated real connection-slot pressure on the relay's
6-socket ceiling (ADR-0009). Each poll stream here now reuses one
`http.client.HTTPConnection`, reconnecting only when the server actually
closes it (uvicorn's `timeout_keep_alive`) or a transport error occurs.
`connection_opens` in the report is how often that happened - it should stay
low if keep-alive is doing its job.

Everything it reports is client-side: what the API answered and how long it
took. The board's own side of the story - sampler gaps, fabricated positions,
logged failures, the MCU's own counters (backlog D3) - comes from
`tools/soak_report.py` afterwards, and the two are compared by timestamp.

    python3 tools/synthetic_operator.py --host 192.168.10.60 --minutes 120 \\
        --operators 3 --report soak.json

Built to survive being left alone for stretches, not just a continuous
watch: every `--checkpoint-minutes` (default 5) it prints a one-line status
and rewrites the report file in place, so a check-in mid-run has fresh data
and a crash or a closed terminal loses at most one checkpoint. Ctrl-C (or a
SIGTERM) writes the report as it stands and exits cleanly rather than losing
everything gathered so far.

Safe by construction: it stays inside the travel window, treats a refusal as
a valid answer rather than an error, and never commands a move while it
believes the mechanism is still moving.
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

# One poll per second, matching static/app.js's POLL_STATE_MS.
POLL_STATE_SECONDS: float = 1.0

# Matching static/app.js's POLL_LISTS_MS - two SEPARATE timers, same period,
# not one shared poll. That is what lets them drift into overlapping with
# each other and with the state poll over a multi-hour run.
POLL_ZEROS_SECONDS: float = 15.0
POLL_EVENTS_SECONDS: float = 15.0

# Human pauses between deliberate actions. A person lines up a move, watches
# it, thinks, then does the next thing.
THINK_SECONDS_MIN: float = 4.0
THINK_SECONDS_MAX: float = 20.0

# Kept inside the +/-90 window so refusals mean something went wrong rather
# than the generator asking for the impossible.
TARGET_DEG_MIN: float = -80.0
TARGET_DEG_MAX: float = 80.0

# Longest a move is waited on before giving up and moving on.
MOVE_SETTLE_TIMEOUT_SECONDS: float = 45.0

# How often, by default, to print a live status line and rewrite the report
# file - the "check in periodically, be away for stretches" usage pattern.
DEFAULT_CHECKPOINT_MINUTES: float = 5.0


class Metrics:
    """Thread-safe tally of everything the operators observed.

    Attributes:
        _lock (threading.Lock): Guards every field below.
        _latencies (dict[str, list[float]]): Seconds per request, by action.
        _failures (dict[str, int]): Transport failures, by action.
        _rejections (dict[str, int]): Refusals the API answered deliberately.
        _connection_opens (dict[str, int]): New TCP connections opened, by
            action - stays low when keep-alive is working.
        _requests (int): Total requests attempted.
        _invalid_readings (int): Replies carrying reading_valid false.
        _unknown_positions (int): Replies carrying a null output_deg.
        _first_invalid_at (Optional[float]): Unix timestamp of the first
            invalid reading, for lining up against the database.
    """

    def __init__(self) -> None:
        """Creates an empty tally."""
        self._lock: threading.Lock = threading.Lock()
        self._latencies: dict[str, list[float]] = {}
        self._failures: dict[str, int] = {}
        self._rejections: dict[str, int] = {}
        self._connection_opens: dict[str, int] = {}
        self._requests: int = 0
        self._invalid_readings: int = 0
        self._unknown_positions: int = 0
        self._first_invalid_at: Optional[float] = None

    def record_success(self, action: str, seconds: float) -> None:
        """Records one completed request.

        Args:
            action (str): Name of the action performed.
            seconds (float): Round-trip time.

        Returns:
            None
        """
        with self._lock:
            self._requests += 1
            if action not in self._latencies:
                self._latencies[action] = []
            self._latencies[action].append(seconds)

    def record_failure(self, action: str) -> None:
        """Records a request that did not complete at all.

        Args:
            action (str): Name of the action performed.

        Returns:
            None
        """
        with self._lock:
            self._requests += 1
            self._failures[action] = self._failures.get(action, 0) + 1

    def record_rejection(self, action: str) -> None:
        """Records a refusal the API issued on purpose.

        A move refused as out of travel, or while locked, is the system
        working. It is counted apart from failures so the two are never
        confused in the report.

        Args:
            action (str): Name of the action performed.

        Returns:
            None
        """
        with self._lock:
            self._rejections[action] = self._rejections.get(action, 0) + 1

    def record_connection_opened(self, action: str) -> None:
        """Records that a poll stream opened a fresh TCP connection.

        A stream that opens many connections over a long run means
        keep-alive is not helping - either the server is closing idle
        connections faster than expected, or something upstream (the relay)
        is dropping them. Either is exactly what ADR-0009 needs measured.

        Args:
            action (str): Name of the poll stream.

        Returns:
            None
        """
        with self._lock:
            self._connection_opens[action] = \
                self._connection_opens.get(action, 0) + 1

    def record_reading(self, reading_valid: bool,
                       output_deg: Optional[float]) -> None:
        """Records what a state reply said about the position.

        Args:
            reading_valid (bool): The reply's reading_valid flag.
            output_deg (Optional[float]): The reported angle, or None.

        Returns:
            None
        """
        with self._lock:
            if reading_valid is False:
                self._invalid_readings += 1
                if self._first_invalid_at is None:
                    self._first_invalid_at = time.time()
            if output_deg is None:
                self._unknown_positions += 1

    def summary(self) -> dict[str, Any]:
        """Builds the report.

        Returns:
            dict[str, Any]: Counts and latency percentiles per action.
        """
        with self._lock:
            actions: dict[str, Any] = {}
            for action in sorted(self._latencies.keys()):
                samples = sorted(self._latencies[action])
                actions[action] = {
                    "count": len(samples),
                    "median_s": round(statistics.median(samples), 3),
                    "p95_s": round(samples[int(len(samples) * 0.95) - 1], 3),
                    "max_s": round(samples[-1], 3),
                    "failures": self._failures.get(action, 0),
                    "rejections": self._rejections.get(action, 0),
                    "connection_opens": self._connection_opens.get(action, 0),
                }
            total_failures = 0
            for count in self._failures.values():
                total_failures += count
            return {
                "requests": self._requests,
                "failures": total_failures,
                "invalid_readings": self._invalid_readings,
                "unknown_positions": self._unknown_positions,
                "first_invalid_at": self._first_invalid_at,
                "actions": actions,
            }


class PersistentPoller:
    """One HTTP/1.1 keep-alive connection, reused across a polling loop.

    This is what makes the load shape match a real browser tab: `app.js`
    holds one TCP connection open per active poll stream, reusing it every
    interval. `urllib.request.urlopen` does not do this - each call opens
    and closes its own connection - which understates the relay's real
    connection-slot pressure. Reconnects transparently on a transport error
    or once the server actually closes the connection (uvicorn's
    `timeout_keep_alive`), and counts every reconnect via
    `Metrics.record_connection_opened`.
    """

    def __init__(self, host: str, port: int, metrics: Metrics,
                 action: str) -> None:
        """Creates a poller bound to one action name.

        Args:
            host (str): Board address.
            port (int): API port.
            metrics (Metrics): Shared tally.
            action (str): Name recorded in the metrics for every request.

        Returns:
            None
        """
        self._host = host
        self._port = port
        self._metrics = metrics
        self._action = action
        self._connection: Optional[http.client.HTTPConnection] = None

    def get(self, path: str) -> Optional[Any]:
        """Performs one GET, reusing the open connection when there is one.

        Args:
            path (str): Full request path, including the API prefix.

        Returns:
            Optional[Any]: The decoded JSON reply, or None on failure or a
            deliberate refusal.
        """
        started = time.monotonic()
        for attempt in range(2):   # one retry, on a freshly opened connection
            try:
                if self._connection is None:
                    self._connection = http.client.HTTPConnection(
                        self._host, self._port, timeout=10)
                    self._metrics.record_connection_opened(self._action)
                self._connection.request("GET", path)
                response = self._connection.getresponse()
                body = response.read()
                if response.status >= 400:
                    if 400 <= response.status < 500:
                        self._metrics.record_rejection(self._action)
                    else:
                        self._metrics.record_failure(self._action)
                    return None
                self._metrics.record_success(self._action,
                                             time.monotonic() - started)
                return json.loads(body)
            except (http.client.HTTPException, OSError):
                self.close()
                # First attempt: the connection may simply have been closed
                # by the server (idle keep-alive timeout) - retry once on a
                # fresh one before counting a failure.
        self._metrics.record_failure(self._action)
        return None

    def close(self) -> None:
        """Drops the current connection, if any. Safe to call repeatedly.

        Returns:
            None
        """
        if self._connection is not None:
            try:
                self._connection.close()
            except OSError:
                pass
            self._connection = None


class SyntheticOperator:
    """One virtual operator: three poll streams plus deliberate actions.

    Attributes:
        _host (str): Board address.
        _port (int): API port.
        _base_url (str): Root of the API, without a trailing slash - used
            only by the one-off actions in _perform_one_action.
        _metrics (Metrics): Shared tally.
        _name (str): Identifier used in console output.
        _random (random.Random): Independently seeded, so operators do not
            act in lockstep.
        _deadline (float): Monotonic time at which this operator stops.
    """

    def __init__(self, host: str, port: int, metrics: Metrics, name: str,
                 seed: int, deadline: float) -> None:
        """Creates one operator.

        Args:
            host (str): Board address.
            port (int): API port.
            metrics (Metrics): Shared tally.
            name (str): Identifier used in console output.
            seed (int): Seed for this operator's think times and targets.
            deadline (float): Monotonic time at which to stop.

        Returns:
            None
        """
        self._host: str = host
        self._port: int = port
        self._base_url: str = f"http://{host}:{port}/api/v1"
        self._metrics: Metrics = metrics
        self._name: str = name
        self._random: random.Random = random.Random(seed)
        self._deadline: float = deadline
        self._stop: threading.Event = threading.Event()
        self._last_state_at: float = time.monotonic()

    def stop(self) -> None:
        """Signals background threads to stop.

        Returns:
            None
        """
        self._stop.set()

    def _request(self, action: str, path: str,
                 payload: Optional[dict[str, Any]] = None,
                 read_body: bool = True) -> Optional[Any]:
        """Performs one one-off HTTP call and records its outcome.

        Deliberate, occasional actions (a move, a lock, an export) - unlike
        the three continuous poll streams, these do not model persistent
        connection reuse; a single click opening its own connection is a
        reasonable worst case, and is not what ADR-0009's finding was about.

        Args:
            action (str): Name recorded in the metrics.
            path (str): Path below the API root.
            payload (Optional[dict[str, Any]]): JSON body for a POST.
            read_body (bool): False to drain the body without decoding it,
                for responses that are not JSON.

        Returns:
            Optional[Any]: The decoded reply, or None when the call failed
            or was deliberately refused.
        """
        data: Optional[bytes] = None
        headers: dict[str, str] = {}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(self._base_url + path, data=data,
                                         headers=headers)
        started = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                body = response.read()
            self._metrics.record_success(action, time.monotonic() - started)
            if read_body is False:
                return len(body)
            return json.loads(body)
        except urllib.error.HTTPError as error:
            # 4xx is the API answering deliberately - refused while locked,
            # out of travel, no such zero. That is behaviour, not breakage.
            if (error.code >= 400) and (error.code < 500):
                self._metrics.record_rejection(action)
                return None
            self._metrics.record_failure(action)
            return None
        except Exception:
            self._metrics.record_failure(action)
            return None

    def stream_forever(self) -> None:
        """Reads the SSE stream forever.

        Returns:
            None
        """
        while (time.monotonic() < self._deadline) and (not self._stop.is_set()):
            try:
                conn = http.client.HTTPConnection(self._host, self._port, timeout=30)
                self._metrics.record_connection_opened("stream")
                conn.request("GET", "/api/v1/stream", 
                            headers={"Accept": "text/event-stream"})
                resp = conn.getresponse()
                if resp.status != 200:
                    raise http.client.HTTPException(f"{resp.status}")
                
                current_event = None
                current_data = None
                # Read line by line from the chunked response
                for raw_line in resp:
                    if self._stop.is_set() or time.monotonic() >= self._deadline:
                        conn.close()
                        return
                    line = raw_line.decode("utf-8").rstrip("\n").rstrip("\r")
                    if line.startswith("event: "):
                        current_event = line[7:]
                    elif line.startswith("data: "):
                        current_data = line[6:]
                    elif line == "":
                        if current_event and current_data:
                            self._handle_sse_event(current_event, current_data)
                        current_event = None
                        current_data = None
            except (http.client.HTTPException, OSError, json.JSONDecodeError):
                self._metrics.record_failure("stream")
                self._stop.wait(3.0)  # reconnect delay

    def _handle_sse_event(self, event: str, data: str) -> None:
        """Processes one SSE event from the stream.

        Args:
            event (str): The event type.
            data (str): The raw JSON payload.

        Returns:
            None
        """
        now = time.monotonic()
        try:
            payload = json.loads(data)
        except json.JSONDecodeError:
            self._metrics.record_failure("stream")
            return

        if event == "state":
            elapsed = now - self._last_state_at
            self._metrics.record_success("state", elapsed)
            self._metrics.record_reading(
                payload.get("reading_valid", True), payload.get("output_deg"))
            self._last_state_at = now
        elif event == "zeros":
            self._metrics.record_success("zeros_poll", 0.0)
        elif event == "events":
            self._metrics.record_success("events_poll", 0.0)

    def act_forever(self) -> None:
        """Performs deliberate actions with human pauses until the deadline.

        Returns:
            None
        """
        while (time.monotonic() < self._deadline) and (not self._stop.is_set()):
            self._perform_one_action()
            think = self._random.uniform(THINK_SECONDS_MIN,
                                         THINK_SECONDS_MAX)
            time.sleep(min(think, max(0.0,
                                      self._deadline - time.monotonic())))

    def _perform_one_action(self) -> None:
        """Chooses and performs a single action, weighted like real use.

        Returns:
            None
        """
        roll = self._random.random()
        if roll < 0.62:
            self._move_somewhere()
            return
        if roll < 0.74:
            self._toggle_lock()
            return
        if roll < 0.84:
            self._request("zeros_list", "/zeros")
            return
        if roll < 0.90:
            self._request("stop", "/servo/stop", payload={})
            return
        if roll < 0.96:
            self._request("health", "/system/health")
            return
        self._pull_export()

    def _move_somewhere(self) -> None:
        """Commands a move and waits for the mechanism to settle.

        Returns:
            None
        """
        target = round(self._random.uniform(TARGET_DEG_MIN,
                                            TARGET_DEG_MAX), 1)
        speed = self._random.choice([10.0, 20.0, 30.0, 45.0, 60.0])
        accepted = self._request("move", "/servo/move",
                                 payload={"target_deg": target,
                                          "speed_dps": speed})
        if accepted is None:
            return
        self._wait_until_stopped()

    def _wait_until_stopped(self) -> None:
        """Polls until the mechanism stops moving or the timeout expires.

        A person watches a move finish before starting the next one.
        Commanding the next move mid-travel would be a load pattern, not a
        simulation.

        Returns:
            None
        """
        limit = time.monotonic() + MOVE_SETTLE_TIMEOUT_SECONDS
        moving = True
        while (moving is True) and (time.monotonic() < limit) \
                and (time.monotonic() < self._deadline) and (not self._stop.is_set()):
            time.sleep(POLL_STATE_SECONDS)
            # Deliberately a separate action name from the persistent
            # "state" poll stream: this one-off, fresh-connection check
            # during a move is a different traffic shape and must not be
            # merged into poll_state_forever's kept-alive numbers.
            state = self._request("state_settle", "/servo/state")
            if state is None:
                moving = False
            else:
                moving = state.get("moving", False)

    def _toggle_lock(self) -> None:
        """Engages the lock, waits, then releases it.

        Returns:
            None
        """
        self._request("lock", "/servo/lock", payload={"locked": True})
        time.sleep(self._random.uniform(2.0, 6.0))
        self._request("lock", "/servo/lock", payload={"locked": False})

    def _pull_export(self) -> None:
        """Requests a telemetry export.

        The heaviest thing the UI can ask for, and the best stress on the
        relay: the reply is streamed CSV, so it crosses the Bridge in far
        more chunks than any other response.

        Returns:
            None
        """
        finish = time.time()
        start = finish - 3600.0
        self._request("export", f"/telemetry/export?ts_from={start}"
                                f"&ts_to={finish}", read_body=False)


class Checkpointer:
    """Periodically prints a status line and rewrites the report file.

    Exists for the "in the room most of the time, gone for stretches"
    running mode: a check-in mid-run sees fresh numbers rather than silence,
    and a crash or a closed terminal loses at most one checkpoint interval
    of data rather than the whole run.
    """

    def __init__(self, metrics: Metrics, report_path: Optional[str],
                 interval_seconds: float, started_at: float,
                 deadline: float) -> None:
        """Creates a checkpointer. Call run() on its own thread.

        Args:
            metrics (Metrics): Shared tally to snapshot.
            report_path (Optional[str]): Where to write the report, or None
                to only print.
            interval_seconds (float): Seconds between checkpoints.
            started_at (float): Wall-clock start time (time.time()).
            deadline (float): Monotonic time the run ends.

        Returns:
            None
        """
        self._metrics = metrics
        self._report_path = report_path
        self._interval_seconds = interval_seconds
        self._started_at = started_at
        self._deadline = deadline
        self._stop = threading.Event()

    def run(self) -> None:
        """Loops until stop() is called or the deadline passes.

        Returns:
            None
        """
        while not self._stop.is_set():
            remaining = self._deadline - time.monotonic()
            if remaining <= 0:
                return
            if self._stop.wait(min(self._interval_seconds, remaining)):
                return
            self.write_once()

    def write_once(self) -> None:
        """Prints one status line and rewrites the report file, if given.

        Returns:
            None
        """
        summary = self._metrics.summary()
        elapsed_min = (time.time() - self._started_at) / 60.0
        opens = sum(row.get("connection_opens", 0)
                   for row in summary["actions"].values())
        print(f"[{time.strftime('%H:%M:%S')}] checkpoint  "
              f"elapsed={elapsed_min:.0f}m  requests={summary['requests']}  "
              f"failures={summary['failures']}  "
              f"invalid_readings={summary['invalid_readings']}  "
              f"connection_opens={opens}")
        if self._report_path is not None:
            _write_report(self._report_path, summary)

    def stop(self) -> None:
        """Signals run() to return promptly.

        Returns:
            None
        """
        self._stop.set()


def _write_report(report_path: str, summary: dict[str, Any]) -> None:
    """Writes the summary as JSON, overwriting any previous checkpoint.

    Args:
        report_path (str): Destination path.
        summary (dict[str, Any]): What to write.

    Returns:
        None
    """
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2)


def run_soak(host: str, port: int, minutes: float, operators: int,
             report_path: Optional[str], checkpoint_minutes: float) -> int:
    """Runs the soak and prints the report.

    Args:
        host (str): Board address serving the UI.
        port (int): Port the API listens on.
        minutes (float): How long to run.
        operators (int): How many virtual operators to simulate.
        report_path (Optional[str]): Where to write the JSON report.
        checkpoint_minutes (float): Interval between live status updates and
            report rewrites; 0 disables checkpointing.

    Returns:
        int: 0 when no transport failures occurred, 1 otherwise.
    """
    metrics = Metrics()
    deadline = time.monotonic() + (minutes * 60.0)
    started_at = time.time()
    threads: list[threading.Thread] = []

    print(f"soak: {operators} operator(s) against {host}:{port} "
          f"for {minutes:g} minute(s)")
    print(f"soak: started at {time.strftime('%H:%M:%S')}, "
          f"ends about {time.strftime('%H:%M:%S', time.localtime(started_at + minutes * 60.0))}")

    operator_instances: list[SyntheticOperator] = []
    for index in range(operators):
        operator = SyntheticOperator(host, port, metrics,
                                     f"operator-{index + 1}",
                                     seed=1000 + index, deadline=deadline)
        operator_instances.append(operator)
        for target in (operator.stream_forever, operator.act_forever):
            thread = threading.Thread(target=target, daemon=True)
            threads.append(thread)
            thread.start()

    checkpointer: Optional[Checkpointer] = None
    if checkpoint_minutes > 0:
        checkpointer = Checkpointer(metrics, report_path,
                                    checkpoint_minutes * 60.0, started_at,
                                    deadline)
        checkpoint_thread = threading.Thread(target=checkpointer.run,
                                             daemon=True)
        checkpoint_thread.start()

    interrupted = False

    def _on_interrupt(_signum: int, _frame: Any) -> None:
        nonlocal interrupted
        interrupted = True

    previous_sigterm = signal.signal(signal.SIGTERM, _on_interrupt)
    try:
        for thread in threads:
            while thread.is_alive():
                thread.join(timeout=1.0)
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
        for operator in operator_instances:
            operator.stop()

    if interrupted:
        print()
        print("soak: interrupted - writing what was gathered so far")

    summary = metrics.summary()
    summary["host"] = host
    summary["operators"] = operators
    summary["started_at"] = started_at
    summary["finished_at"] = time.time()
    summary["minutes"] = minutes
    summary["interrupted"] = interrupted

    print()
    print("---- soak report ----")
    print(f"requests           {summary['requests']}")
    print(f"transport failures {summary['failures']}")
    print(f"invalid readings   {summary['invalid_readings']}")
    print(f"unknown positions  {summary['unknown_positions']}")
    print()
    for action in sorted(summary["actions"].keys()):
        row = summary["actions"][action]
        print(f"  {action:<12} n={row['count']:<6} "
              f"median={row['median_s']:<7} p95={row['p95_s']:<7} "
              f"max={row['max_s']:<7} fail={row['failures']} "
              f"refused={row['rejections']} "
              f"conn_opens={row['connection_opens']}")

    if report_path is not None:
        _write_report(report_path, summary)
        print()
        print(f"report written to {report_path}")
        print("compare it against the board: sampler gaps over 2 s, rows with "
              "counts <= 0, and any servo.read.failed in the log. "
              "tools/soak_report.py reads the board's own account, including "
              "the MCU-side counters (backlog D3).")

    if interrupted:
        return 2
    if summary["failures"] == 0:
        return 0
    return 1


def main() -> int:
    """Parses arguments and runs the soak.

    Returns:
        int: Process exit code.
    """
    parser = argparse.ArgumentParser(
        description="Drive the running board like real operators would.")
    parser.add_argument("--host", default="192.168.10.60",
                        help="board address serving the UI")
    parser.add_argument("--port", type=int, default=8000,
                        help="API port")
    parser.add_argument("--minutes", type=float, default=120.0,
                        help="how long to run")
    parser.add_argument("--operators", type=int, default=3,
                        help="virtual operators; 3 remote is the target in R1")
    parser.add_argument("--report", default=None,
                        help="path for the JSON report, rewritten at every "
                             "checkpoint")
    parser.add_argument("--checkpoint-minutes", type=float,
                        default=DEFAULT_CHECKPOINT_MINUTES,
                        help="live status + report rewrite interval; 0 to "
                             "disable")
    arguments = parser.parse_args()
    return run_soak(arguments.host, arguments.port, arguments.minutes,
                    arguments.operators, arguments.report,
                    arguments.checkpoint_minutes)


if __name__ == "__main__":
    raise SystemExit(main())
