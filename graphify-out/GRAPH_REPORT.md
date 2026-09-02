# Graph Report - servo_mvp  (2026-09-02)

## Corpus Check
- 152 files · ~152,646 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2474 nodes · 4222 edges · 165 communities (128 shown, 37 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 380 edges (avg confidence: 0.56)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `78810141`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- TelemetryService
- fine_approach_trial.py
- get_motion_service
- Frontend API Client
- ServoStateStore
- Operator Metrics Tally
- Relay E2E Tests
- Saved Positions Route Tests
- SavedPosition
- Database
- Virtual Operator Behavior
- Architecture Decision Records
- Project Manifest & Environment
- Client Behavior Check Script
- Open Questions Doc
- TestCrud
- LogRecord
- TelemetrySample
- TEST
- test_mcu_log.py
- telemetry_service.py
- Verification Script
- TestLevelGating
- deps.py
- SSE Stream Tests
- test_bridge_servo_repository.py
- ServoController.cpp
- Graphify Navigation Notes
- Travel Window ADRs
- Closed Backlog Items D10-19
- Core Backend Modules
- Requirements Backlog (R-Items)
- Logger Stub
- database.py
- TuningSnapshot
- Workflows Doc
- get_isolation_service
- BridgeServoRepository
- TestCalibrate
- stream.py
- Deliver Skill Doc
- Coding Conventions Doc
- TestSamplerLifecycleIsolation
- OnTarget.ino
- Backlog T-Items
- ServoAppException
- ServoSnapshot
- TestTravelWindow
- Rig Testing Protocol Doc
- test_pure_logic.cpp
- Relay Connection Ceiling
- Early Defects List
- Servo Bus Draining
- ServoStateView
- System Audit Doc
- Soak Test Checkpointer
- TestTorque
- Hardware Config Fallback
- get_database
- Soak Report Tests
- AppStub
- SqliteTelemetryRepository
- MotionService
- Synthetic Operator Tests
- Angle Converter (C++)
- Defects — detail
- ServoBus
- Backlog R-Items
- Ordering, rewritten 8 August 2026 — by session, with sizes
- TestStopLock
- Hardware Bench Facts
- Firmware Prose Strip Task
- TestInvalidFlagHonoured
- TestExport
- Twin-Review Skill Doc
- Python Dependencies
- Python Prose Strip Task
- FlakyServo
- test_logging_setup.py
- SavedPositionService
- TestMoveGuardOverHttp
- TestOutOfTravelSurfaced
- Design Diagrams Task
- McuLog
- get_telemetry_service
- decode_sign_magnitude
- repo
- Deploy Push Notes
- Synthetic Operator Script
- Backlog Index Doc
- Shared SQLite Connection
- Connection Acceptance
- Disconnect Detection
- No Bricks Constraint
- Single Source Of Truth
- Closed Sessions Doc
- TestNothingIsReportedAsMeasuredOnAFailedRead
- Domain Glossary
- Sprint Planning Log
- Small Screen UI Bug
- test_motion_service.py
- test_telemetry_service.py
- Bridge Payload Contract
- CSV Export Feature
- Duplicate Script Tag Bug
- Status Fault Grid
- Move Controls UI
- Router Bridge Library
- Relay Chunk Size Contract
- Loop Yield Requirement
- Bridge Network Contract
- Safe Function Registration
- Serial Monitor Note
- routers/saved_positions.py
- Brace Balance Checker Script
- Saved Positions Datum
- get_state_store
- get_settings
- TestMove
- BridgeApi.cpp
- TelemetrySnapshot
- Repo Working Conventions
- Calibration And Saved Positions
- Sketch Class Design
- wait_until
- Simulated Path Coverage Caveat
- Soak Test Runner
- Position Terminology
- Mechanical Restraint Lock
- Jira Import — Servo MVP
- Apply Conventions Task
- Repository Layout
- TestGetSet
- Arduino UNO Q + Waveshare ST3215
- test_servo_routes.py
- Simulated Servo Methods
- Bridge Command Tests
- Skills Archive
- Failed Read Handling
- Diagnostics & Isolation Routes
- Operator Lens Skill
- EventService
- BridgeRelay
- BridgeStub
- test_operator_scenario.py
- Settings
- test_system_routes.py
- Bridge Contract Checker
- Connection Ceiling Decision
- Motor Isolation Persistence
- Servo Protocol Choice

## God Nodes (most connected - your core abstractions)
1. `get_state_store()` - 89 edges
2. `ServoStateStore` - 64 edges
3. `wait_until()` - 62 edges
4. `TelemetrySnapshot` - 50 edges
5. `Closed items` - 47 edges
6. `Database` - 42 edges
7. `get_motion_service()` - 41 edges
8. `TestCommands` - 41 edges
9. `BridgeServoRepository` - 39 edges
10. `get_isolation_service()` - 37 edges

## Surprising Connections (you probably didn't know these)
- `Single-context documentation layout` --semantically_similar_to--> `Document reading flow (router)`  [INFERRED] [semantically similar]
  docs/agents/domain.md → CLAUDE.md
- `sshfs board mount as working copy` --semantically_similar_to--> `Development shortcut — sshfs mount of the board`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Apply SpiRemap twice` --semantically_similar_to--> `Confirm the Ethernet patch survived the first build`  [INFERRED] [semantically similar]
  sketch/README.md → README.md
- `list_positions()` --references--> `_get()`  [EXTRACTED]
  python/app/routers/saved_positions.py → tools/fine_approach_trial.py
- `get_torque_register()` --references--> `_get()`  [EXTRACTED]
  python/app/routers/servo.py → tools/fine_approach_trial.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Consequences of the air-gap constraint** — docs_adr_0005_air_gapped_by_default_development_decision, docs_adr_0002_no_frontend_framework_decision, readme_air_gapped_bundle, readme_core_version_pin, sketch_readme_tinytest_harness, docs_backlog_t2_package_the_air_gapped_bundle [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]

## Communities (165 total, 37 thin omitted)

### Community 0 - "TelemetryService"
Cohesion: 0.16
Nodes (8): Samples until stopped, at the configured interval., Reads one coherent snapshot and persists it., Applies retention at the configured interval., Persists the full sensory input every sampler interval. Attributes: _telemetry…, Starts the background sampling thread., Stops the background sampling thread, if one was started., Packs telemetry samples in range into a compact binary byte stream. Args:…, TelemetryService

### Community 1 - "fine_approach_trial.py"
Cohesion: 0.08
Nodes (38): alias, get_state(), Returns the full state snapshot for the client. Args: state (ServoStateStore):…, export_binary(), Query, StreamingResponse, Exports compact packed binary telemetry data for client-side rendering. Args:…, StateDep (+30 more)

### Community 2 - "get_motion_service"
Cohesion: 0.09
Nodes (23): get_event_service(), get_motion_service(), get_saved_position_service(), Returns the motion service. Returns: MotionService: The process-wide motion…, Returns the saved-position service. Returns: SavedPositionService: The process-…, Returns the shared event buffer. Returns: EventService: The process-wide event…, Cross-service integration flows (no HTTP): components working together., Telemetry sampler records a real movement profile. (+15 more)

### Community 3 - "Frontend API Client"
Cohesion: 0.06
Nodes (79): ADR-0008, ANGLE_FIELDS, ANGLE_SERIES, angleSortedDownsampleRefs(), apiDelete(), apiGet(), apiPatch(), apiPost() (+71 more)

### Community 4 - "ServoStateStore"
Cohesion: 0.04
Nodes (31): AppStateRepository, ABC, Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):…, Contract for a small persisted key-value store of operator intent., Records that the servo acknowledged an isolation write. Args: isolated (bool):…, Returns the acknowledged isolation state shown to operator. Returns: bool: True…, Marks the position reference as verified after calibration. (+23 more)

### Community 5 - "Operator Metrics Tally"
Cohesion: 0.09
Nodes (13): Metrics, Thread-safe tally of everything the synthetic operators observed. Attributes:…, Initializes an empty metrics tally., Records one completed REST request. Args: action (str): Name of the action…, Records a request that failed to connect or completed with a 5xx error. Args:…, Records a deliberate 4xx refusal from the API with its reason. Args: action…, Records an SSE stream connection open. Args: is_reconnect (bool): True if this…, Records a disconnect or transport failure on an SSE stream. (+5 more)

### Community 6 - "Relay E2E Tests"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 7 - "Saved Positions Route Tests"
Cohesion: 0.09
Nodes (9): Saved-positions API routes: list, create, update, delete, go., POST /api/v1/positions/{id}/go., PATCH /api/v1/positions/{id}., POST and GET /api/v1/positions., DELETE /api/v1/positions/{id}., TestCreateList, TestDelete, TestGo (+1 more)

### Community 8 - "SavedPosition"
Cohesion: 0.09
Nodes (21): DuplicateNameError, Raised when a saved position name is already in use., A named, described position an operator can return to. Attributes: id…, SavedPosition, Persists a new saved position. Args: position (SavedPosition): Entity with…, Returns all saved positions, newest first. Returns: list[SavedPosition]: All…, Returns one saved position by id. Args: position_id (int): Database identifier.…, Overwrites a saved position's editable fields. Args: position_id (int):… (+13 more)

### Community 9 - "Database"
Cohesion: 0.10
Nodes (15): Database, Carries the old zeros table's rows into app_state and saved_positions., Closes the connection., Creates tables and indexes when missing., Owns the SQLite connection and serializes all access to it. Attributes:…, Adds columns introduced after a database was first created., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):… (+7 more)

### Community 10 - "Virtual Operator Behavior"
Cohesion: 0.14
Nodes (13): One virtual operator running an SSE stream and deliberate HTTP actions.…, Signals worker threads to stop., Performs one REST HTTP call and updates metrics. Args: action (str): Metrics…, Executes deliberate actions with think times., Dispatches an action based on the operator's profile., Commands a motion to a quantized valid angle., Polls until movement settles or timeout elapses., Exercises saved-position CRUD operations. (+5 more)

### Community 11 - "Architecture Decision Records"
Cohesion: 0.07
Nodes (20): Consequences, The network path runs through the MCU, not the Linux side, Consequences, Considered and rejected, Plain HTML, CSS and JavaScript — no framework, no build step, Consequences, Travel window is ±90 output degrees, and multi-turn stays off, Consequences (+12 more)

### Community 12 - "Project Manifest & Environment"
Cohesion: 0.13
Nodes (16): Servo Control App Manifest, sshfs board mount as working copy, ADR-0002 — Plain HTML/CSS/JS, no framework, ADR-0005 — Develop as if already air-gapped, R7 — Handover logistics depend on adapter delivery, T2 — Package the air-gapped bundle, T3 — Run the on-target test suite, Environment right now (+8 more)

### Community 13 - "Client Behavior Check Script"
Cohesion: 0.17
Nodes (7): APP, ctx, els, fs, path, toasts, vm

### Community 14 - "Open Questions Doc"
Cohesion: 0.13
Nodes (14): For the operators, For the programme, For whoever receives the MVP, Open questions, Q10 — Should code-level docs/comments carry rationale, or move to `docs/`? `answered`, Q1 — What screen will you actually use? `answered`, Q2 — How many operators at once, really, and doing what? `answered`, Q3 — When the machine misbehaves on site, what do you want to be able to do? `answered` (+6 more)

### Community 15 - "TestCrud"
Cohesion: 0.19
Nodes (6): _position(), Builds an unsaved saved-position entity. Args: name: Position name. counts: Raw…, Create, read, update, delete., The UNIQUE constraint surfaces as a domain exception, not a 500., TestCrud, TestNameUniqueness

### Community 16 - "LogRecord"
Cohesion: 0.10
Nodes (20): kLogRingCapacity, DiagLog, Drain, dropped_total, Init, lock_, Push, ring_ (+12 more)

### Community 17 - "TelemetrySample"
Cohesion: 0.18
Nodes (7): One persisted telemetry row. Attributes: timestamp (float): Unix timestamp of…, TelemetrySample, Persists one sample. Args: sample (TelemetrySample): The sample to store., Yields samples inside a time range, oldest first. Args: ts_from (float): Range…, Persists one sample. Args: sample (TelemetrySample): The sample to store., Yields samples inside a time range, oldest first. Args: ts_from (float): Range…, TestRetention

### Community 18 - "TEST"
Cohesion: 0.07
Nodes (28): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, log_ring_drops_oldest_when_full_and_counts_it (+20 more)

### Community 19 - "test_mcu_log.py"
Cohesion: 0.11
Nodes (14): _lines(), mcu_log(), fixture, McuLog: receiving and writing diagnostic events forwarded from the MCU., Behavior when the board runtime is absent (dev PC)., Fresh registered receiver, writing into a throwaway file. Returns: The receiver…, Reads every JSON line from a file. Args: path: File to read. Returns: One dict…, Bridge callback registration. (+6 more)

### Community 20 - "telemetry_service.py"
Cohesion: 0.20
Nodes (7): ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Counts samples in range and returns count and base timestamp. Args: ts_from…, Deletes samples older than the retention window. Args: days (int): Retention…, TelemetryRepository, Telemetry: periodic sampling, retention, and binary export.

### Community 21 - "Verification Script"
Cohesion: 0.14
Nodes (23): _delta(), _ensure_local_venv_mirror(), _load_baseline(), main(), _mirror_python_source(), Path, Runs the five verification checks once and prints one summary block. python3…, Runs a command, capturing combined stdout+stderr as text. Args: cmd: Argv list.… (+15 more)

### Community 23 - "deps.py"
Cohesion: 0.06
Nodes (34): In-memory ring buffer of structured events for the events endpoint., get_calibration_service(), get_servo_repository(), Composition root: cached provider functions that construct and wire., Returns the calibration service. Returns: CalibrationService: The process-wide…, Returns the servo repository chosen by use_hardware_servo. Returns:…, Calibration, Immutable domain entities shared across layers. (+26 more)

### Community 24 - "SSE Stream Tests"
Cohesion: 0.22
Nodes (12): MonkeyPatch, _parse_sse_events(), Exception, SSE stream API integration tests., Reads exactly count lines from the response iterator. Args: response: The…, Parses SSE lines into a list of event dictionaries. Args: lines: Raw SSE lines.…, Custom exception to terminate stream generator during tests., _read_sse_lines() (+4 more)

### Community 25 - "test_bridge_servo_repository.py"
Cohesion: 0.08
Nodes (15): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, A misbehaving bus must not take the backend down., deps honours use_hardware_servo. (+7 more)

### Community 26 - "ServoController.cpp"
Cohesion: 0.23
Nodes (20): ClampAmplification(), ClampByteRegister(), ClampDeadband(), ClampMinStartForce(), ServoController, Begin, CentreHere, ClearFault (+12 more)

### Community 27 - "Graphify Navigation Notes"
Cohesion: 0.25
Nodes (8): Document reading flow (router), Graphify extraction gaps (.ino and .css), Graphify-first navigation rule, ADR inclusion criteria, Open work lives only in docs/BACKLOG.md, Single-context documentation layout, How to pick up work, Why the code lives in src/

### Community 28 - "Travel Window ADRs"
Cohesion: 0.31
Nodes (9): ADR-0003 — Travel window is +/-90 output degrees, multi-turn off, No modulus-360 wrapping anywhere, ADR-0007 — Moves permitted while position is unverified, Remote site makes refusal less safe, not more, D1 — A move to a negative angle stops at 0, D2 — capture() can store a failed read as position 0, Suggested order, T4 — Moves while unverified: decided, permitted (+1 more)

### Community 29 - "Closed Backlog Items D10-19"
Cohesion: 0.04
Nodes (47): Closed items, D10 — `logger.exception` swallows the exception; the sampler's real fault was a thread-safety bug in the SQLite layer, D11 — A single failed poll is presented as a disconnection, D12 — No way to return to the datum after activating a saved zero, D13 — Requests arriving faster than slots free up are refused, D14 — The most likely error in the system shows the operator "Failed to fetch", D15 — A command in flight looks identical to a command that did nothing, D16 — On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured (+39 more)

### Community 30 - "Core Backend Modules"
Cohesion: 0.06
Nodes (30): Design Notes, python/app/core/config.py, python/app/core/events.py, python/app/core/logging_setup.py, python/app/db/database.py, python/app/deps.py, python/app/relay/bridge_relay.py, python/app/repositories/abstract/servo_repository.py (+22 more)

### Community 31 - "Requirements Backlog (R-Items)"
Cohesion: 0.22
Nodes (11): The relay-capacity argument is unverified, Candidate ADR — how isolation, Lock and e-stop compose, R2 — Motor isolation: cut drive power, keep sensors alive, R3 — Confirm whether the Bridge could carry a frontend framework, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R5 — Metrics export and benchmarking output, R6 — Define 'stable' by benchmark, not by adjective, R6 — Define "stable" by benchmark, not by adjective (+3 more)

### Community 32 - "Logger Stub"
Cohesion: 0.18
Nodes (5): LoggerStub, Mirrors the real logger: the exception rides with the record. Must attach it,…, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 33 - "database.py"
Cohesion: 0.25
Nodes (6): SQLite connection management and schema initialization., SQLite implementation of the app-state key/value repository., fixture, SqliteAppStateRepository: get/set of persisted operator-intent flags., App-state repository over a fresh database. Returns: The repository under test., repo()

### Community 34 - "TuningSnapshot"
Cohesion: 0.25
Nodes (8): TuningSnapshot, ccw_dead_zone, cw_dead_zone, min_start_force, position_d, position_i, position_p, valid

### Community 35 - "Workflows Doc"
Cohesion: 0.11
Nodes (17): 1. superpowers — the methodology layer, 2. agentic-awesome-skills — the catalogue, 3. Arduino-Agent — the hardware seam, 4. IoT-SkillsBench — the evidence, and the argument for writing our own, Every flow ends the same way, Sources, The flows, Tooling to install first (+9 more)

### Community 36 - "get_isolation_service"
Cohesion: 0.07
Nodes (21): get_isolation_service(), Returns the motor-isolation service. Returns: IsolationService: The process-…, IsolationService, Writes intent to the database so it survives a restart. Args: isolated (bool):…, Manages motor isolation intent, reconciliation, and idle timeout. Attributes:…, Sets operator intent and reconciles it immediately. Args: isolated (bool):…, Advances the idle timer and retries pending reconciliation., Auto-engages isolation once the lock has been idle long enough. (+13 more)

### Community 37 - "BridgeServoRepository"
Cohesion: 0.07
Nodes (22): BridgeServoRepository, Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position. Returns: bool: True when the servo…, Configures the servo dead-zone width. Args: counts (int): Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn…, Cuts or restores drive torque while sensors stay powered. Args: enabled (bool):…, Reads register 0x28 directly. Returns: Optional[int]: Register value (0 or 1),…, Reads the position-loop tuning registers directly. Returns:… (+14 more)

### Community 39 - "stream.py"
Cohesion: 0.10
Nodes (26): EventDep, FastAPI, ge, le, StreamingResponse, SSE stream for servo state, saved positions and events., Streams servo state, saved positions, and events over SSE. Args: request…, Generates SSE events for state, saved positions and events. Args: request… (+18 more)

### Community 40 - "Deliver Skill Doc"
Cohesion: 0.20
Nodes (9): Deliver, Phase 0 — Orient (cheap, no approval needed), Phase 1 — Plan, then STOP, Phase 2 — Run it, all of it, Phase 3 — Hardware never runs unattended, Phase 4 — Verify, Phase 5 — Record, or it is not done, The rule that overrides your instincts (+1 more)

### Community 41 - "Coding Conventions Doc"
Cohesion: 0.10
Nodes (19): Architecture, Booleans and conditions, C++ (sketch side), Class docstrings carry `Attributes:`, Control flow, Conventions, Current gap against this standard, Database access (+11 more)

### Community 42 - "TestSamplerLifecycleIsolation"
Cohesion: 0.29
Nodes (4): D26: a sampler thread that outlived its test used to log into a later test's…, The ordering itself is the fix - proven directly, not risked. An earlier…, The same mechanism, for MotionService's own background thread - added once that…, TestSamplerLifecycleIsolation

### Community 43 - "OnTarget.ino"
Cohesion: 0.18
Nodes (9): MoveCommand, acceleration, speed_counts_per_second, target_counts, Check(), CheckNear(), MoveTo(), setup() (+1 more)

### Community 44 - "Backlog T-Items"
Cohesion: 0.14
Nodes (13): T10 — Write the recovery runbook, in two halves, T11 — Write the operations manual, T13 — Distil the remaining documents, T17 — Get a mechanical rig on the bench so R2's hand-turn scenario can actually be tested, T18 — Front-end conventions, and split `app.js` by feature, T20 — Doc-truth sweep from the whole-app review, T21 — Constants and dead code with no shared source, T2 — Package the air-gapped bundle (+5 more)

### Community 45 - "ServoAppException"
Cohesion: 0.25
Nodes (6): NotFoundException, Exception, Appends this class's error-code segment to its parent's. Args: code…, Base for 404s: a referenced entity does not exist., Base for every domain exception. Every subclass declares only its own error-…, ServoAppException

### Community 46 - "ServoSnapshot"
Cohesion: 0.11
Nodes (17): ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage, ServoSnapshot (+9 more)

### Community 48 - "Rig Testing Protocol Doc"
Cohesion: 0.14
Nodes (13): 1. Physical Architecture & Kinematics (Per Documentation), 2. Pre-Test Inspection & Mechanical Setup Checklist, 3. The 7 Rigorous Test Protocols, 4. Post-Test Data Archival & Backlog Sign-Off, Mechanical Rig Test Protocol: 44:30 Belt Reduction & Rotary Drive, Motion & Coordinate Invariants, Protocol 1: Mid-Travel Datum Calibration & Belt Backlash, Protocol 2: R2 Motor Isolation & Hand-Turn Dynamics (T17 Acceptance) (+5 more)

### Community 49 - "test_pure_logic.cpp"
Cohesion: 0.16
Nodes (8): main(), MakeConverter(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 50 - "Relay Connection Ceiling"
Cohesion: 0.38
Nodes (7): ADR-0001 — Network path runs through the MCU, kMaxRelaySockets = 6 is the only connection ceiling, D4 — Connection drops after a few commands, D6 — App load time is sometimes slow, R1 — Determine the real concurrent-operator ceiling, T8 — Instrumented run on the board over adb, Served from the board to any machine on the network

### Community 51 - "Early Defects List"
Cohesion: 0.20
Nodes (10): D2 — `capture()` can store a failed read as position 0, D3 — The C++ side has no logging, D4 — Connection drops after a few commands; requires a page refresh, D5 — Log output is connect/disconnect noise, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D7 — UI is not verified on small operator screens, D8 — `.env` must be created before the first run of this version, Defects (+2 more)

### Community 53 - "ServoStateView"
Cohesion: 0.06
Nodes (59): CalibrationDep, IsolationDep, MotionDep, Coherent snapshot of servo, lock, and baseline state. Attributes: output_deg…, ServoStateView, get_present_speed(), get_torque_register(), get_tuning_registers() (+51 more)

### Community 54 - "System Audit Doc"
Cohesion: 0.15
Nodes (12): 1. A reading now carries its own validity, 2. Calibration refuses a reading the servo never gave, 3. Unreachable targets are refused, not clamped, 4. The default baseline is the CENTRE of travel, not zero, 5. Calibration warns when the datum is off-centre, 6. Bridge access is serialised (previous round), Answering "did we even test the sketch?", Full-system audit (+4 more)

### Community 55 - "Soak Test Checkpointer"
Cohesion: 0.15
Nodes (12): Checkpointer, Any, Orchestrates synthetic operators during a soak test. Args: host (str): Board…, Builds a comprehensive summary dictionary. Returns: dict[str, Any]: Detailed…, Periodically prints status and persists checkpoint reports., Initializes checkpointer., Executes the checkpoint loop until stopped., Prints a live summary line and rewrites the report file. (+4 more)

### Community 56 - "TestTorque"
Cohesion: 0.05
Nodes (13): SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Mirrors the real controller's un-isolate ordering: the target snaps to wherever…, Nothing in this repository writes these registers - it must report what an…, configure_range records the travel-range mode., Absolute counts beyond one turn and below zero (contract)., Basic motion profile., Motor isolation: cutting torque must stop the shaft actually moving, not just…, TestDeadband (+5 more)

### Community 57 - "Hardware Config Fallback"
Cohesion: 0.33
Nodes (6): Missing python/.env silently runs the simulator, ADR-0004 — Repository abstraction with a simulated backend, D8 — .env must be created before the first run, cp .env.board .env — the only manual deploy step, run_dev.py — dev-PC entrypoint, Going live is a configuration flag

### Community 58 - "get_database"
Cohesion: 0.50
Nodes (4): get_database(), get_saved_position_repository(), Returns the shared database wrapper. Returns: Database: The process-wide…, Returns the saved-position repository. Returns: SavedPositionRepository: The…

### Community 59 - "Soak Report Tests"
Cohesion: 0.06
Nodes (45): _israel_time(), fixture, Path, tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded, plus…, Tests for print_r1_scorecard() and report_telemetry() anomaly detection., Forces a non-UTC timezone (IDT, UTC+3 in August) for this module. Returns: None., A record just outside the local cutoff but inside the UTC one., Pins _utc_cutoff() itself: the helper both call sites share. (+37 more)

### Community 60 - "AppStub"
Cohesion: 0.50
Nodes (3): AppStub, Stub of the App loop runner., Does nothing. Returns: None.

### Community 61 - "SqliteTelemetryRepository"
Cohesion: 0.11
Nodes (14): SQLite implementation of the telemetry repository., Stores telemetry samples in the telemetry table. Attributes: _db (Database):…, Counts samples in range and returns count and base timestamp. Args: ts_from…, Deletes samples older than the retention window. Args: days (int): Retention…, SqliteTelemetryRepository, fixture, SqliteTelemetryRepository: add, ranged query, purge, fault columns., Telemetry repository over a fresh database. Returns: The repository under test. (+6 more)

### Community 62 - "MotionService"
Cohesion: 0.09
Nodes (17): MotionService, Records the single 'move accepted' event and its log line. Args: target_deg…, Stops the current move at the present position. Raises:…, Changes the digital lock, honoring the optional move guard. Args: locked…, Clears a tripped overload fault by re-commanding the position. Raises:…, Records and raises a non-acknowledgement, never a false success. Args: event…, Records a failure event and logs it at error level. Args: event (str): Event…, Validates and executes movement commands in output-degree space. Attributes:… (+9 more)

### Community 63 - "Synthetic Operator Tests"
Cohesion: 0.06
Nodes (20): Unit tests for tools/synthetic_operator.py., Stream frame reception and inter-arrival jitter calculation., Tests for quantize_deg() step quantization., Exact multiples of 0.06 deg should remain unchanged., Arbitrary floating point angles snap to nearest 0.06 grid., Tests for classify_settle_result() convergence classification., A measured angle equal to the commanded one always converges., A small deviation inside the stated tolerance still converges. (+12 more)

### Community 64 - "Angle Converter (C++)"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 65 - "Defects — detail"
Cohesion: 0.13
Nodes (14): D28 — MCU boot-time `mcu_log` notify lost to a startup race, D36 — Several tests construct their own `Database` and never close it, D38 — A saved position's "earlier reference" tag has no way to dismiss it, D41 — Firmware commands real moves off failed reads and malformed payloads, D42 — Errors that vanish: SSE stream, migration, sqlite writes, D43 — Guards that fail open on an invalid read, D44 — Operator-facing UI gaps found by the whole-app review, D45 — Relay and firmware robustness gaps found by the whole-app review (+6 more)

### Community 66 - "ServoBus"
Cohesion: 0.20
Nodes (14): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, ServoBus::ServoBus(), WriteByte (+6 more)

### Community 67 - "Backlog R-Items"
Cohesion: 0.25
Nodes (7): R11 — Accept any typed angle; snap to the nearest step and show the delta, R12 — Extended travel: soft limit ±90°, hard limit ±95°, confirmed in between, R1 — Determine the real concurrent-operator ceiling, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R7 — Handover logistics depend on adapter delivery, R8 — Emergency stop, R-items — detail

### Community 68 - "Ordering, rewritten 8 August 2026 — by session, with sizes"
Cohesion: 0.14
Nodes (14): Batch 1 — Desk work, no board — **DONE 8 August 2026**, Batch 2 — Make the machine diagnosable — **DONE 8 August 2026** (desk work), Batch 3 — The measurement session (board, supervised, one long run), Batch 4 — The two unbuilt MVP features, Batch 5 — The handover pack, Batch 6 — Mechanical, suits an executing agent, D35 — Commanded speed and actual speed disagree by roughly 1.5-2x, D40 — A move settles short under load and re-commanding the same target does not correct it (+6 more)

### Community 70 - "Hardware Bench Facts"
Cohesion: 0.67
Nodes (4): The 44:30 belt reduction is the whole point, Bench-verified hardware facts, Confirm the Ethernet patch survived the first build, Apply SpiRemap twice

### Community 71 - "Firmware Prose Strip Task"
Cohesion: 0.20
Nodes (9): A — Doxygen doc comments (`///` and `/** */` blocks), B — inline comments, C — relocate what is not already written down, Constraints, D — two comment classes that need special handling, found the hard way, Report back, Scope, Task: strip explanatory prose from sketch/src/ (+1 more)

### Community 73 - "TestExport"
Cohesion: 0.25
Nodes (3): A sample taken before any move has target_valid=0; one taken after an accepted…, Binary telemetry export contract. XLSX assembly is client-side (app.js) by…, TestExport

### Community 74 - "Twin-Review Skill Doc"
Cohesion: 0.15
Nodes (12): 1. Twin path, 2. Operator impact, 3. Relay and hardware safety, 4. Doc truth, 5. General correctness, How to run it, Not yet scoped, Reporting (+4 more)

### Community 75 - "Python Dependencies"
Cohesion: 0.50
Nodes (4): Dev And Test Dependencies, Runtime Dependencies, ARM64 Platform Wheels Required, Offline Wheelhouse

### Community 76 - "Python Prose Strip Task"
Cohesion: 0.22
Nodes (8): A — docstrings (`python/app/**/*.py`), B — inline comments, C — relocate what is not already written down, Constraints, D — the remaining style gaps (`python/app/` only), Report back, Task: strip explanatory prose from python/app/, Verification — after every file, not only at the end

### Community 77 - "FlakyServo"
Cohesion: 0.15
Nodes (8): flaky(), FlakyServo, fixture, Wraps the real simulator but can be told to refuse the next torque…, Swaps the cached servo repository for one whose ack is controllable, for the…, The sampler thread survives sampling failures., The record must carry the cause, not just the fact. A live board run on 7…, TestSamplerResilience

### Community 78 - "test_logging_setup.py"
Cohesion: 0.40
Nodes (3): Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 79 - "SavedPositionService"
Cohesion: 0.05
Nodes (39): NotFoundError, PositionOutOfRangeError, Raised when a referenced entity does not exist., Raised when a saved position's angle falls outside the travel window., Raised when an edit targets a saved position changed since it was read., StalePositionError, get_app_state_repository(), Returns the persisted operator-intent repository. Returns: AppStateRepository:… (+31 more)

### Community 83 - "McuLog"
Cohesion: 0.13
Nodes (12): get_mcu_log(), Returns the MCU diagnostic log receiver. Returns: McuLog: The process-wide…, McuLog, _now_iso(), Returns current UTC time as an ISO-8601 string with milliseconds. Returns: str:…, Bridge receiver that writes MCU-originated events to their own file.…, Registers the Bridge callback for MCU logs., Handles one diagnostic record forwarded from the MCU. Args: level (int):… (+4 more)

### Community 84 - "get_telemetry_service"
Cohesion: 0.09
Nodes (22): create_app(), FastAPI application assembly: routers and domain-error mapping., Creates and configures the FastAPI application. Returns: FastAPI: The…, Maps every domain exception to its HTTP response and log line. Args: app…, _register_error_handlers(), get_relay(), get_telemetry_service(), Returns the telemetry service. Returns: TelemetryService: The process-wide… (+14 more)

### Community 85 - "decode_sign_magnitude"
Cohesion: 0.12
Nodes (11): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. Args: value (int):…, parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude, parametrize (+3 more)

### Community 86 - "repo"
Cohesion: 0.67
Nodes (3): fixture, Saved-position repository over a fresh database. Returns: The repository under…, repo()

### Community 88 - "Synthetic Operator Script"
Cohesion: 0.15
Nodes (25): classify_settle_result(), find_minimum_effective_step(), _probe_get_state(), _probe_move(), _probe_wait_settle(), quantize_deg(), Synthetic operators that drive the running board like people would. Written for…, Protocol C: approach fresh, observe a shortfall, then re-command. Stages away… (+17 more)

### Community 89 - "Backlog Index Doc"
Cohesion: 0.25
Nodes (7): Backlog, T1 — Apply `CONVENTIONS.md` across the codebase, T4 — Moves while unverified: DECIDED, permitted, T5 — Add `design_diagrams/` with PlantUML, T6 — Restructure the exception hierarchy, T7 — Add the database abstraction, Tasks

### Community 95 - "Closed Sessions Doc"
Cohesion: 0.25
Nodes (7): Not in these three sessions, Session 1, Batch 1 — DONE, 8 August 2026, Session 1, Batch 2 — DONE, 8 August 2026, Session 2 — The soak — IN PROGRESS, Session 3 — SSE first, then Batch 4, START HERE — the session plan, Suggested order — SUPERSEDED 8 August 2026

### Community 96 - "TestNothingIsReportedAsMeasuredOnAFailedRead"
Cohesion: 0.36
Nodes (4): A failed read yields no numbers at all, not a position alone. D16.…, Nulling a field must not remove it: clients read every key., D23, amends ADR-0008: the same rule as the five readings above. moving and the…, TestNothingIsReportedAsMeasuredOnAFailedRead

### Community 97 - "Domain Glossary"
Cohesion: 0.29
Nodes (6): Control and safety, Language, MCU boundary, Position and geometry, Servo MVP — context, Telemetry

### Community 98 - "Sprint Planning Log"
Cohesion: 0.29
Nodes (6): Committed (~13.25h claude/operator-serial / 13.5h capacity — pulled in, Jira-pasteable blocks, Retro (fill in at sprint close), Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start), Sprints, Stretch (attempted only if committed scope finishes with room left)

### Community 100 - "test_motion_service.py"
Cohesion: 0.08
Nodes (35): CommandNotAcknowledgedError, ConflictException, IsolatedError, LockedAndIsolatedError, LockedError, MovingError, OutOfTravelError, Domain exceptions: each carries its own HTTP mapping and log metadata. (+27 more)

### Community 101 - "test_telemetry_service.py"
Cohesion: 0.15
Nodes (11): get_telemetry_repository(), Returns the telemetry repository. Returns: TelemetryRepository: The process-…, fixture, TelemetryService: sampling, CSV export, retention timing., Fresh telemetry service (sampler NOT started). Returns: The service under test., A stalled bus must leave a gap, not a row claiming position 0. Seven such rows…, The stored row must come from a single coherent read. The row used to be…, Single-sample persistence. (+3 more)

### Community 102 - "Bridge Payload Contract"
Cohesion: 0.33
Nodes (6): Three verification commands (186 / 164 / agree), ADR-0006 — Bridge payloads are CSV strings, Field order is a contract, Current status — everything exists, nothing is stable, Bridge contract checker, The Bridge payload contract with Python

### Community 128 - "routers/saved_positions.py"
Cohesion: 0.11
Nodes (29): delete, patch, PositionsDep, create_position(), delete_position(), go_to_position(), list_positions(), post (+21 more)

### Community 129 - "Brace Balance Checker Script"
Cohesion: 0.32
Nodes (7): check_file(), main(), Path, Brace-balance check for sketch/src/ files the native suite can't compile.…, Removes // and /* */ comments and "..."/'...' literals. Args: text (str): Raw…, Returns the file's final brace depth (0 means balanced). Args: path (Path):…, strip_comments_and_strings()

### Community 131 - "get_state_store"
Cohesion: 0.07
Nodes (17): get_state_store(), Returns the atomic servo/lock/baseline/isolation state store. Returns:…, Reads the settle state from the store. Args: backend: The backend fixture…, _settling(), A read the servo never answered must not become a position. Observed on the…, The rule that nulls the position governs the readings beside it. The docstring…, Nulling on failure must not null on success., D23, amends ADR-0008: the same rule governs moving and the six fault flags.… (+9 more)

### Community 132 - "get_settings"
Cohesion: 0.18
Nodes (9): get_settings(), Returns the process-wide settings singleton. Returns: Settings: The cached…, get_health(), Returns service health including the MCU status line. Args: settings…, Settings: defaults, environment override, caching., Behavior of the pydantic-settings configuration., TestSettings, RelayDep (+1 more)

### Community 135 - "BridgeApi.cpp"
Cohesion: 0.05
Nodes (56): bin_t, GPIO_TypeDef, k_timeout_t, App, Begin, Tick, Ack(), BridgeApi (+48 more)

### Community 136 - "TelemetrySnapshot"
Cohesion: 0.06
Nodes (35): InvalidReadingError, Raised when an operation needs a reading the servo did not supply., Instantaneous sensory readout from the servo layer. Attributes: raw_counts…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: TelemetrySnapshot:…, backend(), _clear_all_caches(), client() (+27 more)

### Community 141 - "wait_until"
Cohesion: 0.08
Nodes (17): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), _events(), A command the servo never acknowledged is never reported as accepted - the…, Consistent-direction anti-backlash approach., An upward move gets the same correction as a downward one - a plain direct…, A failed read must not crash the backlash decision - it has no information to…, D34: 0.06 deg is the real minimum step; a message rounded to 1 decimal cannot… (+9 more)

### Community 143 - "Soak Test Runner"
Cohesion: 0.50
Nodes (4): main(), Parses arguments and runs the soak., Queries board status and prints pre-flight diagnostics. Args: host (str): Board…, run_preflight()

### Community 146 - "Jira Import — Servo MVP"
Cohesion: 0.33
Nodes (5): Committed, Jira Import — Servo MVP, Section A — Current Sprint (30 August – 3 September 2026), Section B — Backlog (not yet scheduled into a sprint), Stretch (attempted only if the committed work above finishes with time left)

### Community 150 - "TestGetSet"
Cohesion: 0.25
Nodes (3): A key that was never written reads back as None; a written one reads back as…, The whole point of this table: a second process (or a restart) reading the same…, TestGetSet

### Community 153 - "Arduino UNO Q + Waveshare ST3215"
Cohesion: 0.10
Nodes (20): 1. This is not a normal Arduino, 2. The ST3215 servo, 3. Geometry — and the one law that matters, 4. The Ethernet-shield relay, 5. The Bridge contract, 6. Symptom → cause, 7. Deployment traps, 8. Working rules (+12 more)

### Community 155 - "test_servo_routes.py"
Cohesion: 0.15
Nodes (9): Servo API routes: state, move, stop, lock, calibrate, recover., POST /api/v1/servo/recover., Calibrating on a dead bus must refuse, not store a datum., The refusal carries the configured step, not a hardcoded one. A regression…, GET /api/v1/servo/state., TestInvalidReadingSurfaced, TestRecover, TestState (+1 more)

### Community 170 - "Simulated Servo Methods"
Cohesion: 0.07
Nodes (15): Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position. Returns: bool: Always True on simulated…, Records the range configuration. Args: multi_turn (bool): Enable multi-turn…, Configures the simulated dead-zone width. Args: counts (int): Dead-zone width…, Cuts or restores simulated drive torque. Args: enabled (bool): True to restore…, Returns the simulated torque state. Returns: int: 1 when torque is enabled, 0…, Returns the tuning registers as last written, or factory default. Returns:…, Records any subset of the position-loop tuning registers. Args: position_p… (+7 more)

### Community 246 - "Bridge Command Tests"
Cohesion: 0.05
Nodes (4): Commands become the payloads the sketch parses., The ack is load-bearing here too: a caller must never believe a move was…, The ack is load-bearing for this one command: callers must never believe…, TestCommands

### Community 279 - "Skills Archive"
Cohesion: 0.29
Nodes (6): Skills archive, Sources, The gap this archive does not fill, What's here, What was stripped, and why, Why the big one is not tracked

### Community 288 - "Failed Read Handling"
Cohesion: 0.29
Nodes (6): A failed read is reported as unknown, never as a number, Consequences, Extended, 8 August 2026 — `valid` governs the whole snapshot, Status, The alternative that was considered, Why

### Community 302 - "Diagnostics & Isolation Routes"
Cohesion: 0.12
Nodes (7): Two different gates must surface as two different reasons - an operator refused…, GET /api/v1/servo/diagnostics/torque_register - diagnostic, independent of the…, GET /api/v1/servo/diagnostics/tuning_registers - the readback this delivery…, GET /api/v1/servo/diagnostics/present_speed - grounds D40c's creep-speed…, POST /api/v1/servo/diagnostics/tuning_registers - the measurement-campaign…, POST /api/v1/servo/isolate, and its refusal of a move., TestIsolate

### Community 303 - "Operator Lens Skill"
Cohesion: 0.25
Nodes (7): Also wear the client's hat, Operator lens, Output — file it, do not just say it, Rule zero, The control surface, The five questions, per control, The four failures worth memorising

### Community 309 - "EventService"
Cohesion: 0.14
Nodes (10): Event, EventService, One operator-facing event. Attributes: timestamp (str): ISO timestamp. event…, Thread-safe fixed-size store of recent events. Attributes: _events…, Stores one event. Args: event (str): Dotted event identifier. message (str):…, Returns the newest events, newest first. Args: limit (int): Maximum number of…, EventService: recording, ordering, capacity, thread safety., D33: an offset-less timestamp is read as local time by a browser, and the… (+2 more)

### Community 325 - "BridgeRelay"
Cohesion: 0.16
Nodes (9): BridgeRelay, socket, Streams FastAPI reply bytes back down to the sketch. Args: slot (int):…, Closes and forgets one mirrored connection. Args: slot (int): Connection slot…, Byte pump between the sketch's network clients and FastAPI. Attributes:…, Registers all Bridge callbacks., Handles a new network client reported by the sketch. Args: slot (int):…, Forwards client bytes to FastAPI. Args: slot (int): Connection slot identifier.… (+1 more)

### Community 344 - "BridgeStub"
Cohesion: 0.07
Nodes (21): BridgeStub, Recording stub of the Arduino Bridge., Clears recorded state between tests. Returns: None., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths. (+13 more)

### Community 351 - "test_operator_scenario.py"
Cohesion: 0.40
Nodes (3): E2E: a full operator session against the live server over real HTTP., Boot -> calibrate -> move -> lock -> saved positions -> telemetry -> fault., TestOperatorSession

### Community 397 - "Settings"
Cohesion: 0.09
Nodes (26): BaseSettings, Typed application settings loaded from the environment / .env file., Backend configuration, overridable via environment or .env. Attributes:…, Settings, Logging configuration built on Logger461 (loguru JSON wrapper)., Initializes Logger461 for the process. Args: settings (Settings): Application…, setup_logging(), Linux half of the TCP relay; counterpart of EthernetRelay (sketch). (+18 more)

### Community 399 - "test_system_routes.py"
Cohesion: 0.12
Nodes (9): System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent., The health endpoint names the servo backend in use., GET /api/v1/system/health., TestEvents, TestHealth, TestHealthDevComputer (+1 more)

### Community 443 - "Bridge Contract Checker"
Cohesion: 0.39
Nodes (7): collect_python(), collect_sketch(), main(), Path, Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 447 - "Connection Ceiling Decision"
Cohesion: 0.50
Nodes (3): Consequences, The connection ceiling stays at 6 this batch, Why

### Community 450 - "Motor Isolation Persistence"
Cohesion: 0.40
Nodes (4): Consequences, Motor isolation state survives a reboot, Status, Why

## Knowledge Gaps
- **380 isolated node(s):** `state`, `REFUSALS`, `EVENT_LABELS`, `DAY_SHEET_COLS`, `RAW_HEADERS` (+375 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **37 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_state_store()` connect `get_state_store` to `get_motion_service`, `get_settings`, `get_isolation_service`, `ServoStateStore`, `stream.py`, `Relay E2E Tests`, `TelemetrySnapshot`, `test_motion_service.py`, `test_telemetry_service.py`, `TestSamplerLifecycleIsolation`, `Settings`, `wait_until`, `SavedPositionService`, `FlakyServo`, `TestOutOfTravelSurfaced`, `get_telemetry_service`, `deps.py`, `test_servo_routes.py`?**
  _High betweenness centrality (0.036) - this node is a cross-community bridge._
- **Why does `wait_until()` connect `wait_until` to `get_motion_service`, `get_state_store`, `test_motion_service.py`, `get_isolation_service`, `Relay E2E Tests`, `TestMove`, `TelemetrySnapshot`, `test_telemetry_service.py`, `TestSamplerLifecycleIsolation`, `FlakyServo`, `Diagnostics & Isolation Routes`, `SavedPositionService`, `TestMoveGuardOverHttp`, `BridgeStub`, `TestTorque`, `test_servo_routes.py`, `test_operator_scenario.py`?**
  _High betweenness centrality (0.033) - this node is a cross-community bridge._
- **Why does `ServoStateStore` connect `ServoStateStore` to `TelemetryService`, `get_state_store`, `test_motion_service.py`, `get_isolation_service`, `stream.py`, `TelemetrySnapshot`, `SavedPositionService`, `telemetry_service.py`, `EventService`, `ServoStateView`, `deps.py`, `MotionService`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `ServoStateStore` (e.g. with `CalibrationService` and `IsolationService`) actually correct?**
  _`ServoStateStore` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `REFUSALS`, `EVENT_LABELS` to the rest of the system?**
  _380 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `fine_approach_trial.py` be split into smaller, more focused modules?**
  _Cohesion score 0.07827260458839407 - nodes in this community are weakly interconnected._