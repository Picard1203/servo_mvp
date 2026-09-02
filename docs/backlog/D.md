# Defects — detail

Full entries for every open `D`-numbered item. Indexed one line each in
`../BACKLOG.md`; read this file only for the item you're picking up.

---

### D48 — Diagnose the load-induced settling oscillation properly: fast instrumentation first, then a structured experiment, not another tuning sweep
**Status:** open · **Severity:** high · **Found:** Session 22, immediately
after D40d — the operator's own explicit call: this needs designing
properly, not repeating the same ad hoc register-nudging that produced a
confusing, non-convergent picture in D40d

**What was wrong with D40d's own method, stated plainly so it is not
repeated.** D40d changed one register at a time, N=1–5 per configuration,
against no pre-declared pass/fail bar, and kept moving to a new variable
whenever the current one looked ambiguous. Given D40d's own data shows
roughly a 40–60% failure rate at some settings, N=2–3 cannot tell a real
fix from a lucky pair of repeats — several of D40d's "clean" results were
almost certainly luck, not fixes, and the session's own conclusion (P=24
kept, dead zone reverted, real state still unresolved) reflects that. This
item exists to run the properly designed version.

**Two independent deep-research passes (Claude and Gemini, 2 September
2026, same prompt) converge on the same diagnosis and the same gap in
today's own method** — full text kept in
`docs/research/D40_resonance_research_claude.md` and
`docs/research/D40_resonance_research_gemini.md` (Gemini's response was cut
off mid-protocol by a 50,000-character paste limit; the missing tail is
noted in the file, not silently absent). Both converge on:

1. **The mechanism is more consistent with load-coupled mechanical
   resonance (a two-mass system: motor+pulley vs. output+load, coupled
   through the compliant belt) than with simple Coulomb stick-slip** —
   non-monotonic register response, position-specific severity unrelated to
   travel-limit proximity, ~40–60% intermittency, and reliable hand-damping
   all match the resonance signature better than the friction one.
2. **This is inferred, not confirmed, and today's own instrumentation
   cannot confirm it.** Belt-transmission resonances typically sit in the
   tens-to-hundreds of Hz; D40d's raw position polling ran at ~7–12 Hz
   (80–150ms intervals) — far below the Nyquist rate needed, so it aliases
   any true high-frequency oscillation into something that merely looks
   like a slow, confusing wobble. **Confirming the mechanism, not guessing
   at it, is Stage 0 below and is the single highest-value thing this item
   does that D40d did not.**
3. **Three concrete, cheap, never-tried levers**, all live-writable or
   config-only, no reflash needed to test: **position D gain** (register
   0x16, held at the factory default 32 all session — the literal textbook
   damping term, direct electronic analog of the hand that reliably
   suppressed this all night); **a softened final leg**
   (`fine_approach_final_speed_dps`/`fine_approach_final_acceleration`,
   built in D40c, never used — both reports independently flag the
   overshoot-then-hard-reversal stop as a likely resonance-injection event,
   which is consistent with reducing overshoot *distance* not helping in
   D40d, since the excitation is in the stop, not the swing); **P lowered
   further than D40d tried**, toward the LeRobot community's own validated
   10–16 range (D40d only reached 16/24), accepting more steady-state droop
   that the existing fine-approach mechanism is already built to correct.

**Files:**
- `tools/jitter_probe.py` (new this session, promoted from a scratch
  script D40d built and validated live) — polls `output_deg`/`current_a`
  continuously through a move and counts real direction reversals near
  target, instead of trusting the firmware's own settle-completion event
  (D40d confirmed that event is blind to sustained trembling — see D40,
  `docs/history/CLOSED.md`). Use this, not `fine_approach_trial.py` alone,
  for every trial in this item — `fine_approach_trial.py`'s own settle
  wait is the exact metric this tool exists to not trust.
- A new tool, to be built as Stage 0 below: a fast current/load logger.
  `current_a` is already exposed by `/servo/state` (no new firmware) — the
  gap is polling it fast enough, simultaneously with position, during a
  known-bad trial, and telling a coherent oscillating trace apart from
  sharp spikes concentrated at reversal moments only.
- `sketch/src/Config.h`/`ServoController.{h,cpp}` — only if Stage 2's D
  gain result is kept permanently; mirror the existing `kPositionGainP`
  boot-write pattern added this session (same file, same discipline: bake
  the kept value in, do not leave it live-only in EEPROM).
- `python/.env`/`.env.board` — only if `fine_approach_final_speed_dps` or
  `fine_approach_final_acceleration` is kept; both settings already exist
  and are unit-tested, unused since D40c built them.

**The protocol, in order — do not skip Stage 0, it is what D40d skipped.**

- **Stage 0 — confirm the mechanism (prerequisite, ~30–45 min, decisive).**
  Build a script that logs `current_a` (already exposed) alongside
  `output_deg`, polled as fast as the HTTP/Bridge round trip allows, during
  a reliably-reproducing bad trial (−60°, the D40d worst point, under the
  same hand-plus-improvised-weight proxy load). **State the achieved
  polling rate honestly against the ideal** (both research reports put true
  belt resonance at 30–300 Hz, needing ≥60–600 Hz to resolve by strict
  Nyquist — this project's own HTTP+Bridge path will likely not reach
  that) — this test is not a full spectral confirmation, but it can still
  tell a coherent, sinusoidal-ish current oscillation (resonance
  signature) apart from sharp asymmetric spikes concentrated only at
  direction-reversal moments (stick-slip signature), which is enough to
  choose Stage 2a vs. 2b below with real evidence instead of inference.
- **Stage 1 — read Stage 0's result and pick a branch**, stated before
  starting, not decided after seeing which branch looks more convenient:
  resonance signature → Stage 2a; stick-slip signature → Stage 2b.
- **Stage 2a (resonance, expected) — test the three new levers, at real
  statistical power this time.** One test point only, −60°, the point
  D40d found fails most reliably — do not spread thin across many angles
  the way D40d's own final sweep did. **N≥10 per configuration**, not
  D40d's N=2–5 — the ~40–60% failure rate D40d measured means fewer
  repeats cannot distinguish a real fix from a lucky run. **Declare the
  pass bar before running each configuration**, in writing, in this
  entry's own working notes: e.g. "0 of 10 trials show >3 reversals past
  5s, or ≤1 does" — decided in advance, not adjusted after seeing the
  data, which is what let D40d's goalposts drift. Test, in this order: (i)
  D raised from 32 (try 48, then 64) alone; (ii) the final leg softened
  (`fine_approach_final_speed_dps` set well below the move's own speed, or
  `fine_approach_final_acceleration` set low) alone; (iii) **if both (i)
  and (ii) individually help, do not stop there — run the small 2×2
  factorial** (both low, both high, each alone) at N≥5 per cell. Testing
  factors one at a time can miss real interactions between them and
  produce a misleading conclusion — exactly the shape of confusion D40d
  ran into jumping between P, MinStartForce, dead zone and overshoot
  without ever checking whether they interacted. (iv) P lowered further,
  toward 14–16, checked against the resulting steady-state droop.
- **Stage 2b (stick-slip, if Stage 0 says so) — the friction-remedy path
  D40d already ran is the relevant one.** Revisit dead zone (D40d's own
  `2/2` result: 4 of 5 clean at the worst point) and `MinStartForce`
  85–95 (D40d's own clean-ish, small-offset range) with the same N≥10
  rigor Stage 2a specifies, rather than treating D40d's small-N results as
  final.
- **Stage 3 — only if Stage 2 does not converge to a pass**, probe the
  velocity-loop registers both reports independently surfaced (0x25/speed
  P, default 10; 0x27/speed I, default 200) — real but not documented in
  an official English register table; change one at a time, reversibly,
  and record the originals before writing anything.
- **Stage 4 — bracket the real arm without it.** Repeat the best Stage 2
  (or 3) configuration with a deliberately *exaggerated* bench inertia
  (added mass at a longer lever than the improvised weight used in D40d)
  to approximate the real arm's worst-case reflected inertia. A
  configuration that holds across that exaggerated range is a defensible
  real-arm starting point; one that does not means the fix needs D47's
  real hardware regardless, and that should be said plainly rather than
  assumed away.

**Acceptance:** a configuration is found that passes its own pre-declared
Stage 2/3 bar at −60° (N≥10) **and** does not regress the other points
D40d already measured clean (0°, ±60°, ±90°, N≥3 each, confirming no
regression rather than re-running a full campaign). That configuration is
written permanently (`Config.h` and/or `.env`/`.env.board`, matching
whichever settings changed) the same session it is confirmed, mirroring
D40d's own persistence discipline. **This item does not require D47's real
arm to close** — D47 stays open afterward regardless, as the final
real-hardware confirmation; this item is about reaching a real,
statistically credible answer on the mechanism and the best available
proxy-load fix.

**Related:** D40 (closed, `docs/history/CLOSED.md`), D47 (real-arm
verification, stays open independently of this item's outcome).

---

### D47 — Verify the anti-backlash fix holds once the servo carries its real load
**Status:** open · **Severity:** medium · **Found:** Session 22, D40d
proxy-load testing

D40 (closed this session, `docs/history/CLOSED.md`) landed a real,
permanent improvement (`P=24`, baked into `Config.h::kPositionGainP`; the
already-permanent `MinStartForce=150` held under a steady hand-drag load)
but explicitly did **not** verify the fix holds under load, and accepted a
known residual risk deliberately rather than chase it further today.
Today's proxy load (a hand grip plus an improvised weight, no rigid mount)
produced position-dependent, intermittent settling oscillation — worst at
−60°, sustained past 15s in some trials — that no combination tried
(`MinStartForce` 85–200, dead zone 0/1/2, fine-approach overshoot
0.4°/1.5°) reliably removed without a real accuracy cost. **Dead zone was
tried at 2/2 (4 of 5 trials clean at the worst point, 1 still failed) and
deliberately reverted to the factory-boot default 0/0** — the operator's
own call, accepting that a move may jitter but should still settle
eventually, rather than trading accuracy for a partial fix. The evidence
points to mechanical resonance rather than stiction alone: non-monotonic
response to every register tried, no consistent effect from overshoot
magnitude, roughly half of identical repeats failing and half not, and
direct hand contact reliably damping it (the textbook resonance remedy).
Resonant frequency is a property of the attached mass and mounting
stiffness — the proxy load has no reason to share the real arm's frequency
response, which is why this needs the real rig rather than more bench
tuning. A deep-research prompt capturing the full investigation was
prepared for further external research the same session (not committed to
this repo — ephemeral, handed to the operator directly).

**Final live register state, Session 22 close:** `P=24 D=32 I=0
MinStartForce=150 cw_dead_zone=0 ccw_dead_zone=0` — `P` and
`MinStartForce` are boot-permanent (`Config.h`); dead zone is deliberately
left at the firmware's own boot default.

**Acceptance:** run `tools/fine_approach_trial.py accuracy --loaded`
(anchors plus ±60/±75/±90, N≥5) once the servo carries its real mounted
load, **watching the shaft directly for trembling** — D40d confirmed the
server's own `servo.move.fine_approach` event (`wait_elapsed_s`) is blind to
sustained low-amplitude oscillation, so do not judge this from the event log
alone. If oscillation reproduces at specific angles, treat it as a
mechanical resonance question (damping, mounting stiffness, mass
distribution) rather than continuing to search for a register fix — D40d
already swept the plausible register space without finding one.

**Related:** D40 (closed, `docs/history/CLOSED.md`).

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
