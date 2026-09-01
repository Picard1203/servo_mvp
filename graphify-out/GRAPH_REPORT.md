# Graph Report - servo_mvp  (2026-09-01)

## Corpus Check
- 150 files · ~131,349 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2272 nodes · 3834 edges · 167 communities (133 shown, 34 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 351 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `99b33ef8`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- NetworkRelay
- .snapshot
- SavedPositionService
- app.js
- ServoStateStore
- Metrics
- test_relay_path.py
- test_saved_positions_routes.py
- TestFailedReadIsNeverAPosition
- Database
- SyntheticOperator
- adr/README.md
- ADR-0005 — Develop as if already air-gapped
- check_client_behaviour.js
- For the operators
- TestCrud
- LogRecord
- TestGetSet
- TEST
- test_mcu_log.py
- get_app_state_repository
- verify.py
- Settings
- deps.py
- _read_sse_lines
- test_bridge_servo_repository.py
- ServoController.cpp
- Document reading flow (router)
- D2 — capture() can store a failed read as position 0
- Closed items
- Design Notes
- Requirements captured but not yet designed
- LoggerStub
- OnTarget.ino
- get_settings
- The flows
- get_isolation_service
- BridgeServoRepository
- AppStub
- get_events
- Deliver
- Conventions
- TestExport
- App.cpp
- Tasks — detail
- IsolationService
- ServoSnapshot
- SavedPositionResponse
- 3. The 7 Rigorous Test Protocols
- test_pure_logic.cpp
- T8 — Instrumented run on the board over adb
- Defects
- Drain with while, never if
- ServoStateView
- What changed
- run_soak
- routers/system.py
- D8 — .env must be created before the first run
- TestNothingIsReportedAsMeasuredOnAFailedRead
- soak_report.py
- export_binary
- TelemetrySample
- MotionService
- test_synthetic_operator.py
- AngleConverter
- Defects — detail
- ServoBus
- R-items — detail
- Ordering, rewritten 8 August 2026 — by session, with sizes
- FakeBridge
- Bench-verified hardware facts
- Task: strip explanatory prose from sketch/src/
- DiagLog
- TestExport
- Twin review
- Dev And Test Dependencies
- Task: strip explanatory prose from python/app/
- FlakyServo
- setup_logging
- SavedPosition
- TestRangeConfiguration
- database.py
- T5 — Add design_diagrams/ with PlantUML
- McuLog
- e2e/conftest.py
- TestTravelWindow
- SpiRemap.cpp
- adb push never deletes
- synthetic_operator.py
- Tasks
- .connection
- Adopt Connections With accept(), Never available
- Detect Disconnects Before Accepting
- No Bricks Constraint
- One fact lives in exactly one file
- START HERE — the session plan
- get_mcu_log
- Language
- Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start)
- D7 — UI not verified on small operator screens
- test_motion_service.py
- TelemetryService
- Bridge contract checker
- Export 24h CSV
- Duplicate app.js Script Tag
- Six-Fault Status Grid
- Angle And Speed Move Controls
- Arduino_RouterBridge
- kRelayChunkBytes Must Match relay_chunk_bytes
- loop() Must Yield
- Bridge Net Contract
- provide_safe Registration
- Serial Works; Monitor Is Optional
- TestFailedReadsAreNotStored
- routers/saved_positions.py
- check_file
- Saved positions replace zeros; the datum is the only reference
- get_state_store
- TestResilience
- get_telemetry_service
- TelemetrySnapshot
- BridgeApi.cpp
- test_servo_state.py
- How to work on this repo
- Calibrate Control
- decode_sign_magnitude
- Sketch class responsibilities
- get_motion_service
- A green suite proves only the simulated path
- .stop
- Four easily conflated position terms
- R4 — Post-MVP mechanical restraint unified under one Lock
- test_calibration_service.py
- T1 — Apply CONVENTIONS.md across the codebase
- Repository layout
- Arduino UNO Q + Waveshare ST3215
- SimulatedServoRepository
- TestCommands
- Skills archive
- A failed read is reported as unknown, never as a number
- TestMove
- TestIsolate
- Operator lens
- EventService
- BridgeRelay
- get_relay
- wait_until
- main.py
- BridgeStub
- main
- The connection ceiling stays at 6 this batch
- Motor isolation state survives a reboot
- Use SMS_STS, Never SCSCL

## God Nodes (most connected - your core abstractions)
1. `get_state_store()` - 76 edges
2. `ServoStateStore` - 64 edges
3. `TelemetrySnapshot` - 50 edges
4. `wait_until()` - 50 edges
5. `Closed items` - 46 edges
6. `Database` - 42 edges
7. `TEST()` - 37 edges
8. `get_isolation_service()` - 36 edges
9. `get_settings()` - 35 edges
10. `BridgeServoRepository` - 35 edges

## Surprising Connections (you probably didn't know these)
- `Single-context documentation layout` --semantically_similar_to--> `Document reading flow (router)`  [INFERRED] [semantically similar]
  docs/agents/domain.md → CLAUDE.md
- `sshfs board mount as working copy` --semantically_similar_to--> `Development shortcut — sshfs mount of the board`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Apply SpiRemap twice` --semantically_similar_to--> `Confirm the Ethernet patch survived the first build`  [INFERRED] [semantically similar]
  sketch/README.md → README.md
- `Served from the board to any machine on the network` --conceptually_related_to--> `R1 — Determine the real concurrent-operator ceiling`  [INFERRED]
  README.md → docs/BACKLOG.md
- `Graphify-first navigation rule` --conceptually_related_to--> `Single-context documentation layout`  [INFERRED]
  CLAUDE.md → docs/agents/domain.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Consequences of the air-gap constraint** — docs_adr_0005_air_gapped_by_default_development_decision, docs_adr_0002_no_frontend_framework_decision, readme_air_gapped_bundle, readme_core_version_pin, sketch_readme_tinytest_harness, docs_backlog_t2_package_the_air_gapped_bundle [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]

## Communities (167 total, 34 thin omitted)

### Community 0 - "NetworkRelay"
Cohesion: 0.11
Nodes (23): k_timeout_t, ByteSink, CloseSink, OpenSink, ByteSink, CloseSink, OpenSink, NetworkRelay (+15 more)

### Community 1 - ".snapshot"
Cohesion: 0.13
Nodes (9): Converts raw counts to output degrees against the datum. Args: raw_counts…, Returns output angles reachable from the datum. Returns: tuple[float, float]:…, Reports whether a target maps inside the servo count range. Args: output_deg…, Converts an output angle to absolute encoder counts. Args: output_deg (float):…, Returns a coherent snapshot of servo, lock and datum state. Returns:…, Returns current output angle relative to the datum. Returns: Optional[float]:…, Returns the datum in raw counts, or mid-travel if uncalibrated. Returns: int:…, Converts counts to servo pre-ratio degrees. Args: raw_counts (int): Absolute… (+1 more)

### Community 2 - "SavedPositionService"
Cohesion: 0.10
Nodes (20): Raised when an edit targets a saved position changed since it was read., StalePositionError, get_saved_position_repository(), Returns the saved-position repository. Returns: SavedPositionRepository: The…, A saved position enriched with its live angle, for display. Attributes: id…, SavedPositionView, ABC, Abstract persistence of saved positions. (+12 more)

### Community 3 - "app.js"
Cohesion: 0.06
Nodes (79): ADR-0008, ANGLE_FIELDS, ANGLE_SERIES, angleSortedDownsampleRefs(), apiDelete(), apiGet(), apiPatch(), apiPost() (+71 more)

### Community 4 - "ServoStateStore"
Cohesion: 0.05
Nodes (24): InvalidReadingError, Raised when an operation needs a reading the servo did not supply., Calibration, The calibration datum. Attributes: raw_counts (int): Absolute encoder position…, CalibrationService, Captures the current physical position as the datum. Attributes: _servo…, Captures the current physical position as the datum. Returns: Calibration: The…, Records that the servo acknowledged an isolation write. Args: isolated (bool):… (+16 more)

### Community 5 - "Metrics"
Cohesion: 0.09
Nodes (13): Metrics, Records one completed REST request. Args: action (str): Name of the action…, Records a request that failed to connect or completed with a 5xx error. Args:…, Records a deliberate 4xx refusal from the API with its reason. Args: action…, Records an SSE stream connection open. Args: is_reconnect (bool): True if this…, Records a disconnect or transport failure on an SSE stream., Records reception of one SSE frame. Args: event (str): Event name (state,…, Records whether a state snapshot carried valid telemetry. Args: reading_valid… (+5 more)

### Community 6 - "test_relay_path.py"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 7 - "test_saved_positions_routes.py"
Cohesion: 0.09
Nodes (9): Saved-positions API routes: list, create, update, delete, go., POST /api/v1/positions/{id}/go., PATCH /api/v1/positions/{id}., POST and GET /api/v1/positions., DELETE /api/v1/positions/{id}., TestCreateList, TestDelete, TestGo (+1 more)

### Community 8 - "TestFailedReadIsNeverAPosition"
Cohesion: 0.13
Nodes (7): A read the servo never answered must not become a position. Observed on the…, The rule that nulls the position governs the readings beside it. The docstring…, Nulling on failure must not null on success., D23, amends ADR-0008: the same rule governs moving and the six fault flags.…, Nulling on failure must not null on success (D23)., read_counts()'s own guard (D24): unexercised since it was written, same defect…, TestFailedReadIsNeverAPosition

### Community 9 - "Database"
Cohesion: 0.10
Nodes (15): Database, Carries the old zeros table's rows into app_state and saved_positions., Closes the connection., Creates tables and indexes when missing., Owns the SQLite connection and serializes all access to it. Attributes:…, Adds columns introduced after a database was first created., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):… (+7 more)

### Community 10 - "SyntheticOperator"
Cohesion: 0.16
Nodes (12): One virtual operator running an SSE stream and deliberate HTTP actions.…, Performs one REST HTTP call and updates metrics. Args: action (str): Metrics…, Executes deliberate actions with think times., Dispatches an action based on the operator's profile., Commands a motion to a quantized valid angle., Polls until movement settles or timeout elapses., Exercises saved-position CRUD operations., Engages digital lock, waits briefly, and releases it. (+4 more)

### Community 11 - "adr/README.md"
Cohesion: 0.07
Nodes (20): Consequences, The network path runs through the MCU, not the Linux side, Consequences, Considered and rejected, Plain HTML, CSS and JavaScript — no framework, no build step, Consequences, Travel window is ±90 output degrees, and multi-turn stays off, Consequences (+12 more)

### Community 12 - "ADR-0005 — Develop as if already air-gapped"
Cohesion: 0.13
Nodes (16): Servo Control App Manifest, sshfs board mount as working copy, ADR-0002 — Plain HTML/CSS/JS, no framework, ADR-0005 — Develop as if already air-gapped, R7 — Handover logistics depend on adapter delivery, T2 — Package the air-gapped bundle, T3 — Run the on-target test suite, Environment right now (+8 more)

### Community 13 - "check_client_behaviour.js"
Cohesion: 0.17
Nodes (7): APP, ctx, els, fs, path, toasts, vm

### Community 14 - "For the operators"
Cohesion: 0.13
Nodes (14): For the operators, For the programme, For whoever receives the MVP, Open questions, Q10 — Should code-level docs/comments carry rationale, or move to `docs/`? `answered`, Q1 — What screen will you actually use? `answered`, Q2 — How many operators at once, really, and doing what? `answered`, Q3 — When the machine misbehaves on site, what do you want to be able to do? `answered` (+6 more)

### Community 15 - "TestCrud"
Cohesion: 0.19
Nodes (6): _position(), Builds an unsaved saved-position entity. Args: name: Position name. counts: Raw…, Create, read, update, delete., The UNIQUE constraint surfaces as a domain exception, not a 500., TestCrud, TestNameUniqueness

### Community 16 - "LogRecord"
Cohesion: 0.14
Nodes (11): LogRecord, arg1, arg2, event, level, message, uptime_ms, LogRing (+3 more)

### Community 17 - "TestGetSet"
Cohesion: 0.25
Nodes (3): A key that was never written reads back as None; a written one reads back as…, The whole point of this table: a second process (or a restart) reading the same…, TestGetSet

### Community 18 - "TEST"
Cohesion: 0.07
Nodes (28): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, log_ring_drops_oldest_when_full_and_counts_it (+20 more)

### Community 19 - "test_mcu_log.py"
Cohesion: 0.15
Nodes (9): _lines(), McuLog: receiving and writing diagnostic events forwarded from the MCU., Reads every JSON line from a file. Args: path: File to read. Returns: One dict…, Bridge callback registration., One event in, one JSON line out., Size-based single-backup rotation., TestRegistration, TestRotation (+1 more)

### Community 20 - "get_app_state_repository"
Cohesion: 0.05
Nodes (29): NotFoundError, NotFoundException, PositionOutOfRangeError, Exception, Raised when a referenced entity does not exist., Raised when a saved position's angle falls outside the travel window., Appends this class's error-code segment to its parent's. Args: code…, Base for 404s: a referenced entity does not exist. (+21 more)

### Community 21 - "verify.py"
Cohesion: 0.14
Nodes (23): _delta(), _ensure_local_venv_mirror(), _load_baseline(), main(), _mirror_python_source(), Path, Runs the five verification checks once and prints one summary block. python3…, Runs a command, capturing combined stdout+stderr as text. Args: cmd: Argv list.… (+15 more)

### Community 22 - "Settings"
Cohesion: 0.17
Nodes (8): BaseSettings, Backend configuration, overridable via environment or .env. Attributes:…, Settings, main.py: the board entry point's own guards (D8, D29). conftest.py installs a…, D8: the board must not run the simulator by accident., D29: the Logger461 stand-in must honour LOG_LEVEL., TestLevelGating, TestRefuseSilentSimulator

### Community 23 - "deps.py"
Cohesion: 0.07
Nodes (31): Typed application settings loaded from the environment / .env file., In-memory ring buffer of structured events for the events endpoint., Composition root: cached provider functions that construct and wire., Immutable domain entities shared across layers., Linux half of the TCP relay; counterpart of EthernetRelay (sketch)., Receives diagnostic events forwarded from the MCU side., AppStateRepository, ABC (+23 more)

### Community 24 - "_read_sse_lines"
Cohesion: 0.22
Nodes (12): MonkeyPatch, _parse_sse_events(), Exception, SSE stream API integration tests., Reads exactly count lines from the response iterator. Args: response: The…, Parses SSE lines into a list of event dictionaries. Args: lines: Raw SSE lines.…, Custom exception to terminate stream generator during tests., _read_sse_lines() (+4 more)

### Community 25 - "test_bridge_servo_repository.py"
Cohesion: 0.13
Nodes (7): BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, deps honours use_hardware_servo., Field 0 of the snapshot payload is the sketch saying 'no answer'., The snapshot payload maps onto TelemetrySnapshot., TestBackendSelection, TestInvalidFlagHonoured, TestSnapshotDecoding

### Community 26 - "ServoController.cpp"
Cohesion: 0.30
Nodes (14): BridgeApi::BridgeApi(), ClampAmplification(), ClampDeadband(), ServoController, Begin, CentreHere, ClearFault, ConfigureRange (+6 more)

### Community 27 - "Document reading flow (router)"
Cohesion: 0.25
Nodes (8): Document reading flow (router), Graphify extraction gaps (.ino and .css), Graphify-first navigation rule, ADR inclusion criteria, Open work lives only in docs/BACKLOG.md, Single-context documentation layout, How to pick up work, Why the code lives in src/

### Community 28 - "D2 — capture() can store a failed read as position 0"
Cohesion: 0.31
Nodes (9): ADR-0003 — Travel window is +/-90 output degrees, multi-turn off, No modulus-360 wrapping anywhere, ADR-0007 — Moves permitted while position is unverified, Remote site makes refusal less safe, not more, D1 — A move to a negative angle stops at 0, D2 — capture() can store a failed read as position 0, Suggested order, T4 — Moves while unverified: decided, permitted (+1 more)

### Community 29 - "Closed items"
Cohesion: 0.04
Nodes (46): Closed items, D10 — `logger.exception` swallows the exception; the sampler's real fault was a thread-safety bug in the SQLite layer, D11 — A single failed poll is presented as a disconnection, D12 — No way to return to the datum after activating a saved zero, D13 — Requests arriving faster than slots free up are refused, D14 — The most likely error in the system shows the operator "Failed to fetch", D15 — A command in flight looks identical to a command that did nothing, D16 — On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured (+38 more)

### Community 30 - "Design Notes"
Cohesion: 0.06
Nodes (30): Design Notes, python/app/core/config.py, python/app/core/events.py, python/app/core/logging_setup.py, python/app/db/database.py, python/app/deps.py, python/app/relay/bridge_relay.py, python/app/repositories/abstract/servo_repository.py (+22 more)

### Community 31 - "Requirements captured but not yet designed"
Cohesion: 0.22
Nodes (11): The relay-capacity argument is unverified, Candidate ADR — how isolation, Lock and e-stop compose, R2 — Motor isolation: cut drive power, keep sensors alive, R3 — Confirm whether the Bridge could carry a frontend framework, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R5 — Metrics export and benchmarking output, R6 — Define 'stable' by benchmark, not by adjective, R6 — Define "stable" by benchmark, not by adjective (+3 more)

### Community 32 - "LoggerStub"
Cohesion: 0.18
Nodes (5): LoggerStub, Mirrors the real logger: the exception rides with the record. Must attach it,…, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 33 - "OnTarget.ino"
Cohesion: 0.17
Nodes (9): MoveCommand, acceleration, speed_counts_per_second, target_counts, Check(), CheckNear(), MoveTo(), setup() (+1 more)

### Community 34 - "get_settings"
Cohesion: 0.09
Nodes (23): get_settings(), Returns the process-wide settings singleton. Returns: Settings: The cached…, get_servo_repository(), Returns the servo repository chosen by use_hardware_servo. Returns:…, _ensure_logger461(), main(), Dev-PC runner: the full backend + web UI, no board required. The app modules…, Boots the backend + web UI and runs the dev console. Returns: None. (+15 more)

### Community 35 - "The flows"
Cohesion: 0.11
Nodes (17): 1. superpowers — the methodology layer, 2. agentic-awesome-skills — the catalogue, 3. Arduino-Agent — the hardware seam, 4. IoT-SkillsBench — the evidence, and the argument for writing our own, Every flow ends the same way, Sources, The flows, Tooling to install first (+9 more)

### Community 36 - "get_isolation_service"
Cohesion: 0.11
Nodes (12): get_event_service(), get_isolation_service(), Returns the motor-isolation service. Returns: IsolationService: The process-…, Returns the shared event buffer. Returns: EventService: The process-wide event…, IsolationService: intent, reconciliation against hardware, idle backup., The idle timer only ever catches 'locked but forgot to isolate'., A deliberate un-isolate while still locked must not be immediately re-isolated…, Regression for the inversion bug: `set_torque`'s argument means "restore… (+4 more)

### Community 37 - "BridgeServoRepository"
Cohesion: 0.08
Nodes (19): BridgeServoRepository, Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position., Configures the servo dead-zone width. Args: counts (int): Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn…, Cuts or restores drive torque while sensors stay powered. Args: enabled (bool):…, Reads register 0x28 directly. Returns: Optional[int]: Register value (0 or 1),…, Invokes a Bridge function, converting failures into empty results. Args: name… (+11 more)

### Community 38 - "AppStub"
Cohesion: 0.50
Nodes (3): AppStub, Stub of the App loop runner., Does nothing. Returns: None.

### Community 39 - "get_events"
Cohesion: 0.12
Nodes (19): EventDep, ge, le, get_events(), get_health(), get, Query, Returns service health including the MCU status line. Args: settings… (+11 more)

### Community 40 - "Deliver"
Cohesion: 0.20
Nodes (9): Deliver, Phase 0 — Orient (cheap, no approval needed), Phase 1 — Plan, then STOP, Phase 2 — Run it, all of it, Phase 3 — Hardware never runs unattended, Phase 4 — Verify, Phase 5 — Record, or it is not done, The rule that overrides your instincts (+1 more)

### Community 41 - "Conventions"
Cohesion: 0.10
Nodes (19): Architecture, Booleans and conditions, C++ (sketch side), Class docstrings carry `Attributes:`, Control flow, Conventions, Current gap against this standard, Database access (+11 more)

### Community 42 - "TestExport"
Cohesion: 0.29
Nodes (3): Telemetry API route: compact binary export. XLSX assembly happens client-side…, GET /api/v1/telemetry/binary., TestExport

### Community 43 - "App.cpp"
Cohesion: 0.24
Nodes (3): App, Begin, Tick

### Community 44 - "Tasks — detail"
Cohesion: 0.14
Nodes (13): T10 — Write the recovery runbook, in two halves, T11 — Write the operations manual, T13 — Distil the remaining documents, T17 — Get a mechanical rig on the bench so R2's hand-turn scenario can actually be tested, T18 — Front-end conventions, and split `app.js` by feature, T20 — Doc-truth sweep from the whole-app review, T21 — Constants and dead code with no shared source, T2 — Package the air-gapped bundle (+5 more)

### Community 45 - "IsolationService"
Cohesion: 0.24
Nodes (7): IsolationService, Writes intent to the database so it survives a restart. Args: isolated (bool):…, Manages motor isolation intent, reconciliation, and idle timeout. Attributes:…, Sets operator intent and reconciles it immediately. Args: isolated (bool):…, Advances the idle timer and retries pending reconciliation., Auto-engages isolation once the lock has been idle long enough., Drives the acknowledged hardware state toward intent once. Args: reason (str):…

### Community 46 - "ServoSnapshot"
Cohesion: 0.10
Nodes (18): ReadSnapshot, ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage (+10 more)

### Community 47 - "SavedPositionResponse"
Cohesion: 0.17
Nodes (16): patch, PositionsDep, create_position(), go_to_position(), list_positions(), get, post, Moves the mechanism to a saved position. Args: position_id (int): Database… (+8 more)

### Community 48 - "3. The 7 Rigorous Test Protocols"
Cohesion: 0.14
Nodes (13): 1. Physical Architecture & Kinematics (Per Documentation), 2. Pre-Test Inspection & Mechanical Setup Checklist, 3. The 7 Rigorous Test Protocols, 4. Post-Test Data Archival & Backlog Sign-Off, Mechanical Rig Test Protocol: 44:30 Belt Reduction & Rotary Drive, Motion & Coordinate Invariants, Protocol 1: Mid-Travel Datum Calibration & Belt Backlash, Protocol 2: R2 Motor Isolation & Hand-Turn Dynamics (T17 Acceptance) (+5 more)

### Community 49 - "test_pure_logic.cpp"
Cohesion: 0.18
Nodes (8): main(), MakeConverter(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 50 - "T8 — Instrumented run on the board over adb"
Cohesion: 0.38
Nodes (7): ADR-0001 — Network path runs through the MCU, kMaxRelaySockets = 6 is the only connection ceiling, D4 — Connection drops after a few commands, D6 — App load time is sometimes slow, R1 — Determine the real concurrent-operator ceiling, T8 — Instrumented run on the board over adb, Served from the board to any machine on the network

### Community 51 - "Defects"
Cohesion: 0.20
Nodes (10): D2 — `capture()` can store a failed read as position 0, D3 — The C++ side has no logging, D4 — Connection drops after a few commands; requires a page refresh, D5 — Log output is connect/disconnect noise, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D7 — UI is not verified on small operator screens, D8 — `.env` must be created before the first run of this version, Defects (+2 more)

### Community 53 - "ServoStateView"
Cohesion: 0.06
Nodes (50): CalibrationDep, IsolationDep, MotionDep, Coherent snapshot of servo, lock, and baseline state. Attributes: output_deg…, ServoStateView, get_state(), get_torque_register(), post_calibrate() (+42 more)

### Community 54 - "What changed"
Cohesion: 0.15
Nodes (12): 1. A reading now carries its own validity, 2. Calibration refuses a reading the servo never gave, 3. Unreachable targets are refused, not clamped, 4. The default baseline is the CENTRE of travel, not zero, 5. Calibration warns when the datum is off-centre, 6. Bridge access is serialised (previous round), Answering "did we even test the sketch?", Full-system audit (+4 more)

### Community 55 - "run_soak"
Cohesion: 0.15
Nodes (12): Checkpointer, Any, Builds a comprehensive summary dictionary. Returns: dict[str, Any]: Detailed…, Periodically prints status and persists checkpoint reports., Initializes checkpointer., Executes the checkpoint loop until stopped., Prints a live summary line and rewrites the report file., Terminates the checkpoint loop. (+4 more)

### Community 56 - "routers/system.py"
Cohesion: 0.29
Nodes (7): FastAPI, create_app(), FastAPI application assembly: routers and domain-error mapping., Creates and configures the FastAPI application. Returns: FastAPI: The…, Maps every domain exception to its HTTP response and log line. Args: app…, _register_error_handlers(), System endpoints: health and recent events.

### Community 57 - "D8 — .env must be created before the first run"
Cohesion: 0.33
Nodes (6): Missing python/.env silently runs the simulator, ADR-0004 — Repository abstraction with a simulated backend, D8 — .env must be created before the first run, cp .env.board .env — the only manual deploy step, run_dev.py — dev-PC entrypoint, Going live is a configuration flag

### Community 58 - "TestNothingIsReportedAsMeasuredOnAFailedRead"
Cohesion: 0.36
Nodes (4): A failed read yields no numbers at all, not a position alone. D16.…, Nulling a field must not remove it: clients read every key., D23, amends ADR-0008: the same rule as the five readings above. moving and the…, TestNothingIsReportedAsMeasuredOnAFailedRead

### Community 59 - "soak_report.py"
Cohesion: 0.06
Nodes (45): _israel_time(), fixture, Path, tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded, plus…, Tests for print_r1_scorecard() and report_telemetry() anomaly detection., Forces a non-UTC timezone (IDT, UTC+3 in August) for this module. Returns: None., A record just outside the local cutoff but inside the UTC one., Pins _utc_cutoff() itself: the helper both call sites share. (+37 more)

### Community 60 - "export_binary"
Cohesion: 0.29
Nodes (7): alias, export_binary(), get, Query, StreamingResponse, Exports compact packed binary telemetry data for client-side rendering. Args:…, TelemetryDep

### Community 61 - "TelemetrySample"
Cohesion: 0.09
Nodes (20): One persisted telemetry row. Attributes: timestamp (float): Unix timestamp of…, TelemetrySample, Persists one sample. Args: sample (TelemetrySample): The sample to store., Yields samples inside a time range, oldest first. Args: ts_from (float): Range…, SQLite implementation of the telemetry repository., Stores telemetry samples in the telemetry table. Attributes: _db (Database):…, Persists one sample. Args: sample (TelemetrySample): The sample to store., Counts samples in range and returns count and base timestamp. Args: ts_from… (+12 more)

### Community 62 - "MotionService"
Cohesion: 0.09
Nodes (12): MotionService, Stops the current move at the present position., Changes the digital lock, honoring the optional move guard. Args: locked…, Clears a tripped overload fault by re-commanding the position. Raises:…, Decides whether the anti-backlash approach applies. Args: start_deg (float):…, Runs the two-leg consistent-direction approach. Args: target_deg (float):…, Refuses targets the servo would silently clamp. Args: target_deg (float):…, Validates and executes movement commands in output-degree space. Attributes:… (+4 more)

### Community 63 - "test_synthetic_operator.py"
Cohesion: 0.14
Nodes (9): Unit tests for tools/synthetic_operator.py., Tests for quantize_deg() step quantization., Exact multiples of 0.06 deg should remain unchanged., Arbitrary floating point angles snap to nearest 0.06 grid., Tests for Metrics class request and stream tracking., Requests, failures, and refusals categorized by reason., Stream frame reception and inter-arrival jitter calculation., TestMetricsTally (+1 more)

### Community 64 - "AngleConverter"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 65 - "Defects — detail"
Cohesion: 0.12
Nodes (15): D28 — MCU boot-time `mcu_log` notify lost to a startup race, D35 — Commanded speed and actual speed disagree by roughly 1.5-2x, D36 — Several tests construct their own `Database` and never close it, D38 — A saved position's "earlier reference" tag has no way to dismiss it, D40 — A move settles short under load and re-commanding the same target does not correct it, D41 — Firmware commands real moves off failed reads and malformed payloads, D42 — Errors that vanish: SSE stream, migration, sqlite writes, D43 — Guards that fail open on an invalid read (+7 more)

### Community 66 - "ServoBus"
Cohesion: 0.25
Nodes (13): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, ServoBus::ServoBus(), WriteByte (+5 more)

### Community 67 - "R-items — detail"
Cohesion: 0.25
Nodes (7): R11 — Accept any typed angle; snap to the nearest step and show the delta, R12 — Extended travel: soft limit ±90°, hard limit ±95°, confirmed in between, R1 — Determine the real concurrent-operator ceiling, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R7 — Handover logistics depend on adapter delivery, R8 — Emergency stop, R-items — detail

### Community 68 - "Ordering, rewritten 8 August 2026 — by session, with sizes"
Cohesion: 0.17
Nodes (12): Batch 1 — Desk work, no board — **DONE 8 August 2026**, Batch 2 — Make the machine diagnosable — **DONE 8 August 2026** (desk work), Batch 3 — The measurement session (board, supervised, one long run), Batch 4 — The two unbuilt MVP features, Batch 5 — The handover pack, Batch 6 — Mechanical, suits an executing agent, Not scheduled, Ordering, rewritten 8 August 2026 — by session, with sizes (+4 more)

### Community 69 - "FakeBridge"
Cohesion: 0.20
Nodes (8): bridge(), FakeBridge, fixture, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, A fake bridge returning a healthy snapshot. Returns: The fake., Repository wired to the fake bridge. Returns: The repository under test., repo()

### Community 70 - "Bench-verified hardware facts"
Cohesion: 0.67
Nodes (4): The 44:30 belt reduction is the whole point, Bench-verified hardware facts, Confirm the Ethernet patch survived the first build, Apply SpiRemap twice

### Community 71 - "Task: strip explanatory prose from sketch/src/"
Cohesion: 0.20
Nodes (9): A — Doxygen doc comments (`///` and `/** */` blocks), B — inline comments, C — relocate what is not already written down, Constraints, D — two comment classes that need special handling, found the hard way, Report back, Scope, Task: strip explanatory prose from sketch/src/ (+1 more)

### Community 72 - "DiagLog"
Cohesion: 0.27
Nodes (9): kLogRingCapacity, DiagLog, Drain, dropped_total, Init, lock_, Push, ring_ (+1 more)

### Community 73 - "TestExport"
Cohesion: 0.20
Nodes (4): A sample taken before any move has target_valid=0; one taken after an accepted…, isolated shares a byte with target_valid rather than widening the 20-byte…, Binary telemetry export contract. XLSX assembly is client-side (app.js) by…, TestExport

### Community 74 - "Twin review"
Cohesion: 0.15
Nodes (12): 1. Twin path, 2. Operator impact, 3. Relay and hardware safety, 4. Doc truth, 5. General correctness, How to run it, Not yet scoped, Reporting (+4 more)

### Community 75 - "Dev And Test Dependencies"
Cohesion: 0.50
Nodes (4): Dev And Test Dependencies, Runtime Dependencies, ARM64 Platform Wheels Required, Offline Wheelhouse

### Community 76 - "Task: strip explanatory prose from python/app/"
Cohesion: 0.22
Nodes (8): A — docstrings (`python/app/**/*.py`), B — inline comments, C — relocate what is not already written down, Constraints, D — the remaining style gaps (`python/app/` only), Report back, Task: strip explanatory prose from python/app/, Verification — after every file, not only at the end

### Community 77 - "FlakyServo"
Cohesion: 0.15
Nodes (8): flaky(), FlakyServo, fixture, Wraps the real simulator but can be told to refuse the next torque…, Swaps the cached servo repository for one whose ack is controllable, for the…, The sampler thread survives sampling failures., The record must carry the cause, not just the fact. A live board run on 7…, TestSamplerResilience

### Community 78 - "setup_logging"
Cohesion: 0.25
Nodes (6): Logging configuration built on Logger461 (loguru JSON wrapper)., Initializes Logger461 for the process. Args: settings (Settings): Application…, setup_logging(), Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 79 - "SavedPosition"
Cohesion: 0.08
Nodes (24): DuplicateNameError, Raised when a saved position name is already in use., A named, described position an operator can return to. Attributes: id…, SavedPosition, Persists a new saved position. Args: position (SavedPosition): Entity with…, Returns all saved positions, newest first. Returns: list[SavedPosition]: All…, Returns one saved position by id. Args: position_id (int): Database identifier.…, Overwrites a saved position's editable fields. Args: position_id (int):… (+16 more)

### Community 81 - "database.py"
Cohesion: 0.25
Nodes (6): SQLite connection management and schema initialization., SQLite implementation of the app-state key/value repository., fixture, SqliteAppStateRepository: get/set of persisted operator-intent flags., App-state repository over a fresh database. Returns: The repository under test., repo()

### Community 83 - "McuLog"
Cohesion: 0.18
Nodes (8): McuLog, _now_iso(), Returns current UTC time as an ISO-8601 string with milliseconds. Returns: str:…, Bridge receiver that writes MCU-originated events to their own file.…, Registers the Bridge callback for MCU logs., Handles one diagnostic record forwarded from the MCU. Args: level (int):…, Appends one JSON line, rotating the file past size threshold. Args: line…, Renames path to path.1 once grown past threshold. Args: path (str): The log…

### Community 84 - "e2e/conftest.py"
Cohesion: 0.32
Nodes (7): _bound_socket(), live_backend(), fixture, socket, E2E fixtures: the backend booted the way main.py boots it. A real uvicorn…, Binds an ephemeral localhost TCP socket and leaves it open. Finding a free…, Boots the full backend on a live socket, mirroring main.py. Yields: Namespace…

### Community 86 - "SpiRemap.cpp"
Cohesion: 0.39
Nodes (7): GPIO_TypeDef, PortFor(), SpiRemap, ApplyJspiMapping, kAlternateFunctionSpi2, ReleaseTopHeaderCopies, SetAlternateFunction

### Community 88 - "synthetic_operator.py"
Cohesion: 0.29
Nodes (7): main(), quantize_deg(), Synthetic operators that drive the running board like people would. Written for…, Snaps an angle to the nearest valid step multiple. Args: deg (float): Desired…, Queries board status and prints pre-flight diagnostics. Args: host (str): Board…, Parses arguments and runs the soak., run_preflight()

### Community 89 - "Tasks"
Cohesion: 0.25
Nodes (7): Backlog, T1 — Apply `CONVENTIONS.md` across the codebase, T4 — Moves while unverified: DECIDED, permitted, T5 — Add `design_diagrams/` with PlantUML, T6 — Restructure the exception hierarchy, T7 — Add the database abstraction, Tasks

### Community 95 - "START HERE — the session plan"
Cohesion: 0.25
Nodes (7): Not in these three sessions, Session 1, Batch 1 — DONE, 8 August 2026, Session 1, Batch 2 — DONE, 8 August 2026, Session 2 — The soak — IN PROGRESS, Session 3 — SSE first, then Batch 4, START HERE — the session plan, Suggested order — SUPERSEDED 8 August 2026

### Community 96 - "get_mcu_log"
Cohesion: 0.25
Nodes (7): get_mcu_log(), Returns the MCU diagnostic log receiver. Returns: McuLog: The process-wide…, mcu_log(), fixture, Behavior when the board runtime is absent (dev PC)., Fresh registered receiver, writing into a throwaway file. Returns: The receiver…, TestDevComputerPath

### Community 97 - "Language"
Cohesion: 0.29
Nodes (6): Control and safety, Language, MCU boundary, Position and geometry, Servo MVP — context, Telemetry

### Community 98 - "Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start)"
Cohesion: 0.29
Nodes (6): Committed (~13.25h claude/operator-serial / 13.5h capacity — pulled in, Jira-pasteable blocks, Retro (fill in at sprint close), Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start), Sprints, Stretch (attempted only if committed scope finishes with room left)

### Community 100 - "test_motion_service.py"
Cohesion: 0.09
Nodes (39): ConflictException, IsolatedError, LockedAndIsolatedError, LockedError, MovingError, OutOfTravelError, Domain exceptions: each carries its own HTTP mapping and log metadata., Raised when a target lies outside the servo's physical count range. (+31 more)

### Community 101 - "TelemetryService"
Cohesion: 0.09
Nodes (16): ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Counts samples in range and returns count and base timestamp. Args: ts_from…, Deletes samples older than the retention window. Args: days (int): Retention…, TelemetryRepository, Telemetry endpoints: binary telemetry stream export., Telemetry: periodic sampling, retention, and binary export. (+8 more)

### Community 102 - "Bridge contract checker"
Cohesion: 0.33
Nodes (6): Three verification commands (186 / 164 / agree), ADR-0006 — Bridge payloads are CSV strings, Field order is a contract, Current status — everything exists, nothing is stable, Bridge contract checker, The Bridge payload contract with Python

### Community 127 - "TestFailedReadsAreNotStored"
Cohesion: 0.40
Nodes (3): A stalled bus must leave a gap, not a row claiming position 0. Seven such rows…, The stored row must come from a single coherent read. The row used to be…, TestFailedReadsAreNotStored

### Community 128 - "routers/saved_positions.py"
Cohesion: 0.18
Nodes (16): delete, delete_position(), Saved-position endpoints: list, create, update, delete, go., Deletes a saved position. Args: position_id (int): Database identifier. request…, DeletedResponse, GoResponse, BaseModel, Request/response schemas for the saved-positions router. (+8 more)

### Community 129 - "check_file"
Cohesion: 0.32
Nodes (7): check_file(), main(), Path, Brace-balance check for sketch/src/ files the native suite can't compile.…, Removes // and /* */ comments and "..."/'...' literals. Args: text (str): Raw…, Returns the file's final brace depth (0 means balanced). Args: path (Path):…, strip_comments_and_strings()

### Community 131 - "get_state_store"
Cohesion: 0.08
Nodes (16): get_state_store(), Returns the atomic servo/lock/baseline/isolation state store. Returns:…, Intent -> acknowledged hardware state, and never the reverse., The whole point of ADR-0010: a rebuilt process (a restart) must see the intent…, The false-safety-claim case this feature exists to prevent: if the servo does…, TestReconciliation, Target angle capture: set once on accept, stale (not cleared) on stop, never…, TestTarget (+8 more)

### Community 133 - "get_telemetry_service"
Cohesion: 0.09
Nodes (23): get_database(), get_telemetry_repository(), get_telemetry_service(), Returns the telemetry service. Returns: TelemetryService: The process-wide…, Returns the shared database wrapper. Returns: Database: The process-wide…, Returns the telemetry repository. Returns: TelemetryRepository: The process-…, _clear_all_caches(), Clears every cached provider so each test builds fresh singletons. Returns:… (+15 more)

### Community 134 - "TelemetrySnapshot"
Cohesion: 0.08
Nodes (20): Instantaneous sensory readout from the servo layer. Attributes: raw_counts…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: TelemetrySnapshot:…, Servo API routes: state, move, stop, lock, calibrate, recover., POST /api/v1/servo/calibrate., POST /api/v1/servo/recover., guard_move_to_lock surfaces as 409 reason=moving., An unreachable target must be refused, not silently clamped. (+12 more)

### Community 135 - "BridgeApi.cpp"
Cohesion: 0.22
Nodes (19): bin_t, Ack(), BridgeApi, DrainDiagLog, FormatSnapshot, Register, FieldAt(), ForwardDiagLog() (+11 more)

### Community 136 - "test_servo_state.py"
Cohesion: 0.10
Nodes (11): ServoStateStore: conversions, lock/settle, verified flag, snapshot., Coherent snapshot content., servo_direction inverts commanded and reported motion together. Round-trip…, The usable window depends on where the datum sits., Lock state and settle window., Post-boot position verification., TestDirection, TestLockAndSettle (+3 more)

### Community 139 - "decode_sign_magnitude"
Cohesion: 0.12
Nodes (11): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. Args: value (int):…, parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude, parametrize (+3 more)

### Community 141 - "get_motion_service"
Cohesion: 0.10
Nodes (13): get_motion_service(), get_saved_position_service(), Returns the motion service. Returns: MotionService: The process-wide motion…, Returns the saved-position service. Returns: SavedPositionService: The process-…, Calibration, saved positions, state store and motion interacting., TestCalibrationAndSavedPositionsAcrossServices, _events(), motion() (+5 more)

### Community 146 - "test_calibration_service.py"
Cohesion: 0.22
Nodes (6): fixture, CalibrationService: captures the datum, and only the datum., Fresh calibration service. Returns: The service under test., Calibration must not capture a reading the servo never gave. A failed read…, service(), TestCalibrationRobustness

### Community 153 - "Arduino UNO Q + Waveshare ST3215"
Cohesion: 0.11
Nodes (17): 1. This is not a normal Arduino, 2. The ST3215 servo, 3. Geometry — and the one law that matters, 4. The Ethernet-shield relay, 5. The Bridge contract, 6. Symptom → cause, 7. Deployment traps, 8. Working rules (+9 more)

### Community 170 - "SimulatedServoRepository"
Cohesion: 0.09
Nodes (12): Stops motion at the current position., Records the range configuration. Args: multi_turn (bool): Enable multi-turn…, Configures the simulated dead-zone width. Args: counts (int): Dead-zone width…, Cuts or restores simulated drive torque. Args: enabled (bool): True to restore…, Returns the simulated torque state. Returns: int: 1 when torque is enabled, 0…, Thread-driven simulation of one ST3215-class servo. Attributes: _lock (Lock):…, Trips the simulated overload fault., Advances position toward target until process termination. (+4 more)

### Community 246 - "TestCommands"
Cohesion: 0.11
Nodes (3): Commands become the payloads the sketch parses., The ack is load-bearing for this one command: callers must never believe…, TestCommands

### Community 279 - "Skills archive"
Cohesion: 0.29
Nodes (6): Skills archive, Sources, The gap this archive does not fill, What's here, What was stripped, and why, Why the big one is not tracked

### Community 288 - "A failed read is reported as unknown, never as a number"
Cohesion: 0.29
Nodes (6): A failed read is reported as unknown, never as a number, Consequences, Extended, 8 August 2026 — `valid` governs the whole snapshot, Status, The alternative that was considered, Why

### Community 302 - "TestIsolate"
Cohesion: 0.20
Nodes (4): Two different gates must surface as two different reasons - an operator refused…, GET /api/v1/servo/diagnostics/torque_register - diagnostic, independent of the…, POST /api/v1/servo/isolate, and its refusal of a move., TestIsolate

### Community 303 - "Operator lens"
Cohesion: 0.25
Nodes (7): Also wear the client's hat, Operator lens, Output — file it, do not just say it, Rule zero, The control surface, The five questions, per control, The four failures worth memorising

### Community 309 - "EventService"
Cohesion: 0.10
Nodes (17): Event, EventService, One operator-facing event. Attributes: timestamp (str): ISO timestamp. event…, Thread-safe fixed-size store of recent events. Attributes: _events…, Stores one event. Args: event (str): Dotted event identifier. message (str):…, Returns the newest events, newest first. Args: limit (int): Maximum number of…, get, StreamingResponse (+9 more)

### Community 325 - "BridgeRelay"
Cohesion: 0.16
Nodes (9): BridgeRelay, socket, Streams FastAPI reply bytes back down to the sketch. Args: slot (int):…, Closes and forgets one mirrored connection. Args: slot (int): Connection slot…, Byte pump between the sketch's network clients and FastAPI. Attributes:…, Registers all Bridge callbacks., Handles a new network client reported by the sketch. Args: slot (int):…, Forwards client bytes to FastAPI. Args: slot (int): Connection slot identifier.… (+1 more)

### Community 344 - "get_relay"
Cohesion: 0.08
Nodes (16): get_relay(), Returns the Bridge relay. Returns: BridgeRelay: The process-wide relay., echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Remaining failure branches., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Behavior when the board runtime is absent (dev PC). (+8 more)

### Community 351 - "wait_until"
Cohesion: 0.08
Nodes (13): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), TestCalibrate, SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Mirrors the real controller's un-isolate ordering: the target snaps to wherever…, Absolute counts beyond one turn and below zero (contract)., Basic motion profile., Motor isolation: cutting torque must stop the shaft actually moving, not just… (+5 more)

### Community 397 - "main.py"
Cohesion: 0.18
Nodes (13): _ensure_logger461(), _level_enabled(), main(), Entry point: initialize, serve FastAPI, run the App loop. App Lab runs this…, Refuses to start if nothing chose the simulator on purpose. A missing .env and…, Runs uvicorn on localhost; relay and adb-forward are the doors. Args: app: The…, Starts the telemetry sampler, isolation reconciler and Bridge relay. Returns:…, Decides whether a record at `level` should be emitted at `minimum`. Args:… (+5 more)

### Community 399 - "BridgeStub"
Cohesion: 0.08
Nodes (16): BridgeStub, Recording stub of the Arduino Bridge., Clears recorded state between tests. Returns: None., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent. (+8 more)

### Community 443 - "main"
Cohesion: 0.39
Nodes (7): collect_python(), collect_sketch(), main(), Path, Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 447 - "The connection ceiling stays at 6 this batch"
Cohesion: 0.50
Nodes (3): Consequences, The connection ceiling stays at 6 this batch, Why

### Community 450 - "Motor isolation state survives a reboot"
Cohesion: 0.40
Nodes (4): Consequences, Motor isolation state survives a reboot, Status, Why

## Knowledge Gaps
- **365 isolated node(s):** `state`, `REFUSALS`, `EVENT_LABELS`, `DAY_SHEET_COLS`, `RAW_HEADERS` (+360 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **34 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BridgeStub` connect `BridgeStub` to `get_mcu_log`, `get_settings`, `TestResilience`, `FakeBridge`, `test_relay_path.py`, `BridgeServoRepository`, `decode_sign_magnitude`, `test_mcu_log.py`, `TestCommands`, `get_relay`, `test_bridge_servo_repository.py`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `get_servo_repository()` connect `get_settings` to `get_state_store`, `test_motion_service.py`, `BridgeServoRepository`, `get_isolation_service`, `test_saved_positions_routes.py`, `TelemetrySnapshot`, `test_servo_state.py`, `SimulatedServoRepository`, `get_motion_service`, `deps.py`, `test_bridge_servo_repository.py`, `TestNothingIsReportedAsMeasuredOnAFailedRead`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `get_settings()` connect `get_settings` to `get_mcu_log`, `routers/saved_positions.py`, `get_relay`, `get_isolation_service`, `get_telemetry_service`, `get_state_store`, `get_events`, `ServoStateStore`, `TelemetrySnapshot`, `get_motion_service`, `main.py`, `ServoStateView`, `Settings`, `deps.py`, `routers/system.py`, `test_bridge_servo_repository.py`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `ServoStateStore` (e.g. with `CalibrationService` and `IsolationService`) actually correct?**
  _`ServoStateStore` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `REFUSALS`, `EVENT_LABELS` to the rest of the system?**
  _365 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `NetworkRelay` be split into smaller, more focused modules?**
  _Cohesion score 0.10591133004926108 - nodes in this community are weakly interconnected._