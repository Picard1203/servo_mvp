# Defects — detail

Full entries for every open `D`-numbered item. Indexed one line each in
`../BACKLOG.md`; read this file only for the item you're picking up.

---

### D40 — A move settles short under load and re-commanding the same target does not correct it
**Status:** open · **Severity:** high · **Found:** rig hand-testing, 1
September 2026 · **the operator's own top-priority defect**

Under load, a move to e.g. 90° can settle at ~89°. Pressing 90° again produces
no corrective step. Commanding several degrees further does reach the target.
The operator cannot trust that the number on screen is the number achieved.

**Ruled out, read from code, this session.** No stale-target short-circuit
exists in `MotionService.move_to()`/`_command()` — every call reaches
`command_move()` unconditionally, so the second press *is* dispatched.
`servo_deadband_counts` is `0` on the board's live `.env`, so no software dead
zone is swallowing it.

**Three live candidates, in the order the investigation should test them:**
1. **Acked as success but never executed** — `_command()`
   (`bridge_servo_repository.py:207-220`) only logs a warning on a non-`"ok"`
   Bridge reply and returns success regardless (Session 14 `/twin-review`,
   backend finding 1, HIGH — verified with a stubbed `"err"` reply). "Press 90
   again, nothing happens" is exactly what a false `202 {"accepted": true}`
   looks like.
2. **Static friction under load** — the servo's own controller may not break
   stiction for a residual of a few counts, but can for a larger error.
   Matches "a few degrees further works."
3. **Direction-dependent backlash** — an anti-backlash mechanism already
   exists (`fine_approach_enabled`, off by default, never board-tuned) but is
   one-directional: `_needs_fine_approach()` (`motion_service.py:189-201`)
   only fires when `target_deg < start_deg`. If the shortfall bites on
   *increasing* moves, it cannot help as written.

**Prerequisites before `fine_approach` is ever flipped on** — both live code
waiting on that flag, both Session 14 `/twin-review` HIGHs:
- No `None`-guard on `start_deg`: `current_output_deg()` returns `None` on an
  invalid read, `_needs_fine_approach()` does `target_deg < start_deg`
  unguarded. **Verified**: reproduces `TypeError` at `motion_service.py:177`.
- The fine-approach thread (`motion_service.py:98-102`) has no cancellation
  and unconditionally issues its *original* target after sleeping up to 30s —
  a second `move_to()` call during that sleep is silently overridden
  afterward — and its body is unguarded, so any exception inside it
  (including the one above) is swallowed by `threading` with no trace.

**Proposed mechanism:** a bounded convergence retry — after settle, if
|measured − target| exceeds a tolerance, re-command with an offset large
enough to break stiction, up to N attempts, aborting on overload or on no
progress between attempts, recording an event either way. Config-gated,
default off until board-validated. `fine_approach` stays a separate switch —
it addresses backlash direction, not residual error; whether its direction
gate needs generalizing is answered by the investigation above, not assumed.

**Twin-path:** `move_to()` and `move_to_counts()` are the two entry points,
and `move_to_counts()` is what every saved-position "go" uses — D2's shape
(`calibrate()` fixed, `capture()` not) if the mechanism only reaches one.

**Acceptance:** a move converges to its target within a stated tolerance, or
reports plainly that it could not — never silently settles short while
reporting success. Reproduced and tuned with the operator holding the rig as
a temporary fixed point (the real pipe is not yet connected to it); tolerance
and attempt-count values are re-tuned once it is.

**Related:** D46 (the false-ack finding this investigation checks first),
ADR-0008 (the anti-pattern this mirrors on the Python side).

---

### D41 — Firmware commands real moves off failed reads and malformed payloads
**Status:** open · **Severity:** high · **Found:** Session 14 `/twin-review`
(`docs/REVIEW_FINDINGS.md`, firmware findings 2–4), triaged 1 September 2026

ADR-0008's anti-pattern (fixed on the Python side) reproduced in firmware,
confirmed independently by multiple lenses:
- `ReadRawCounts()` returns `0` on a failed position read with no failure
  signal, and three callers — `Stop()`, `SetTorque(true)`, `ClearFault()`
  (`ServoController.cpp:68-71,95-102,140-145,151-165`) — use the result as
  "hold here" and dispatch it through `Move()`, which acks success
  regardless. A bus glitch during Stop or torque-enable can silently command
  the servo toward position 0 while reporting success.
- `ReadSnapshot()` doesn't validate its 6 individual reads before marking the
  snapshot `valid=true` (`:43-66`) — a failed status-byte read defaults
  `faults` to all-`false` ("no faults") rather than unknown, while `valid`
  stays `true`.
- An empty/malformed `servo_move` Bridge payload silently commands a move to
  counts 0 and acks `"ok"` — `FieldAt`'s fallback for a missing field is `0`
  (`BridgeApi.cpp:25-40,53-63`), and 0 is a legal target.

**Must land before the real loaded rig day**, regardless of which sprint it
falls in — a bus glitch driving the servo toward count 0 is a physical event
once there is real load and an enclosure, not just a reporting bug.

**Acceptance:** a failed read is never dispatched as a move target; a
malformed payload is refused, not silently defaulted; `ReadSnapshot()`
reflects per-field validity the way the Python side already does.

**Related:** ADR-0008.

---

### D42 — Errors that vanish: SSE stream, migration, sqlite writes
**Status:** open · **Severity:** medium · **Found:** Session 14 `/twin-review`,
triaged 1 September 2026

Four findings, one family — a failure the operator or a developer needs to
see is silently absorbed:
- SSE stream generator swallows every exception with no logging
  (`routers/stream.py:93-94`) — found independently by three lenses.
  `TelemetryService._run()` handles the identical situation with
  `logger.exception(...)` (`telemetry_service.py:131-133`); this is the
  operator's primary live view and it can go stale with zero server-side
  trace.
- `_migrate()` swallows every `sqlite3.OperationalError`, not just "duplicate
  column" (`db/database.py:100-104`) — including "database is locked"
  (documented as real and reproduced on this mount, `CLAUDE.md` §6) — with no
  logging, so a genuinely failed migration is indistinguishable from an
  already-applied one.
- No sqlite exception handling anywhere in the concrete repositories — a
  "database is locked" occurrence surfaces as a generic unmapped 500, unlike
  every other error in the API.
- `diagnostics/torque_register` returns ambiguous `null` on any failure, no
  distinct status for "bus didn't answer" vs. "unexpected value."

**Acceptance:** each of the four either logs and surfaces its failure
distinguishably, or the entry says why the current behavior is fine.

---

### D43 — Guards that fail open on an invalid read
**Status:** open · **Severity:** medium · **Found:** Session 14 `/twin-review`,
triaged 1 September 2026

Three findings, one family — the one moment state is least certain is when a
safety check silently assumes the safe answer:
- `set_lock()`'s move-guard fails open on an invalid read —
  `read_snapshot().moving is True` is `False` whenever the read is invalid,
  because `_empty_snapshot()` hardcodes `moving=False`
  (`motion_service.py:139-141`, `bridge_servo_repository.py:230`).
- `snapshot()` blanks all telemetry/faults to `None` on a single invalid
  read, no hysteresis between a one-tick miss and a sustained fault
  (`servo_state.py:256-290`) — same shape as D11 ("shouted OFFLINE at one
  dropped packet").
- `calibrate()`'s off-centre warning re-derives reachability independently of
  the canonical per-side check, using a symmetric `half_window` instead of
  `ServoStateStore.is_reachable()` (`zero_service.py:139-152`) — **verified**
  to disagree on an asymmetric window (`-30`/`90`). The `servo.calibrated`
  event never records the off-centre condition even when it warns.

**Acceptance:** each guard reflects genuine uncertainty rather than a
hardcoded safe default; `calibrate()`'s check agrees with the canonical one
by construction (shared code), not by coincidence.

**Related:** D11.

---

### D44 — Operator-facing UI gaps found by the whole-app review
**Status:** open · **Severity:** medium · **Found:** Session 14
`/twin-review`, triaged 1 September 2026

Eight frontend findings, none individually large, batched as one item:
alarm banner can show a measured position **and** "(last known — position
unknown)" simultaneously, because `faultIsStale` gates on `!measured` instead
of `!known` (`app.js:523,610`); 5 of 6 fault types have no recovery control
or remedy text, only overload gets "Clear fault & resume" (`:565,605-624`,
D12-shaped); a date-range error ("start must be earlier than end") is
misrouted through `sayError()` and shows as generic "controller busy"
(`:1959-1961`); the speed nudge has no bound and a rejected out-of-range
speed reaches the operator as raw backend text with no field name
(`:2070-2079,744-753`); exporting a zero-sample range downloads a
structurally valid, silently empty `.xlsx` (`:2030-2068`); the
connecting-state LED shows the same green as confirmed-healthy
(`index.html:15`); an empty Recent Activity feed renders as a blank panel
with no placeholder (`:726-740`); `servoRatio === 0` treated the same as "no
ratio" in export (`:935`, defensive-only).

**Acceptance:** each either gets a fix or the entry records why it's fine as
is; no bulk close without touching each one.

**Related:** D12.

---

### D45 — Relay and firmware robustness gaps found by the whole-app review
**Status:** open · **Severity:** medium · **Found:** Session 14
`/twin-review`, triaged 1 September 2026

Six firmware findings, batched: `NetworkRelay::Poll()`'s bulk-read loop
`return`s (not `continue`s) on a lock timeout inside a `for` over slots 0..5,
deterministically starving the same higher-numbered slots every pass
(`:155-167`) — a plausible second mechanism for SSE disturbance during a
large export, distinct from the known 256-byte overflow (D6); `WriteToClient`
holds `chip_lock_` across `client.write()`, and Python's `bridge_relay.py`
serializes all replies through one global lock too — a stalled peer could
stall every client (partially unverified: the vendored Ethernet library
isn't in this checkout); `WriteByte`/`WriteWord` have zero retries and zero
diagnostic logging unlike every read path (`ServoBus.cpp:58-64`); `Move()`'s
`WritePosEx` failure path logs nothing while the harmless out-of-range
refusal logs clearly (`ServoController.cpp:73-93`) — inverted
signal-to-noise; `DiagLog::Push` in the write-timeout path isn't
rate-limited and can overrun the 32-entry ring during exactly the high-load
condition it exists to diagnose (relevant to T9); a half-configured boot
reports "ready" identically to a fully good one — config-write failures
(torque limit, angle range) log nothing and don't affect `get_status`
(`App.cpp:29,47,58-59`).

**Acceptance:** each either gets a fix or the entry records why it's fine as
is.

**Related:** D6, T9.

---

### D46 — Backend robustness gaps found by the whole-app review
**Status:** open · **Severity:** medium (one finding HIGH — see D40) ·
**Found:** Session 14 `/twin-review`, triaged 1 September 2026

Four findings, batched: three operator-facing controls (`/servo/move`,
`/servo/stop`, `/servo/isolate`) report success without hardware
acknowledgement — `_command()` (`bridge_servo_repository.py:207-220`) only
warns on a non-`"ok"` reply, never raises (**verified**, HIGH — this is D40's
first investigation candidate, tracked there, not duplicated here);
`BridgeServoRepository`'s hardware import has no `except ImportError` unlike
three identical sites, so `use_hardware_servo=True` without the `arduino`
package crashes startup instead of degrading (mirror image of D8);
Pydantic validation errors (e.g. a bad `speed_dps`) return FastAPI's default
`422 {"detail": [...]}` shape while every domain error returns
`{"detail": "...", "reason": "..."}` — the error an operator is most likely
to actually trigger looks different from every other one; `move_to()` blocks
synchronously up to `settling_seconds` (1.5s) before responding when a
lock-state change happened recently — a button press produces nothing for
over a second.

**Acceptance:** each either gets a fix or the entry records why it's fine as
is.

**Related:** D8, D40 (the ack-surfacing fix tracked there).

---

---

### D36 — Several tests construct their own `Database` and never close it
**Status:** open · **Severity:** low · **Found:** 25 August 2026, chasing D26

Nine call sites in `test_database.py`, `test_sqlite_zero_repository.py` and
`test_sqlite_telemetry_repository.py` build a `Database(tmp_path / ...)`
directly rather than through the cached `deps.get_database()` singleton, so
none of them are closed by `_clear_all_caches()`'s new teardown ordering
(D26). Each leaves a `ResourceWarning: unclosed database` at some later,
unpredictable point in the suite. Does not fail the suite and is not the
D26 mechanism (these are per-test SQLite files, not the shared connection a
zombie thread can race) — found opportunistically, not chased down, because
nine call sites is a real piece of work, not a one-line fix alongside D26.

**Acceptance:** each either uses a fixture that closes it (`yield db;
db.close()`) or the pattern is judged fine as-is and this entry says why.

**Related:** D26.

---

### D28 — MCU boot-time `mcu_log` notify lost to a startup race
**Status:** open · **Severity:** low · **Found on real hardware, 8 August 2026**

Confirmed while checking D3's firmware after the first real flash:
`NetworkRelay::Begin()` pushes `mcu.relay.ready` during `App::Begin()`, and
the first `Tick()` drains and sends it within milliseconds of `setup()`
returning. Python's `get_mcu_log().register()` (`main.py:_start_background()`)
runs later — after the telemetry sampler starts and the relay registers —
which is well into Python's own container startup. `Bridge.notify` is
fire-and-forget with no acknowledgement (confirmed by reading
`Arduino_RouterBridge`'s source), so a notify sent before Python's handler
is registered is silently lost. After several minutes of uptime on the real
board, no `mcu.relay.ready` line and no `mcu.jsonl` file existed at all.

**Likely confined to boot-time events** — nothing else has been observed
lost, but nothing else has fired yet either (0 rejections, 0 timeouts in
that run). Whether a steady-state event (fired minutes into a session, long
past the startup race) has the same problem is untested — it needs an
actual rejection or write-lock timeout to occur.

**Acceptance:** either move `get_mcu_log().register()` earlier in Python's
startup (before the uvicorn serving thread starts) to shrink the race
window, or confirm via a deliberately-triggered post-boot event that
steady-state notifies are not affected, whichever is cheaper to establish
first.

**Related:** D3, `docs/adr/0009-connection-ceiling.md`.

---

### D35 — Commanded speed and actual speed disagree by roughly 1.5-2x
**Status:** open, not yet investigated · **Severity:** medium · **Found:**
24 August 2026, bench-testing D32's proposed speed-step enforcement

**The measurement.** Board-tested (not simulated): commanded a move of
17.92° (90.07° → 72.06°) at `speed_dps: 1.8`. Settled somewhere between
t=4.4s (still moving) and t=6.58s (settled) — actual average speed
**2.7-4.1 deg/s against a commanded 1.8**, roughly **1.5x to 2.3x faster**
than asked. This is why D32's speed-step enforcement (reusing `output_step_deg`
for speed, on the theory that 1 `GoalSpeed` unit = 1 encoder count/s, same as
position) was pulled from that item and postponed here instead of shipped on
an unverified assumption.

**Ruled out, both cheaply and concretely:**
- **Python-side inconsistency between the position and speed conversions.**
  `ServoStateStore.counts_from_output_deg()` and
  `.counts_speed_from_output_speed()` (`servo_state.py:186-210`) read the
  identical `self._servo_deg_per_output_deg` / `self._counts_per_servo_deg`
  set once in `__init__` — they cannot disagree with each other within this
  codebase.
- **Firmware-side double conversion.** `AngleMath.h:56-64`
  (`CountsPerSecondFromOutputSpeed()`) exists and independently reapplies the
  belt ratio, which would explain a faster-than-commanded result — but
  `BridgeApi.cpp`'s `HandleServoMove` never calls it; it passes the
  Python-computed `speed_counts_per_second` straight through to
  `ServoController::Move()` and on to `WritePosEx`. **Worth its own small
  finding: this firmware function is written, header-only tested, and
  unreachable from the live command path** — either dead code or a sign
  something was meant to call it and doesn't.
- **Fine-approach overshoot or acceleration ramp.** Both can only add time,
  never remove it, so neither explains a *faster* result.

**Not yet ruled out — the operator's suspicion, and the leading hypothesis:**
the belt ratio (44/30 = **1.4667**) sits almost exactly at the low end of the
measured ratio range, and its square (**2.1511**) sits near the high end. Both
are consistent with the crude timing bounds above. This points at the
servo's own `GoalSpeed` register (0x2E) not actually sharing position's
encoder-count LSB the way `ServoRegisters.h:57`'s `// step/s` comment and the
shared register-block/packet-format evidence suggested — i.e., the codebase's
pipeline is internally consistent (see above), but the *assumption* that 1
`GoalSpeed` unit is worth exactly one position-encoder-count/s may itself be
wrong by a belt-ratio-shaped factor, applied once or twice somewhere between
the register's real meaning and this project's model of it.

**Next step:** a tighter bench test — command a few different `GoalSpeed`
values, read `PRESENT_SPEED` (register 0x3A, not currently exposed by the
API) during the move rather than inferring from elapsed wall-clock time, and
correlate against known real angular distance over a precisely-timed window.
The official Feetech memory-table PDF (`feetechrc.com`, password-gated) would
settle this outright if it can be obtained. **Blocks:** the speed-step half
of D32's enforcement.

**Related:** D32 (the postponed enforcement this measurement blocks), R9
(closed 30 August 2026 — the global move speed it fixed at 30 deg/s
commanded depends on this measurement; resolving D35 may show that figure
needs revisiting).

---

### D5 — Log output is dominated by connect/disconnect noise, and is not useful
**Status:** open · **Severity:** medium · **cause identified 7 August 2026**

**Uvicorn access logging is ruled out.** `main.py:143` runs uvicorn at
`log_level="warning"`, and a board run with a browser polling continuously
produced **zero** access lines. The candidate this entry named as "most likely
remaining" is dead.

**The churn is the relay's own DEBUG lines, and it is by design.**
`main.py:142` sets `timeout_keep_alive=5` so an idle connection does not park
one of the W5500's six slots. The observed 5–6 second open/close cadence is
exactly that timeout working. 224 churn lines in one run; 168 in a later
7-minute run — roughly 24 lines per minute per operator.

So there is no fault to fix here. What remains is presentation: at INFO the
lines are **now** silent — D29 (closed 25 August 2026) found the Logger461
stand-in accepted a level and silently discarded it, so this claim was false
on the board the whole time this entry has existed; it is true now that the
stand-in actually filters. The work is still to make the default level read
as a narrative of what the system *did* — moves, calibrations, faults —
rather than what its sockets did. The phrasing complaint stands unchanged.

**Original report follows.**

**Severity:** medium

The Python console fills with connecting/disconnecting lines until they crowd out
everything else.

Source not yet identified. Ruled out so far: the two relay lines at
`python/app/relay/bridge_relay.py:80` and `:115` are `logger.debug`, and both the
code default and `.env.board` set `LOG_LEVEL=INFO`, so they are silent unless
something is running at DEBUG. The MCU is also ruled out — `App.cpp`'s prints are
a one-time setup banner, and nothing on the C++ side logs during operation (D3).

Most likely remaining candidate: **uvicorn access logging**. `app.js` polls state
continuously, and every poll is one access-log line at INFO. Confirm before
changing anything.

Separately, the messages themselves are judged not meaningful enough and their
phrasing not professional enough.

**Acceptance:** at default level the log reads as a useful narrative of what the
system did. Per-connection churn is available at DEBUG but off by default.

---

### D6 — App load time is sometimes slow
**Status:** open (chunk-size half closed, 23 August 2026) · **Severity:** medium

Occasional slow first paint. Cause unmeasured. Suspected inefficiency in the
serving path, plausibly interacting with D4. First paint itself is still
unmeasured — that half stays open.

Numbers already in hand: a warm app restart is 15.8 s, a cold one ~7 minutes
(empty `.cache/`); a `/api/v1/servo/state` call served in 0.117–0.134 s.

**The relay-chunk-size half is closed, 23 August 2026 — with a cause, not just
a number.** `kRelayChunkBytes`/`relay_chunk_bytes` raised **128 → 224**,
board-validated on a live 44,827-row telemetry export: zero churn, zero
dropped transfers, ~49% throughput gain (4.5 KB/s → 6.7 KB/s). The old
"256 is the working value, but the operator recalls it failing" contradiction
(`RELAY_NOTES.md` §5) is resolved, not just avoided: 256 overflows the
vendored `Arduino_RPClite`/`Arduino_RouterBridge` library's own fixed
256-byte RPC message buffer (`DECODER_BUFFER_SIZE/4`), leaving only ~236
bytes of real payload room once MsgPack framing is subtracted — confirmed by
re-testing 256 on the current, rule-7-fixed relay and reproducing instant
export failures and connection churn directly. Full derivation and the exact
`#define`s are in `RELAY_NOTES.md` §5 — read that before touching this value
again.

**Acceptance:** load time measured and stated; a number to hold against.

---

### D7 — UI is not verified on small operator screens
**Status:** open · **Severity:** medium

**Narrowed 8 August 2026: it is not a touch screen** (operator, answering the
touch half of Q1). That settles the *interaction* model — and D15 was designed
against it.

**26 August 2026: no longer blocked on an exact device.** The operator recalls
iPad mini but isn't certain, and decided against blocking on a device that
can't be confirmed. Target a responsive range instead: **768–1024px width**
(iPad mini portrait/landscape) up through common laptop widths, degrading
gracefully outside it rather than breaking.

**Acceptance:** UI verified via devtools responsive mode at 768px, 1024px, and
one laptop width (e.g. 1366px); layout fixed at any width in that range that
breaks rather than degrades.

**Corroborated 30 August 2026, Session 16:** rebuilding the saved-positions
panel gave cause to check all three widths with Playwright. 1024px and
1366px render correctly; at 768px `.content` collapses to `height:0` and
`.col`'s children report zero-height bounding rects — the page renders as
blank below the header. Not investigated further or fixed this session
(out of R10's scope); real, reproducible, and it is `.content`/`.col`'s
own grid sizing under the `@media (max-width:900px)` rule, not the
positions panel specifically.

---

### D38 — A saved position's "earlier reference" tag has no way to dismiss it
**Status:** open · **Severity:** low · **Found by:** operator, session 16
(R10's build)

`SavedPositionService._to_view()` flags a position `stale_reference` whenever
its `updated_at` predates the datum's `datum_captured_at` — the UI shows this
as an "earlier reference" pill (`app.js:renderPositions()`,
`style.css:.pos-tag`). The only way to clear it today is to re-save the
position (any edit sets a new `updated_at`), which is not why an operator
would open the edit dialog.

**The concern, not yet observed but easy to predict:** after one
recalibration, every position saved before it carries the tag permanently,
whether or not the drift is meaningful to the operator (0.06° is not the
same concern as 6°) — a list-wide badge with no way to say "seen, fine"
reads as a persistent low-grade alarm rather than useful information the
first time it is noticed.

**Acceptance:** an operator can dismiss the tag on a position (or a
recalibration's whole batch of newly-stale positions) without editing its
name, description or angle — dismissal should not silently change what the
position stores.

**Related:** R10.

---
