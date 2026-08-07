# Graph Report - .  (2026-08-07)

## Corpus Check
- Corpus is ~35,684 words - fits in a single context window. You may not need a graph.

## Summary
- 1230 nodes · 2178 edges · 94 communities (75 shown, 19 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 229 edges (avg confidence: 0.59)
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
- schemas Package Init

## God Nodes (most connected - your core abstractions)
1. `ServoStateStore` - 43 edges
2. `get_state_store()` - 39 edges
3. `wait_until()` - 38 edges
4. `BridgeServoRepository` - 35 edges
5. `TelemetrySnapshot` - 33 edges
6. `TEST()` - 32 edges
7. `get_settings()` - 29 edges
8. `Database` - 29 edges
9. `BridgeStub` - 29 edges
10. `ZeroReference` - 28 edges

## Surprising Connections (you probably didn't know these)
- `Zero Reference (glossary)` --implements--> `ZeroReference`  [INFERRED]
  CONTEXT.md → python/app/models/entities.py
- `Sample (glossary)` --implements--> `TelemetrySample`  [INFERRED]
  CONTEXT.md → python/app/models/entities.py
- `Output Degree (glossary)` --implements--> `AngleConverter`  [INFERRED]
  CONTEXT.md → sketch/src/AngleMath.h
- `Bridge (glossary)` --implements--> `BridgeApi`  [INFERRED]
  CONTEXT.md → sketch/src/BridgeApi.h
- `Relay (glossary)` --implements--> `NetworkRelay`  [INFERRED]
  CONTEXT.md → sketch/src/NetworkRelay.h

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Failed Read Becomes A Calibration Datum** — docs_audit_bridge_serialisation_rlock, docs_audit_telemetrysnapshot_valid, docs_audit_invalidreadingerror, docs_audit_datum_at_zero_strands_negative_half, docs_audit_silent_clamping, docs_audit_outoftravelerror [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]
- **The Ubiquitous Language** — context_count, context_output_degree, context_datum, context_zero_reference, context_travel_window, context_snapshot, context_sample, context_fault, context_bridge, context_relay, context_slot, context_lock, context_backend [EXTRACTED 1.00]
- **Air-Gap Constraint Set** — context_air_gapped_deployment, context_no_framework, app_no_bricks, libraries_readme_vendored_libraries, python_wheelhouse_readme_offline_wheels, sketch_readme_tinytest, readme_core_version_pin [EXTRACTED 1.00]

## Communities (94 total, 19 thin omitted)

### Community 0 - "Dependency Injection Providers"
Cohesion: 0.06
Nodes (43): bin_t, App, Begin, Tick, Ack(), BridgeApi, BridgeApi::BridgeApi(), FormatSnapshot (+35 more)

### Community 1 - "FastAPI Application Assembly"
Cohesion: 0.06
Nodes (33): Typed application settings loaded from the environment / .env file., In-memory ring buffer of structured events for the events endpoint. Kept…, Composition root: cached provider functions that construct and wire. This is…, ABC, Abstract servo access: the seam between simulation and hardware., Returns the absolute encoder position in counts (multi-turn). Contract: the…, Starts a move toward an absolute counts target. A new position command also…, Configures the travel-range mode before normal operation. With multi_turn False… (+25 more)

### Community 2 - "Motion Service And Settings"
Cohesion: 0.06
Nodes (47): Fault (glossary), ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, ServoBus::ServoBus() (+39 more)

### Community 3 - "Bridge API (MCU Side)"
Cohesion: 0.06
Nodes (30): get_telemetry_repository(), Returns the telemetry repository. Returns: The process-wide telemetry…, One persisted telemetry row. Attributes: timestamp: Unix timestamp of the…, TelemetrySample, ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Persists one sample. Args: sample: The sample to store. Returns: None. (+22 more)

### Community 4 - "Domain Error Types"
Cohesion: 0.17
Nodes (36): apiDelete(), apiGet(), apiPost(), asApiError(), askConfirm(), askText(), bind(), clearNotice() (+28 more)

### Community 5 - "Web UI Client Script"
Cohesion: 0.12
Nodes (25): Exception, DomainError, LockedError, MovingError, OutOfTravelError, Domain exceptions, mapped to HTTP responses by the application layer., Raised when a lock change is requested while a move is in progress., Raised when a target lies outside the servo's physical count range. The servo… (+17 more)

### Community 6 - "Servo HTTP Routes"
Cohesion: 0.08
Nodes (33): MotionDep, get_state(), post_calibrate(), post_lock(), post_move(), post_recover(), post_stop(), get (+25 more)

### Community 7 - "Domain Entities And Repository Seam"
Cohesion: 0.09
Nodes (19): ActiveZeroError, DatumZeroError, InvalidReadingError, NotFoundError, Raised when a referenced entity does not exist., Raised when attempting to delete the active zero reference., Raised when attempting to delete the calibration datum zero., Raised when an operation needs a reading the servo did not supply. (+11 more)

### Community 8 - "Zeros HTTP Routes"
Cohesion: 0.09
Nodes (21): get_database(), get_servo_repository(), get_state_store(), get_zero_repository(), Returns the atomic servo/lock/baseline state store. Returns: The process-wide…, Returns the shared database wrapper. Returns: The process-wide database., Returns the servo repository chosen by use_hardware_servo. Simulated by default…, Returns the zero repository. Returns: The process-wide zero repository. (+13 more)

### Community 9 - "Zero Reference Contract"
Cohesion: 0.13
Nodes (17): Database, SQLite connection management and schema initialization., Owns the SQLite connection and serializes write access. SQLite permits…, SQLite implementation of the telemetry repository., Stores telemetry samples in the telemetry table., Deletes samples older than the retention window. Args: days: Retention in days.…, SqliteTelemetryRepository, Database: schema creation, migration of old schemas, row survival. (+9 more)

### Community 10 - "Bridge Stub And System Route Tests"
Cohesion: 0.09
Nodes (14): echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Remaining failure branches., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Behavior when the board runtime is absent (dev PC)., Fresh registered relay. Returns: The relay under test., Bridge callback registration. (+6 more)

### Community 11 - "Angle And Range Native Tests"
Cohesion: 0.11
Nodes (13): BaseSettings, Backend configuration, overridable via environment or .env. Attributes:…, Settings, BridgeRelay, Linux half of the TCP relay; counterpart of EthernetRelay (sketch).…, Handles the network client going away. Args: slot: Connection slot. Returns:…, Streams FastAPI reply bytes back down to the sketch. Args: slot: Connection…, Closes and forgets one mirrored connection. Args: slot: Connection slot.… (+5 more)

### Community 12 - "Domain Exception Hierarchy"
Cohesion: 0.10
Nodes (13): BridgeStub, Recording stub of the Arduino Bridge., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent., The health endpoint names the servo backend in use. (+5 more)

### Community 13 - "SQLite Zero Repository"
Cohesion: 0.09
Nodes (22): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, range_a_datum_at_zero_strands_the_negative_half (+14 more)

### Community 14 - "Bridge Relay Tests"
Cohesion: 0.11
Nodes (13): Stores zero references in the zeros table., Creates or updates THE calibration datum zero. Args: raw_counts: Captured raw…, Maps a database row to the entity. Args: row: SQLite row. Returns: The mapped…, Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Deletes one zero reference. Args: zero_id: Database id. Returns: True when a…, Marks one zero active and clears the previous active flag. Args: zero_id:… (+5 more)

### Community 15 - "SQLite Database Layer"
Cohesion: 0.11
Nodes (12): Lock (glossary), MotionService, Changes the digital lock, honoring the optional move guard. Args: locked:…, Clears a tripped overload fault by re-commanding the position. Hardware…, Decides whether the anti-backlash approach applies. Args: start_deg: Current…, Runs the two-leg consistent-direction approach. Leg 1 overshoots below the…, Refuses targets the servo would silently clamp. The servo accepts counts…, Validates and executes movement commands in output-degree space. (+4 more)

### Community 16 - "End-To-End Operator Tests"
Cohesion: 0.13
Nodes (20): delete, activate_zero(), capture_zero(), delete_zero(), list_zeros(), get, post, ZeroDep (+12 more)

### Community 17 - "System Health And Events Routes"
Cohesion: 0.13
Nodes (16): get_settings(), Returns the singleton settings instance. Returns: The process-wide Settings,…, get_relay(), Returns the Bridge relay. Returns: The process-wide relay., _ensure_logger461(), main(), Entry point: initialize, serve FastAPI, run the App loop. App Lab runs this…, Provides Logger461 when the real wheel is not installed. Logger461 is our own… (+8 more)

### Community 18 - "Simulated Servo Repository"
Cohesion: 0.12
Nodes (19): EventDep, ge, le, get_events(), get_health(), get, Query, Returns service health including the MCU status line. Args: settings: Injected… (+11 more)

### Community 19 - "Relay Connection Mirroring"
Cohesion: 0.11
Nodes (11): Immutable domain entities shared across layers., A saved baseline position. Attributes: id: Database id; None before…, ZeroReference, Persists a new zero reference. Args: zero: Entity with id=None. Returns: The…, Returns all zero references, newest first. Returns: All stored zeros., Returns one zero reference by id. Args: zero_id: Database id. Returns: The…, Returns the active zero reference, if any. Returns: The active zero, or None., Creates or updates THE calibration datum zero. At most one datum exists: the… (+3 more)

### Community 20 - "Event Service"
Cohesion: 0.13
Nodes (10): Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), Reads the settle state from the store. Args: backend: The backend fixture…, _settling(), SimulatedServoRepository: motion, deadband, faults, signed multi-turn., Absolute counts beyond one turn and below zero (contract)., Basic motion profile., TestDeadband (+2 more)

### Community 21 - "Shared Test Fixtures"
Cohesion: 0.13
Nodes (9): SqliteZeroRepository: CRUD, active selection, datum upsert., Builds an unsaved zero entity. Args: name: Zero name. counts: Raw counts.…, Create, read, delete., Active-baseline selection., Upsert of THE calibration datum., TestActive, TestCrud, TestDatum (+1 more)

### Community 22 - "Air-Gap Deployment Constraints"
Cohesion: 0.11
Nodes (19): No Bricks Constraint, Servo Control App Manifest, Air-Gapped Deployment, Coverage Is Not Correctness, Native Tests Cover Pure Maths Only, IPAddress Cast Patch For Ethernet 2.0.2, Vendored Arduino Libraries, Dev And Test Dependencies (+11 more)

### Community 23 - "Bridge Servo Repository Tests"
Cohesion: 0.15
Nodes (17): Backend (glossary), Sample (glossary), Snapshot (glossary), Failures Never Distinguishable From Data, TelemetrySnapshot.valid, Confirm Which Backend Is Live, BridgeServoRepository, check_bridge_contract.py (+9 more)

### Community 24 - "Telemetry Service Wiring"
Cohesion: 0.16
Nodes (9): Event, EventService, One operator-facing event. Attributes: timestamp: ISO timestamp. event: Dotted…, Thread-safe fixed-size store of recent events., Stores one event. Args: event: Dotted event identifier. message: Human-readable…, Returns the newest events, newest first. Args: limit: Maximum number of events…, EventService: recording, ordering, capacity, thread safety., Behavior of the operator-event ring buffer. (+1 more)

### Community 25 - "Telemetry Sampler And Retention"
Cohesion: 0.12
Nodes (9): Records the range configuration. The simulator already models unbounded signed…, Configures the simulated dead-zone width. Args: counts: Dead-zone width in…, Trips the simulated overload fault (testing/commissioning aid). Returns: None., Advances position toward the target until the process ends. Returns: None., Thread-driven simulation of one ST3215-class servo., Returns the absolute encoder position in counts. Returns: Current raw counts., Starts a move toward an absolute counts target. Clears a simulated overload…, Stops motion at the current position. Returns: None. (+1 more)

### Community 26 - "Logger Stub"
Cohesion: 0.14
Nodes (14): AppStub, backend(), _clear_all_caches(), client(), fixture, Shared test configuration: stubs, environment, and fixtures. Runs entirely on a…, Clears every cached provider so each test builds fresh singletons. Returns:…, Fresh backend context: new DB, cleared caches, recording stubs. Yields: A… (+6 more)

### Community 27 - "Zeros Route Tests"
Cohesion: 0.14
Nodes (10): get_zero_service(), Returns the zero service. Returns: The process-wide zero service., Cross-service integration flows (no HTTP): components working together., Zeros, state store and motion interacting., TestZeroLifecycleAcrossServices, The servo clamps silently outside counts 0..4095; we must not. Commanding past…, TestTravelLimits, fixture (+2 more)

### Community 28 - "Failure-Visibility Contract"
Cohesion: 0.14
Nodes (11): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, Field 0 of the snapshot payload is the sketch saying 'no answer'., A fake bridge returning a healthy snapshot. Returns: The fake. (+3 more)

### Community 29 - "Telemetry Sample Entity"
Cohesion: 0.16
Nodes (11): Logging configuration built on Logger461 (loguru JSON wrapper). Logger461 emits…, Initializes Logger461 for the process. Args: settings: Application settings…, setup_logging(), _ensure_logger461(), main(), Dev-PC runner: the full backend + web UI, no board required. The app modules…, Boots the backend + web UI and runs the dev console. Returns: None., Provides Logger461 when the real wheel is not installed. Logger461 is our own… (+3 more)

### Community 30 - "Bridge Servo Repository"
Cohesion: 0.14
Nodes (9): get_telemetry_service(), Returns the telemetry service. Returns: The process-wide telemetry service., Telemetry sampler records a real movement profile., Overload flag reaches persisted telemetry., TestFaultVisibleInSampledHistory, TestSamplerObservesMotion, Telemetry API route: CSV export., GET /api/v1/telemetry/export. (+1 more)

### Community 31 - "Servo State Store Geometry"
Cohesion: 0.20
Nodes (4): LoggerStub, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 32 - "Bench-Measured Servo Geometry"
Cohesion: 0.13
Nodes (6): Zeros API routes: list, capture, activate, delete + error mapping., DELETE /{id} and its protections., POST /capture and GET list., TestActivate, TestCaptureList, TestDelete

### Community 33 - "Telemetry Snapshot"
Cohesion: 0.18
Nodes (9): get_event_service(), get_motion_service(), Returns the motion service. Returns: The process-wide motion service., Returns the shared event buffer. Returns: The process-wide event service., _events(), motion(), fixture, Fresh motion service. Returns: The service under test. (+1 more)

### Community 34 - "Relay Path E2E Tests"
Cohesion: 0.20
Nodes (8): BridgeServoRepository, Talks to the servo through the MCU Bridge., Creates the repository. Args: bridge: Object exposing call(name, payload).…, With no bridge injected it falls back to the Arduino Bridge., The Bridge is a single multiplexed link; only one call at a time., Two threads reading at once must not overlap on the wire. Overlapping RPC…, TestConcurrencySafety, TestDefaultBridge

### Community 35 - "Zero Repository Tests"
Cohesion: 0.14
Nodes (7): Returns the output angles reachable from the current baseline. The servo…, Reports whether a target maps inside the servo's count range. Args: output_deg:…, Converts an output angle to absolute encoder counts. Args: output_deg: Output…, Returns the current output angle relative to the active zero. Returns: Output…, Returns the current absolute encoder position in counts. Returns: Current raw…, Returns the active baseline in raw counts. With no zero captured the baseline…, Converts raw counts to output degrees against the active zero. Args:…

### Community 36 - "ServoBus Serial Driver"
Cohesion: 0.19
Nodes (13): Relay (glossary), Slot (glossary), Read The Working Reference Before Rewriting, Relay And Controller Have No Automated Coverage, Network Options Tradeoff Study, Working Relay Reference Implementations, Known Gaps, NetworkRelay (+5 more)

### Community 37 - "Hardware Bus Facts"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 38 - "Servo Route Tests"
Cohesion: 0.18
Nodes (12): Datum (glossary), Typed Inputs, Not Sliders, Zero Reference (glossary), Centre-Of-Travel Default Baseline, Datum At Zero Strands The Negative Half, InvalidReadingError, Off-Centre Datum Warning, OutOfTravelError (+4 more)

### Community 39 - "Sketch Entrypoint And App"
Cohesion: 0.23
Nodes (7): FastAPI, FastAPI application assembly: routers and domain-error mapping. Construction of…, Maps domain exceptions to HTTP responses. Args: app: The FastAPI application.…, _register_error_handlers(), System endpoints: health and recent events., Telemetry endpoints: CSV export by time range., Zero-reference endpoints: list, capture, activate, delete.

### Community 40 - "AngleConverter (MCU)"
Cohesion: 0.20
Nodes (3): AngleConverter, counts_per_servo_deg_, servo_deg_per_output_deg_

### Community 41 - "ServoController (MCU)"
Cohesion: 0.20
Nodes (7): Instantaneous sensory readout from the servo layer. Attributes: raw_counts:…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: Position, motion flag…, Simulated servo: sprint-1 stand-in for the real serial bus. Models raw encoder…, Returns position, motion flag and mock telemetry. Returns: The instantaneous…, Calibrating on a dead bus must refuse, not store a zero., TestInvalidReadingSurfaced

### Community 42 - "Project History And Known Gaps"
Cohesion: 0.22
Nodes (7): main(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 43 - "Telemetry Repository Contract"
Cohesion: 0.20
Nodes (5): Performs one real bus read. The caller must hold the lock. Returns: The…, Returns the absolute encoder position in counts. The value is ABSOLUTE MULTI-…, Invokes a Bridge function, converting failures into empty results. Args: name:…, Builds the reading used when the bus did not answer. Returns: A snapshot with…, Reads one coherent snapshot from the servo. Returns: The snapshot. On a bus…

### Community 44 - "TinyTest Harness"
Cohesion: 0.20
Nodes (5): Starts a move toward an absolute counts target. A new position command also…, Stops motion at the current position. Returns: None., Configures the servo's dead-zone width. Args: counts: Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn:…, Invokes a Bridge function and logs a non-ok acknowledgement. Args: name: Bridge…

### Community 45 - "Bridge Read Path"
Cohesion: 0.20
Nodes (5): parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude

### Community 46 - "Bridge Command Path"
Cohesion: 0.25
Nodes (9): Count (glossary), 0.06 Degrees Per Count, Output Degree (glossary), Speed Saturates Near 1100 Counts/s, Travel Window (glossary), Servo Diagnostic App, Bench-Measured Settings, Multi-Turn Support (+1 more)

### Community 47 - "Fault Bit Tests"
Cohesion: 0.39
Nodes (7): GPIO_TypeDef, PortFor(), SpiRemap, ApplyJspiMapping, kAlternateFunctionSpi2, ReleaseTopHeaderCopies, SetAlternateFunction

### Community 48 - "Zero Service Tests"
Cohesion: 0.28
Nodes (8): create_app(), Creates and configures the FastAPI application. Returns: The configured…, _free_port(), live_backend(), fixture, E2E fixtures: the backend booted the way main.py boots it. A real uvicorn…, Finds a free localhost TCP port. Returns: An ephemeral port number currently…, Boots the full backend on a live socket, mirroring main.py. Yields: Namespace…

### Community 49 - "ServoSnapshot Struct"
Cohesion: 0.28
Nodes (6): decode_sign_magnitude(), Decodes a sign-magnitude field from the servo wire format. STS position fields…, parametrize, Sign-magnitude decoding: the ~32700 wrap bug., Wire-format decoding for STS position fields., TestDecodeSignMagnitude

### Community 50 - "Telemetry CSV Export"
Cohesion: 0.22
Nodes (5): Servo API routes: state, move, stop, lock, calibrate, recover., An unreachable target must be refused, not silently clamped., POST /stop and /lock., TestOutOfTravelSurfaced, TestStopLock

### Community 52 - "Fault Persistence Tests"
Cohesion: 0.29
Nodes (8): Agent Skills Configuration, Graphify Extraction Gaps, Graph-First Codebase Navigation, Ubiquitous Language Glossary, Use The Glossary's Vocabulary, Single-Context Domain Layout, Domain Skill Chain, GitHub Issue Tracker

### Community 53 - "Sign-Magnitude Decoding"
Cohesion: 0.39
Nodes (7): Path, collect_python(), collect_sketch(), main(), Finds what Python calls and what it provides. Args: root: The python/app…, Finds what the sketch provides and what it notifies. Args: path: BridgeApi.cpp.…, Entry point. Returns: 0 when both sides agree, 1 otherwise.

### Community 55 - "Telemetry Persistence Tests"
Cohesion: 0.32
Nodes (4): Builds a sample. Args: timestamp: Unix timestamp. overload: Overload flag…, Persistence round-trips., _sample(), TestAddQuery

### Community 56 - "ServoFaults Decoder"
Cohesion: 0.29
Nodes (7): alias, export_csv(), get, Query, Streams telemetry samples in a time range as CSV. Args: telemetry: Injected…, StreamingResponse, TelemetryDep

### Community 57 - "Bridge Contract Checker"
Cohesion: 0.29
Nodes (7): Bridge (glossary), Bridge Serialisation RLock, App Composition Root, .h Files Are Not Auto-Included, src/ Avoids .ino Preprocessing, loop() Must Yield, provide_safe Registration

### Community 58 - "SQLite Telemetry Repository"
Cohesion: 0.33
Nodes (7): LCARS Light Theme With ISA-101 Safety Colours, Six-Fault Status Grid, angle_fault Status Flag, AngleConverter, Header-Only Arduino-Free Classes, ServoFaults, SignMagnitude

### Community 59 - "Bridge Command Payload Tests"
Cohesion: 0.29
Nodes (7): Plain HTML/CSS/JS, No Framework, timestamp (glossary), Attach PROJECT_STATE At Chat Start, Locked Decisions, Export 24h CSV, Duplicate app.js Script Tag, timestamp Never ts

### Community 61 - "UI And Travel-Range Decisions"
Cohesion: 0.33
Nodes (6): Serial1 At 1 Mbps, Zero Deadband, servo_truth.md Register Reference, Use SMS_STS, Never SCSCL, ServoBus, ServoController

### Community 62 - "Settings Tests"
Cohesion: 0.33
Nodes (4): Coherent snapshot of servo + lock + baseline, read atomically. Attributes:…, ServoStateView, Returns a coherent snapshot of servo, lock and baseline. Returns: The atomic…, Converts counts to output degrees using a prefetched baseline. Args:…

### Community 66 - "Fault Display And Theme"
Cohesion: 0.40
Nodes (3): E2E: a full operator session against the live server over real HTTP., Boot -> calibrate -> move -> lock -> zeros -> telemetry -> fault., TestOperatorSession

## Ambiguous Edges - Review These
- `Duplicate app.js Script Tag` → `Plain HTML/CSS/JS, No Framework`  [AMBIGUOUS]
  python/static/index.html · relation: conceptually_related_to

## Knowledge Gaps
- **53 isolated node(s):** `state`, `EVENT_LABELS`, `counts_per_servo_deg_`, `servo_deg_per_output_deg_`, `cs_pin_` (+48 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **19 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Duplicate app.js Script Tag` and `Plain HTML/CSS/JS, No Framework`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `TelemetrySnapshot` connect `ServoController (MCU)` to `FastAPI Application Assembly`, `Relay Path E2E Tests`, `Bus Resilience Tests`, `Domain Entities And Repository Seam`, `Range Configuration Tests`, `Telemetry Repository Contract`, `Calibration Datum Upsert Tests`, `Test Strategy Rationale`, `Telemetry CSV Export`, `Relay Connection Mirroring`, `SpiRemap`, `Bridge Servo Repository Tests`, `Telemetry Sampler And Retention`, `AngleMath And SignMagnitude Headers`?**
  _High betweenness centrality (0.243) - this node is a cross-community bridge._
- **Why does `Snapshot (glossary)` connect `Bridge Servo Repository Tests` to `ServoController (MCU)`, `Fault Persistence Tests`?**
  _High betweenness centrality (0.214) - this node is a cross-community bridge._
- **Why does `Ubiquitous Language Glossary` connect `Fault Persistence Tests` to `Servo Route Tests`, `ServoBus Serial Driver`, `Bridge Command Path`, `Bridge Servo Repository Tests`?**
  _High betweenness centrality (0.197) - this node is a cross-community bridge._
- **Are the 13 inferred relationships involving `ServoStateStore` (e.g. with `MotionService` and `ServoStateView`) actually correct?**
  _`ServoStateStore` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 13 inferred relationships involving `BridgeServoRepository` (e.g. with `Backend (glossary)` and `TelemetrySnapshot`) actually correct?**
  _`BridgeServoRepository` has 13 INFERRED edges - model-reasoned connections that need verification._
- **Are the 18 inferred relationships involving `TelemetrySnapshot` (e.g. with `Snapshot (glossary)` and `ServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 18 INFERRED edges - model-reasoned connections that need verification._