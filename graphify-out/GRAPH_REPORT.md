# Graph Report - servo_mvp  (2026-08-30)

## Corpus Check
- 145 files · ~122,936 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 2171 nodes · 3661 edges · 166 communities (136 shown, 30 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 368 edges (avg confidence: 0.59)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `1149793e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- NetworkRelay
- get_zero_service
- TestCrud
- app.js
- ServoStateStore
- deps.py
- test_relay_path.py
- SqliteZeroRepository
- TestFailedReadIsNeverAPosition
- SqliteAppStateRepository
- Database
- adr/README.md
- Tasks
- check_client_behaviour.js
- For the operators
- main.py
- LogRecord
- get_settings
- TEST
- test_mcu_log.py
- post_isolate
- verify.py
- Settings
- Conventions
- _read_sse_lines
- test_bridge_servo_repository.py
- ServoController.cpp
- Document reading flow (router)
- ADR-0003 — Travel window is +/-90 output degrees, multi-turn off
- Closed items
- Design Notes
- Requirements captured but not yet designed
- LoggerStub
- TestDelete
- TelemetrySnapshot
- The flows
- get_state_store
- BridgeServoRepository
- get_servo_repository
- routers/system.py
- Deliver
- TestValidation
- get_telemetry_service
- OnTarget.ino
- Tasks — detail
- IsolationService
- ServoSnapshot
- setup_logging
- InvalidReadingError
- TinyTest.h
- D4 — Connection drops after a few commands
- Defects
- Current gap against the standard
- routers/servo.py
- D3 — The C++ side has no logging
- SyntheticOperator
- get_relay
- ADR-0004 — Repository abstraction with a simulated backend
- TestNothingIsReportedAsMeasuredOnAFailedRead
- soak_report.py
- telemetry.py
- SqliteTelemetryRepository
- telemetry_service.py
- routers/zeros.py
- AngleConverter
- Defects — detail
- ServoBus
- R-items — detail
- Ordering, rewritten 8 August 2026 — by session, with sizes
- ServoRepository
- D2 — capture() can store a failed read as position 0
- Task: strip explanatory prose from sketch/src/
- DiagLog
- TestExport
- Twin review
- Dev And Test Dependencies
- Task: strip explanatory prose from python/app/
- FlakyServo
- START HERE — the session plan
- test_pure_logic.cpp
- get_motion_service
- Full typing with lowercase builtin generics
- Layout divergence from the reference src/ tree
- isolation_service.py
- ServoStateResponse
- TestTravelWindow
- SpiRemap.cpp
- adb push never deletes
- TestSnapshotDecoding
- ZeroReference
- TestIsolationGate
- Adopt Connections With accept(), Never available
- Detect Disconnects Before Accepting
- No Bricks Constraint
- One fact lives in exactly one file
- timestamp
- Git branching and commit message rules
- Grouped, parenthesised imports
- Trailing commas force vertical layout (ruff)
- D7 — UI not verified on small operator screens
- MotionService
- TelemetryService
- Review findings — Session 14 whole-app twin-review
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
- TelemetrySample
- app.py
- check_file
- _stream_generator
- TestFailedReadsAreNotStored
- get_database
- get_telemetry_repository
- test_servo_routes.py
- BridgeApi.cpp
- TestLockGate
- TestConversions
- TestOutOfTravelSurfaced
- decode_sign_magnitude
- OutOfTravelError
- test_motion_service.py
- StepError
- TestTarget
- TestActivateDelete
- TestActive
- TestCalibrate
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
- test_bridge_relay.py
- wait_until
- McuLog
- BridgeStub
- main
- motion_service.py
- The connection ceiling stays at 6 this batch
- Motor isolation state survives a reboot
- Use SMS_STS, Never SCSCL

## God Nodes (most connected - your core abstractions)
1. `get_state_store()` - 73 edges
2. `ServoStateStore` - 63 edges
3. `TelemetrySnapshot` - 54 edges
4. `wait_until()` - 49 edges
5. `Database` - 40 edges
6. `Closed items` - 38 edges
7. `ZeroReference` - 37 edges
8. `TEST()` - 37 edges
9. `get_isolation_service()` - 36 edges
10. `BridgeServoRepository` - 35 edges

## Surprising Connections (you probably didn't know these)
- `Single-context documentation layout` --semantically_similar_to--> `Document reading flow (router)`  [INFERRED] [semantically similar]
  docs/agents/domain.md → CLAUDE.md
- `sshfs board mount as working copy` --semantically_similar_to--> `Development shortcut — sshfs mount of the board`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Apply SpiRemap twice` --semantically_similar_to--> `Confirm the Ethernet patch survived the first build`  [INFERRED] [semantically similar]
  sketch/README.md → README.md
- `Unreachable targets are refused, not clamped` --conceptually_related_to--> `Travel window`  [INFERRED]
  docs/AUDIT.md → CONTEXT.md
- `D4 — Connection drops after a few commands` --conceptually_related_to--> `Slot`  [INFERRED]
  docs/BACKLOG.md → CONTEXT.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **The datum-at-zero failure mode** — context_datum, context_travel_window, docs_audit_defect_chain, docs_backlog_d1_a_move_to_a_negative_angle_stops_at_0, docs_backlog_d2, docs_adr_0003_travel_window_plus_minus_90_output_degrees_decision, docs_project_state_linchpin [INFERRED 0.85]
- **Consequences of the air-gap constraint** — docs_adr_0005_air_gapped_by_default_development_decision, docs_adr_0002_no_frontend_framework_decision, readme_air_gapped_bundle, readme_core_version_pin, sketch_readme_tinytest_harness, docs_backlog_t2_package_the_air_gapped_bundle [EXTRACTED 1.00]
- **The MCU/Linux boundary contract** — context_bridge, docs_adr_0006_csv_bridge_payloads_decision, docs_adr_0006_csv_bridge_payloads_field_order_contract, readme_bridge_contract_checker, sketch_readme_bridge_payload_contract, docs_adr_0001_network_path_through_the_mcu_decision [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]

## Communities (166 total, 30 thin omitted)

### Community 0 - "NetworkRelay"
Cohesion: 0.11
Nodes (23): k_timeout_t, ByteSink, CloseSink, OpenSink, ByteSink, CloseSink, OpenSink, NetworkRelay (+15 more)

### Community 1 - "get_zero_service"
Cohesion: 0.10
Nodes (12): get_zero_service(), Returns the zero service. Returns: ZeroService: The process-wide zero service., Cross-service integration flows (no HTTP): components working together., Zeros, state store and motion interacting., TestZeroLifecycleAcrossServices, fixture, ZeroService: capture, activate, delete rules, calibrate., Fresh zero service. Returns: The service under test. (+4 more)

### Community 2 - "TestCrud"
Cohesion: 0.18
Nodes (6): Builds an unsaved zero entity. Args: name: Zero name. counts: Raw counts.…, Create, read, delete., Upsert of THE calibration datum., TestCrud, TestDatum, _zero()

### Community 3 - "app.js"
Cohesion: 0.07
Nodes (75): ADR-0008, ANGLE_SERIES, angleSortedDownsampleRefs(), apiDelete(), apiGet(), apiPost(), asApiError(), askConfirm() (+67 more)

### Community 4 - "ServoStateStore"
Cohesion: 0.05
Nodes (26): Returns the operator current isolation intent. Returns: bool: True when…, Records that the servo acknowledged an isolation write. Args: isolated (bool):…, Returns the acknowledged isolation state shown to operator. Returns: bool: True…, Marks the position reference as verified after calibration., Returns whether the position reference has been verified. Returns: bool: True…, Returns seconds left in the settle window (0.0 if none). Returns: float:…, Records a newly accepted move target and clears staleness. Args: target_deg…, Marks current target as no longer being pursued. (+18 more)

### Community 5 - "deps.py"
Cohesion: 0.10
Nodes (20): ActiveZeroError, DatumZeroError, NotFoundError, Raised when a referenced entity does not exist., Raised when attempting to delete the active zero reference., Raised when attempting to delete the calibration datum zero., Composition root: cached provider functions that construct and wire., ABC (+12 more)

### Community 6 - "test_relay_path.py"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 7 - "SqliteZeroRepository"
Cohesion: 0.11
Nodes (13): Stores zero references in the zeros table. Attributes: _db (Database): Database…, Returns the active zero reference, if any. Returns: Optional[ZeroReference]:…, Creates or updates the calibration datum zero. Args: raw_counts (int): Captured…, Maps a database row to the entity. Args: row (object): SQLite row. Returns:…, Persists a new zero reference. Args: zero (ZeroReference): Entity with id=None.…, Returns all zero references, newest first. Returns: list[ZeroReference]: All…, Returns one zero reference by id. Args: zero_id (int): Database identifier.…, Deletes one zero reference. Args: zero_id (int): Database identifier. Returns:… (+5 more)

### Community 8 - "TestFailedReadIsNeverAPosition"
Cohesion: 0.13
Nodes (7): A read the servo never answered must not become a position. Observed on the…, The rule that nulls the position governs the readings beside it. The docstring…, Nulling on failure must not null on success., D23, amends ADR-0008: the same rule governs moving and the six fault flags.…, Nulling on failure must not null on success (D23)., read_counts()'s own guard (D24): unexercised since it was written, same defect…, TestFailedReadIsNeverAPosition

### Community 9 - "SqliteAppStateRepository"
Cohesion: 0.11
Nodes (12): SQLite implementation of the app-state key/value repository., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):…, Stores small operator-intent flags in the app_state table. Attributes: _db…, SqliteAppStateRepository, fixture, SqliteAppStateRepository: get/set of persisted operator-intent flags., App-state repository over a fresh database. Returns: The repository under test. (+4 more)

### Community 10 - "Database"
Cohesion: 0.12
Nodes (12): Connection, Database, Returns the shared SQLite connection. Returns: sqlite3.Connection: The open…, Closes the connection., Creates tables and indexes when missing., Owns the SQLite connection and serializes all access to it. Attributes:…, Adds columns introduced after a database was first created., Fresh-database schema. (+4 more)

### Community 11 - "adr/README.md"
Cohesion: 0.07
Nodes (20): Consequences, The network path runs through the MCU, not the Linux side, Consequences, Considered and rejected, Plain HTML, CSS and JavaScript — no framework, no build step, Consequences, Travel window is ±90 output degrees, and multi-turn stays off, Consequences (+12 more)

### Community 12 - "Tasks"
Cohesion: 0.09
Nodes (24): Servo Control App Manifest, sshfs board mount as working copy, Abstract Database with concrete SqliteDatabase, Three-tier exception hierarchy, ADR-0005 — Develop as if already air-gapped, Native tests cover pure maths only, R7 — Handover logistics depend on adapter delivery, T1 — Apply `CONVENTIONS.md` across the codebase (+16 more)

### Community 13 - "check_client_behaviour.js"
Cohesion: 0.18
Nodes (7): APP, ctx, els, fs, path, toasts, vm

### Community 14 - "For the operators"
Cohesion: 0.13
Nodes (14): For the operators, For the programme, For whoever receives the MVP, Open questions, Q10 — Should code-level docs/comments carry rationale, or move to `docs/`? `answered`, Q1 — What screen will you actually use? `answered`, Q2 — How many operators at once, really, and doing what? `answered`, Q3 — When the machine misbehaves on site, what do you want to be able to do? `answered` (+6 more)

### Community 15 - "main.py"
Cohesion: 0.16
Nodes (15): get_mcu_log(), Returns the MCU diagnostic log receiver. Returns: McuLog: The process-wide…, _ensure_logger461(), _level_enabled(), main(), Entry point: initialize, serve FastAPI, run the App loop. App Lab runs this…, Refuses to start if nothing chose the simulator on purpose. A missing .env and…, Runs uvicorn on localhost; relay and adb-forward are the doors. Args: app: The… (+7 more)

### Community 16 - "LogRecord"
Cohesion: 0.15
Nodes (11): LogRecord, arg1, arg2, event, level, message, uptime_ms, LogRing (+3 more)

### Community 17 - "get_settings"
Cohesion: 0.15
Nodes (12): create_app(), Creates and configures the FastAPI application. Returns: FastAPI: The…, get_settings(), Returns the process-wide settings singleton. Returns: Settings: The cached…, _ensure_logger461(), main(), Dev-PC runner: the full backend + web UI, no board required. The app modules…, Boots the backend + web UI and runs the dev console. Returns: None. (+4 more)

### Community 18 - "TEST"
Cohesion: 0.07
Nodes (27): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, log_ring_drops_oldest_when_full_and_counts_it (+19 more)

### Community 19 - "test_mcu_log.py"
Cohesion: 0.11
Nodes (14): _lines(), mcu_log(), fixture, McuLog: receiving and writing diagnostic events forwarded from the MCU., Behavior when the board runtime is absent (dev PC)., Fresh registered receiver, writing into a throwaway file. Returns: The receiver…, Reads every JSON line from a file. Args: path: File to read. Returns: One dict…, Bridge callback registration. (+6 more)

### Community 20 - "post_isolate"
Cohesion: 0.15
Nodes (16): IsolationDep, MotionDep, post_calibrate(), post_isolate(), post_lock(), post_move(), post_recover(), post_stop() (+8 more)

### Community 21 - "verify.py"
Cohesion: 0.14
Nodes (23): _delta(), _ensure_local_venv_mirror(), _load_baseline(), main(), _mirror_python_source(), Path, Runs the five verification checks once and prints one summary block. python3…, Runs a command, capturing combined stdout+stderr as text. Args: cmd: Argv list.… (+15 more)

### Community 22 - "Settings"
Cohesion: 0.14
Nodes (10): BaseSettings, Typed application settings loaded from the environment / .env file., Backend configuration, overridable via environment or .env. Attributes:…, Settings, Logging configuration built on Logger461 (loguru JSON wrapper)., main.py: the board entry point's own guards (D8, D29). conftest.py installs a…, D8: the board must not run the simulator by accident., D29: the Logger461 stand-in must honour LOG_LEVEL. (+2 more)

### Community 23 - "Conventions"
Cohesion: 0.11
Nodes (18): Architecture, Booleans and conditions, C++ (sketch side), Class docstrings carry `Attributes:`, Control flow, Conventions, Current gap against this standard, Database access (+10 more)

### Community 24 - "_read_sse_lines"
Cohesion: 0.21
Nodes (12): MonkeyPatch, _parse_sse_events(), Exception, SSE stream API integration tests., Reads exactly count lines from the response iterator. Args: response: The…, Parses SSE lines into a list of event dictionaries. Args: lines: Raw SSE lines.…, Custom exception to terminate stream generator during tests., _read_sse_lines() (+4 more)

### Community 25 - "test_bridge_servo_repository.py"
Cohesion: 0.10
Nodes (13): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., A misbehaving bus must not take the backend down., Records one call. Args: name: Bridge function name. payload: Request payload.…, deps honours use_hardware_servo. (+5 more)

### Community 26 - "ServoController.cpp"
Cohesion: 0.26
Nodes (15): BridgeApi::BridgeApi(), ClampAmplification(), ClampDeadband(), ServoController, Begin, CentreHere, ClearFault, ConfigureRange (+7 more)

### Community 27 - "Document reading flow (router)"
Cohesion: 0.10
Nodes (21): Document reading flow (router), Graphify extraction gaps (.ino and .css), Graphify-first navigation rule, Three verification commands (186 / 164 / agree), How to work on this repo, Bridge, Project ubiquitous language (glossary), Naming rules drawn from the glossary (+13 more)

### Community 28 - "ADR-0003 — Travel window is +/-90 output degrees, multi-turn off"
Cohesion: 0.13
Nodes (19): Baseline, Count, Datum, Output degree, Travel window, Zero reference, The 44:30 belt reduction is the whole point, ADR-0003 — Travel window is +/-90 output degrees, multi-turn off (+11 more)

### Community 29 - "Closed items"
Cohesion: 0.05
Nodes (38): Closed items, D10 — `logger.exception` swallows the exception; the sampler's real fault was a thread-safety bug in the SQLite layer, D11 — A single failed poll is presented as a disconnection, D12 — No way to return to the datum after activating a saved zero, D13 — Requests arriving faster than slots free up are refused, D14 — The most likely error in the system shows the operator "Failed to fetch", D15 — A command in flight looks identical to a command that did nothing, D16 — On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured (+30 more)

### Community 30 - "Design Notes"
Cohesion: 0.06
Nodes (30): Design Notes, python/app/core/config.py, python/app/core/events.py, python/app/core/logging_setup.py, python/app/db/database.py, python/app/deps.py, python/app/relay/bridge_relay.py, python/app/repositories/abstract/servo_repository.py (+22 more)

### Community 31 - "Requirements captured but not yet designed"
Cohesion: 0.21
Nodes (13): Emergency stop, Lock, Mechanical restraint, Motor isolation, The relay-capacity argument is unverified, Candidate ADR — how isolation, Lock and e-stop compose, R2 — Motor isolation: cut drive power, keep sensors alive, R3 — Confirm whether the Bridge could carry a frontend framework (+5 more)

### Community 32 - "LoggerStub"
Cohesion: 0.18
Nodes (5): LoggerStub, Mirrors the real logger: the exception rides with the record. Must attach it,…, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 33 - "TestDelete"
Cohesion: 0.13
Nodes (6): Zeros API routes: list, capture, activate, delete + error mapping., DELETE /{id} and its protections., POST /capture and GET list., TestActivate, TestCaptureList, TestDelete

### Community 34 - "TelemetrySnapshot"
Cohesion: 0.16
Nodes (9): Instantaneous sensory readout from the servo layer. Attributes: raw_counts…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: TelemetrySnapshot:…, Calibrating on a dead bus must refuse, not store a zero., TestInvalidReadingSurfaced, Calibration must not capture a reading the servo never gave. A failed read…, capture() must not do what D2 already fixed for calibrate(). D2 gave…, TestCalibrationRobustness (+1 more)

### Community 35 - "The flows"
Cohesion: 0.11
Nodes (17): 1. superpowers — the methodology layer, 2. agentic-awesome-skills — the catalogue, 3. Arduino-Agent — the hardware seam, 4. IoT-SkillsBench — the evidence, and the argument for writing our own, Every flow ends the same way, Sources, The flows, Tooling to install first (+9 more)

### Community 36 - "get_state_store"
Cohesion: 0.12
Nodes (17): get_app_state_repository(), get_event_service(), get_isolation_service(), get_state_store(), Returns the atomic servo/lock/baseline/isolation state store. Returns:…, Returns the motor-isolation service. Returns: IsolationService: The process-…, Returns the shared event buffer. Returns: EventService: The process-wide event…, Returns the persisted operator-intent repository. Returns: AppStateRepository:… (+9 more)

### Community 37 - "BridgeServoRepository"
Cohesion: 0.08
Nodes (19): BridgeServoRepository, Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position., Configures the servo dead-zone width. Args: counts (int): Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn…, Cuts or restores drive torque while sensors stay powered. Args: enabled (bool):…, Reads register 0x28 directly. Returns: Optional[int]: Register value (0 or 1),…, Invokes a Bridge function, converting failures into empty results. Args: name… (+11 more)

### Community 38 - "get_servo_repository"
Cohesion: 0.12
Nodes (16): get_servo_repository(), Returns the servo repository chosen by use_hardware_servo. Returns:…, AppStub, backend(), client(), fixture, Shared test configuration: stubs, environment, and fixtures. Runs entirely on a…, Fresh backend context: new DB, cleared caches, recording stubs. Yields: A… (+8 more)

### Community 39 - "routers/system.py"
Cohesion: 0.13
Nodes (20): EventDep, ge, le, get_events(), get_health(), get, Query, System endpoints: health and recent events. (+12 more)

### Community 40 - "Deliver"
Cohesion: 0.20
Nodes (9): Deliver, Phase 0 — Orient (cheap, no approval needed), Phase 1 — Plan, then STOP, Phase 2 — Run it, all of it, Phase 3 — Hardware never runs unattended, Phase 4 — Verify, Phase 5 — Record, or it is not done, The rule that overrides your instincts (+1 more)

### Community 41 - "TestValidation"
Cohesion: 0.29
Nodes (4): parametrize, Step-size validation., D34: 0.06 deg is the real minimum step; a message rounded to 1 decimal cannot…, TestValidation

### Community 42 - "get_telemetry_service"
Cohesion: 0.14
Nodes (10): get_telemetry_service(), Returns the telemetry service. Returns: TelemetryService: The process-wide…, Overload flag reaches persisted telemetry., TestFaultVisibleInSampledHistory, Telemetry API route: compact binary export. XLSX assembly happens client-side…, GET /api/v1/telemetry/binary., TestExport, fixture (+2 more)

### Community 43 - "OnTarget.ino"
Cohesion: 0.16
Nodes (8): App, Begin, Tick, Check(), CheckNear(), MoveTo(), setup(), WaitSettled()

### Community 44 - "Tasks — detail"
Cohesion: 0.15
Nodes (12): T10 — Write the recovery runbook, in two halves, T11 — Write the operations manual, T13 — Distil the remaining documents, T17 — Get a mechanical rig on the bench so R2's hand-turn scenario can actually be tested, T18 — Front-end conventions, and split `app.js` by feature, T2 — Package the air-gapped bundle, T3 — Run the on-target test suite, T5 — Add `design_diagrams/` with PlantUML (+4 more)

### Community 45 - "IsolationService"
Cohesion: 0.24
Nodes (7): IsolationService, Writes intent to the database so it survives a restart. Args: isolated (bool):…, Manages motor isolation intent, reconciliation, and idle timeout. Attributes:…, Sets operator intent and reconciles it immediately. Args: isolated (bool):…, Advances the idle timer and retries pending reconciliation., Auto-engages isolation once the lock has been idle long enough., Drives the acknowledged hardware state toward intent once. Args: reason (str):…

### Community 46 - "ServoSnapshot"
Cohesion: 0.08
Nodes (21): ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage, MoveCommand (+13 more)

### Community 47 - "setup_logging"
Cohesion: 0.33
Nodes (5): Initializes Logger461 for the process. Args: settings (Settings): Application…, setup_logging(), Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 48 - "InvalidReadingError"
Cohesion: 0.07
Nodes (20): InvalidReadingError, Raised when an operation needs a reading the servo did not supply., get_zero_repository(), Returns the zero repository. Returns: ZeroRepository: The process-wide zero…, ServoStateStore: conversions, lock/settle, verified flag, snapshot., Coherent snapshot content., The display and the motion path must share one baseline. Observed on the board:…, servo_direction inverts commanded and reported motion together. Round-trip… (+12 more)

### Community 49 - "TinyTest.h"
Cohesion: 0.22
Nodes (7): main(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 50 - "D4 — Connection drops after a few commands"
Cohesion: 0.18
Nodes (14): Fault, Relay, Slot, Pure-logic C++ classes stay header-only and Arduino-free, ADR-0001 — Network path runs through the MCU, kMaxRelaySockets = 6 is the only connection ceiling, ADR-0002 — Plain HTML/CSS/JS, no framework, D4 — Connection drops after a few commands (+6 more)

### Community 51 - "Defects"
Cohesion: 0.22
Nodes (8): Backlog, D2 — `capture()` can store a failed read as position 0, D4 — Connection drops after a few commands; requires a page refresh, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D7 — UI is not verified on small operator screens, D8 — `.env` must be created before the first run of this version, Defects, Suggested order

### Community 52 - "Current gap against the standard"
Cohesion: 0.22
Nodes (9): Class docstrings carry Attributes:, Control-flow prohibitions, Explicit boolean checks, no implicit truthiness, Current gap against the standard, Google docstrings with types in Args/Returns, Drain loops are exempt from the no-while rule, T1 — Apply CONVENTIONS.md across the codebase, Drain with while, never if (+1 more)

### Community 53 - "routers/servo.py"
Cohesion: 0.17
Nodes (23): Coherent snapshot of servo, lock, and baseline state. Attributes: output_deg…, ServoStateView, Servo endpoints: state, move, stop, lock., IsolateRequest, IsolateResponse, LockRequest, LockResponse, MoveAcceptedResponse (+15 more)

### Community 54 - "D3 — The C++ side has no logging"
Cohesion: 0.22
Nodes (9): Logging mandatory in hardware and network files, The relay and controller have no automated coverage, D3 — The C++ side has no logging, D5 — Log output is connect/disconnect noise, R5 — Metrics export and benchmarking output, R6 — Define 'stable' by benchmark, not by adjective, Known gaps, stated honestly, The bar for a delivered MVP (+1 more)

### Community 55 - "SyntheticOperator"
Cohesion: 0.05
Nodes (41): Checkpointer, main(), Metrics, PersistentPoller, Any, Synthetic operators that drive the running board like people would. Written for…, Creates an empty tally., Records one completed request. Args: action (str): Name of the action… (+33 more)

### Community 56 - "get_relay"
Cohesion: 0.19
Nodes (11): get_relay(), Returns the Bridge relay. Returns: BridgeRelay: The process-wide relay., _bound_socket(), live_backend(), fixture, socket, E2E fixtures: the backend booted the way main.py boots it. A real uvicorn…, Binds an ephemeral localhost TCP socket and leaves it open. Finding a free… (+3 more)

### Community 57 - "ADR-0004 — Repository abstraction with a simulated backend"
Cohesion: 0.29
Nodes (8): Missing python/.env silently runs the simulator, Backend (servo backend), Thin routers, services hold logic, abstract repositories only, ADR-0004 — Repository abstraction with a simulated backend, D8 — .env must be created before the first run, cp .env.board .env — the only manual deploy step, run_dev.py — dev-PC entrypoint, Going live is a configuration flag

### Community 58 - "TestNothingIsReportedAsMeasuredOnAFailedRead"
Cohesion: 0.36
Nodes (4): A failed read yields no numbers at all, not a position alone. D16.…, Nulling a field must not remove it: clients read every key., D23, amends ADR-0008: the same rule as the five readings above. moving and the…, TestNothingIsReportedAsMeasuredOnAFailedRead

### Community 59 - "soak_report.py"
Cohesion: 0.07
Nodes (37): _israel_time(), fixture, Path, tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded. D30:…, Forces a non-UTC timezone (IDT, UTC+3 in August) for this module. Returns: None., A record just outside the local cutoff but inside the UTC one., Pins _utc_cutoff() itself: the helper both call sites share., TestUtcLocalCutoff (+29 more)

### Community 60 - "telemetry.py"
Cohesion: 0.22
Nodes (8): alias, export_binary(), get, Query, StreamingResponse, Telemetry endpoints: binary telemetry stream export., Exports compact packed binary telemetry data for client-side rendering. Args:…, TelemetryDep

### Community 61 - "SqliteTelemetryRepository"
Cohesion: 0.12
Nodes (13): Stores telemetry samples in the telemetry table. Attributes: _db (Database):…, Counts samples in range and returns count and base timestamp. Args: ts_from…, Deletes samples older than the retention window. Args: days (int): Retention…, SqliteTelemetryRepository, fixture, SqliteTelemetryRepository: add, ranged query, purge, fault columns., Telemetry repository over a fresh database. Returns: The repository under test., Builds a sample. Args: timestamp: Unix timestamp. overload: Overload flag… (+5 more)

### Community 62 - "telemetry_service.py"
Cohesion: 0.14
Nodes (9): ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Persists one sample. Args: sample (TelemetrySample): The sample to store., Counts samples in range and returns count and base timestamp. Args: ts_from…, Yields samples inside a time range, oldest first. Args: ts_from (float): Range…, Deletes samples older than the retention window. Args: days (int): Retention…, TelemetryRepository (+1 more)

### Community 63 - "routers/zeros.py"
Cohesion: 0.14
Nodes (21): delete, activate_zero(), capture_zero(), delete_zero(), list_zeros(), get, post, ZeroDep (+13 more)

### Community 64 - "AngleConverter"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 65 - "Defects — detail"
Cohesion: 0.22
Nodes (8): D17 — The position bar cannot show the negative half of travel, D28 — MCU boot-time `mcu_log` notify lost to a startup race, D35 — Commanded speed and actual speed disagree by roughly 1.5-2x, D36 — Several tests construct their own `Database` and never close it, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D6 — App load time is sometimes slow, D7 — UI is not verified on small operator screens, Defects — detail

### Community 66 - "ServoBus"
Cohesion: 0.25
Nodes (13): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, ServoBus::ServoBus(), WriteByte (+5 more)

### Community 67 - "R-items — detail"
Cohesion: 0.17
Nodes (11): R10 — Zero service overhaul: calibration stays, "zeros" become saved points, R1 — Determine the real concurrent-operator ceiling, R3 — Confirm whether the Bridge could carry a frontend framework, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R5 — Metrics export and benchmarking output, R6 — Define "stable" by benchmark, not by adjective, R7 — Handover logistics depend on adapter delivery, R8 — Emergency stop (+3 more)

### Community 68 - "Ordering, rewritten 8 August 2026 — by session, with sizes"
Cohesion: 0.17
Nodes (12): Batch 1 — Desk work, no board — **DONE 8 August 2026**, Batch 2 — Make the machine diagnosable — **DONE 8 August 2026** (desk work), Batch 3 — The measurement session (board, supervised, one long run), Batch 4 — The two unbuilt MVP features, Batch 5 — The handover pack, Batch 6 — Mechanical, suits an executing agent, Not scheduled, Ordering, rewritten 8 August 2026 — by session, with sizes (+4 more)

### Community 69 - "ServoRepository"
Cohesion: 0.13
Nodes (8): Contract for reading and commanding the servo (real or simulated)., Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position., Configures the travel-range mode before normal operation. Args: multi_turn…, Configures the servo dead-zone width. Args: counts (int): Dead-zone width in…, Cuts or restores drive torque while sensors stay powered. Args: enabled (bool):…, Reads the torque-enable register directly. Returns: Optional[int]: Register…, ServoRepository

### Community 70 - "D2 — capture() can store a failed read as position 0"
Cohesion: 0.21
Nodes (13): Sample, Snapshot, Field order is a contract, Calibration refuses a reading the servo never gave, The six-step defect chain, Failures were never distinguishable from data, The stored datum is still 0, A reading now carries its own validity (+5 more)

### Community 71 - "Task: strip explanatory prose from sketch/src/"
Cohesion: 0.20
Nodes (9): A — Doxygen doc comments (`///` and `/** */` blocks), B — inline comments, C — relocate what is not already written down, Constraints, D — two comment classes that need special handling, found the hard way, Report back, Scope, Task: strip explanatory prose from sketch/src/ (+1 more)

### Community 72 - "DiagLog"
Cohesion: 0.27
Nodes (9): kLogRingCapacity, DiagLog, Drain, dropped_total, Init, lock_, Push, ring_ (+1 more)

### Community 73 - "TestExport"
Cohesion: 0.25
Nodes (3): A sample taken before any move has target_valid=0; one taken after an accepted…, Binary telemetry export contract. XLSX assembly is client-side (app.js) by…, TestExport

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
Cohesion: 0.22
Nodes (5): flaky(), FlakyServo, fixture, Wraps the real simulator but can be told to refuse the next torque…, Swaps the cached servo repository for one whose ack is controllable, for the…

### Community 78 - "START HERE — the session plan"
Cohesion: 0.25
Nodes (7): Not in these three sessions, Session 1, Batch 1 — DONE, 8 August 2026, Session 1, Batch 2 — DONE, 8 August 2026, Session 2 — The soak — IN PROGRESS, Session 3 — SSE first, then Batch 4, START HERE — the session plan, Suggested order — SUPERSEDED 8 August 2026

### Community 80 - "get_motion_service"
Cohesion: 0.18
Nodes (6): get_motion_service(), Returns the motion service. Returns: MotionService: The process-wide motion…, _events(), Returns recorded operator events. Args: backend: The backend fixture namespace.…, The overshoot leg commands PAST the requested angle - the operator must see…, isolated shares a byte with target_valid rather than widening the 20-byte…

### Community 81 - "Full typing with lowercase builtin generics"
Cohesion: 0.67
Nodes (3): C++ sketch-side standard (proposal), Optional[X] never X | None, Full typing with lowercase builtin generics

### Community 82 - "Layout divergence from the reference src/ tree"
Cohesion: 0.67
Nodes (3): Layout divergence from the reference src/ tree, T5 — Add design_diagrams/ with PlantUML, Repository layout

### Community 83 - "isolation_service.py"
Cohesion: 0.20
Nodes (7): AppStateRepository, ABC, Abstract persistence of small operator-intent flags that survive a reboot., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):…, Contract for a small persisted key-value store of operator intent., Motor isolation: operator intent and hardware reconciliation.

### Community 84 - "ServoStateResponse"
Cohesion: 0.20
Nodes (10): get_state(), get_torque_register(), get, Reads the servo torque-enable register directly. Args: servo (ServoRepository):…, Returns the full state snapshot for the client. Args: state (ServoStateStore):…, Full state snapshot for the client poller. Attributes: output_deg…, Builds the response from one coherent state view. Args: view (ServoStateView):…, ServoStateResponse (+2 more)

### Community 86 - "SpiRemap.cpp"
Cohesion: 0.39
Nodes (7): GPIO_TypeDef, PortFor(), SpiRemap, ApplyJspiMapping, kAlternateFunctionSpi2, ReleaseTopHeaderCopies, SetAlternateFunction

### Community 89 - "ZeroReference"
Cohesion: 0.07
Nodes (20): SQLite connection management and schema initialization., Immutable domain entities shared across layers., A saved baseline position. Attributes: id (Optional[int]): Database identifier…, ZeroReference, ABC, Abstract persistence of zero references., Persists a new zero reference. Args: zero (ZeroReference): Entity with id=None.…, Returns all zero references, newest first. Returns: list[ZeroReference]: All… (+12 more)

### Community 90 - "TestIsolationGate"
Cohesion: 0.25
Nodes (5): The two gates must not collapse into one reason code - an operator refused for…, Neither single-condition gate may fire alone here - an operator who clears one…, Motor isolation gates a move the same way the digital lock does., Unlike a lock change, isolating must take effect immediately even mid-move - it…, TestIsolationGate

### Community 100 - "MotionService"
Cohesion: 0.12
Nodes (11): MotionService, Stops the current move at the present position., Changes the digital lock, honoring the optional move guard. Args: locked…, Clears a tripped overload fault by re-commanding the position. Raises:…, Decides whether the anti-backlash approach applies. Args: start_deg (float):…, Runs the two-leg consistent-direction approach. Args: target_deg (float):…, Refuses targets the servo would silently clamp. Args: target_deg (float):…, Blocks until any active settle window elapses. (+3 more)

### Community 101 - "TelemetryService"
Cohesion: 0.14
Nodes (10): Samples until stopped, at the configured interval., Reads one coherent snapshot and persists it., Applies retention at the configured interval., Persists the full sensory input every sampler interval. Attributes: _telemetry…, Starts the background sampling thread., Stops the background sampling thread, if one was started., Packs telemetry samples in range into a compact binary byte stream. Args:…, TelemetryService (+2 more)

### Community 102 - "Review findings — Session 14 whole-app twin-review"
Cohesion: 0.22
Nodes (8): Backend — doc truth, Backend — `python/app/`, Docs — `docs/`, `CLAUDE.md`, `CONTEXT.md`, `CONVENTIONS.md`, `docs/adr/`, Firmware — doc truth, Firmware — `sketch/src/` (+ `sketch/sketch.ino`, `OnTarget.ino`), Frontend — doc truth, Frontend — `python/static/` (+ `style.css`), Review findings — Session 14 whole-app twin-review

### Community 127 - "TelemetrySample"
Cohesion: 0.21
Nodes (8): One persisted telemetry row. Attributes: timestamp (float): Unix timestamp of…, TelemetrySample, Persists one sample. Args: sample (TelemetrySample): The sample to store., Yields samples inside a time range, oldest first. Args: ts_from (float): Range…, TelemetryService: sampling, CSV export, retention timing., The sampler thread survives sampling failures., TestRetention, TestSamplerResilience

### Community 128 - "app.py"
Cohesion: 0.32
Nodes (5): FastAPI, FastAPI application assembly: routers and domain-error mapping., Maps domain exceptions to HTTP responses. Args: app (FastAPI): The FastAPI…, _register_error_handlers(), SSE stream for servo state, zeros and events.

### Community 129 - "check_file"
Cohesion: 0.32
Nodes (7): check_file(), main(), Path, Brace-balance check for sketch/src/ files the native suite can't compile.…, Removes // and /* */ comments and "..."/'...' literals. Args: text (str): Raw…, Returns the file's final brace depth (0 means balanced). Args: path (Path):…, strip_comments_and_strings()

### Community 130 - "_stream_generator"
Cohesion: 0.33
Nodes (7): get, StreamingResponse, Streams servo state, zeros, and events over SSE. Args: request (Request): The…, Generates SSE events for state, zeros and events. Args: request (Request): The…, stream(), _stream_generator(), Request

### Community 131 - "TestFailedReadsAreNotStored"
Cohesion: 0.40
Nodes (3): A stalled bus must leave a gap, not a row claiming position 0. Seven such rows…, The stored row must come from a single coherent read. The row used to be…, TestFailedReadsAreNotStored

### Community 132 - "get_database"
Cohesion: 0.33
Nodes (5): get_database(), Returns the shared database wrapper. Returns: Database: The process-wide…, _clear_all_caches(), Clears every cached provider so each test builds fresh singletons. Returns:…, The ordering itself is the fix - proven directly, not risked. An earlier…

### Community 133 - "get_telemetry_repository"
Cohesion: 0.20
Nodes (7): get_telemetry_repository(), Returns the telemetry repository. Returns: TelemetryRepository: The process-…, Telemetry sampler records a real movement profile., TestSamplerObservesMotion, The record must carry the cause, not just the fact. A live board run on 7…, Single-sample persistence., TestSampling

### Community 134 - "test_servo_routes.py"
Cohesion: 0.12
Nodes (11): Servo API routes: state, move, stop, lock, calibrate, recover., POST /api/v1/servo/recover., guard_move_to_lock surfaces as 409 reason=moving., The refusal carries the configured step, not a hardcoded one. A regression…, POST /stop and /lock., GET /api/v1/servo/state., TestMoveGuardOverHttp, TestRecover (+3 more)

### Community 135 - "BridgeApi.cpp"
Cohesion: 0.22
Nodes (19): bin_t, Ack(), BridgeApi, DrainDiagLog, FormatSnapshot, Register, FieldAt(), ForwardDiagLog() (+11 more)

### Community 136 - "TestLockGate"
Cohesion: 0.29
Nodes (4): Reads the settle state from the store. Args: backend: The backend fixture…, Digital lock gating and settle-wait., _settling(), TestLockGate

### Community 137 - "TestConversions"
Cohesion: 0.29
Nodes (3): D9 guard: output_deg must be DERIVED from servo_deg, not a second, independent…, Angle <-> counts math with the 44:30 ratio., TestConversions

### Community 139 - "decode_sign_magnitude"
Cohesion: 0.12
Nodes (11): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. Args: value (int):…, parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude, parametrize (+3 more)

### Community 140 - "OutOfTravelError"
Cohesion: 0.33
Nodes (4): OutOfTravelError, Raised when a target lies outside the servo's physical count range., The servo clamps silently outside counts 0..4095; we must not. Commanding past…, TestTravelLimits

### Community 141 - "test_motion_service.py"
Cohesion: 0.19
Nodes (13): LockedAndIsolatedError, LockedError, Raised when movement is refused for both reasons at once., Raised when movement is requested while the digital lock is engaged., motion(), fixture, MotionService: validation, gating, settle-wait, fine approach, recover., Fresh motion service. Returns: The service under test. (+5 more)

### Community 142 - "StepError"
Cohesion: 0.33
Nodes (4): Raised when a commanded angle violates the configured step size., StepError, Acceleration pass-through., TestAcceleration

### Community 153 - "Arduino UNO Q + Waveshare ST3215"
Cohesion: 0.11
Nodes (17): 1. This is not a normal Arduino, 2. The ST3215 servo, 3. Geometry — and the one law that matters, 4. The Ethernet-shield relay, 5. The Bridge contract, 6. Symptom → cause, 7. Deployment traps, 8. Working rules (+9 more)

### Community 170 - "SimulatedServoRepository"
Cohesion: 0.08
Nodes (13): Simulated servo: sprint-1 stand-in for the real serial bus., Stops motion at the current position., Records the range configuration. Args: multi_turn (bool): Enable multi-turn…, Configures the simulated dead-zone width. Args: counts (int): Dead-zone width…, Cuts or restores simulated drive torque. Args: enabled (bool): True to restore…, Returns the simulated torque state. Returns: int: 1 when torque is enabled, 0…, Thread-driven simulation of one ST3215-class servo. Attributes: _lock (Lock):…, Trips the simulated overload fault. (+5 more)

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
Cohesion: 0.14
Nodes (11): Event, EventService, In-memory ring buffer of structured events for the events endpoint., One operator-facing event. Attributes: timestamp (str): ISO timestamp. event…, Thread-safe fixed-size store of recent events. Attributes: _events…, Stores one event. Args: event (str): Dotted event identifier. message (str):…, Returns the newest events, newest first. Args: limit (int): Maximum number of…, EventService: recording, ordering, capacity, thread safety. (+3 more)

### Community 325 - "BridgeRelay"
Cohesion: 0.14
Nodes (10): BridgeRelay, socket, Linux half of the TCP relay; counterpart of EthernetRelay (sketch)., Streams FastAPI reply bytes back down to the sketch. Args: slot (int):…, Closes and forgets one mirrored connection. Args: slot (int): Connection slot…, Byte pump between the sketch's network clients and FastAPI. Attributes:…, Registers all Bridge callbacks., Handles a new network client reported by the sketch. Args: slot (int):… (+2 more)

### Community 344 - "test_bridge_relay.py"
Cohesion: 0.10
Nodes (12): echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Remaining failure branches., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Fresh registered relay. Returns: The relay under test., Bytes both directions., Backend unreachable and server-side close. (+4 more)

### Community 351 - "wait_until"
Cohesion: 0.08
Nodes (14): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Mirrors the real controller's un-isolate ordering: the target snaps to wherever…, configure_range records the travel-range mode., Absolute counts beyond one turn and below zero (contract)., Basic motion profile., Motor isolation: cutting torque must stop the shaft actually moving, not just… (+6 more)

### Community 397 - "McuLog"
Cohesion: 0.16
Nodes (9): McuLog, _now_iso(), Receives diagnostic events forwarded from the MCU side., Returns current UTC time as an ISO-8601 string with milliseconds. Returns: str:…, Bridge receiver that writes MCU-originated events to their own file.…, Registers the Bridge callback for MCU logs., Handles one diagnostic record forwarded from the MCU. Args: level (int):…, Appends one JSON line, rotating the file past size threshold. Args: line… (+1 more)

### Community 399 - "BridgeStub"
Cohesion: 0.07
Nodes (18): BridgeStub, Recording stub of the Arduino Bridge., Clears recorded state between tests. Returns: None., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent. (+10 more)

### Community 443 - "main"
Cohesion: 0.39
Nodes (7): collect_python(), collect_sketch(), main(), Path, Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 445 - "motion_service.py"
Cohesion: 0.25
Nodes (9): DomainError, IsolatedError, MovingError, Exception, Domain exceptions, mapped to HTTP responses by the application layer., Raised when a lock change is requested while a move is in progress., Raised when movement is requested while the motor is isolated., Base class for all domain-level errors. (+1 more)

### Community 447 - "The connection ceiling stays at 6 this batch"
Cohesion: 0.50
Nodes (3): Consequences, The connection ceiling stays at 6 this batch, Why

### Community 450 - "Motor isolation state survives a reboot"
Cohesion: 0.40
Nodes (4): Consequences, Motor isolation state survives a reboot, Status, Why

## Knowledge Gaps
- **330 isolated node(s):** `state`, `REFUSALS`, `EVENT_LABELS`, `DAY_SHEET_COLS`, `RAW_HEADERS` (+325 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **30 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_state_store()` connect `get_state_store` to `app.py`, `get_zero_service`, `ServoStateStore`, `deps.py`, `test_relay_path.py`, `get_telemetry_repository`, `TestLockGate`, `TestConversions`, `TestFailedReadIsNeverAPosition`, `OutOfTravelError`, `test_motion_service.py`, `TestTarget`, `get_settings`, `get_servo_repository`, `get_telemetry_service`, `InvalidReadingError`, `routers/servo.py`, `FlakyServo`, `get_motion_service`, `TelemetryService`, `TelemetrySample`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._
- **Why does `BridgeServoRepository` connect `BridgeServoRepository` to `TelemetrySnapshot`, `ServoRepository`, `deps.py`, `get_servo_repository`, `decode_sign_magnitude`, `BridgeStub`, `TestCommands`, `TestSnapshotDecoding`, `test_bridge_servo_repository.py`?**
  _High betweenness centrality (0.039) - this node is a cross-community bridge._
- **Why does `BridgeStub` connect `BridgeStub` to `BridgeServoRepository`, `get_servo_repository`, `test_relay_path.py`, `decode_sign_magnitude`, `test_mcu_log.py`, `TestCommands`, `test_bridge_relay.py`, `test_bridge_servo_repository.py`, `get_relay`, `TestSnapshotDecoding`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Are the 19 inferred relationships involving `ServoStateStore` (e.g. with `IsolationService` and `MotionService`) actually correct?**
  _`ServoStateStore` has 19 INFERRED edges - model-reasoned connections that need verification._
- **Are the 35 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 35 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `Database` (e.g. with `SqliteAppStateRepository` and `SqliteTelemetryRepository`) actually correct?**
  _`Database` has 12 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `REFUSALS`, `EVENT_LABELS` to the rest of the system?**
  _330 weakly-connected nodes found - possible documentation gaps or missing edges._