# Design Notes

Distilled facts, rationale, and implementation details relocated from source docstrings and comments.

## sketch/src/Config.h

- **Bus read retries**: `kBusReadRetries = 4` to handle transient single-register misses on the half-duplex servo bus.
- **Log ring capacity and drain pacing**: `kLogRingCapacity = 32` absorbs event bursts between `Tick()` drains without consuming RAM; `kMcuLogDrainPerTick = 4` bounds Bridge notifications per pass to ensure `loop()` yields (RELAY_NOTES.md rule 3).
- **Socket allocations**: W5500 provides 8 hardware sockets; 1 is consumed by the listener and 6 are allocated for client relay slots (`kMaxRelaySockets = 6`), leaving 1 spare.

## sketch/src/LogRing.h

- **String storage in LogRecord**: `LogRecord` stores raw `const char*` pointers expected to reference flash-resident literals (`F(...)`), avoiding dynamic allocation in the ring buffer.
- **Eviction policy**: When full, `LogRing::Push()` overwrites the oldest entry to retain the freshest state and increments `dropped_total_` to monitor drain lag.

## sketch/src/ServoRegisters.h

- **Torque constant scaling**: `kKgCmPerAmp = 11.0F` derived from the 12V ST3215 model stall rating: `2.7 A * 11.0 kg·cm/A = 29.7 kg·cm` (~30 kg·cm rated stall torque).
- **Sign bit locations**: STS multi-turn position and speed fields use bit 15 (`kPositionSignBit = 15`), whereas the EEPROM position offset register (0x1F) uses bit 11 (`kOffsetSignBit = 11`).

## sketch/src/DiagLog.h

- **Global sink pattern**: Process-wide static ring and mutex avoids threading references through every subsystem; drained exclusively by `BridgeApi::DrainDiagLog()` from `Tick()` outside locks (RELAY_NOTES.md rule 7 note).

## sketch/src/ServoBus.h / sketch/src/ServoBus.cpp

- **EEPROM write preservation**: `WriteEepromByte` and `WriteEepromWord` read current register values first and return immediately if unchanged, avoiding EEPROM write-cycle wear.
- **Telemetry refresh failure logging**: `ServoBus::Refresh()` logs `mcu.servo.refresh_failed` as a distinct event rather than folding into byte/word failures because persistent refresh exhaustion indicates bus stalls.

## sketch/src/ServoController.h / sketch/src/ServoController.cpp

- **SCServo Ack return convention trap**: `EnableTorque` and `WritePosEx` return `Ack()`'s 0 (fail) / 1 (success) convention, *never* -1. Comparing against `-1` causes failed writes to be treated as success.
- **Reachability guard defence-in-depth**: `ServoController::Move()` verifies `0 <= target_counts < 4096` before dispatching to `WritePosEx`, protecting against silent hardware clamping and logging `mcu.servo.move_rejected_out_of_range` if Linux reachability checks failed or diverged.
- **Re-command before torque enable**: Restoring torque re-commands the current position while torque is still off to prevent the servo from snapping to a stale goal or a manually displaced position upon re-energising.
- **Position mode invariant**: `ConfigureRange` enforces mode 0 (position mode) for both single-turn and multi-turn; mode 3 (step mode) is relative stepping and invalid for absolute positioning.

## sketch/src/NetworkRelay.h / sketch/src/NetworkRelay.cpp

- **Running total diagnostic args**: In `WriteToClient` and `Poll` rejection logs, event arguments carry running totals (`write_lock_timeouts_`, `rejected_total_`) so offline analysis (`soak_report.py`) can detect dropped log records.
- **Thread lock and callback sequencing**: `chip_lock_` is always released before invoking `OpenSink`, `ByteSink`, or `CloseSink` callbacks to prevent deadlocking with Bridge thread calls (`net_tx`/`net_shutdown`) (RELAY_NOTES.md rule 7).

## sketch/src/BridgeApi.h / sketch/src/BridgeApi.cpp

- **get_status signature**: `HandleGetStatus` takes zero parameters because Python calls `get_status` without payload; adding a parameter prevents Bridge method binding.
- **uptime_s roll-over prevention**: `ForwardDiagLog` converts `uptime_ms` to whole seconds before sending via Bridge so that 32-bit integer representations do not overflow after ~24.8 days during extended runs.
- **Health status diagnostic metrics**: `HandleGetStatus` appends `relay=<conn>/rejected=<rej>` and `diag_dropped=<dropped>` to the health string to surface network exhaustion and log drop metrics to operator health checks.
- **CentreHere deliberate exclusion**: `CentreHere()` is not exposed across the Bridge because zero calibration is managed in Python/SQLite; exposing it would create competing sources of truth.

## sketch/src/App.h / sketch/src/App.cpp

- **Boot ordering and static allocation**: Static global instances avoid heap allocation on the MCU; `DiagLog::Init()` is invoked first in `App::Begin()` before multi-threaded activity can occur.
- **UART peripheral separation**: `Serial1` (USART1 on D0/D1) is dedicated to the servo bus while Router Bridge uses `LPUART1`, avoiding hardware peripheral conflict.

## python/app/core/config.py

- **Settings env_file path**: Configured using an absolute path anchored to `Path(__file__).resolve().parent.parent.parent / ".env"` rather than a relative path, ensuring settings load consistently regardless of working directory (see D8/CLAUDE.md §5 for what a relative path breaks on the board).
- **Angle resolution scaling**: `output_step_deg = (360/counts_per_turn) * (belt_driven/belt_driving)` = `(360/4096) * (30/44)` ≈ **0.0599°**, rounded to 0.06. Target degrees round to integer counts to avoid accumulating drift.
- **Travel window sizing**: default ±90 output deg = 264 servo deg = 3004 counts, inside one servo turn (4096) with room to spare. Widen `output_min_deg`/`output_max_deg` alone to change the window; past one servo turn, also set `multi_turn_enabled`.
- **Speed ceiling, measured**: the servo saturates near 1100 counts/s regardless of the commanded value (~66 output deg/s). `default_speed_dps = 30` (fixed for every move, R9) sits well inside it. Relevant background for **D35**'s open speed-disagreement investigation.

## python/app/core/events.py

- **Kept separate from Logger461 on purpose**: services log via Logger461 AND record an event here only when it's worth surfacing to the operator UI — no coupling between the two in either direction.

## python/app/core/logging_setup.py

- **Logger461 calling convention**, used throughout the codebase: `logger.<level>(message, event=<dotted.event>, metadata={...}, extra={...})` — `event` is a dotted identifier, `metadata` is debugging context, `extra` is numeric statistics.

## python/app/db/database.py

- **`write_lock` guards every statement, reads included**: `Database` holds one `sqlite3.Connection` (`check_same_thread=False`) shared across the sampler thread and API request threads; two threads calling `execute()` on the same connection without a shared lock can hand back a corrupted `sqlite3.Row` — this is **D10**'s actual mechanism. Every repository built on this class must run all its statements through `write_lock`, not just writes.
- **`telemetry.target_deg` is nullable, no default**: `NULL` means no move has been commanded yet this run; a fabricated `0.0` would misreport a target that was never actually requested.
- **`telemetry.isolated` is `NOT NULL DEFAULT 0`**, unlike `target_deg`: it is app-held operator intent, not a servo measurement, so a value always exists — same reasoning `locked` already rests on. (Settles the null-handling question R2's original design deliberately left open — see `CLOSED.md`'s R2 entry.)

## python/app/deps.py

- **`get_isolation_service()`'s eager construction matters**: constructing it reconciles hardware toward persisted intent once, so building it eagerly at startup (`main.py`) is part of what makes ADR-0010's reboot-latch requirement actually hold — a fresh process should stop energising an isolated motor as soon as possible, not only once something else happens to touch the provider first.
- **`get_servo_repository()`**: simulated by default (no hardware needed for dev/tests); range and dead zone are applied at construction either way, so the startup path is identical for both backends.
- **`get_telemetry_service()` also ticks `IsolationService`**: the isolation reconciler and idle timer ride the telemetry sampler's own loop each cycle rather than getting a second thread — one more unsupervised thread is exactly the shape of bug `stop_sampler()` (D26) exists to prevent.

## python/app/relay/bridge_relay.py

- **Socket timeout during large responses**: Bridge socket read timeouts are set high enough to accommodate slow consumers or large streamed payload generation (e.g. multi-megabyte binary telemetry exports) without dropping the MCU link.
- **Message queue locking**: Bridge RPC calls (`self._bridge.call`) share a single serialized channel. Concurrent calls from multiple threads (e.g. telemetry sampler and FastAPI request handlers) interleave message IDs unless protected by `_bridge_lock`.

## python/app/repositories/abstract/servo_repository.py

- **Deliberately no `read_raw_counts()` on this contract**: a bare `int` return means a failed read arrives as 0, identical to a genuine reading at the bottom of travel, discarding the snapshot's own `valid` flag. Every caller must take a full snapshot and handle an invalid read explicitly. Removing the method removes the mistake at every call site that will ever exist, not just the ones caught so far. (`SimulatedServoRepository.read_raw_counts()` is a test-only affordance, not part of this contract — see below.)
- **`set_torque()`'s return value is uniquely load-bearing**: unlike every other command here, callers must never report isolation engaged or cleared on a write the servo did not actually acknowledge.

## python/app/repositories/concrete/bridge_servo_repository.py

- **Snapshot wire payload, field order** (matches `sketch/src/BridgeApi.h`): `valid,counts,moving,temp_c,volt_v,curr_a,torque_kgcm,load,status_bits`. Fault bits in the final field mirror status register 0x41 (bit0 voltage, bit1 sensor, bit2 temperature, bit3 current, bit4 angle, bit5 overload).
- **`decode_sign_magnitude()`**: STS position fields carry the sign in a dedicated bit, not two's complement — naive parsing shows ~32700 for a position just below zero. Applies to any raw register read directly, not just position.
- **`cache_seconds`**: the telemetry sampler and every HTTP request want the same servo reading at roughly the same moment; without a short cache each pays its own bus round trip.
- **One Bridge conversation at a time**: the RPC multiplexes requests/replies over a single link by message id. Two threads calling in concurrently interleave those ids, surfacing as "Response for unknown msgid" followed by 10s timeouts — the sampler thread and every HTTP request both read the servo, so this is the normal case, not a rare race.
- **`set_torque()` uses `_call` directly, not `_command`**: the ack is load-bearing here, unlike every other command in this class (see the abstract contract's note above).

## python/app/repositories/concrete/simulated_servo_repository.py

- **Models raw counts as an unbounded signed integer**, matching the real STS multi-turn position after sign-magnitude decoding, so nothing above this layer needs to change between simulated and hardware backends.
- **`read_raw_counts()` is a test-only affordance**, not part of the `ServoRepository` contract — the simulator cannot fail a read, so a bare `int` is safe here specifically; production code must go through `read_snapshot()` and honour `valid`.
- **`set_torque()` mirrors the real controller's un-isolate ordering**: restoring torque snaps the target to the present position first, so the simulator doesn't resume driving toward a stale goal — matching `ServoController`/`BridgeServoRepository` on real hardware.

## python/app/repositories/concrete/sqlite_telemetry_repository.py

- **`query()` fetches the whole matching set while holding the lock, then yields from that list.** The connection is shared across threads with no per-row isolation; holding the lock across `yield` would block every writer for the caller's entire consumption time, and dropping it before the fetch finished is **D10**'s actual unguarded-read bug. Fetch-then-yield is the only option that avoids both.

## python/app/repositories/concrete/sqlite_zero_repository.py / python/app/services/zero_service.py

- **`ZeroService.calibrate()` refuses outright on a failed read**: a failed read reports zero, and a datum of zero silently puts the entire negative half of travel out of reach — the servo clamps at count 0 and stops early while still reporting success. Same failure mode as D2/D9, a third call site.

## python/app/schemas/servo.py

- **`ServoStateResponse.from_view()` is the single builder for both the poller and the SSE stream** — two independent field lists here would be the exact twin-path shape that has already cost this project four defects (D2, D9, D10, D16).

## python/app/routers/servo.py

- **`POST /servo/isolate`'s response reflects intent, not confirmation**: accepted synchronously, it does not guarantee the servo has acknowledged the write. Poll `/servo/state` (or the SSE stream) for the confirmed `isolated` field.
- **`POST /servo/calibrate`**: call when the mechanism is physically at the documented reference position (install, and after any power-off) — creates/updates the datum zero, activates it, and marks the position verified.

## python/app/routers/stream.py

- **Zeros/events push roughly every 15s of wall clock**, independent of the state-push interval — two unrelated cadences sharing one loop.

## python/app/services/motion_service.py

- **Target persistence across stops**: When a motion is stopped via `stop()`, the target angle is marked stale rather than cleared so that UI telemetry retains the intended-vs-actual comparison.
- **Overload recovery command**: Clearing an overload fault on ST3215 hardware requires sending a position command. The current position is re-commanded to release the de-rate without moving the physical axis.
- **`recover()`'s "without moving" depends entirely on the read**: a failed read reports count 0, so recovering on a stalled bus used to command position 0 — driving the mechanism to the bottom of its travel in the name of not moving it. Now guarded by `InvalidReadingError`.
- **Refusal gates on intent, not acknowledged state**: `move_to()` checks `is_isolated_intent()`, not the acknowledged hardware flag, so the very first request this process ever serves refuses correctly, before `IsolationService`'s reconciler has had a chance to run (ADR-0010).

## python/app/services/isolation_service.py

- **A reconciler, not three mechanisms**: boot re-apply, the idle backup, and retry-on-failure all converge the servo's acknowledged torque state toward the same stored intent; isolation is reported to the operator only once acknowledged, never on intent alone.
- **Isolate is never gated on an in-progress move**: unlike a lock change, cutting power on demand must take effect immediately.

## python/app/services/servo_state.py

- **`_baseline_counts()` is the ONLY definition of the baseline — do not duplicate it.** With no zero captured, the baseline is the MIDDLE of the servo's travel, not count 0 (count 0 would strand the negative half of the range before the operator does anything). This exact fact used to be stated a second time, as a bare 0, in the conversion the snapshot used — the display and the motion path disagreed by half a turn, and on 7 August 2026 that sent the mechanism 212.7° on a command of 90° (**D9**). `_to_servo_deg()` is the only place the 44:30 belt division happens, for the same reason.
- **`_target_deg`/`_target_stale` are never fabricated**: `_target_deg` stays `None` until a move is actually commanded this power cycle, and `_target_stale` is only ever set by `stop()`, never inferred from `moving` — a second definition of the same fact is what D9/D10 cost.
- **One lock guards the whole store**: lock state, baseline, isolation, and settle timing are read behind a single lock, so a snapshot can never straddle a concurrent change.

## python/app/services/telemetry_service.py

- **Binary export struct format is a twin path with `parseBinaryTelemetry()` in `static/app.js`** — this comment, the Python struct string, and the JS parser are three independent statements of one wire format that must all agree; a stale copy here once disagreed with both the struct and the client (see `static/app.js` itself, which still carries the full field-by-field breakdown and this same warning — not relocated here to avoid a fourth copy).
- **Batching**: Samples are accumulated into `_BATCH` chunks before streaming to optimize socket throughput (board-validated 23 Aug 2026, see D6 — the Bridge's 224-byte-per-message ceiling still dominates regardless of batch size).
- **`_sample_once()` builds its row from one snapshot only**: it used to take a second, independent read for `raw_counts`, so a single row could describe two different instants and cost two Bridge calls per sample.
- **A failed read is skipped, not stored**: it would land as position 0, indistinguishable from a genuine sample at the bottom of travel — a gap in the series is honest and visible.
- **Sampler lifecycle in tests**: Background sampling threads must be explicitly stopped via `stop_sampler()` during test teardown to prevent orphaned threads from accessing mock objects across test boundaries (D26).

## python/static/app.js

**Not touched by T15a** — this file's comments were reverted to their original state after review. `CONVENTIONS.md` has no JavaScript section yet, so there was no decided convention to strip *to*; stripping proceeded anyway on the first run and lost real content (the twin-path telemetry warning, the D9/D16/D25 rendering-logic rationale, the whole XLSX/OOXML verification history) with almost nothing relocated. **T18** establishes JS conventions first; `app.js` gets its own considered pass against that rule, not a byproduct of the Python one.

## sketch/src/ (T15b, 26 August 2026)

Most of what this pass touched was already covered in `skills/uno-q-st3215/SKILL.md` and `sketch/src/RELAY_NOTES.md` — the register-128 collision, the SpiRemap-twice quirk, the dead-zone table, the STS-vs-SC warning, the SetTorque re-command rationale, and the whole relay threading model were all already documented there, often more thoroughly than the removed comments. Genuinely new facts, not previously written down:

- **`ServoRegisters.h`'s provenance**: cross-checked against the SCServo library headers and confirmed by a full register dump from the project's own servo (firmware 3.9 / servo 9.3).
- **`Config.h`'s `kTorqueLimit = 1000`**: full torque in service — not a reduced/protective value.
- **`ServoBus.cpp`'s `Refresh()` failure gets its own diagnostic event** (`mcu.servo.refresh_failed`), not folded into the byte/word read failures, because the sampler calls it once a second and exhaustion here is the same signature as the D4/D10 stalls.
- **`DiagLog::Init()` must be called synchronously, before any thread that could call `Push()` starts** — `App::Begin()` is single-threaded (before `loop()` or any Bridge callback can run), which is what makes it the one safe place to initialise the shared mutex without a race.
