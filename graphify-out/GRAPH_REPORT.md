# Graph Report - .  (2026-08-07)

## Corpus Check
- Corpus is ~34,884 words - fits in a single context window. You may not need a graph.

## Summary
- 1213 nodes · 2147 edges · 100 communities (81 shown, 19 thin omitted)
- Extraction: 90% EXTRACTED · 10% INFERRED · 0% AMBIGUOUS · INFERRED: 220 edges (avg confidence: 0.58)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Dependency Injection Providers
- FastAPI Application Assembly
- Motion Service And Settings
- Bridge API (MCU Side)
- Domain Error Types
- Web UI Client Script
- Servo HTTP Routes
- Domain Entities And Repository Seam
- Zeros HTTP Routes
- Zero Reference Contract
- Bridge Stub And System Route Tests
- Angle And Range Native Tests
- Domain Exception Hierarchy
- SQLite Zero Repository
- Bridge Relay Tests
- SQLite Database Layer
- End-To-End Operator Tests
- System Health And Events Routes
- Simulated Servo Repository
- Relay Connection Mirroring
- Event Service
- Shared Test Fixtures
- Air-Gap Deployment Constraints
- Bridge Servo Repository Tests
- Telemetry Service Wiring
- Telemetry Sampler And Retention
- Logger Stub
- Zeros Route Tests
- Failure-Visibility Contract
- Telemetry Sample Entity
- Bridge Servo Repository
- Servo State Store Geometry
- Bench-Measured Servo Geometry
- Telemetry Snapshot
- Relay Path E2E Tests
- Zero Repository Tests
- ServoBus Serial Driver
- Hardware Bus Facts
- Servo Route Tests
- Sketch Entrypoint And App
- AngleConverter (MCU)
- ServoController (MCU)
- Project History And Known Gaps
- Telemetry Repository Contract
- TinyTest Harness
- Bridge Read Path
- Bridge Command Path
- Fault Bit Tests
- Zero Service Tests
- ServoSnapshot Struct
- Telemetry CSV Export
- SpiRemap
- Fault Persistence Tests
- Sign-Magnitude Decoding
- Move Endpoint Tests
- Telemetry Persistence Tests
- ServoFaults Decoder
- Bridge Contract Checker
- SQLite Telemetry Repository
- Bridge Command Payload Tests
- Agent Skills And Doc Conventions
- UI And Travel-Range Decisions
- Settings Tests
- AngleMath And SignMagnitude Headers
- Servo Register Definitions
- On-Target Test Sketch
- Fault Display And Theme
- Travel Window Tests
- Relay Error Path Tests
- Bus Resilience Tests
- Zero Activation Rule Tests
- Database Schema Migration
- Snapshot Decoding Tests
- Logging Setup Tests
- Range Configuration Tests
- Calibration Datum Upsert Tests
- Test Strategy Rationale
- Calibrate Endpoint Tests
- Backend Selection Tests
- Overload Fault Tests
- SMS_STS Bus Binding
- SQLite Connection
- Move And Lock Guard Tests
- State Endpoint Tests
- Buffer Draining Rules
- Console Choice Rationale

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
- `check_bridge_contract.py` --semantically_similar_to--> `Failures Never Distinguishable From Data`  [INFERRED] [semantically similar]
  README.md → docs/AUDIT.md
- `.env.board Copy Is The Only Manual Step` --semantically_similar_to--> `Failures Never Distinguishable From Data`  [INFERRED] [semantically similar]
  README.md → docs/AUDIT.md
- `Read The Working Reference Before Rewriting` --semantically_similar_to--> `Rewriting Instead Of Porting Reintroduced Solved Bugs`  [INFERRED] [semantically similar]
  CONTEXT.md → sketch/src/RELAY_NOTES.md
- `kRelayChunkBytes Must Match relay_chunk_bytes` --conceptually_related_to--> `check_bridge_contract.py`  [INFERRED]
  sketch/src/RELAY_NOTES.md → README.md
- `TinyTest.h Harness` --rationale_for--> `Air-Gapped Deployment`  [EXTRACTED]
  sketch/README.md → CONTEXT.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Failed Read Becomes A Calibration Datum** — docs_audit_bridge_serialisation_rlock, docs_audit_telemetrysnapshot_valid, docs_audit_invalidreadingerror, docs_audit_datum_at_zero_strands_negative_half, docs_audit_silent_clamping, docs_audit_outoftravelerror [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]
- **Air-Gap Constraint Set** — context_air_gapped_deployment, context_no_framework, app_no_bricks, libraries_readme_vendored_libraries, python_wheelhouse_readme_offline_wheels, sketch_readme_tinytest, readme_core_version_pin [EXTRACTED 1.00]

## Communities (100 total, 19 thin omitted)

### Community 0 - "Dependency Injection Providers"
Cohesion: 0.06
Nodes (33): get_servo_repository(), get_state_store(), get_zero_repository(), get_zero_service(), Returns the atomic servo/lock/baseline state store. Returns: The process-wide…, Returns the zero service. Returns: The process-wide zero service., Returns the servo repository chosen by use_hardware_servo. Simulated by default…, Returns the zero repository. Returns: The process-wide zero repository. (+25 more)

### Community 1 - "FastAPI Application Assembly"
Cohesion: 0.08
Nodes (38): FastAPI, create_app(), FastAPI application assembly: routers and domain-error mapping. Construction of…, Creates and configures the FastAPI application. Returns: The configured…, Maps domain exceptions to HTTP responses. Args: app: The FastAPI application.…, _register_error_handlers(), get_settings(), Typed application settings loaded from the environment / .env file. (+30 more)

### Community 2 - "Motion Service And Settings"
Cohesion: 0.05
Nodes (26): BaseSettings, Backend configuration, overridable via environment or .env. Attributes:…, Settings, Servo endpoints: state, move, stop, lock., MotionService, Movement orchestration: lock gate, settle-wait, angle math, commands,…, Clears a tripped overload fault by re-commanding the position. Hardware…, Decides whether the anti-backlash approach applies. Args: start_deg: Current… (+18 more)

### Community 3 - "Bridge API (MCU Side)"
Cohesion: 0.08
Nodes (35): bin_t, Ack(), BridgeApi, BridgeApi::BridgeApi(), FormatSnapshot, Register, FieldAt(), HandleConfigureRange() (+27 more)

### Community 4 - "Domain Error Types"
Cohesion: 0.08
Nodes (29): LockedError, MovingError, OutOfTravelError, Raised when a lock change is requested while a move is in progress., Raised when a target lies outside the servo's physical count range. The servo…, Raised when a commanded angle violates the configured step size., Raised when movement is requested while the digital lock is engaged., StepError (+21 more)

### Community 5 - "Web UI Client Script"
Cohesion: 0.17
Nodes (36): apiDelete(), apiGet(), apiPost(), asApiError(), askConfirm(), askText(), bind(), clearNotice() (+28 more)

### Community 6 - "Servo HTTP Routes"
Cohesion: 0.09
Nodes (30): MotionDep, get_state(), post_lock(), post_move(), post_recover(), post_stop(), get, post (+22 more)

### Community 7 - "Domain Entities And Repository Seam"
Cohesion: 0.10
Nodes (16): Immutable domain entities shared across layers., Coherent snapshot of servo + lock + baseline, read atomically. Attributes:…, ServoStateView, ABC, Abstract servo access: the seam between simulation and hardware., Returns the absolute encoder position in counts (multi-turn). Contract: the…, Starts a move toward an absolute counts target. A new position command also…, Stops motion at the current position. Returns: None. (+8 more)

### Community 8 - "Zeros HTTP Routes"
Cohesion: 0.11
Nodes (23): delete, post_calibrate(), ZeroDep, Captures the current physical position as the calibration datum. Call when the…, activate_zero(), capture_zero(), delete_zero(), list_zeros() (+15 more)

### Community 9 - "Zero Reference Contract"
Cohesion: 0.11
Nodes (14): A saved baseline position. Attributes: id: Database id; None before…, ZeroReference, ABC, Contract for storing and selecting zero references., Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Deletes one zero reference. Args: zero_id: Database id. Returns: True when a… (+6 more)

### Community 10 - "Bridge Stub And System Route Tests"
Cohesion: 0.10
Nodes (13): BridgeStub, Recording stub of the Arduino Bridge., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent., The health endpoint names the servo backend in use. (+5 more)

### Community 11 - "Angle And Range Native Tests"
Cohesion: 0.09
Nodes (22): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, range_a_datum_at_zero_strands_the_negative_half (+14 more)

### Community 12 - "Domain Exception Hierarchy"
Cohesion: 0.14
Nodes (17): Exception, ActiveZeroError, DatumZeroError, DomainError, InvalidReadingError, NotFoundError, Domain exceptions, mapped to HTTP responses by the application layer., Raised when a referenced entity does not exist. (+9 more)

### Community 13 - "SQLite Zero Repository"
Cohesion: 0.11
Nodes (13): Stores zero references in the zeros table., Creates or updates THE calibration datum zero. Args: raw_counts: Captured raw…, Maps a database row to the entity. Args: row: SQLite row. Returns: The mapped…, Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Deletes one zero reference. Args: zero_id: Database id. Returns: True when a…, Marks one zero active and clears the previous active flag. Args: zero_id:… (+5 more)

### Community 14 - "Bridge Relay Tests"
Cohesion: 0.10
Nodes (14): echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Behavior when the board runtime is absent (dev PC)., Fresh registered relay. Returns: The relay under test., Bridge callback registration., Bytes both directions. (+6 more)

### Community 15 - "SQLite Database Layer"
Cohesion: 0.15
Nodes (12): Database, SQLite connection management and schema initialization., Owns the SQLite connection and serializes write access. SQLite permits…, SQLite implementation of the telemetry repository., SQLite implementation of the zero-reference repository., Database: schema creation, migration of old schemas, row survival., Upgrading a database created before this change pack., Fresh-database schema. (+4 more)

### Community 16 - "End-To-End Operator Tests"
Cohesion: 0.13
Nodes (11): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), E2E: a full operator session against the live server over real HTTP., Boot -> calibrate -> move -> lock -> zeros -> telemetry -> fault., TestOperatorSession, SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Absolute counts beyond one turn and below zero (contract)., Basic motion profile. (+3 more)

### Community 17 - "System Health And Events Routes"
Cohesion: 0.12
Nodes (19): EventDep, ge, le, get_events(), get_health(), get, Query, Returns service health including the MCU status line. Args: settings: Injected… (+11 more)

### Community 18 - "Simulated Servo Repository"
Cohesion: 0.11
Nodes (10): Simulated servo: sprint-1 stand-in for the real serial bus. Models raw encoder…, Records the range configuration. The simulator already models unbounded signed…, Configures the simulated dead-zone width. Args: counts: Dead-zone width in…, Trips the simulated overload fault (testing/commissioning aid). Returns: None., Advances position toward the target until the process ends. Returns: None., Thread-driven simulation of one ST3215-class servo., Returns the absolute encoder position in counts. Returns: Current raw counts., Starts a move toward an absolute counts target. Clears a simulated overload… (+2 more)

### Community 19 - "Relay Connection Mirroring"
Cohesion: 0.12
Nodes (12): Handles the network client going away. Args: slot: Connection slot. Returns:…, Streams FastAPI reply bytes back down to the sketch. Args: slot: Connection…, Closes and forgets one mirrored connection. Args: slot: Connection slot.…, Handles a new network client reported by the sketch. Args: slot: Connection…, Forwards client bytes to FastAPI. Args: slot: Connection slot. data: Raw bytes…, _free_port(), live_backend(), fixture (+4 more)

### Community 20 - "Event Service"
Cohesion: 0.16
Nodes (9): Event, EventService, One operator-facing event. Attributes: timestamp: ISO timestamp. event: Dotted…, Thread-safe fixed-size store of recent events., Stores one event. Args: event: Dotted event identifier. message: Human-readable…, Returns the newest events, newest first. Args: limit: Maximum number of events…, EventService: recording, ordering, capacity, thread safety., Behavior of the operator-event ring buffer. (+1 more)

### Community 21 - "Shared Test Fixtures"
Cohesion: 0.14
Nodes (14): AppStub, backend(), _clear_all_caches(), client(), fixture, Shared test configuration: stubs, environment, and fixtures. Runs entirely on a…, Clears every cached provider so each test builds fresh singletons. Returns:…, Fresh backend context: new DB, cleared caches, recording stubs. Yields: A… (+6 more)

### Community 22 - "Air-Gap Deployment Constraints"
Cohesion: 0.13
Nodes (16): FastAPI Serves The Static UI, No Bricks Constraint, Servo Control App Manifest, Air-Gapped Deployment, IPAddress Cast Patch For Ethernet 2.0.2, Vendored Arduino Libraries, Dev And Test Dependencies, Runtime Dependencies (+8 more)

### Community 23 - "Bridge Servo Repository Tests"
Cohesion: 0.14
Nodes (11): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, Field 0 of the snapshot payload is the sketch saying 'no answer'., A fake bridge returning a healthy snapshot. Returns: The fake. (+3 more)

### Community 24 - "Telemetry Service Wiring"
Cohesion: 0.14
Nodes (10): get_telemetry_service(), Returns the telemetry service. Returns: The process-wide telemetry service., Telemetry sampler records a real movement profile., TestSamplerObservesMotion, Telemetry API route: CSV export., GET /api/v1/telemetry/export., TestExport, fixture (+2 more)

### Community 25 - "Telemetry Sampler And Retention"
Cohesion: 0.16
Nodes (9): Applies retention at the configured interval. Returns: None., Persists the full sensory input every sampler interval., Starts the background sampling thread. Returns: None., Streams a CSV of samples in the range, capped for the relay. Args: ts_from:…, Samples until the process ends, at the configured interval. Returns: None., Reads one coherent snapshot and persists it. Returns: None., TelemetryService, The sampler thread survives sampling failures. (+1 more)

### Community 26 - "Logger Stub"
Cohesion: 0.20
Nodes (4): LoggerStub, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 27 - "Zeros Route Tests"
Cohesion: 0.13
Nodes (6): Zeros API routes: list, capture, activate, delete + error mapping., DELETE /{id} and its protections., POST /capture and GET list., TestActivate, TestCaptureList, TestDelete

### Community 28 - "Failure-Visibility Contract"
Cohesion: 0.19
Nodes (14): Failures Never Distinguishable From Data, TelemetrySnapshot.valid, Confirm Which Backend Is Live, BridgeServoRepository, check_bridge_contract.py, .env.board Copy Is The Only Manual Step, Repository Abstraction Swap, run_dev.py Dev-PC Entrypoint (+6 more)

### Community 29 - "Telemetry Sample Entity"
Cohesion: 0.18
Nodes (7): One persisted telemetry row. Attributes: timestamp: Unix timestamp of the…, TelemetrySample, Persists one sample. Args: sample: The sample to store. Returns: None., Yields samples inside a time range, oldest first. Args: ts_from: Range start,…, TelemetryService: sampling, CSV export, retention timing., TestExport, TestRetention

### Community 30 - "Bridge Servo Repository"
Cohesion: 0.20
Nodes (8): BridgeServoRepository, Talks to the servo through the MCU Bridge., Creates the repository. Args: bridge: Object exposing call(name, payload).…, With no bridge injected it falls back to the Arduino Bridge., The Bridge is a single multiplexed link; only one call at a time., Two threads reading at once must not overlap on the wire. Overlapping RPC…, TestConcurrencySafety, TestDefaultBridge

### Community 31 - "Servo State Store Geometry"
Cohesion: 0.14
Nodes (7): Returns the output angles reachable from the current baseline. The servo…, Reports whether a target maps inside the servo's count range. Args: output_deg:…, Converts an output angle to absolute encoder counts. Args: output_deg: Output…, Returns the current output angle relative to the active zero. Returns: Output…, Returns the current absolute encoder position in counts. Returns: Current raw…, Returns the active baseline in raw counts. With no zero captured the baseline…, Converts raw counts to output degrees against the active zero. Args:…

### Community 32 - "Bench-Measured Servo Geometry"
Cohesion: 0.17
Nodes (13): 0.06 Degrees Per Count, Speed Saturates Near 1100 Counts/s, Plus/Minus 90 Degree Travel Window, Centre-Of-Travel Default Baseline, InvalidReadingError, Off-Centre Datum Warning, Servo Diagnostic App, Calibrate Control (+5 more)

### Community 33 - "Telemetry Snapshot"
Cohesion: 0.18
Nodes (8): Instantaneous sensory readout from the servo layer. Attributes: raw_counts:…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: Position, motion flag…, Returns position, motion flag and mock telemetry. Returns: The instantaneous…, Calibrating on a dead bus must refuse, not store a zero., TestInvalidReadingSurfaced, Calibration must not capture a reading the servo never gave. A failed read…, TestCalibrationRobustness

### Community 34 - "Relay Path E2E Tests"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 35 - "Zero Repository Tests"
Cohesion: 0.18
Nodes (6): Builds an unsaved zero entity. Args: name: Zero name. counts: Raw counts.…, Create, read, delete., Active-baseline selection., TestActive, TestCrud, _zero()

### Community 36 - "ServoBus Serial Driver"
Cohesion: 0.29
Nodes (11): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, WriteByte, WriteEepromByte (+3 more)

### Community 37 - "Hardware Bus Facts"
Cohesion: 0.17
Nodes (12): Serial1 At 1 Mbps, Zero Deadband, Bridge Serialisation RLock, servo_truth.md Register Reference, Use SMS_STS, Never SCSCL, App Composition Root, .h Files Are Not Auto-Included, ServoBus (+4 more)

### Community 38 - "Servo Route Tests"
Cohesion: 0.17
Nodes (7): Servo API routes: state, move, stop, lock, calibrate, recover., POST /api/v1/servo/recover., An unreachable target must be refused, not silently clamped., POST /stop and /lock., TestOutOfTravelSurfaced, TestRecover, TestStopLock

### Community 39 - "Sketch Entrypoint And App"
Cohesion: 0.24
Nodes (3): App, Begin, Tick

### Community 40 - "AngleConverter (MCU)"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 41 - "ServoController (MCU)"
Cohesion: 0.38
Nodes (11): ClampAmplification(), ClampDeadband(), ServoController, Begin, CentreHere, ClearFault, ConfigureRange, Move (+3 more)

### Community 42 - "Project History And Known Gaps"
Cohesion: 0.24
Nodes (11): Read The Working Reference Before Rewriting, Relay And Controller Have No Automated Coverage, Network Options Tradeoff Study, Working Relay Reference Implementations, Known Gaps, NetworkRelay, On-Target Test Tier, Adopt Connections With accept(), Never available() (+3 more)

### Community 43 - "Telemetry Repository Contract"
Cohesion: 0.20
Nodes (7): ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Persists one sample. Args: sample: The sample to store. Returns: None., Yields samples inside a time range, oldest first. Args: ts_from: Range start,…, Deletes samples older than the retention window. Args: days: Retention in days.…, TelemetryRepository

### Community 44 - "TinyTest Harness"
Cohesion: 0.22
Nodes (7): main(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 45 - "Bridge Read Path"
Cohesion: 0.20
Nodes (5): Performs one real bus read. The caller must hold the lock. Returns: The…, Returns the absolute encoder position in counts. The value is ABSOLUTE MULTI-…, Invokes a Bridge function, converting failures into empty results. Args: name:…, Builds the reading used when the bus did not answer. Returns: A snapshot with…, Reads one coherent snapshot from the servo. Returns: The snapshot. On a bus…

### Community 46 - "Bridge Command Path"
Cohesion: 0.20
Nodes (5): Starts a move toward an absolute counts target. A new position command also…, Stops motion at the current position. Returns: None., Configures the servo's dead-zone width. Args: counts: Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn:…, Invokes a Bridge function and logs a non-ok acknowledgement. Args: name: Bridge…

### Community 47 - "Fault Bit Tests"
Cohesion: 0.20
Nodes (5): parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude

### Community 48 - "Zero Service Tests"
Cohesion: 0.20
Nodes (4): ZeroService: capture, activate, delete rules, calibrate., Ordinary zero capture., TestCalibrate, TestCapture

### Community 49 - "ServoSnapshot Struct"
Cohesion: 0.20
Nodes (10): ServoSnapshot, current_a, faults, load_duty, moving, raw_counts, temperature_c, torque_kgcm (+2 more)

### Community 50 - "Telemetry CSV Export"
Cohesion: 0.22
Nodes (8): alias, export_csv(), get, Query, Telemetry endpoints: CSV export by time range., Streams telemetry samples in a time range as CSV. Args: telemetry: Injected…, StreamingResponse, TelemetryDep

### Community 51 - "SpiRemap"
Cohesion: 0.39
Nodes (7): GPIO_TypeDef, PortFor(), SpiRemap, ApplyJspiMapping, kAlternateFunctionSpi2, ReleaseTopHeaderCopies, SetAlternateFunction

### Community 52 - "Fault Persistence Tests"
Cohesion: 0.25
Nodes (6): get_telemetry_repository(), Returns the telemetry repository. Returns: The process-wide telemetry…, Overload flag reaches persisted telemetry., TestFaultVisibleInSampledHistory, Single-sample persistence., TestSampling

### Community 53 - "Sign-Magnitude Decoding"
Cohesion: 0.28
Nodes (6): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. STS position fields…, parametrize, Sign-magnitude decoding: the ~32700 wrap bug., Wire-format decoding for STS position fields., TestDecodeSignMagnitude

### Community 55 - "Telemetry Persistence Tests"
Cohesion: 0.28
Nodes (5): Builds a sample. Args: timestamp: Unix timestamp. overload: Overload flag…, Persistence round-trips., _sample(), TestAddQuery, TestPurge

### Community 56 - "ServoFaults Decoder"
Cohesion: 0.25
Nodes (7): ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage

### Community 57 - "Bridge Contract Checker"
Cohesion: 0.39
Nodes (7): Path, collect_python(), collect_sketch(), main(), Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 58 - "SQLite Telemetry Repository"
Cohesion: 0.25
Nodes (6): Stores telemetry samples in the telemetry table., Deletes samples older than the retention window. Args: days: Retention in days.…, SqliteTelemetryRepository, fixture, Telemetry repository over a fresh database. Returns: The repository under test., repo()

### Community 60 - "Agent Skills And Doc Conventions"
Cohesion: 0.29
Nodes (7): Agent Skills Configuration, Single-Context Domain Layout, GitHub Issue Tracker, Attach PROJECT_STATE At Chat Start, Locked Decisions, Export 24h CSV, timestamp Never ts

### Community 61 - "UI And Travel-Range Decisions"
Cohesion: 0.29
Nodes (7): Plain HTML/CSS/JS, No Framework, Typed Inputs, Not Sliders, Datum At Zero Strands The Negative Half, OutOfTravelError, Silent Servo Clamping, Duplicate app.js Script Tag, Angle And Speed Move Controls

### Community 62 - "Settings Tests"
Cohesion: 0.29
Nodes (3): Settings: defaults, environment override, caching., Behavior of the pydantic-settings configuration., TestSettings

### Community 64 - "Servo Register Definitions"
Cohesion: 0.29
Nodes (4): MoveCommand, acceleration, speed_counts_per_second, target_counts

### Community 65 - "On-Target Test Sketch"
Cohesion: 0.48
Nodes (5): Check(), CheckNear(), MoveTo(), setup(), WaitSettled()

### Community 66 - "Fault Display And Theme"
Cohesion: 0.40
Nodes (6): LCARS Light Theme With ISA-101 Safety Colours, Six-Fault Status Grid, angle_fault Status Flag, Header-Only Arduino-Free Classes, ServoFaults, SignMagnitude

### Community 73 - "Logging Setup Tests"
Cohesion: 0.40
Nodes (3): Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 76 - "Test Strategy Rationale"
Cohesion: 0.50
Nodes (4): Coverage Is Not Correctness, Native Tests Cover Pure Maths Only, Host-Native Test Tier, TinyTest.h Harness

### Community 80 - "SMS_STS Bus Binding"
Cohesion: 0.50
Nodes (3): ServoBus::ServoBus(), SMS_STS, ReadSnapshot

## Ambiguous Edges - Review These
- `Plain HTML/CSS/JS, No Framework` → `Duplicate app.js Script Tag`  [AMBIGUOUS]
  python/static/index.html · relation: conceptually_related_to

## Knowledge Gaps
- **51 isolated node(s):** `state`, `EVENT_LABELS`, `counts_per_servo_deg_`, `servo_deg_per_output_deg_`, `cs_pin_` (+46 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Plain HTML/CSS/JS, No Framework` and `Duplicate app.js Script Tag`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `BridgeServoRepository` connect `Bridge Servo Repository` to `Dependency Injection Providers`, `FastAPI Application Assembly`, `Telemetry Snapshot`, `Bus Resilience Tests`, `Domain Entities And Repository Seam`, `Snapshot Decoding Tests`, `Bridge Read Path`, `Bridge Command Path`, `Backend Selection Tests`, `Fault Bit Tests`, `Bridge Servo Repository Tests`, `Bridge Command Payload Tests`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Why does `ServoStateStore` connect `Motion Service And Settings` to `Dependency Injection Providers`, `FastAPI Application Assembly`, `Telemetry Snapshot`, `Domain Entities And Repository Seam`, `Zero Reference Contract`, `Domain Exception Hierarchy`, `Telemetry Sampler And Retention`, `Servo State Store Geometry`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `TelemetrySnapshot` connect `Telemetry Snapshot` to `Motion Service And Settings`, `Travel Window Tests`, `Servo Route Tests`, `Domain Entities And Repository Seam`, `Zero Activation Rule Tests`, `Bridge Read Path`, `Calibrate Endpoint Tests`, `Zero Service Tests`, `Simulated Servo Repository`, `Move And Lock Guard Tests`, `State Endpoint Tests`, `Move Endpoint Tests`, `Bridge Servo Repository`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `ServoStateStore` (e.g. with `MotionService` and `ServoStateView`) actually correct?**
  _`ServoStateStore` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `BridgeServoRepository` (e.g. with `TelemetrySnapshot` and `ServoRepository`) actually correct?**
  _`BridgeServoRepository` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 17 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 17 INFERRED edges - model-reasoned connections that need verification._