# Graph Report - servo_mvp  (2026-08-07)

## Corpus Check
- 110 files · ~42,264 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1364 nodes · 2294 edges · 127 communities (88 shown, 39 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 249 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `7549945d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- NetworkRelay
- deps.py
- ServoRepository
- app.js
- TestValidation
- ServoStateStore
- routers/servo.py
- ZeroReference
- test_zero_service.py
- get_state_store
- BridgeServoRepository
- README.md
- Tasks
- Database
- test_motion_service.py
- TelemetryService
- routers/zeros.py
- BridgeStub
- TEST
- BridgeRelay
- wait_until
- test_bridge_servo_repository.py
- get_events
- Conventions
- EventService
- decode_sign_magnitude
- SqliteZeroRepository
- Document reading flow (router)
- D2 — capture() can store a failed read as position 0
- SimulatedServoRepository
- test_bridge_relay.py
- Requirements captured but not yet designed
- LoggerStub
- TestDelete
- ServoBus
- The flows
- test_sqlite_zero_repository.py
- Travel window
- tests/conftest.py
- test_relay_path.py
- TestCrud
- TelemetrySnapshot
- TelemetryRepository
- App.cpp
- AngleConverter
- ServoController.cpp
- ServoSnapshot
- TestTravelWindow
- TestMove
- TinyTest.h
- D4 — Connection drops after a few commands
- Defects
- Current gap against the standard
- TelemetrySample
- ._active_counts
- SqliteTelemetryRepository
- ServoFaults
- ADR-0004 — Repository abstraction with a simulated backend
- main
- TestCommands
- export_csv
- e2e/conftest.py
- get_telemetry_service
- TestSettings
- test_pure_logic.cpp
- MoveCommand
- OnTarget.ino
- The relay and controller have no automated coverage
- get_telemetry_repository
- TestResilience
- Bench-verified hardware facts
- zero_service.py
- TestPumping
- test_logging_setup.py
- TestActive
- Dev And Test Dependencies
- TestDatum
- TestStopLock
- TestCalibrate
- TestBackendSelection
- TestInvalidFlagHonoured
- Full typing with lowercase builtin generics
- Layout divergence from the reference src/ tree
- test_servo_routes.py
- ReadSnapshot
- TestRecover
- test_telemetry_service.py
- adb push never deletes
- .activate
- _ensure_logger461
- _ensure_logger461
- Adopt Connections With accept(), Never available
- Detect Disconnects Before Accepting
- No Bricks Constraint
- One fact lives in exactly one file
- timestamp
- Git branching and commit message rules
- Grouped, parenthesised imports
- Trailing commas force vertical layout (ruff)
- D7 — UI not verified on small operator screens
- Arduino_UNO_Q_Complete_Field_Guide.md
- mvp_design_plan.md
- servo_diag_app.txt
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

## God Nodes (most connected - your core abstractions)
1. `ServoStateStore` - 43 edges
2. `get_state_store()` - 39 edges
3. `wait_until()` - 38 edges
4. `BridgeServoRepository` - 34 edges
5. `TelemetrySnapshot` - 32 edges
6. `TEST()` - 32 edges
7. `get_settings()` - 29 edges
8. `Database` - 29 edges
9. `BridgeStub` - 29 edges
10. `ZeroReference` - 27 edges

## Surprising Connections (you probably didn't know these)
- `Single-context documentation layout` --semantically_similar_to--> `Document reading flow (router)`  [INFERRED] [semantically similar]
  docs/agents/domain.md → CLAUDE.md
- `sshfs board mount as working copy` --semantically_similar_to--> `Development shortcut — sshfs mount of the board`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Apply SpiRemap twice` --semantically_similar_to--> `Confirm the Ethernet patch survived the first build`  [INFERRED] [semantically similar]
  sketch/README.md → README.md
- `Travel window` --conceptually_related_to--> `ADR-0003 — Travel window is +/-90 output degrees, multi-turn off`  [INFERRED]
  CONTEXT.md → docs/adr/0003-travel-window-plus-minus-90-output-degrees.md
- `Unreachable targets are refused, not clamped` --conceptually_related_to--> `Travel window`  [INFERRED]
  docs/AUDIT.md → CONTEXT.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **The datum-at-zero failure mode** — context_datum, context_travel_window, docs_audit_defect_chain, docs_backlog_d1_a_move_to_a_negative_angle_stops_at_0, docs_backlog_d2, docs_adr_0003_travel_window_plus_minus_90_output_degrees_decision, docs_project_state_linchpin [INFERRED 0.85]
- **Consequences of the air-gap constraint** — docs_adr_0005_air_gapped_by_default_development_decision, docs_adr_0002_no_frontend_framework_decision, readme_air_gapped_bundle, readme_core_version_pin, sketch_readme_tinytest_harness, docs_backlog_t2_package_the_air_gapped_bundle [EXTRACTED 1.00]
- **The MCU/Linux boundary contract** — context_bridge, docs_adr_0006_csv_bridge_payloads_decision, docs_adr_0006_csv_bridge_payloads_field_order_contract, readme_bridge_contract_checker, sketch_readme_bridge_payload_contract, docs_adr_0001_network_path_through_the_mcu_decision [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]

## Communities (127 total, 39 thin omitted)

### Community 0 - "NetworkRelay"
Cohesion: 0.07
Nodes (41): bin_t, GPIO_TypeDef, Ack(), BridgeApi, FormatSnapshot, Register, FieldAt(), HandleConfigureRange() (+33 more)

### Community 1 - "deps.py"
Cohesion: 0.09
Nodes (34): BaseSettings, FastAPI, create_app(), FastAPI application assembly: routers and domain-error mapping. Construction of…, Creates and configures the FastAPI application. Returns: The configured…, Maps domain exceptions to HTTP responses. Args: app: The FastAPI application.…, _register_error_handlers(), get_settings() (+26 more)

### Community 2 - "ServoRepository"
Cohesion: 0.05
Nodes (40): Exception, DomainError, LockedError, MovingError, OutOfTravelError, Domain exceptions, mapped to HTTP responses by the application layer., Raised when a lock change is requested while a move is in progress., Raised when a target lies outside the servo's physical count range. The servo… (+32 more)

### Community 3 - "app.js"
Cohesion: 0.17
Nodes (36): apiDelete(), apiGet(), apiPost(), asApiError(), askConfirm(), askText(), bind(), clearNotice() (+28 more)

### Community 4 - "TestValidation"
Cohesion: 0.40
Nodes (3): parametrize, Step-size validation., TestValidation

### Community 5 - "ServoStateStore"
Cohesion: 0.07
Nodes (25): get_servo_repository(), get_zero_repository(), Returns the servo repository chosen by use_hardware_servo. Simulated by default…, Returns the zero repository. Returns: The process-wide zero repository., Coherent snapshot of servo + lock + baseline, read atomically. Attributes:…, ServoStateView, Converts output speed to encoder counts per second. Args: speed_dps: Output…, Returns a coherent snapshot of servo, lock and baseline. Returns: The atomic… (+17 more)

### Community 6 - "routers/servo.py"
Cohesion: 0.11
Nodes (31): MotionDep, get_state(), post_lock(), post_move(), post_recover(), post_stop(), get, post (+23 more)

### Community 7 - "ZeroReference"
Cohesion: 0.10
Nodes (16): A saved baseline position. Attributes: id: Database id; None before…, ZeroReference, Contract for storing and selecting zero references., Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Deletes one zero reference. Args: zero_id: Database id. Returns: True when a…, Marks one zero active and clears the previous active flag. Args: zero_id:… (+8 more)

### Community 8 - "test_zero_service.py"
Cohesion: 0.10
Nodes (20): ActiveZeroError, DatumZeroError, InvalidReadingError, NotFoundError, Raised when a referenced entity does not exist., Raised when attempting to delete the active zero reference., Raised when attempting to delete the calibration datum zero., Raised when an operation needs a reading the servo did not supply. (+12 more)

### Community 9 - "get_state_store"
Cohesion: 0.10
Nodes (13): get_state_store(), get_zero_service(), Returns the atomic servo/lock/baseline state store. Returns: The process-wide…, Returns the zero service. Returns: The process-wide zero service., Cross-service integration flows (no HTTP): components working together., Zeros, state store and motion interacting., TestZeroLifecycleAcrossServices, The servo clamps silently outside counts 0..4095; we must not. Commanding past… (+5 more)

### Community 10 - "BridgeServoRepository"
Cohesion: 0.08
Nodes (18): BridgeServoRepository, Performs one real bus read. The caller must hold the lock. Returns: The…, Returns the absolute encoder position in counts. The value is ABSOLUTE MULTI-…, Starts a move toward an absolute counts target. A new position command also…, Stops motion at the current position. Returns: None., Configures the servo's dead-zone width. Args: counts: Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn:…, Invokes a Bridge function, converting failures into empty results. Args: name:… (+10 more)

### Community 11 - "README.md"
Cohesion: 0.07
Nodes (20): Consequences, The network path runs through the MCU, not the Linux side, Consequences, Considered and rejected, Plain HTML, CSS and JavaScript — no framework, no build step, Consequences, Travel window is ±90 output degrees, and multi-turn stays off, Consequences (+12 more)

### Community 12 - "Tasks"
Cohesion: 0.09
Nodes (25): Servo Control App Manifest, sshfs board mount as working copy, Abstract Database with concrete SqliteDatabase, Three-tier exception hierarchy, ADR-0002 — Plain HTML/CSS/JS, no framework, ADR-0005 — Develop as if already air-gapped, Native tests cover pure maths only, R7 — Handover logistics depend on adapter delivery (+17 more)

### Community 13 - "Database"
Cohesion: 0.15
Nodes (11): Connection, Database, Returns the shared SQLite connection. Returns: The open connection., Creates tables and indexes when missing. Returns: None., Adds columns introduced after a database was first created. Uses the ALTER-and-…, Owns the SQLite connection and serializes write access. SQLite permits…, Database: schema creation, migration of old schemas, row survival., Upgrading a database created before this change pack. (+3 more)

### Community 14 - "test_motion_service.py"
Cohesion: 0.12
Nodes (16): get_event_service(), get_motion_service(), Returns the motion service. Returns: The process-wide motion service., Returns the shared event buffer. Returns: The process-wide event service., _events(), motion(), fixture, MotionService: validation, gating, settle-wait, fine approach, recover. (+8 more)

### Community 15 - "TelemetryService"
Cohesion: 0.16
Nodes (9): Applies retention at the configured interval. Returns: None., Persists the full sensory input every sampler interval., Starts the background sampling thread. Returns: None., Streams a CSV of samples in the range, capped for the relay. Args: ts_from:…, Samples until the process ends, at the configured interval. Returns: None., Reads one coherent snapshot and persists it. Returns: None., TelemetryService, The sampler thread survives sampling failures. (+1 more)

### Community 16 - "routers/zeros.py"
Cohesion: 0.12
Nodes (24): delete, post_calibrate(), ZeroDep, Captures the current physical position as the calibration datum. Call when the…, activate_zero(), capture_zero(), delete_zero(), list_zeros() (+16 more)

### Community 17 - "BridgeStub"
Cohesion: 0.10
Nodes (13): BridgeStub, Recording stub of the Arduino Bridge., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent., The health endpoint names the servo backend in use. (+5 more)

### Community 18 - "TEST"
Cohesion: 0.09
Nodes (22): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, range_a_datum_at_zero_strands_the_negative_half (+14 more)

### Community 19 - "BridgeRelay"
Cohesion: 0.16
Nodes (9): BridgeRelay, Handles the network client going away. Args: slot: Connection slot. Returns:…, Streams FastAPI reply bytes back down to the sketch. Args: slot: Connection…, Closes and forgets one mirrored connection. Args: slot: Connection slot.…, Byte pump between the sketch's network clients and FastAPI., Registers all Bridge callbacks. Call once at startup. On a machine without the…, Handles a new network client reported by the sketch. Args: slot: Connection…, Forwards client bytes to FastAPI. Args: slot: Connection slot. data: Raw bytes… (+1 more)

### Community 20 - "wait_until"
Cohesion: 0.08
Nodes (14): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), E2E: a full operator session against the live server over real HTTP., Boot -> calibrate -> move -> lock -> zeros -> telemetry -> fault., TestOperatorSession, SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Absolute counts beyond one turn and below zero (contract)., Basic motion profile. (+6 more)

### Community 21 - "test_bridge_servo_repository.py"
Cohesion: 0.13
Nodes (11): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, A fake bridge returning a healthy snapshot. Returns: The fake., Repository wired to the fake bridge. Returns: The repository under test. (+3 more)

### Community 22 - "get_events"
Cohesion: 0.12
Nodes (19): EventDep, ge, le, get_events(), get_health(), get, Query, Returns service health including the MCU status line. Args: settings: Injected… (+11 more)

### Community 23 - "Conventions"
Cohesion: 0.11
Nodes (18): Architecture, Booleans and conditions, C++ (sketch side), Class docstrings carry `Attributes:`, Control flow, Conventions, Current gap against this standard, Database access (+10 more)

### Community 24 - "EventService"
Cohesion: 0.15
Nodes (10): Event, EventService, In-memory ring buffer of structured events for the events endpoint. Kept…, One operator-facing event. Attributes: timestamp: ISO timestamp. event: Dotted…, Thread-safe fixed-size store of recent events., Stores one event. Args: event: Dotted event identifier. message: Human-readable…, Returns the newest events, newest first. Args: limit: Maximum number of events…, EventService: recording, ordering, capacity, thread safety. (+2 more)

### Community 25 - "decode_sign_magnitude"
Cohesion: 0.12
Nodes (11): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. STS position fields…, parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude, parametrize (+3 more)

### Community 26 - "SqliteZeroRepository"
Cohesion: 0.13
Nodes (10): Stores zero references in the zeros table., Creates or updates THE calibration datum zero. Args: raw_counts: Captured raw…, Maps a database row to the entity. Args: row: SQLite row. Returns: The mapped…, Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Deletes one zero reference. Args: zero_id: Database id. Returns: True when a…, Marks one zero active and clears the previous active flag. Args: zero_id:… (+2 more)

### Community 27 - "Document reading flow (router)"
Cohesion: 0.15
Nodes (14): Document reading flow (router), Graphify extraction gaps (.ino and .css), Graphify-first navigation rule, Three verification commands (186 / 164 / agree), How to work on this repo, Project ubiquitous language (glossary), Naming rules drawn from the glossary, A green suite proves only the simulated path (+6 more)

### Community 28 - "D2 — capture() can store a failed read as position 0"
Cohesion: 0.16
Nodes (18): Sample, Snapshot, ADR-0003 — Travel window is +/-90 output degrees, multi-turn off, No modulus-360 wrapping anywhere, Field order is a contract, ADR-0007 — Moves permitted while position is unverified, Remote site makes refusal less safe, not more, Calibration refuses a reading the servo never gave (+10 more)

### Community 29 - "SimulatedServoRepository"
Cohesion: 0.12
Nodes (9): Records the range configuration. The simulator already models unbounded signed…, Configures the simulated dead-zone width. Args: counts: Dead-zone width in…, Trips the simulated overload fault (testing/commissioning aid). Returns: None., Advances position toward the target until the process ends. Returns: None., Thread-driven simulation of one ST3215-class servo., Returns the absolute encoder position in counts. Returns: Current raw counts., Starts a move toward an absolute counts target. Clears a simulated overload…, Stops motion at the current position. Returns: None. (+1 more)

### Community 30 - "test_bridge_relay.py"
Cohesion: 0.09
Nodes (14): echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Remaining failure branches., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Behavior when the board runtime is absent (dev PC)., Fresh registered relay. Returns: The relay under test., Bridge callback registration. (+6 more)

### Community 31 - "Requirements captured but not yet designed"
Cohesion: 0.21
Nodes (13): Emergency stop, Lock, Mechanical restraint, Motor isolation, The relay-capacity argument is unverified, Candidate ADR — how isolation, Lock and e-stop compose, R2 — Motor isolation: cut drive power, keep sensors alive, R3 — Confirm whether the Bridge could carry a frontend framework (+5 more)

### Community 32 - "LoggerStub"
Cohesion: 0.20
Nodes (4): LoggerStub, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 33 - "TestDelete"
Cohesion: 0.13
Nodes (6): Zeros API routes: list, capture, activate, delete + error mapping., DELETE /{id} and its protections., POST /capture and GET list., TestActivate, TestCaptureList, TestDelete

### Community 34 - "ServoBus"
Cohesion: 0.29
Nodes (11): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, WriteByte, WriteEepromByte (+3 more)

### Community 35 - "The flows"
Cohesion: 0.12
Nodes (16): 1. superpowers — the methodology layer, 2. agentic-awesome-skills — the catalogue, 3. Arduino-Agent — the hardware seam, 4. IoT-SkillsBench — the evidence, and the argument for writing our own, Every flow ends the same way, Sources, The flows, Tooling to install first (+8 more)

### Community 36 - "test_sqlite_zero_repository.py"
Cohesion: 0.25
Nodes (6): SQLite connection management and schema initialization., SQLite implementation of the zero-reference repository., fixture, SqliteZeroRepository: CRUD, active selection, datum upsert., Zero repository over a fresh database. Returns: The repository under test., repo()

### Community 37 - "Travel window"
Cohesion: 0.19
Nodes (13): Baseline, Count, Datum, Output degree, Travel window, Zero reference, The 44:30 belt reduction is the whole point, Four easily conflated position terms (+5 more)

### Community 38 - "tests/conftest.py"
Cohesion: 0.14
Nodes (14): AppStub, backend(), _clear_all_caches(), client(), fixture, Shared test configuration: stubs, environment, and fixtures. Runs entirely on a…, Clears every cached provider so each test builds fresh singletons. Returns:…, Fresh backend context: new DB, cleared caches, recording stubs. Yields: A… (+6 more)

### Community 39 - "test_relay_path.py"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 40 - "TestCrud"
Cohesion: 0.32
Nodes (4): Builds an unsaved zero entity. Args: name: Zero name. counts: Raw counts.…, Create, read, delete., TestCrud, _zero()

### Community 41 - "TelemetrySnapshot"
Cohesion: 0.18
Nodes (7): Instantaneous sensory readout from the servo layer. Attributes: raw_counts:…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: Position, motion flag…, Simulated servo: sprint-1 stand-in for the real serial bus. Models raw encoder…, Returns position, motion flag and mock telemetry. Returns: The instantaneous…, Calibrating on a dead bus must refuse, not store a zero., TestInvalidReadingSurfaced

### Community 42 - "TelemetryRepository"
Cohesion: 0.18
Nodes (7): ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Persists one sample. Args: sample: The sample to store. Returns: None., Yields samples inside a time range, oldest first. Args: ts_from: Range start,…, Deletes samples older than the retention window. Args: days: Retention in days.…, TelemetryRepository

### Community 43 - "App.cpp"
Cohesion: 0.24
Nodes (3): App, Begin, Tick

### Community 44 - "AngleConverter"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 45 - "ServoController.cpp"
Cohesion: 0.33
Nodes (12): BridgeApi::BridgeApi(), ClampAmplification(), ClampDeadband(), ServoController, Begin, CentreHere, ClearFault, ConfigureRange (+4 more)

### Community 46 - "ServoSnapshot"
Cohesion: 0.20
Nodes (10): ServoSnapshot, current_a, faults, load_duty, moving, raw_counts, temperature_c, torque_kgcm (+2 more)

### Community 49 - "TinyTest.h"
Cohesion: 0.22
Nodes (7): main(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 50 - "D4 — Connection drops after a few commands"
Cohesion: 0.13
Nodes (18): Bridge, Fault, Relay, Slot, Pure-logic C++ classes stay header-only and Arduino-free, ADR-0001 — Network path runs through the MCU, kMaxRelaySockets = 6 is the only connection ceiling, ADR-0006 — Bridge payloads are CSV strings (+10 more)

### Community 51 - "Defects"
Cohesion: 0.18
Nodes (10): Open work lives only in docs/BACKLOG.md, Backlog, D2 — `capture()` can store a failed read as position 0, D4 — Connection drops after a few commands; requires a page refresh, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D7 — UI is not verified on small operator screens, D8 — `.env` must be created before the first run of this version, Defects (+2 more)

### Community 52 - "Current gap against the standard"
Cohesion: 0.22
Nodes (9): Class docstrings carry Attributes:, Control-flow prohibitions, Explicit boolean checks, no implicit truthiness, Current gap against the standard, Google docstrings with types in Args/Returns, Drain loops are exempt from the no-while rule, T1 — Apply CONVENTIONS.md across the codebase, Drain with while, never if (+1 more)

### Community 53 - "TelemetrySample"
Cohesion: 0.29
Nodes (5): One persisted telemetry row. Attributes: timestamp: Unix timestamp of the…, TelemetrySample, Persists one sample. Args: sample: The sample to store. Returns: None., Yields samples inside a time range, oldest first. Args: ts_from: Range start,…, TestRetention

### Community 54 - "._active_counts"
Cohesion: 0.14
Nodes (7): Returns the output angles reachable from the current baseline. The servo…, Reports whether a target maps inside the servo's count range. Args: output_deg:…, Converts an output angle to absolute encoder counts. Args: output_deg: Output…, Returns the current output angle relative to the active zero. Returns: Output…, Returns the current absolute encoder position in counts. Returns: Current raw…, Returns the active baseline in raw counts. With no zero captured the baseline…, Converts raw counts to output degrees against the active zero. Args:…

### Community 55 - "SqliteTelemetryRepository"
Cohesion: 0.13
Nodes (13): SQLite implementation of the telemetry repository., Stores telemetry samples in the telemetry table., Deletes samples older than the retention window. Args: days: Retention in days.…, SqliteTelemetryRepository, fixture, SqliteTelemetryRepository: add, ranged query, purge, fault columns., Telemetry repository over a fresh database. Returns: The repository under test., Builds a sample. Args: timestamp: Unix timestamp. overload: Overload flag… (+5 more)

### Community 56 - "ServoFaults"
Cohesion: 0.25
Nodes (7): ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage

### Community 57 - "ADR-0004 — Repository abstraction with a simulated backend"
Cohesion: 0.29
Nodes (8): Missing python/.env silently runs the simulator, Backend (servo backend), Thin routers, services hold logic, abstract repositories only, ADR-0004 — Repository abstraction with a simulated backend, D8 — .env must be created before the first run, cp .env.board .env — the only manual deploy step, run_dev.py — dev-PC entrypoint, Going live is a configuration flag

### Community 58 - "main"
Cohesion: 0.39
Nodes (7): Path, collect_python(), collect_sketch(), main(), Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 60 - "export_csv"
Cohesion: 0.29
Nodes (7): alias, export_csv(), get, Query, Streams telemetry samples in a time range as CSV. Args: telemetry: Injected…, StreamingResponse, TelemetryDep

### Community 61 - "e2e/conftest.py"
Cohesion: 0.33
Nodes (6): _free_port(), live_backend(), fixture, E2E fixtures: the backend booted the way main.py boots it. A real uvicorn…, Finds a free localhost TCP port. Returns: An ephemeral port number currently…, Boots the full backend on a live socket, mirroring main.py. Yields: Namespace…

### Community 62 - "get_telemetry_service"
Cohesion: 0.18
Nodes (7): get_telemetry_service(), Returns the telemetry service. Returns: The process-wide telemetry service., Telemetry sampler records a real movement profile., TestSamplerObservesMotion, Telemetry API route: CSV export., GET /api/v1/telemetry/export., TestExport

### Community 63 - "TestSettings"
Cohesion: 0.29
Nodes (3): Settings: defaults, environment override, caching., Behavior of the pydantic-settings configuration., TestSettings

### Community 65 - "MoveCommand"
Cohesion: 0.29
Nodes (4): MoveCommand, acceleration, speed_counts_per_second, target_counts

### Community 66 - "OnTarget.ino"
Cohesion: 0.48
Nodes (5): Check(), CheckNear(), MoveTo(), setup(), WaitSettled()

### Community 67 - "The relay and controller have no automated coverage"
Cohesion: 0.20
Nodes (10): Logging mandatory in hardware and network files, The relay and controller have no automated coverage, D3 — The C++ side has no logging, D5 — Log output is connect/disconnect noise, R5 — Metrics export and benchmarking output, R6 — Define 'stable' by benchmark, not by adjective, Working relay reference implementation, Known gaps, stated honestly (+2 more)

### Community 68 - "get_telemetry_repository"
Cohesion: 0.25
Nodes (6): get_telemetry_repository(), Returns the telemetry repository. Returns: The process-wide telemetry…, Overload flag reaches persisted telemetry., TestFaultVisibleInSampledHistory, Single-sample persistence., TestSampling

### Community 70 - "Bench-verified hardware facts"
Cohesion: 0.50
Nodes (5): servo_truth.md — ST3215 register map, Bench-verified hardware facts, Use SMS_STS, Never SCSCL, Confirm the Ethernet patch survived the first build, Apply SpiRemap twice

### Community 71 - "zero_service.py"
Cohesion: 0.33
Nodes (4): Immutable domain entities shared across layers., ABC, Abstract persistence of zero references., Zero references: capture, selection and the active baseline.

### Community 73 - "test_logging_setup.py"
Cohesion: 0.40
Nodes (3): Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 75 - "Dev And Test Dependencies"
Cohesion: 0.50
Nodes (4): Dev And Test Dependencies, Runtime Dependencies, ARM64 Platform Wheels Required, Offline Wheelhouse

### Community 81 - "Full typing with lowercase builtin generics"
Cohesion: 0.67
Nodes (3): C++ sketch-side standard (proposal), Optional[X] never X | None, Full typing with lowercase builtin generics

### Community 82 - "Layout divergence from the reference src/ tree"
Cohesion: 0.67
Nodes (3): Layout divergence from the reference src/ tree, T5 — Add design_diagrams/ with PlantUML, Repository layout

### Community 83 - "test_servo_routes.py"
Cohesion: 0.18
Nodes (7): Servo API routes: state, move, stop, lock, calibrate, recover., guard_move_to_lock surfaces as 409 reason=moving., An unreachable target must be refused, not silently clamped., GET /api/v1/servo/state., TestMoveGuardOverHttp, TestOutOfTravelSurfaced, TestState

### Community 84 - "ReadSnapshot"
Cohesion: 0.50
Nodes (3): ServoBus::ServoBus(), SMS_STS, ReadSnapshot

### Community 86 - "test_telemetry_service.py"
Cohesion: 0.22
Nodes (5): fixture, TelemetryService: sampling, CSV export, retention timing., Fresh telemetry service (sampler NOT started). Returns: The service under test., service(), TestExport

## Knowledge Gaps
- **118 isolated node(s):** `state`, `EVENT_LABELS`, `counts_per_servo_deg_`, `servo_deg_per_output_deg_`, `cs_pin_` (+113 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `BridgeServoRepository` connect `BridgeServoRepository` to `deps.py`, `ServoRepository`, `ServoStateStore`, `TestResilience`, `TelemetrySnapshot`, `TestBackendSelection`, `TestInvalidFlagHonoured`, `test_bridge_servo_repository.py`, `decode_sign_magnitude`, `TestCommands`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Why does `TelemetrySnapshot` connect `TelemetrySnapshot` to `ServoRepository`, `ServoStateStore`, `zero_service.py`, `test_zero_service.py`, `BridgeServoRepository`, `TestStopLock`, `TestCalibrate`, `TestTravelWindow`, `TestMove`, `test_servo_routes.py`, `TestRecover`, `SimulatedServoRepository`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `ServoStateStore` connect `ServoStateStore` to `deps.py`, `ServoRepository`, `routers/servo.py`, `ZeroReference`, `zero_service.py`, `TelemetrySnapshot`, `get_state_store`, `TelemetryRepository`, `TelemetryService`, `._active_counts`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `ServoStateStore` (e.g. with `MotionService` and `ServoStateView`) actually correct?**
  _`ServoStateStore` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `BridgeServoRepository` (e.g. with `TelemetrySnapshot` and `ServoRepository`) actually correct?**
  _`BridgeServoRepository` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 17 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `EVENT_LABELS`, `counts_per_servo_deg_` to the rest of the system?**
  _118 weakly-connected nodes found - possible documentation gaps or missing edges._