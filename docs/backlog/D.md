# Defects — detail

Full entries for every open `D`-numbered item. Indexed one line each in
`../BACKLOG.md`; read this file only for the item you're picking up.

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
