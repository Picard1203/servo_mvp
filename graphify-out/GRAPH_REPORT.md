# Graph Report - servo_mvp  (2026-09-08)

## Corpus Check
- 177 files · ~229,651 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3099 nodes · 5348 edges · 193 communities (152 shown, 41 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 448 edges (avg confidence: 0.55)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `077d87bf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- deps.py
- fine_approach_trial.py
- resonance_campaign.py
- app.js
- d48_decisive.py
- Operator Metrics Tally
- Relay E2E Tests
- test_saved_positions_routes.py
- Database
- _trial
- Virtual Operator Behavior
- Architecture Decision Records
- Project Manifest & Environment
- Client Behavior Check Script
- Open Questions Doc
- DuplicateNameError
- LogRecord
- Research Report: Diagnostics and Mitigation of Load-Dependent Settling Oscillations in Geared Serial-Bus Servos
- TEST
- test_mcu_log.py
- Quantizer-Induced Limit Cycles and Nonlinear Settling Dynamics in Belt-Coupled Serial-Bus Actuators
- Verification Script
- TestExport
- ServoStateStore
- _read_sse_lines
- test_bridge_servo_repository.py
- ServoController.cpp
- Graphify Navigation Notes
- Travel Window ADRs
- Closed items
- Core Backend Modules
- Requirements Backlog (R-Items)
- Logger Stub
- get_state_store
- McuLog
- The flows
- get_isolation_service
- BridgeServoRepository
- OnTarget.ino
- EventService
- Deliver
- Coding Conventions Doc
- tests/conftest.py
- d48_s26_campaign.py
- Tasks — detail
- jitter_probe.py
- ServoSnapshot
- D48 Session 26 — experiment regimen (pre-registration)
- Rig Testing Protocol Doc
- TinyTest.h
- Relay Connection Ceiling
- Early Defects List
- Servo Bus Draining
- ServoStateView
- System Audit Doc
- Soak Test Checkpointer
- d48_decisive_watch.py
- Hardware Config Fallback
- test_jitter_probe.py
- Soak Report Tests
- Details
- TelemetrySample
- SavedPositionService
- Synthetic Operator Tests
- test_telemetry_service.py
- Defects — detail
- ServoBus
- Backlog R-Items
- Ordering, rewritten 8 August 2026 — by session, with sizes
- Details
- Hardware Bench Facts
- Firmware Prose Strip Task
- IsolationService
- TestExport
- Twin-Review Skill Doc
- Python Dependencies
- Python Prose Strip Task
- TuningSnapshot
- _findings
- _ScriptedArm
- BridgeApi.cpp
- get_app_state_repository
- Design Diagrams Task
- test_simulated_servo.py
- test_d48_decisive.py
- bridge_servo_repository.py
- log
- Deploy Push Notes
- Synthetic Operator Script
- Backlog Index Doc
- test_saved_position_service.py
- Connection Acceptance
- Disconnect Detection
- No Bricks Constraint
- Single Source Of Truth
- Closed Sessions Doc
- BridgeRelay
- Domain Glossary
- Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start)
- Small Screen UI Bug
- MotionService
- TelemetryService
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
- D48 Session 26 — runbook for the executing agent
- routers/saved_positions.py
- Brace Balance Checker Script
- Saved Positions Datum
- TelemetrySnapshot
- SavedPosition
- export_binary
- save_findings
- NetworkRelay
- TuningRegisters
- Repo Working Conventions
- Calibration And Saved Positions
- ._init_schema
- Sketch Class Design
- wait_until
- Simulated Path Coverage Caveat
- Soak Test Runner
- Position Terminology
- Mechanical Restraint Lock
- Jira Import — Servo MVP
- Apply Conventions Task
- Repository Layout
- check_cpp_conventions.sh
- D48 follow-up deep-research prompt (prepared, not yet run)
- check_glossary_and_ids.sh
- SavedPositionRepository
- 2. The ST3215 servo
- test_motion_service.py
- TestAddQuery
- TestTorque
- FlakyServo
- TestTravelWindow
- TestAnchorGeometry
- TestLevelGating
- TestOscillationIsMovementOnly
- TestPerAngleCurrentThreshold
- test_logging_setup.py
- d48_bracket_sweep.py
- d48_multi_angle_sweep.py
- main
- post
- score_trial
- TestNaturalArrival
- SimulatedServoRepository
- TestResetPositionEpsilonRenamed
- TestDismissAllStaleReferences
- TestSustainedJitter
- d48_recover_s26_findings.py
- TestQuantize
- TestSamplerLifecycleIsolation
- verdict_p1
- check_python_conventions.sh
- TestCommands
- Skills archive
- Failed Read Handling
- TestIsolate
- Operator Lens Skill
- test_bridge_relay.py
- test_servo_routes.py
- .connection
- get_settings
- BridgeStub
- Bridge Contract Checker
- Connection Ceiling Decision
- Motor Isolation Persistence
- Servo Protocol Choice

## God Nodes (most connected - your core abstractions)
1. `get_state_store()` - 97 edges
2. `wait_until()` - 70 edges
3. `ServoStateStore` - 65 edges
4. `SavedPosition` - 51 edges
5. `TelemetrySnapshot` - 50 edges
6. `get_motion_service()` - 49 edges
7. `Closed items` - 49 edges
8. `Database` - 45 edges
9. `TestCommands` - 43 edges
10. `BridgeServoRepository` - 39 edges

## Surprising Connections (you probably didn't know these)
- `Single-context documentation layout` --semantically_similar_to--> `Document reading flow (router)`  [INFERRED] [semantically similar]
  docs/agents/domain.md → CLAUDE.md
- `sshfs board mount as working copy` --semantically_similar_to--> `Development shortcut — sshfs mount of the board`  [INFERRED] [semantically similar]
  CLAUDE.md → README.md
- `Apply SpiRemap twice` --semantically_similar_to--> `Confirm the Ethernet patch survived the first build`  [INFERRED] [semantically similar]
  sketch/README.md → README.md
- `create_position()` --references--> `post()`  [EXTRACTED]
  python/app/routers/saved_positions.py → tools/d48_recover_registers.py
- `dismiss_reference()` --references--> `post()`  [EXTRACTED]
  python/app/routers/saved_positions.py → tools/d48_recover_registers.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Consequences of the air-gap constraint** — docs_adr_0005_air_gapped_by_default_development_decision, docs_adr_0002_no_frontend_framework_decision, readme_air_gapped_bundle, readme_core_version_pin, sketch_readme_tinytest_harness, docs_backlog_t2_package_the_air_gapped_bundle [EXTRACTED 1.00]
- **The Five Relay Rules** — sketch_src_relay_notes_accept_not_available, sketch_src_relay_notes_disconnect_before_accept, sketch_src_relay_notes_loop_must_yield, sketch_src_relay_notes_bulk_read_per_slot, sketch_src_relay_notes_chunk_size_contract [EXTRACTED 1.00]

## Communities (193 total, 41 thin omitted)

### Community 0 - "deps.py"
Cohesion: 0.07
Nodes (27): get_servo_repository(), Composition root: cached provider functions that construct and wire., Returns the servo repository chosen by use_hardware_servo. Returns:…, AppStateRepository, ABC, Abstract persistence of small operator-intent flags that survive a reboot., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):… (+19 more)

### Community 1 - "fine_approach_trial.py"
Cohesion: 0.07
Nodes (46): datetime, _all_timestamps(), _count(), main(), _median(), p1_planned(), p2_planned_range(), _parse() (+38 more)

### Community 2 - "resonance_campaign.py"
Cohesion: 0.09
Nodes (60): apply_deadzone(), apply_deadzone_resilient(), apply_registers(), apply_registers_resilient(), check_temperature_safety(), checkpoint(), clamp(), classify_angles() (+52 more)

### Community 3 - "app.js"
Cohesion: 0.07
Nodes (81): ADR-0008, ANGLE_FIELDS, ANGLE_SERIES, angleSortedDownsampleRefs(), apiDelete(), apiGet(), apiPatch(), apiPost() (+73 more)

### Community 4 - "d48_decisive.py"
Cohesion: 0.18
Nodes (16): c_max_for(), cell_trials(), ensure_hold_reference(), is_oscillating(), natural_arrival(), Returns the arrival direction the app would pick unaided. Args: start_deg…, Waits until the position AND current stop changing, then returns position.…, Decides oscillation from movement alone - the operator's own rule.… (+8 more)

### Community 5 - "Operator Metrics Tally"
Cohesion: 0.09
Nodes (13): Metrics, Thread-safe tally of everything the synthetic operators observed. Attributes:…, Initializes an empty metrics tally., Records one completed REST request. Args: action (str): Name of the action…, Records a request that failed to connect or completed with a 5xx error. Args:…, Records a deliberate 4xx refusal from the API with its reason. Args: action…, Records an SSE stream connection open. Args: is_reconnect (bool): True if this…, Records a disconnect or transport failure on an SSE stream. (+5 more)

### Community 6 - "Relay E2E Tests"
Cohesion: 0.27
Nodes (9): _http_request(), _parse(), E2E through the relay: raw HTTP bytes over the Bridge callbacks. The closest…, Builds a raw HTTP/1.1 request as the shield's client would send. Args: path:…, Joins all net_tx chunks captured for a slot. Args: slot: Connection slot.…, Splits a raw HTTP reply into (status_code, json_body). Args: reply: Raw HTTP…, Requests through net_open/net_rx; replies through net_tx., _reply_bytes() (+1 more)

### Community 7 - "test_saved_positions_routes.py"
Cohesion: 0.07
Nodes (11): Saved-positions API routes: list, create, update, delete, go., POST /api/v1/positions/{id}/go., POST /api/v1/positions/{id}/dismiss-reference and the batch route., PATCH /api/v1/positions/{id}., POST and GET /api/v1/positions., DELETE /api/v1/positions/{id}., TestCreateList, TestDelete (+3 more)

### Community 8 - "Database"
Cohesion: 0.08
Nodes (23): Database, SQLite connection management and schema initialization., Closes the connection., Owns the SQLite connection and serializes all access to it. Attributes:…, SQLite implementation of the app-state key/value repository., Returns a stored value. Args: key (str): State key to retrieve. Returns:…, Persists a value, replacing any previous one for the same key. Args: key (str):…, Stores small operator-intent flags in the app_state table. Attributes: _db… (+15 more)

### Community 9 - "_trial"
Cohesion: 0.07
Nodes (20): _isolate_findings_path(), fixture, Unit tests for tools/d48_s26_campaign.py's statistics and selection logic…, One-sided hypergeometric p-value for the arm-vs-baseline comparison., The pre-declared promote / drop / re-screen rule., Regression test for the exact bug D48's own entry found in Session 26.…, B9 (the confirmatory re-test) is wired into the block table., `preflight` records into the caller's dict but must not write it out. It writes… (+12 more)

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

### Community 15 - "DuplicateNameError"
Cohesion: 0.10
Nodes (15): DuplicateNameError, Raised when a saved position name is already in use., get_saved_position_repository(), Returns the saved-position repository. Returns: SavedPositionRepository: The…, _position(), SqliteSavedPositionRepository: CRUD, ordering, name uniqueness., A database created before dismissed_at existed gets the column., Builds an unsaved saved-position entity. Args: name: Position name. counts: Raw… (+7 more)

### Community 16 - "LogRecord"
Cohesion: 0.10
Nodes (20): kLogRingCapacity, DiagLog, Drain, dropped_total, Init, lock_, Push, ring_ (+12 more)

### Community 17 - "Research Report: Diagnostics and Mitigation of Load-Dependent Settling Oscillations in Geared Serial-Bus Servos"
Cohesion: 0.09
Nodes (21): Actionable Experimental Protocol (as received — cut off mid-section), Advanced Capabilities of the Feetech STS3215 Architecture, Control-Theoretic Alternatives to Deliberate Overshoot, Control-Theoretic Mitigation Strategies, Differential Diagnostics: Mechanical Resonance Versus Coulomb Friction, Evaluating the Diagnostic Signatures, Introduction, Load-Coupled Mechanical Resonance in Two-Mass Systems (+13 more)

### Community 18 - "TEST"
Cohesion: 0.05
Nodes (32): angle_direction_mirrors_counts_but_still_round_trips, angle_full_travel_window_fits_in_one_servo_turn, angle_one_count_is_the_measured_output_resolution, angle_round_trips_within_one_count, angle_speed_conversion_never_returns_zero, angle_speed_matches_the_measured_ceiling, angle_zero_maps_to_zero_in_both_directions, log_ring_drops_oldest_when_full_and_counts_it (+24 more)

### Community 19 - "test_mcu_log.py"
Cohesion: 0.15
Nodes (10): _lines(), mcu_log(), fixture, McuLog: receiving and writing diagnostic events forwarded from the MCU., Fresh registered receiver, writing into a throwaway file. Returns: The receiver…, Reads every JSON line from a file. Args: path: File to read. Returns: One dict…, One event in, one JSON line out., Size-based single-backup rotation. (+2 more)

### Community 20 - "Quantizer-Induced Limit Cycles and Nonlinear Settling Dynamics in Belt-Coupled Serial-Bus Actuators"
Cohesion: 0.14
Nodes (13): Cascaded Architecture and Velocity-Loop Register Tuning, Drive-Train Compliance and Settling Blind Spots, Non-Uniform and Hysteretic Deadband Architectures, Nonlinear Drive Dynamics and Approach Velocity, Phase 1: Inner Velocity-Loop Reconfiguration (Registers 37 & 39), Phase 2: Trajectory Ramp and Approach Velocity Optimization (Registers 41 & 46), Phase 3: Transmission Compliance and Settle-Time Dwell Enforcement, Phase 4: Diagnostic Isolation of Directional Asymmetry (+5 more)

### Community 21 - "Verification Script"
Cohesion: 0.14
Nodes (23): _delta(), _ensure_local_venv_mirror(), _load_baseline(), main(), _mirror_python_source(), Path, Runs the five verification checks once and prints one summary block. python3…, Runs a command, capturing combined stdout+stderr as text. Args: cmd: Argv list.… (+15 more)

### Community 22 - "TestExport"
Cohesion: 0.29
Nodes (3): Telemetry API route: compact binary export. XLSX assembly happens client-side…, GET /api/v1/telemetry/binary., TestExport

### Community 23 - "ServoStateStore"
Cohesion: 0.03
Nodes (47): InvalidReadingError, Raised when an operation needs a reading the servo did not supply., Calibration, The calibration datum. Attributes: raw_counts (int): Absolute encoder position…, CalibrationService, Captures the current physical position as the datum. Attributes: _servo…, Captures the current physical position as the datum. Returns: Calibration: The…, Sets the operator intent for motor isolation. Args: isolated (bool): Desired… (+39 more)

### Community 24 - "_read_sse_lines"
Cohesion: 0.22
Nodes (12): MonkeyPatch, _parse_sse_events(), Exception, SSE stream API integration tests., Reads exactly count lines from the response iterator. Args: response: The…, Parses SSE lines into a list of event dictionaries. Args: lines: Raw SSE lines.…, Custom exception to terminate stream generator during tests., _read_sse_lines() (+4 more)

### Community 25 - "test_bridge_servo_repository.py"
Cohesion: 0.07
Nodes (17): bridge(), FakeBridge, fixture, BridgeServoRepository: the CSV contract with the sketch. No board and no Bridge…, Records Bridge calls and replies with a scripted payload., Records one call. Args: name: Bridge function name. payload: Request payload.…, A misbehaving bus must not take the backend down., deps honours use_hardware_servo. (+9 more)

### Community 26 - "ServoController.cpp"
Cohesion: 0.21
Nodes (22): BridgeApi::BridgeApi(), ClampAmplification(), ClampByteRegister(), ClampDeadband(), ClampMinStartForce(), ServoController, Begin, CentreHere (+14 more)

### Community 27 - "Graphify Navigation Notes"
Cohesion: 0.25
Nodes (8): Document reading flow (router), Graphify extraction gaps (.ino and .css), Graphify-first navigation rule, ADR inclusion criteria, Open work lives only in docs/BACKLOG.md, Single-context documentation layout, How to pick up work, Why the code lives in src/

### Community 28 - "Travel Window ADRs"
Cohesion: 0.31
Nodes (9): ADR-0003 — Travel window is +/-90 output degrees, multi-turn off, No modulus-360 wrapping anywhere, ADR-0007 — Moves permitted while position is unverified, Remote site makes refusal less safe, not more, D1 — A move to a negative angle stops at 0, D2 — capture() can store a failed read as position 0, Suggested order, T4 — Moves while unverified: decided, permitted (+1 more)

### Community 29 - "Closed items"
Cohesion: 0.04
Nodes (49): Closed items, D10 — `logger.exception` swallows the exception; the sampler's real fault was a thread-safety bug in the SQLite layer, D11 — A single failed poll is presented as a disconnection, D12 — No way to return to the datum after activating a saved zero, D13 — Requests arriving faster than slots free up are refused, D14 — The most likely error in the system shows the operator "Failed to fetch", D15 — A command in flight looks identical to a command that did nothing, D16 — On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured (+41 more)

### Community 30 - "Core Backend Modules"
Cohesion: 0.06
Nodes (30): Design Notes, python/app/core/config.py, python/app/core/events.py, python/app/core/logging_setup.py, python/app/db/database.py, python/app/deps.py, python/app/relay/bridge_relay.py, python/app/repositories/abstract/servo_repository.py (+22 more)

### Community 31 - "Requirements Backlog (R-Items)"
Cohesion: 0.22
Nodes (11): The relay-capacity argument is unverified, Candidate ADR — how isolation, Lock and e-stop compose, R2 — Motor isolation: cut drive power, keep sensors alive, R3 — Confirm whether the Bridge could carry a frontend framework, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R5 — Metrics export and benchmarking output, R6 — Define 'stable' by benchmark, not by adjective, R6 — Define "stable" by benchmark, not by adjective (+3 more)

### Community 32 - "Logger Stub"
Cohesion: 0.18
Nodes (5): LoggerStub, Mirrors the real logger: the exception rides with the record. Must attach it,…, Returns the dotted event names recorded so far. Returns: Event names from…, Recording stub of Logger461's logger object., Records setup configuration. Args: **kwargs: Configuration values. Returns:…

### Community 33 - "get_state_store"
Cohesion: 0.06
Nodes (25): get_calibration_service(), get_state_store(), Returns the atomic servo/lock/baseline/isolation state store. Returns:…, Returns the calibration service. Returns: CalibrationService: The process-wide…, Cross-service integration flows (no HTTP): components working together., Telemetry sampler records a real movement profile., Overload flag reaches persisted telemetry., Calibration, saved positions, state store and motion interacting. (+17 more)

### Community 34 - "McuLog"
Cohesion: 0.18
Nodes (8): McuLog, _now_iso(), Returns current UTC time as an ISO-8601 string with milliseconds. Returns: str:…, Bridge receiver that writes MCU-originated events to their own file.…, Registers the Bridge callback for MCU logs., Handles one diagnostic record forwarded from the MCU. Args: level (int):…, Appends one JSON line, rotating the file past size threshold. Args: line…, Renames path to path.1 once grown past threshold. Args: path (str): The log…

### Community 35 - "The flows"
Cohesion: 0.11
Nodes (18): 1. superpowers — the methodology layer, 2. agentic-awesome-skills — the catalogue, 3. Arduino-Agent — the hardware seam, 4. IoT-SkillsBench — the evidence, and the argument for writing our own, Every flow ends the same way, Sources, The flows, Tooling to install first (+10 more)

### Community 36 - "get_isolation_service"
Cohesion: 0.08
Nodes (19): get_event_service(), get_isolation_service(), Returns the motor-isolation service. Returns: IsolationService: The process-…, Returns the shared event buffer. Returns: EventService: The process-wide event…, IsolationService: intent, reconciliation against hardware, idle backup., The idle timer only ever catches 'locked but forgot to isolate'., A deliberate un-isolate while still locked must not be immediately re-isolated…, Intent -> acknowledged hardware state, and never the reverse. (+11 more)

### Community 37 - "BridgeServoRepository"
Cohesion: 0.08
Nodes (18): BridgeServoRepository, Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position. Returns: bool: True when the servo…, Configures the servo dead-zone width. Args: counts (int): Dead-zone width in…, Configures single-turn or multi-turn absolute positioning. Args: multi_turn…, Cuts or restores drive torque while sensors stay powered. Args: enabled (bool):…, Reads register 0x28 directly. Returns: Optional[int]: Register value (0 or 1),…, Writes any subset of the control-loop tuning registers directly. Args:… (+10 more)

### Community 38 - "OnTarget.ino"
Cohesion: 0.16
Nodes (8): App, Begin, Tick, Check(), CheckNear(), MoveTo(), setup(), WaitSettled()

### Community 39 - "EventService"
Cohesion: 0.07
Nodes (35): EventDep, ge, le, EventService, In-memory ring buffer of structured events for the events endpoint., Thread-safe fixed-size store of recent events. Attributes: _events…, get, StreamingResponse (+27 more)

### Community 40 - "Deliver"
Cohesion: 0.20
Nodes (9): Deliver, Phase 0 — Orient (cheap, no approval needed), Phase 1 — Plan, then STOP, Phase 2 — Run it, all of it, Phase 3 — Hardware never runs unattended, Phase 4 — Verify, Phase 5 — Record, or it is not done, The rule that overrides your instincts (+1 more)

### Community 41 - "Coding Conventions Doc"
Cohesion: 0.10
Nodes (19): Architecture, Booleans and conditions, C++ (sketch side), Class docstrings carry `Attributes:`, Control flow, Conventions, Current gap against this standard, Database access (+11 more)

### Community 42 - "tests/conftest.py"
Cohesion: 0.13
Nodes (12): AppStub, client(), fixture, Shared test configuration: stubs, environment, and fixtures. Runs entirely on a…, FastAPI TestClient over a fresh app (sampler NOT started). Yields: The test…, The fresh simulated servo repository singleton. Returns: The simulator instance., Stub of the App loop runner., Does nothing. Returns: None. (+4 more)

### Community 43 - "d48_s26_campaign.py"
Cohesion: 0.06
Nodes (67): apply_config(), apply_config_resilient(), block_b0(), block_b1(), block_b2(), block_b3(), block_b4(), block_b5() (+59 more)

### Community 44 - "Tasks — detail"
Cohesion: 0.13
Nodes (14): T10 — Write the recovery runbook, in two halves, T11 — Write the operations manual, T13 — Distil the remaining documents, T18 — Front-end conventions, and split `app.js` by feature, T20 — Doc-truth sweep from the whole-app review, T21 — Constants and dead code with no shared source, T23 — Run graphify's semantic pass on the doc backlog it's never had, T24 — A screening filter judges only its first six trials, tainting the "futile" verdicts on the PID gains (+6 more)

### Community 45 - "jitter_probe.py"
Cohesion: 0.15
Nodes (19): main(), Rebuilds findings["trials"]["p1"], recomputes and prints the verdict. Returns:…, _append_csv(), _csv_path(), get(), latest_fine_approach_event(), main(), move() (+11 more)

### Community 46 - "ServoSnapshot"
Cohesion: 0.11
Nodes (17): ServoFaults, angle, overcurrent, overheat, overload, sensor, voltage, ServoSnapshot (+9 more)

### Community 47 - "D48 Session 26 — experiment regimen (pre-registration)"
Cohesion: 0.11
Nodes (18): 10. Handback to Opus, 1. What today's re-analysis of Session 25's own data changed, 2. Design principles (each answers a specific defect above), 3. Outcome measures and estimands, 4. Hypotheses, 5. Blocks, in order. Each checkpoints per trial and resumes., 6. Code changes required, 7. Contingencies — pre-declared, so the run does not need me to improvise (+10 more)

### Community 48 - "Rig Testing Protocol Doc"
Cohesion: 0.14
Nodes (13): 1. Physical Architecture & Kinematics (Per Documentation), 2. Pre-Test Inspection & Mechanical Setup Checklist, 3. The 7 Rigorous Test Protocols, 4. Post-Test Data Archival & Backlog Sign-Off, Mechanical Rig Test Protocol: 44:30 Belt Reduction & Rotary Drive, Motion & Coordinate Invariants, Protocol 1: Mid-Travel Datum Calibration & Belt Backlash, Protocol 2: R2 Motor Isolation & Hand-Turn Dynamics (T17 Acceptance) (+5 more)

### Community 49 - "TinyTest.h"
Cohesion: 0.22
Nodes (7): main(), Registered, fn, name, Registrar, RunAll(), TestFn

### Community 50 - "Relay Connection Ceiling"
Cohesion: 0.38
Nodes (7): ADR-0001 — Network path runs through the MCU, kMaxRelaySockets = 6 is the only connection ceiling, D4 — Connection drops after a few commands, D6 — App load time is sometimes slow, R1 — Determine the real concurrent-operator ceiling, T8 — Instrumented run on the board over adb, Served from the board to any machine on the network

### Community 51 - "Early Defects List"
Cohesion: 0.20
Nodes (10): D2 — `capture()` can store a failed read as position 0, D3 — The C++ side has no logging, D4 — Connection drops after a few commands; requires a page refresh, D5 — Log output is connect/disconnect noise, D5 — Log output is dominated by connect/disconnect noise, and is not useful, D7 — UI is not verified on small operator screens, D8 — `.env` must be created before the first run of this version, Defects (+2 more)

### Community 53 - "ServoStateView"
Cohesion: 0.05
Nodes (63): CalibrationDep, IsolationDep, MotionDep, Coherent snapshot of servo, lock, and baseline state. Attributes: output_deg…, ServoStateView, get_present_speed(), get_state(), get_torque_register() (+55 more)

### Community 54 - "System Audit Doc"
Cohesion: 0.15
Nodes (12): 1. A reading now carries its own validity, 2. Calibration refuses a reading the servo never gave, 3. Unreachable targets are refused, not clamped, 4. The default baseline is the CENTRE of travel, not zero, 5. Calibration warns when the datum is off-centre, 6. Bridge access is serialised (previous round), Answering "did we even test the sketch?", Full-system audit (+4 more)

### Community 55 - "Soak Test Checkpointer"
Cohesion: 0.15
Nodes (12): Checkpointer, Any, Orchestrates synthetic operators during a soak test. Args: host (str): Board…, Builds a comprehensive summary dictionary. Returns: dict[str, Any]: Detailed…, Periodically prints status and persists checkpoint reports., Initializes checkpointer., Executes the checkpoint loop until stopped., Prints a live summary line and rewrites the report file. (+4 more)

### Community 56 - "d48_decisive_watch.py"
Cohesion: 0.14
Nodes (20): interim_read_p1(), interim_read_p2(), load_state(), log(), main(), milestone_floor(), milestone_p1(), milestone_p3() (+12 more)

### Community 57 - "Hardware Config Fallback"
Cohesion: 0.33
Nodes (6): Missing python/.env silently runs the simulator, ADR-0004 — Repository abstraction with a simulated backend, D8 — .env must be created before the first run, cp .env.board .env — the only manual deploy step, run_dev.py — dev-PC entrypoint, Going live is a configuration flag

### Community 58 - "test_jitter_probe.py"
Cohesion: 0.12
Nodes (11): Unit tests for tools/jitter_probe.py's scoring logic (D48). Synthetic traces…, An empty trace (network failure mid-probe) reports None, not a crash., Current is summarised over the score window only, for the mechanism read., Builds a (elapsed_s, output_deg, current_a) trace from short samples. Args:…, A move that reaches target and stays there registers no failure., The false-negative D48 exists to close: not reaching target must FAIL., TestCleanSettle, TestCurrentStats (+3 more)

### Community 59 - "Soak Report Tests"
Cohesion: 0.06
Nodes (45): _israel_time(), fixture, Path, tools/soak_report.py: the UTC/local cutoff bug (D30), regression-guarded, plus…, Tests for print_r1_scorecard() and report_telemetry() anomaly detection., Forces a non-UTC timezone (IDT, UTC+3 in August) for this module. Returns: None., A record just outside the local cutoff but inside the UTC one., Pins _utc_cutoff() itself: the helper both call sites share. (+37 more)

### Community 60 - "Details"
Cohesion: 0.17
Nodes (11): Caveats, Details, Key Findings, Load-Dependent Settling Oscillation in a Geared STS3215 Serial-Bus Servo: Diagnosis and Remedies, Q1 — Literature on load-induced resonant limit cycles vs Coulomb stick-slip; diagnostic signatures; is 10 Hz logging enough?, Q2 — Standard remedies for load-induced resonance (as distinct from friction remedies), Q3 — STS3215 registers/features beyond position P/I/D, MinStartForce and dead zone, Q4 — Does overshoot-and-return anti-backlash interact badly with resonance, and is there a better technique? (+3 more)

### Community 61 - "TelemetrySample"
Cohesion: 0.08
Nodes (23): Immutable domain entities shared across layers., One persisted telemetry row. Attributes: timestamp (float): Unix timestamp of…, TelemetrySample, ABC, Abstract persistence of telemetry samples., Contract for storing and querying telemetry history., Persists one sample. Args: sample (TelemetrySample): The sample to store., Counts samples in range and returns count and base timestamp. Args: ts_from… (+15 more)

### Community 62 - "SavedPositionService"
Cohesion: 0.11
Nodes (20): NotFoundError, Raised when a referenced entity does not exist., Raised when an edit targets a saved position changed since it was read., StalePositionError, A saved position enriched with its live angle, for display. Attributes: id…, SavedPositionView, Saved positions: named, described points the operator can return to., Deletes a saved position. Args: position_id (int): Database identifier.… (+12 more)

### Community 63 - "Synthetic Operator Tests"
Cohesion: 0.06
Nodes (20): Unit tests for tools/synthetic_operator.py., Stream frame reception and inter-arrival jitter calculation., Tests for quantize_deg() step quantization., Exact multiples of 0.06 deg should remain unchanged., Arbitrary floating point angles snap to nearest 0.06 grid., Tests for classify_settle_result() convergence classification., A measured angle equal to the commanded one always converges., A small deviation inside the stated tolerance still converges. (+12 more)

### Community 64 - "test_telemetry_service.py"
Cohesion: 0.14
Nodes (12): get_telemetry_repository(), Returns the telemetry repository. Returns: TelemetryRepository: The process-…, fixture, TelemetryService: sampling, CSV export, retention timing., Fresh telemetry service (sampler NOT started). Returns: The service under test., A stalled bus must leave a gap, not a row claiming position 0. Seven such rows…, The stored row must come from a single coherent read. The row used to be…, Single-sample persistence. (+4 more)

### Community 65 - "Defects — detail"
Cohesion: 0.14
Nodes (13): D28 — MCU boot-time `mcu_log` notify lost to a startup race, D36 — Several tests construct their own `Database` and never close it, D41 — Firmware commands real moves off failed reads and malformed payloads, D42 — Errors that vanish: SSE stream, migration, sqlite writes, D43 — Guards that fail open on an invalid read, D44 — Operator-facing UI gaps found by the whole-app review, D45 — Relay and firmware robustness gaps found by the whole-app review, D46 — Backend robustness gaps found by the whole-app review (+5 more)

### Community 66 - "ServoBus"
Cohesion: 0.25
Nodes (13): ServoBus, Ping, ReadByte, ReadWord, Refresh, retries_, ServoBus::ServoBus(), WriteByte (+5 more)

### Community 67 - "Backlog R-Items"
Cohesion: 0.25
Nodes (7): R11 — Accept any typed angle; snap to the nearest step and show the delta, R12 — Extended travel: soft limit ±90°, hard limit ±95°, confirmed in between, R1 — Determine the real concurrent-operator ceiling, R4 — Post-MVP: mechanical restraint servos, unified under one Lock, R7 — Handover logistics depend on adapter delivery, R8 — Emergency stop, R-items — detail

### Community 68 - "Ordering, rewritten 8 August 2026 — by session, with sizes"
Cohesion: 0.13
Nodes (15): Batch 1 — Desk work, no board — **DONE 8 August 2026**, Batch 2 — Make the machine diagnosable — **DONE 8 August 2026** (desk work), Batch 3 — The measurement session (board, supervised, one long run), Batch 4 — The two unbuilt MVP features, Batch 5 — The handover pack, Batch 6 — Mechanical, suits an executing agent, D35 — Commanded speed and actual speed disagree by roughly 1.5-2x, D40 — A move settles short under load and re-commanding the same target does not correct it (+7 more)

### Community 69 - "Details"
Cohesion: 0.15
Nodes (12): Caveats, Details, Key Findings, Q1 — Does quantizer-limit-cycle theory predict the non-monotonic D response, or is D the wrong axis?, Q2 — Why does softening the final corrective leg make settling reliably worse?, Q3 — Is "residual belt energy that a coarse velocity estimate already calls stopped" a named phenomenon?, Q4 — What causes consistent left/right asymmetry when the control law is direction-symmetric?, Q5 — Predictions and test plan for the untouched velocity loop (37/39) and acceleration (41) (+4 more)

### Community 70 - "Hardware Bench Facts"
Cohesion: 0.67
Nodes (4): The 44:30 belt reduction is the whole point, Bench-verified hardware facts, Confirm the Ethernet patch survived the first build, Apply SpiRemap twice

### Community 71 - "Firmware Prose Strip Task"
Cohesion: 0.20
Nodes (9): A — Doxygen doc comments (`///` and `/** */` blocks), B — inline comments, C — relocate what is not already written down, Constraints, D — two comment classes that need special handling, found the hard way, Report back, Scope, Task: strip explanatory prose from sketch/src/ (+1 more)

### Community 72 - "IsolationService"
Cohesion: 0.14
Nodes (11): Event, One operator-facing event. Attributes: timestamp (str): ISO timestamp. event…, Stores one event. Args: event (str): Dotted event identifier. message (str):…, Returns the newest events, newest first. Args: limit (int): Maximum number of…, IsolationService, Writes intent to the database so it survives a restart. Args: isolated (bool):…, Manages motor isolation intent, reconciliation, and idle timeout. Attributes:…, Sets operator intent and reconciles it immediately. Args: isolated (bool):… (+3 more)

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

### Community 77 - "TuningSnapshot"
Cohesion: 0.12
Nodes (14): MoveCommand, acceleration, speed_counts_per_second, target_counts, TuningSnapshot, ccw_dead_zone, cw_dead_zone, min_start_force (+6 more)

### Community 78 - "_findings"
Cohesion: 0.22
Nodes (8): _findings(), The branch decision: does arrival direction explain the miss?, A floor ships only if every trial passed., Builds one synthetic trial record shaped like run_trial writes. Args:…, Wraps trial records in a findings structure keyed the way the tool keys it.…, TestFloorVerdicts, TestVerdictP1, _trial()

### Community 79 - "_ScriptedArm"
Cohesion: 0.13
Nodes (12): _fast_settle(), Reproduces how this servo actually lands, so the correction loop can be tested…, Records the commanded angle and lands the arm. Args: counts (int): Absolute…, Shrinks the landing-quiet window so tests do not wait on real time. Args:…, The overshoot is placed by the target's sign, not by where the move started.…, Runs one move and returns the angle of its overshoot leg. Args: monkeypatch:…, The move is not done when the servo acknowledges it, but when the arm is…, Several operators watch the same arm. If it reads HOLDING between its own legs… (+4 more)

### Community 80 - "BridgeApi.cpp"
Cohesion: 0.21
Nodes (22): bin_t, Ack(), BridgeApi, DrainDiagLog, FormatSnapshot, Register, FieldAt(), ForwardDiagLog() (+14 more)

### Community 81 - "get_app_state_repository"
Cohesion: 0.17
Nodes (7): get_app_state_repository(), Returns the persisted operator-intent repository. Returns: AppStateRepository:…, The 'earlier reference' signal shown beside a drifted angle., Clearing the 'earlier reference' tag without editing the position., Seeds a position saved before the datum, without touching the real clock - a…, TestDismissReference, TestStaleReference

### Community 83 - "test_simulated_servo.py"
Cohesion: 0.13
Nodes (5): SimulatedServoRepository: motion, deadband, faults, signed multi-turn., configure_range records the travel-range mode., TestDeadband, TestFaults, TestRangeConfiguration

### Community 84 - "test_d48_decisive.py"
Cohesion: 0.15
Nodes (8): _isolate_findings_path(), fixture, Unit tests for tools/d48_decisive.py's geometry and verdict logic (D48). No…, Redirects every save_findings() call in this module to a temp file. `decide()`,…, A post-hoc floor probe must not run without P1's direction rule., The run must end with a recommendation or a named blocker., TestDecision, TestPhaseProbeGuardsMissingP1

### Community 85 - "bridge_servo_repository.py"
Cohesion: 0.11
Nodes (12): decode_sign_magnitude(), Servo access through the Bridge to the MCU., Decodes a sign-magnitude field from the servo wire format. Args: value (int):…, parametrize, The wire-format decoder stays available to callers., Every documented status bit maps to its own flag., TestFaultBits, TestSignMagnitude (+4 more)

### Community 86 - "log"
Cohesion: 0.20
Nodes (14): flat_trials(), log(), phase_p2a(), phase_p2b(), phase_probe(), Prints a timestamped line. Args: msg (str): Message to print., Returns every trial in a phase matching the given field values. Args: findings…, Summarises one floor across every angle it was tested at. Args: findings… (+6 more)

### Community 88 - "Synthetic Operator Script"
Cohesion: 0.15
Nodes (25): classify_settle_result(), find_minimum_effective_step(), _probe_get_state(), _probe_move(), _probe_wait_settle(), quantize_deg(), Synthetic operators that drive the running board like people would. Written for…, Protocol C: approach fresh, observe a shortfall, then re-command. Stages away… (+17 more)

### Community 89 - "Backlog Index Doc"
Cohesion: 0.25
Nodes (7): Backlog, T1 — Apply `CONVENTIONS.md` across the codebase, T4 — Moves while unverified: DECIDED, permitted, T5 — Add `design_diagrams/` with PlantUML, T6 — Restructure the exception hierarchy, T7 — Add the database abstraction, Tasks

### Community 90 - "test_saved_position_service.py"
Cohesion: 0.08
Nodes (16): PositionOutOfRangeError, Raised when a saved position's angle falls outside the travel window., fixture, SavedPositionService: create, edit, delete, go, and their refusals., The change counter the SSE stream polls., Fresh saved-position service. Returns: The service under test., Creating a saved position., Editing a saved position. (+8 more)

### Community 95 - "Closed Sessions Doc"
Cohesion: 0.25
Nodes (7): Not in these three sessions, Session 1, Batch 1 — DONE, 8 August 2026, Session 1, Batch 2 — DONE, 8 August 2026, Session 2 — The soak — IN PROGRESS, Session 3 — SSE first, then Batch 4, START HERE — the session plan, Suggested order — SUPERSEDED 8 August 2026

### Community 96 - "BridgeRelay"
Cohesion: 0.16
Nodes (9): BridgeRelay, socket, Streams FastAPI reply bytes back down to the sketch. Args: slot (int):…, Closes and forgets one mirrored connection. Args: slot (int): Connection slot…, Byte pump between the sketch's network clients and FastAPI. Attributes:…, Registers all Bridge callbacks., Handles a new network client reported by the sketch. Args: slot (int):…, Forwards client bytes to FastAPI. Args: slot (int): Connection slot identifier.… (+1 more)

### Community 97 - "Domain Glossary"
Cohesion: 0.29
Nodes (6): Control and safety, Language, MCU boundary, Position and geometry, Servo MVP — context, Telemetry

### Community 98 - "Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start)"
Cohesion: 0.18
Nodes (10): Committed (~13.25h claude/operator-serial / 13.5h capacity — pulled in, Committed (~17.5h est. / ~21.35h effective capacity — ~82%), Jira-pasteable blocks, Jira-pasteable blocks, Retro (fill in at sprint close), Retro (sprint closed 6 Sept 2026, on starting the next one), Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start), Sprint: 6–10 Sept 2026 (Sun–Thu, work week) (+2 more)

### Community 100 - "MotionService"
Cohesion: 0.08
Nodes (19): MotionService, Records the single 'move accepted' event and its log line. Args: target_deg…, Stops the current move at the present position. Raises:…, Changes the digital lock, honoring the optional move guard. Args: locked…, Clears a tripped overload fault by re-commanding the position. Raises:…, Records and raises a non-acknowledgement, never a false success. Args: event…, Records a failure event and logs it at error level. Args: event (str): Event…, Decides whether the anti-backlash approach applies. Args: start_deg… (+11 more)

### Community 101 - "TelemetryService"
Cohesion: 0.16
Nodes (8): Samples until stopped, at the configured interval., Reads one coherent snapshot and persists it., Applies retention at the configured interval., Persists the full sensory input every sampler interval. Attributes: _telemetry…, Starts the background sampling thread., Stops the background sampling thread, if one was started., Packs telemetry samples in range into a compact binary byte stream. Args:…, TelemetryService

### Community 102 - "Bridge Payload Contract"
Cohesion: 0.33
Nodes (6): Three verification commands (186 / 164 / agree), ADR-0006 — Bridge payloads are CSV strings, Field order is a contract, Current status — everything exists, nothing is stable, Bridge contract checker, The Bridge payload contract with Python

### Community 127 - "D48 Session 26 — runbook for the executing agent"
Cohesion: 0.18
Nodes (10): 1. Hard rules, 2. Prerequisites, 3. Setup, 4. Run it, 5. What each verdict means for you, 6. Contingencies — apply by row, do not improvise, 7. Data to keep, 8. Write-up — you do this yourself this session (+2 more)

### Community 128 - "routers/saved_positions.py"
Cohesion: 0.09
Nodes (39): delete, patch, PositionsDep, create_position(), delete_position(), dismiss_all_stale_references(), dismiss_reference(), go_to_position() (+31 more)

### Community 129 - "Brace Balance Checker Script"
Cohesion: 0.32
Nodes (7): check_file(), main(), Path, Brace-balance check for sketch/src/ files the native suite can't compile.…, Removes // and /* */ comments and "..."/'...' literals. Args: text (str): Raw…, Returns the file's final brace depth (0 means balanced). Args: path (Path):…, strip_comments_and_strings()

### Community 131 - "TelemetrySnapshot"
Cohesion: 0.09
Nodes (18): Instantaneous sensory readout from the servo layer. Attributes: raw_counts…, TelemetrySnapshot, Returns the full instantaneous sensory readout. Returns: TelemetrySnapshot:…, Builds the reading used when the bus did not answer. Returns:…, Reads one coherent snapshot from the servo. Returns: TelemetrySnapshot: The…, Performs one real bus read. Returns: TelemetrySnapshot: The snapshot or empty…, Calibrating on a dead bus must refuse, not store a datum., A failed read yields no numbers at all, not a position alone. D16.… (+10 more)

### Community 132 - "SavedPosition"
Cohesion: 0.12
Nodes (16): A named, described position an operator can return to. Attributes: id…, SavedPosition, Deletes one saved position. Args: position_id (int): Database identifier.…, Stores saved positions in the saved_positions table. Attributes: _db…, Records an acknowledgement, touching only dismissed_at. Args: position_id…, Maps a database row to the entity. Args: row (object): SQLite row. Returns:…, Persists a new saved position. Args: position (SavedPosition): Entity with…, Returns all saved positions, newest first. Returns: list[SavedPosition]: All… (+8 more)

### Community 133 - "export_binary"
Cohesion: 0.29
Nodes (7): alias, export_binary(), get, Query, StreamingResponse, Exports compact packed binary telemetry data for client-side rendering. Args:…, TelemetryDep

### Community 134 - "save_findings"
Cohesion: 0.20
Nodes (12): anchor_for(), apply_floor(), decide(), phase_p3(), quantize(), Emulates the missing software fix and reports whether it converges.…, Combines every verdict into one recommendation, or names the blocker. Args:…, Writes the findings file atomically. A plain in-place write races with this… (+4 more)

### Community 135 - "NetworkRelay"
Cohesion: 0.08
Nodes (30): GPIO_TypeDef, k_timeout_t, ByteSink, CloseSink, OpenSink, ByteSink, CloseSink, OpenSink (+22 more)

### Community 136 - "TuningRegisters"
Cohesion: 0.20
Nodes (6): Diagnostic read of the servo's control-loop tuning registers. speed_p and…, TuningRegisters, Reads the control-loop tuning registers directly. Returns:…, Reads the position-loop tuning registers directly. Returns:…, Simulated servo: sprint-1 stand-in for the real serial bus., Returns the tuning registers as last written, or factory default. Returns:…

### Community 139 - "._init_schema"
Cohesion: 0.29
Nodes (3): Carries the old zeros table's rows into app_state and saved_positions., Creates tables and indexes when missing., Adds columns introduced after a database was first created.

### Community 141 - "wait_until"
Cohesion: 0.06
Nodes (30): get_motion_service(), get_saved_position_service(), Returns the motion service. Returns: MotionService: The process-wide motion…, Returns the saved-position service. Returns: SavedPositionService: The process-…, Polls a predicate until true or timeout. Args: predicate: Zero-argument…, wait_until(), _events(), motion() (+22 more)

### Community 143 - "Soak Test Runner"
Cohesion: 0.50
Nodes (4): main(), Parses arguments and runs the soak., Queries board status and prints pre-flight diagnostics. Args: host (str): Board…, run_preflight()

### Community 146 - "Jira Import — Servo MVP"
Cohesion: 0.33
Nodes (5): Committed, Jira Import — Servo MVP, Section A — Current Sprint (30 August – 3 September 2026), Section B — Backlog (not yet scheduled into a sprint), Stretch (attempted only if the committed work above finishes with time left)

### Community 150 - "D48 follow-up deep-research prompt (prepared, not yet run)"
Cohesion: 0.40
Nodes (4): D48 follow-up deep-research prompt (prepared, not yet run), The prompt itself, What to do with the answer, Why a second pass

### Community 152 - "SavedPositionRepository"
Cohesion: 0.12
Nodes (10): ABC, Abstract persistence of saved positions., Contract for storing and editing saved positions., Persists a new saved position. Args: position (SavedPosition): Entity with…, Returns all saved positions, newest first. Returns: list[SavedPosition]: All…, Returns one saved position by id. Args: position_id (int): Database identifier.…, Overwrites a saved position's editable fields. Args: position_id (int):…, Deletes one saved position. Args: position_id (int): Database identifier.… (+2 more)

### Community 153 - "2. The ST3215 servo"
Cohesion: 0.08
Nodes (23): 1. This is not a normal Arduino, 2. The ST3215 servo, 3. Geometry — and the one law that matters, 4. The Ethernet-shield relay, 5. The Bridge contract, 6. Symptom → cause, 7. Deployment traps, 8. Working rules (+15 more)

### Community 154 - "test_motion_service.py"
Cohesion: 0.07
Nodes (43): CommandNotAcknowledgedError, ConflictException, IsolatedError, LockedAndIsolatedError, LockedError, MovingError, NotFoundException, OutOfTravelError (+35 more)

### Community 155 - "TestAddQuery"
Cohesion: 0.29
Nodes (4): Builds a sample. Args: timestamp: Unix timestamp. overload: Overload flag…, Persistence round-trips., _sample(), TestAddQuery

### Community 156 - "TestTorque"
Cohesion: 0.12
Nodes (5): Mirrors the real controller's un-isolate ordering: the target snaps to wherever…, Nothing in this repository writes these registers - it must report what an…, Velocity-loop gains must round-trip like the position-loop ones. speed_i is the…, Motor isolation: cutting torque must stop the shaft actually moving, not just…, TestTorque

### Community 157 - "FlakyServo"
Cohesion: 0.15
Nodes (8): flaky(), FlakyServo, fixture, Wraps the real simulator but can be told to refuse the next torque…, Swaps the cached servo repository for one whose ack is controllable, for the…, The sampler thread survives sampling failures., The record must carry the cause, not just the fact. A live board run on 7…, TestSamplerResilience

### Community 163 - "test_logging_setup.py"
Cohesion: 0.40
Nodes (3): Logging setup: Logger461 wiring., setup_logging passes the configured sink values to Logger461., TestSetupLogging

### Community 164 - "d48_bracket_sweep.py"
Cohesion: 0.67
Nodes (6): apply_config_resilient(), load_findings(), log(), main(), probe_resilient(), save_findings()

### Community 165 - "d48_multi_angle_sweep.py"
Cohesion: 0.67
Nodes (6): apply_config_resilient(), load_findings(), log(), main(), probe_resilient(), save_findings()

### Community 166 - "main"
Cohesion: 0.20
Nodes (10): acquire_servo_lock(), load_findings(), main(), print_decision(), print_plan(), Prints the final decision block. Args: decision (dict): The decision from…, Prints what the run will do, without touching hardware., Takes an exclusive lock, so two runs can never drive one servo. Two overlapping… (+2 more)

### Community 167 - "post"
Cohesion: 0.33
Nodes (8): get(), main(), post(), Sends one POST and decodes the reply. Args: base_url (str): API base URL. path…, Sends one GET and decodes the reply. Args: base_url (str): API base URL. path…, Polls until the servo answers a register read with real values. Args: base_url…, Runs the recovery sequence. Returns: int: Process exit code., wait_for_servo()

### Community 168 - "score_trial"
Cohesion: 0.33
Nodes (6): _median(), Returns the population standard deviation, or None for <2 values. Args: values…, Returns the median of a list, or None if it is empty. Args: values…, Scores one trial's position/current trace against D48's pre-registered outcome.…, score_trial(), _stdev()

### Community 170 - "SimulatedServoRepository"
Cohesion: 0.07
Nodes (14): Starts a move toward an absolute counts target. Args: target_counts (int):…, Stops motion at the current position. Returns: bool: Always True on simulated…, Records the range configuration. Args: multi_turn (bool): Enable multi-turn…, Configures the simulated dead-zone width. Args: counts (int): Dead-zone width…, Cuts or restores simulated drive torque. Args: enabled (bool): True to restore…, Returns the simulated torque state. Returns: int: 1 when torque is enabled, 0…, Records any subset of the control-loop tuning registers. Args: position_p…, Returns the simulated present speed, signed toward the target. Returns: int:… (+6 more)

### Community 172 - "TestDismissAllStaleReferences"
Cohesion: 0.33
Nodes (3): Clearing every currently-tagged position in one call., Seeds one position saved before the datum and one saved after (this one created…, TestDismissAllStaleReferences

### Community 174 - "d48_recover_s26_findings.py"
Cohesion: 0.50
Nodes (4): main(), _phase_arm(), Splits a CSV tag back into (phase, arm), the way the tool wrote it. Args: tag…, Rebuilds every phase's trials and derived analysis, then saves. Returns: int: 0…

### Community 176 - "TestSamplerLifecycleIsolation"
Cohesion: 0.33
Nodes (4): D26: a sampler thread that outlived its test used to log into a later test's…, The ordering itself is the fix - proven directly, not risked. An earlier…, The same mechanism, for MotionService's own background thread - added once that…, TestSamplerLifecycleIsolation

### Community 177 - "verdict_p1"
Cohesion: 0.33
Nodes (6): phase_p1(), _rate(), Returns the fraction of trials whose boolean field is True. Args: trials…, Decides whether arrival direction explains the positioning miss. Two things are…, Tests the arrival-direction hypothesis at one known-quiet floor. Args: base_url…, verdict_p1()

### Community 246 - "TestCommands"
Cohesion: 0.05
Nodes (5): Commands become the payloads the sketch parses., The ack is load-bearing here too: a caller must never believe a move was…, The ack is load-bearing for this one command: callers must never believe…, A sketch without the velocity-loop fields must read as failure. The payload is…, TestCommands

### Community 279 - "Skills archive"
Cohesion: 0.25
Nodes (7): Considered and left out, Skills archive, Sources, The gap this archive does not fill, What's here, What was stripped, and why, Why the big one is not tracked

### Community 288 - "Failed Read Handling"
Cohesion: 0.29
Nodes (6): A failed read is reported as unknown, never as a number, Consequences, Extended, 8 August 2026 — `valid` governs the whole snapshot, Status, The alternative that was considered, Why

### Community 302 - "TestIsolate"
Cohesion: 0.11
Nodes (8): Two different gates must surface as two different reasons - an operator refused…, GET /api/v1/servo/diagnostics/torque_register - diagnostic, independent of the…, GET /api/v1/servo/diagnostics/tuning_registers - the readback this delivery…, GET /api/v1/servo/diagnostics/present_speed - grounds D40c's creep-speed…, POST /api/v1/servo/diagnostics/tuning_registers - the measurement-campaign…, The velocity loop is reachable over the same diagnostic route. speed_i is the…, POST /api/v1/servo/isolate, and its refusal of a move., TestIsolate

### Community 303 - "Operator Lens Skill"
Cohesion: 0.25
Nodes (7): Also wear the client's hat, Operator lens, Output — file it, do not just say it, Rule zero, The control surface, The five questions, per control, The four failures worth memorising

### Community 344 - "test_bridge_relay.py"
Cohesion: 0.07
Nodes (16): echo_server(), fixture, BridgeRelay: connection mirroring, byte pumping, teardown paths., Remaining failure branches., Local TCP server standing in for FastAPI; echoes received bytes back prefixed…, Behavior when the board runtime is absent (dev PC)., Fresh registered relay. Returns: The relay under test., Bridge callback registration. (+8 more)

### Community 351 - "test_servo_routes.py"
Cohesion: 0.06
Nodes (17): Servo API routes: state, move, stop, lock, calibrate, recover., POST /api/v1/servo/calibrate., POST /api/v1/servo/recover., guard_move_to_lock surfaces as 409 reason=moving., An unreachable target must be refused, not silently clamped., POST /api/v1/servo/move., The refusal carries the configured step, not a hardcoded one. A regression…, POST /stop and /lock. (+9 more)

### Community 397 - "get_settings"
Cohesion: 0.05
Nodes (60): BaseSettings, FastAPI, create_app(), FastAPI application assembly: routers and domain-error mapping., Creates and configures the FastAPI application. Returns: FastAPI: The…, Maps every domain exception to its HTTP response and log line. Args: app…, _register_error_handlers(), get_settings() (+52 more)

### Community 399 - "BridgeStub"
Cohesion: 0.07
Nodes (18): BridgeStub, Recording stub of the Arduino Bridge., Clears recorded state between tests. Returns: None., Records a provided callback. Args: name: Bridge function name. fn: The…, Records a call and returns the configured result. Args: name: Bridge function…, System API routes: health and events., GET /api/v1/system/events., Health reporting when the board runtime is absent. (+10 more)

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
- **467 isolated node(s):** `state`, `REFUSALS`, `EVENT_LABELS`, `DAY_SHEET_COLS`, `RAW_HEADERS` (+462 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **41 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_state_store()` connect `get_state_store` to `deps.py`, `test_telemetry_service.py`, `TelemetrySnapshot`, `get_isolation_service`, `test_saved_position_service.py`, `Relay E2E Tests`, `EventService`, `wait_until`, `get_settings`, `_ScriptedArm`, `get_app_state_repository`, `ServoStateStore`, `test_motion_service.py`, `FlakyServo`, `test_servo_routes.py`?**
  _High betweenness centrality (0.049) - this node is a cross-community bridge._
- **Why does `TelemetrySnapshot` connect `TelemetrySnapshot` to `deps.py`, `get_state_store`, `test_telemetry_service.py`, `BridgeServoRepository`, `TuningRegisters`, `TestExport`, `SimulatedServoRepository`, `TestIsolate`, `TestSamplerLifecycleIsolation`, `bridge_servo_repository.py`, `FlakyServo`, `ServoStateStore`, `TelemetrySample`, `TestTravelWindow`, `test_servo_routes.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `ServoStateStore` connect `ServoStateStore` to `deps.py`, `get_state_store`, `MotionService`, `TelemetryService`, `EventService`, `IsolationService`, `ServoStateView`, `SavedPositionRepository`, `test_motion_service.py`, `SavedPositionService`?**
  _High betweenness centrality (0.029) - this node is a cross-community bridge._
- **Are the 18 inferred relationships involving `ServoStateStore` (e.g. with `CalibrationService` and `IsolationService`) actually correct?**
  _`ServoStateStore` has 18 INFERRED edges - model-reasoned connections that need verification._
- **Are the 23 inferred relationships involving `SavedPosition` (e.g. with `SavedPositionRepository` and `SqliteSavedPositionRepository`) actually correct?**
  _`SavedPosition` has 23 INFERRED edges - model-reasoned connections that need verification._
- **Are the 32 inferred relationships involving `TelemetrySnapshot` (e.g. with `ServoRepository` and `BridgeServoRepository`) actually correct?**
  _`TelemetrySnapshot` has 32 INFERRED edges - model-reasoned connections that need verification._
- **What connects `state`, `REFUSALS`, `EVENT_LABELS` to the rest of the system?**
  _467 weakly-connected nodes found - possible documentation gaps or missing edges._