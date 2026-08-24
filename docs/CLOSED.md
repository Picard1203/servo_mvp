# Closed items

**The past tense of `BACKLOG.md`.** Every entry here is done; the reasoning is
kept because it is the record, not because it is pending. Nothing in this file
is work.

`AUDIT.md` is a different thing again: defects found *before* this backlog
existed, frozen. This file is items that entered the backlog and left it.

Split out of `BACKLOG.md` on 8 August 2026 — closed entries were 25% of the
file every session has to read.

---

### D1 — A move to a negative angle stops at 0
**Status:** done · 7 August 2026 · **Confirmed on hardware, both halves**

Both acceptance conditions were exercised on the board in one session:

- **Datum at count 2049 (mid-travel):** +90 and −90 both reached. Telemetry
  shows `2055 → 3547` for +90, and a clean ramp back down at 10 deg/s. Resting
  count 3549 = −0.06 deg, one count off target.
- **Datum at count 3550 (near the top):** a move to +90 needs count 5051 against
  a 4095 ceiling and was **refused as out of travel, not clamped**. The
  off-centre warning fired at capture time with
  `needed_either_side=1501 usable_counts=4095`.

Root cause was the datum, as suspected — D1 was the symptom, D2 and D9 were the
causes. Kept here rather than moved, because the reasoning is the record.

**Original report follows.**

**Severity:** high · **Reported:** observed on hardware

Commanding a move from, say, +10° to −45° is accepted, the servo starts, and it
stops at count 0 instead of reaching the target.

Suspected cause (operator's read): the datum was captured at real step 0, so the
negative half of travel maps below count 0, and the servo clamps there silently
while still reporting success. If the datum sits mid-travel this may not
reproduce — which makes D2 the likely root cause rather than a separate bug.

**Acceptance:** with a mid-travel datum, a move from +10° to −45° lands within
one count of target. With a datum at 0, the move is *refused* as `out_of_travel`
rather than silently clamped.

**Related:** D2, and `AUDIT.md` "Datum At Zero Strands The Negative Half".

---

### D2 — `capture()` can store a failed read as position 0
**Status:** done · 7 August 2026 · commit `c903182`

Fixed as specified, by the preferred fix rather than the local one:
`read_raw_counts()` is gone from the `ServoRepository` contract and from
`BridgeServoRepository`, so no caller can obtain a position without handling a
snapshot and its `valid` flag. `capture()` now raises `InvalidReadingError`
exactly as `calibrate()` always did.

Removing the method exposed **two further call sites nobody had counted**:

- `ServoStateStore.snapshot()` — the path feeding the UI *and* the telemetry
  database. See D9.
- `MotionService.recover()` — clearing an overload works by re-commanding the
  present position, so on a stalled bus it commanded count 0, driving the
  mechanism to the bottom of travel in the name of not moving it. Now refuses.

That is the argument for deleting the method rather than guarding the call site,
made concrete: guarding `capture()` alone would have left both.

Six tests added, each failing before the change. Suite 186 → 192.

**Original report follows.**

**Severity:** high · **Flow:** `WORKFLOWS.md` W2

`ZeroService.capture()` (`python/app/services/zero_service.py:41`) calls
`read_raw_counts()` with no validity check. `read_raw_counts()`
(`python/app/repositories/concrete/bridge_servo_repository.py:165`) is
`return self.read_snapshot().raw_counts` — it discards the snapshot's `valid`
flag. On a failed or unparsable read the snapshot is `_empty_snapshot()`, so the
call returns `0`, indistinguishable from a genuine reading of zero.

`calibrate()` guards this correctly and raises `InvalidReadingError`. `capture()`
does not. **The guard was applied to one of two paths.**

This is the same defect class `AUDIT.md` was written about, through a different
door: a bus hiccup while an operator saves a named zero stores `raw_counts=0`;
activating that zero later strands the negative half of travel, producing D1.

Not caught by the suite — `test_nothing_is_stored_when_the_read_failed` sits in
`TestCalibrationRobustness` and exercises `calibrate()` only.

**Preferred fix:** remove `read_raw_counts()` from the `ServoRepository`
contract entirely, forcing every caller to handle a snapshot and its `valid`
flag. Guarding `capture()` alone fixes today's call site; deleting the lying
method fixes every call site that will ever exist.

**Acceptance:** no path can convert an invalid reading into a stored position. A
test covers `capture()` with a failed read.

---

### D9 — The display and the motion path used two different baselines
**Status:** done · 7 August 2026 · commit `c903182` · **found on hardware**

With no datum captured and the servo parked at count 0, an operator pressed
"move to 90". The mechanism swept **212.7 output degrees**.

Nothing malfunctioned. Both sides were internally consistent, against different
baselines:

| | baseline used | reported |
|---|---|---|
| Motion (`_active_counts`) | 2048, mid-travel | `from_deg: -122.7 → to_deg: 90.0`, correct |
| Display (`_to_output_deg`) | **0** | "0.0 deg" before, "212.74" after |

The operator commanded 90 from a screen reading 0, and the machine travelled
212.7 at 30 deg/s — seven seconds of wrong movement. Telemetry recorded the
sweep count by count.

The two definitions sat **twelve lines apart in the same file**, and the correct
one carried a six-line docstring explaining precisely why a baseline of 0 is
wrong. The other did it anyway.

`_baseline_counts()` is now the only definition; both callers delegate. The
display conversion also now applies `servo_direction`, which it had never done —
the same twin-path bug would have mirrored the readout against the motion path
under `SERVO_DIRECTION=-1`.

**This is the D2 defect class again**: a rule applied to one path and not its
twin. Third instance in this repository, counting `AUDIT.md`.

---

### D11 — A single failed poll is presented as a disconnection
**Status:** done · 7 August 2026 · **needs an operator's eye on the board**

Both over-reactions now require `FAILURES_BEFORE_ALARM = 3` consecutive
failures — about three seconds at one poll per second. A single lost answer is
invisible; a real stall lasts ten seconds and still shows plainly. On an invalid
reading inside the tolerance the readout holds the last **measured** position
rather than blanking, and only blanks once the position is genuinely unknown.

This paces what is *displayed*. It does not soften what is *reported*: the API
still says `reading_valid: false` the moment a read fails, per ADR-0008. The
honest contract sits underneath a calm surface, which is the split that ADR
deliberately left open.

**Not yet confirmed by eye** — the change is served from the board but wants an
operator to drive it and say whether the flashing has stopped.

**Original report follows.**

`app.js:225-231`: any failed poll immediately flips the UI to OFFLINE and says
"connection lost — retrying…". One dropped request in a continuous poll stream
is enough, so the operator sees a connection failure that did not happen.

The same over-reaction now exists on the position readout: `renderState` shows
`--` the instant one read is invalid, so a single blip makes the position blink
to unknown. Honest at the API — which must keep reporting `null`, see ADR-0008 —
but it reads as "broken" to a non-programmer, and **the end users are not
programmers.**

Both want one treatment: require N consecutive failures before declaring a
state, rather than reacting to a single sample. A real 10-second stall still
surfaces clearly; a blip stops shouting.

**Acceptance:** a single failed poll or invalid read produces no visible alarm; a
sustained one is unmistakable. The threshold is written down here once chosen.

---

### D14 — The most likely error in the system shows the operator "Failed to fetch"
**Status:** done · 8 August 2026 · Batch 1

Every request now goes through one `request()` helper that catches the `fetch`
rejection itself and gives it a reason code of its own, `unreachable` — a
client-side code, because the backend cannot report that it was never asked.
`sayError()` maps it to *"the controller is busy or did not answer — wait a
moment and try again."*

The fallback was the other half of the defect and is also gone. Unmapped
failures now split three ways, because they ask different things of the
operator: **no status** → unreachable (try again), **5xx** → "the controller
reported a fault" (tell someone), **4xx** → "refused — " plus the backend's own
sentence. No branch can now put browser-generated text on screen.

`invalid_reading` and `out_of_travel` were also unmapped and fell through to
`"error: …"`; both are reachable by an operator, so both got treated —
`invalid_reading` with a sentence of ours, `out_of_travel` with the backend's,
because it carries a number (see D21).

**Verified by execution, not by reading**: `tools/check_client_behaviour.js`.
**Not verified in a browser** — see T12.

**Original report follows.**

**Severity:** high · **Found by:** operator lens, 8 August 2026

`sayError()` (`app.js:220`) translates five backend `reason` codes into plain
English. Everything else falls through to `"error: " + err.message`.

**A refused connection never has a reason code.** When the relay runs out of
slots (D13) the `fetch` rejects at the network layer, so `asApiError()` is never
reached, `err.reason` is `undefined`, and the operator is shown the browser's
own string — **"error: Failed to fetch"**.

So the single most likely failure in the whole system — the one D13 measured at
5 in 10 back-to-back requests — produces the least intelligible message in the
whole UI. The end users are not programmers.

**Acceptance:** a network-level failure produces a sentence an operator can act
on ("the controller is busy — try again in a moment"), distinct from a refusal
by the servo and distinct from a fault. No browser-generated text reaches the
screen.

**Related:** D13 (the cause), D15 (why they press again).

---

### D15 — A command in flight looks identical to a command that did nothing
**Status:** done · 8 August 2026 · Batch 1

The guard went into `bind()` rather than into the handlers, because `bind()` is
the one place all nine controls are wired — so a tenth added later inherits it,
and there is no twin to keep in step. While a command is in flight the control
is `disabled` (which blocks the press outright rather than trusting a handler to
check) and carries `.busy`, styled as a slow pulse rather than the standard
disabled dimming: **busy and unavailable are different messages, and the
operator needs "this is working".**

A command unanswered after **2.5 s** says so. The Bridge timeout is 10 s, so
that leaves seven and a half seconds in which the operator used to see nothing
at all — which is the window their second press was landing in.

The guard covers the whole handler including the confirm/prompt dialogs, so a
second press cannot stack a second dialog. Release is in a `finally`, so a
throwing handler cannot strand a control disabled.

**Q1's touch half is answered** (operator, 8 August 2026): it is a mouse-driven
screen, not touch. The design is therefore free to use hover affordances, and
the note in `style.css` says what to revisit if that ever changes. **The
viewport half of Q1 is still open, so D7 stays blocked.**

**The twin-review found the guard had a hole, and it is now closed.** `bind()`'s
comment claimed "the one place all nine are wired" — but **Enter in the angle
field was a tenth entry point**, calling `doMove()` directly. It bypassed the
disable, the busy state and the notice entirely, and `keydown` auto-repeats, so
*holding* Enter streamed moves onto the wire and spent a W5500 slot per repeat.
The keyboard reproduced D15 exactly while the mouse was fixed. It now dispatches
through `moveBtn`, so a disabled control refuses it like any other press.

**The slow notice moved out of `bind()` and into `request()`.** Started on the
click, it announced "the controller has not answered" while a *confirm dialog*
was still open — on Calibrate, Save and Remove, where the thing that had not
answered was the operator. `doSave` waits for a typed name, so it fired on
essentially every save. It now belongs to the request, fires only for commands
and not for background polls, and **is taken down when the command answers** —
`clearTimeout` alone left it asserting silence for 4.5 s while the servo was
visibly moving.

**Verified by execution**: `tools/check_client_behaviour.js`, 44 assertions —
the dropped second press, the release, release-on-throw, the Enter path, and
the notice's appearance, silence on polls, and dismissal. **The claim that
`disabled` blocks a real click is asserted by design, not exercised** — the
stub calls the listener directly. Wants an operator's eye on the board.

**Known gap, filed as D18:** `doExport()` is synchronous, so the guard releases
before it can be seen. It is the only unguarded control.

**Original report follows.**

**Severity:** high · **Found by:** operator lens, 8 August 2026

`bind()` (`app.js:539`) flashes the button for 400 ms. Every command handler is
then `await`-ing an HTTP round trip with **no in-flight state**: the button is
not disabled, nothing spins, and success is deliberately silent
(`/* success: no notice */` appears at nine call sites).

A `servo_read` can take up to the Bridge's 10 s timeout. In that window the
operator sees a 400 ms flash and then nothing, so they press again — **and the
second press opens another connection, which is exactly what exhausts the six
W5500 slots.** The UI's response to slowness actively worsens its cause.

This is the other half of "first press does nothing, press it again". D13
explains why the first press failed; this explains why the operator's instinct
makes it worse.

**Acceptance:** while a command is in flight the control shows it and cannot be
pressed again. A command that has not answered within a stated time says so.

**Related:** D13, D14, D6.

---

### D16 — On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured
**Status:** done · 8 August 2026 · Batch 1 · **the answer was "both sides"**

The choice the entry left open — schema nulls them or client blanks them — was
**both**, because they were two different failures wearing one description:

- **The schema** is where the rule belongs. It is the one place every present
  and future client passes through, and `output_deg` and `raw_counts` already
  carried it one field away. `temperature_c`, `voltage_v`, `current_a` and
  `torque_kgcm` are now `Optional[float]` on `ServoStateResponse` and
  `ServoStateView`, nulled in `servo_state.py` when `reading.valid` is false.
- **The client** had to change regardless: `null.toFixed(2)` throws a
  TypeError, which would have killed `renderState` half-rendered and frozen the
  whole panel. Fixing only the schema would have turned a lie into a freeze.

**The blanking rides the position's existing debounce** rather than inventing a
second rule: hold the last *measured* values through a single blip, blank once
`readFailures` reaches `FAILURES_BEFORE_ALARM`. D9 is what two definitions of
one baseline cost, and there was no reason to build a third.

**Scope was wider than five fields, and deliberately so.** `moving` and the six
fault flags come from the same `_empty_snapshot()`, so an unanswered read
rendered **HOLDING** with every lamp reading a green OK — "stationary and
healthy" about a servo that said nothing. That is this entry's own acceptance
sentence, so the chip and the lamps are included: they now read `—`, and
`setFault()` takes a third state (`null`, "not reported") distinct from `false`
("no fault reported"). The clear-fault control also stops appearing on an
unknown read.

**What was deliberately not done, and is now D23:** the booleans stay non-null
*in the schema*. `bool | None` is a tri-state that ripples into the CSV and
every consumer, and that is an API decision rather than a defect fix. The client
no longer renders them as measured; the contract still states them. **Filed
rather than taken quietly.**

The telemetry database needed nothing: ADR-0008's gap rule already returns early
on `reading_valid`, so no `None` can reach a NOT NULL column. Verified, not
assumed. **ADR-0008 has been amended** to state the rule in its general form —
`valid` governs the whole snapshot, not the position field.

**The twin-review found one more surface still rendering a failed read as a
measurement:** the position bar. `(deg / 360) * 100` clamped to 0 on an unknown
read, and an empty track is pixel-identical to a genuine reading at the datum —
the same claim the numeric readout is careful not to make, in graphical form.
The track now shows that it is not reporting. **This is not D17**, which is
about the bar's *scale* covering the travel window and stays open.

Four tests, two of them RED first (`assert 0.0 is None`); D21 added the fifth. Suite 193 → 198.

**Original report follows.**

**Severity:** high · **Found by:** operator lens, 8 August 2026

`ServoStateResponse` (`python/app/schemas/servo.py:106`) makes `output_deg`
`Optional[float]`, with a docstring that states the rule exactly:

> *"or null when the servo did not answer. Clients must render null as
> 'unknown' and never as 0 — a failed read is not a position."*

**The four fields beside it are plain `float`.** `temperature_c`, `voltage_v`,
`current_a` and `torque_kgcm` carry no null, so on a failed read they arrive as
`0.0` from `_empty_snapshot()` and `renderState` (`app.js:286-289`) prints them
unconditionally. The operator sees **Voltage 0.00 V** next to a position that
correctly says unknown — which reads as *the servo has lost power*, and is
false.

**This is the twin-path defect for the fifth time in this repository.** The rule
was written down, correctly, in a docstring — and applied to one field of five.
Same shape as D2 (`calibrate()` but not `capture()`), D9 (two baselines), D10
(production logger and its test stub).

**Acceptance:** no telemetry value is rendered as a measurement when
`reading_valid` is false. Either the schema nulls them all or the client blanks
them all; one rule, five fields.

**Related:** D2, D9, D10, ADR-0008.

---

### D20 — `eventTime()` claims a compatibility fallback it does not implement
**Status:** done · 8 August 2026 · Batch 1

The dead branch and its comment are gone; `const raw = e.timestamp;` is what is
left. The block comment above the function was **not** removed — it describes
the parse-and-fall-back-to-the-time-part behaviour, which the function really
does have. Only the sentence that lied was deleted.

**Original report follows.**

**Severity:** low · **Found by:** operator lens, 8 August 2026

`app.js:411-412`:

```js
/* backend field is `timestamp` (ISO string); tolerate legacy `timestamp` too */
const raw = e.timestamp != null ? e.timestamp : e.timestamp;
```

Both branches are the same expression. The comment describes a tolerance for a
legacy field name that the code does not provide — presumably `ts`, which
`CONTEXT.md` forbids in favour of `timestamp`.

Harmless today, and worth removing rather than fixing: the glossary settled the
name, so the fallback should not exist. Filed because a comment that describes
behaviour the code does not have is the same species as D10 — *it looks like
diagnosis*.

**Acceptance:** the dead branch and its comment are gone.

---

### D21 — The UI tells the operator the step is 0.1°; it is 0.06°
**Status:** done · 8 August 2026 · Batch 1

`sayError()` no longer holds a step figure at all. `step` is rendered as
`"refused — " + err.message`, so the number the operator reads is the one
`config.py` set and `motion_service.py` enforced — 0.06° today, and whatever
`output_step_deg` becomes tomorrow.

**The rule was drawn where the entry pointed, not around one string.** Reason
codes now split by *who owns the words*: those carrying a
configuration-derived number use the backend's message (`step`,
`out_of_travel`), and those whose backend phrasing is written for a developer
keep a curated sentence (`locked`, `moving`, `active_zero`, `datum_zero`,
`invalid_reading`). The entry's observation that all five mapped codes discard
the backend message is answered — deliberately, per code, rather than by
flipping all five.

`ANGLE_STEP = 0.06` in `app.js` was checked and is **correct**; it agrees with
`config.py` and drives the nudge buttons. There was no second wrong copy — only
the sentence describing it.

The backend test added here is a **regression guard, not a RED test**: the
backend was already right, so it passed before the change. The half that was
broken is the half this repository cannot test in Python. Executed instead via
`tools/check_client_behaviour.js`.

**Original report follows.**

**Severity:** medium · **Found by:** the gear-ratio audit,
8 August 2026

The backend raises the right message, derived from configuration:

```python
step = self._settings.output_step_deg          # 0.06
raise StepError(f"angle must be in steps of {step} deg")
```

**The client throws that message away.** `sayError()` (`app.js:224`) maps the
`step` reason code to a hardcoded string: `"refused — angle must be a multiple
of 0.1°"`. So the operator is told a granularity that is not the one enforced,
by roughly a factor of two, and the correct figure — which travelled all the way
from `config.py` — is discarded on arrival.

The same handler discards the backend's message for **all five** mapped reason
codes; `step` is simply the one where the constant is provably wrong. If
`output_step_deg` is ever retuned (the config docstring at `config.py:53`
explicitly contemplates coarsening every step), the UI keeps saying 0.1°.

**Twin-path again:** one side derives from configuration, the other hardcodes.

**Confirmed by the operator, 8 August 2026:** the 0.1° figure is left over from
an earlier design and is simply wrong. **Fix it.**

**Acceptance:** the operator is shown the enforced step, and it comes from the
backend rather than from a constant in the client.

**Related:** D14 (the same handler is where unmapped errors leak "Failed to
fetch"), ADR-0003.

---

### T8 — Instrumented run on the board over adb
**Status:** done · 7 August 2026 · **Flow:** `WORKFLOWS.md` W1

Ran as designed, and it paid for itself. `.env` created, app started headlessly
with `arduino-app-cli app start user:servo_mvp` at `LOG_LEVEL=DEBUG`, UI driven
by the operator while logs and the database were pulled over `adb`.

**Settled:** D4 (cause found: the W5500 race), D5 (uvicorn ruled out; churn is
`timeout_keep_alive` by design), D1 (confirmed and closed against a real datum).
**Left open:** D6 — first paint still unmeasured.

**Found things nobody was looking for:** D9 (two baselines, 212.7 deg of wrong
movement), the `recover()` hazard under D2, and D10, D11, D12.

The backlog's own argument was right: planning over unknowns produces a plan you
throw away. Three of the four unknowns fell out of one session, and the most
serious defect of the day was not on the list at all.

**Worth repeating** whenever the board is hot and a change is worth watching, at
DEBUG for the duration and INFO afterwards.

**Original entry follows.**

One deliberate session that settles four open defects at once: create `.env`
(D8), start the app, drive `adb` to pull logs and query the database while the UI
is exercised.

Run with the log level at DEBUG for this session specifically, so the relay's
connect/disconnect lines actually appear.

**Settles:** D4 (connection drops), D5 (what is really flooding the log), D6
(load time), and confirms D1 against the real stored datum.

---

### T4 — Moves while unverified: DECIDED, permitted
**Status:** done (decision) · **Recorded in:** ADR-0007

Calibration is an **operator startup ritual**, not a backend startup action: on
first start the operator drives the mechanism to mid-travel and presses Calibrate
to set the datum. Necessary because the mechanism can be moved by hand while
power is off.

`_position_verified` is `False` after every boot (`servo_state.py:35`).

**The UI half is already done** — `app.js:276` flags the Calibrate control and
`:287` shows "Reference not set — press CALIBRATE at the physical home".

`motion_service.py` never consults `position_verified`, so moves are accepted in
that state. **That behaviour is correct and stays** — the site is ~3 hours away,
and refusing movement until someone physically presses Calibrate turns a
recoverable signal loss into a site visit. Full reasoning in ADR-0007.

**Remaining work:** none in code. The unverified warning in `app.js` is now
load-bearing and must not be removed — noted in ADR-0007 so it is not "tidied
away" later.

---

### D3 — The C++ side has no logging
**Status:** done · 8 August 2026 · Batch 2

`ServoBus`, `ServoController` and `NetworkRelay` now log their significant
transitions and failure paths through a new `DiagLog` singleton
(`sketch/src/DiagLog.h/.cpp`) — a bounded ring buffer (`LogRing.h`) fed from
either thread, drained by `BridgeApi::DrainDiagLog()` over a new `mcu_log`
Bridge notify. Bounded per `Tick()` call so a burst cannot make `loop()`
spin, per `RELAY_NOTES.md`'s yield requirement.

Received on the Python side (`app/relay/mcu_log.py`) into its own file,
`logs/mcu.jsonl` — deliberately separate from the main log so a volume spike
on either source cannot evict the other's history, with its own explicit
size-based rotation rather than Logger461's (unverified whether Logger461
supports a second independent sink in this environment). `write_lock_timeouts()`
and `rejected_total()` are both now visible: the former as its own event
(carrying the running total), the latter already did; `DiagLog`'s own
`dropped_total()` (ring evictions) is surfaced in `get_status`'s health line
next to the existing `relay=`/`rejected=` pair. `tools/soak_report.py` pulls
and reports the new file, flagging the D4 write-lock-timeout signature.

**Update, 8 August 2026 — built, flashed, and checked on the real board.**
`arduino-app-cli app start user:servo_mvp` compiled cleanly (143224 bytes
program, 18%; 54649 bytes RAM, 20%) and flashed via OpenOCD/SWD without
error. `Arduino_RouterBridge`'s `notify()` was read directly on the board
(`Arduino_RouterBridge 0.4.3`, `bridge.h:277-287`): it is a variadic
template all the way down to `Arduino_RPClite`'s `RPCClient::notify`, with
no fixed argument-count ceiling — **the six-argument arity concern is
resolved**, not just assumed safe. A live `curl` against the relay IP
(`192.168.10.60:8000/api/v1/system/health`, the correct path per ADR-0001 —
the board's own OS network does not expose the port at all) returned
`"mcu_status":"ready relay=1/rejected=0/diag_dropped=0"` — confirming
`DiagLog::dropped_total()` works end to end through `get_status`.

**One real gap found, not just a theoretical one: the MCU's boot-time
`mcu.relay.ready` notify never arrived.** After several minutes of uptime,
neither `mcu.jsonl` nor any `mcu.*` line exists anywhere in the Python log.
`NetworkRelay::Begin()` pushes that event during `App::Begin()`, and the
first `Tick()` drains and sends it almost immediately after `setup()`
returns — likely *before* Python's `main.py:_start_background()` reaches
`get_mcu_log().register()`, which runs after telemetry-sampler start and
relay registration, i.e. late in Python's own startup. `Bridge.notify` is
fire-and-forget with no acknowledgement (confirmed by reading the library,
above), so a notify sent before the handler is registered is silently lost
— exactly the failure mode named below, now observed rather than
hypothesised. **Practical impact is likely limited to boot-time events
only** — nothing else fired during this run (only 1 relay connection so
far, 0 rejections, 0 timeouts), so this doesn't say whether steady-state
events (fired minutes into a live session, long past the startup race
window) have the same problem; that needs an actual timeout or rejection to
occur to test. Filed as a new backlog item rather than fixed blind.

**Two gaps the drop counter does not cover, stated plainly rather than
implied solved:**

- **`ForwardDiagLog` does not check whether `Bridge.notify` succeeded** —
  matching the existing `net_open`/`net_rx`/`net_close` precedent, none of
  which check it either, so this is not a new inconsistency. But `DiagLog`'s
  ring has already popped the record by the time `notify` runs, so if the
  Bridge is briefly unavailable — the exact condition this logging exists to
  diagnose — the record is silently lost and `dropped_total()` does **not**
  count it. The drop counter only sees ring overflow, not delivery failure.
- **`String(record.message)`/`String(record.event)` allocate on the loop
  thread inside the drain**, up to four small heap allocations per `Tick()`.
  `App.cpp` documents this MCU as having no heap use elsewhere ("no heap on
  the MCU, and the lifetimes are the program's"). Fragmentation risk under
  sustained logging is real and unmeasured — worth watching during the first
  extended board run, not assumed safe because it compiles.

**Original report follows.**

**Severity:** high · **Flow:** `WORKFLOWS.md` W3

Only `App.cpp` produces any output (13 `Serial.print` calls). `ServoBus`,
`ServoController`, `NetworkRelay` and `BridgeApi` have **zero** logging — and
every bug in this project has lived in exactly those four files.

There is currently no way to tell from the board what the MCU side is doing.

**Acceptance:** each of the four files logs its significant transitions and every
failure path, at a level that can be turned down. Log volume must not starve
`loop()` — see `RELAY_NOTES.md` on the yield requirement.

---

### D27 — `synthetic_operator.py` does not reproduce `app.js`'s concurrent poll timers
**Status:** done · 8 August 2026 · Session 2 prep

Rewrote the load generator around a `PersistentPoller` — one kept-alive
`http.client.HTTPConnection` reused across a whole polling loop, closing and
reconnecting only on a transport error or the server's own
`timeout_keep_alive`. This mattered more than the timer-shape gap itself:
the previous version used `urllib.request.urlopen`, which opens and closes a
**fresh** connection on every single call — so the tool was already
massively overstating connection churn relative to a real browser before
D27's finding was even considered.

Each operator now runs three independent poll threads matching `app.js`
exactly — `poll_state_forever` (1 s), `poll_zeros_forever` and
`poll_events_forever` (both 15 s, genuinely separate timers, not one shared
interval) — plus the existing `act_forever` for deliberate actions. A new
`connection_opens` counter per action confirms the fix empirically rather
than by inspection: smoke-tested against a local mock server, each
persistent stream opened **one** connection for the entire run regardless of
request count (e.g. 40 state polls, 2 connection opens — one per operator).

Also added, since this batch's whole point was a run left semi-attended for
hours: a `Checkpointer` that prints a live status line and rewrites the
report file every `--checkpoint-minutes` (default 5), and SIGTERM/Ctrl-C
handling that writes whatever was gathered before exiting rather than losing
it. Both verified directly — a live run with a `SIGTERM` sent mid-run
exited 2, printed "interrupted", and the report file carried
`"interrupted": true` with the partial data intact.

**Not tested:** against the real board over a multi-hour duration — only a
short local run against a mock server. The connection-reuse behavior under
the relay's actual `timeout_keep_alive=5` and W5500 socket ceiling is
exactly what Session 2 itself now measures for the first time with correct
fidelity; that is the soak, not something to simulate again here.

**Original report follows.**

**Severity:** medium · **Raised by:** Batch 2, 8 August 2026

Found while writing ADR 0009. Each simulated operator runs two threads:
`poll_forever` (hits `/servo/state` only) and `act_forever` (sparse, randomised
discrete actions). **Nothing replicates `app.js`'s three independent timers** —
`pollState` on a 1 s `setInterval`, `pollZeros`/`pollEvents` on independent
15 s `setInterval`s (`app.js:9,13,742-744`). A real browser can therefore have
two fetches in flight at once and open a second TCP connection; the synthetic
load never does.

Measuring R1 (the operator ceiling) against this tool as written would
undercount real socket demand and could report R1 "met" without ever
triggering the pattern that motivated ADR 0009 in the first place — the same
trap `OPEN_QUESTIONS.md` Q9 already names for the USB-C question: do not
report a thing measured on the strength of a test that does not exercise it.

**Acceptance:** `synthetic_operator.py`'s poller reproduces the three-timer
shape (or the gap is stated plainly in the soak's own report), before R1 is
reported as met on the strength of a run against it.

**Related:** ADR-0009, R1, D13.

---

### D13 — Requests arriving faster than slots free up are refused
**Status:** done (decided, not fixed) · 8 August 2026 · Batch 2 · **ADR-0009**

`kMaxRelaySockets` stays at **6**. The wall is fixed by hardware (7 sockets,
W5500 minus the listener) and cannot be tuned; the real lever,
`timeout_keep_alive` (`main.py:172`), stays at its current value of 5 because
nobody has measured what a lower value buys yet — tuning it blind repeats the
exact mistake D9 and D4 already cost this project. Session 2's soak is where
that measurement happens.

---

### D4 — Connection drops after a few commands; requires a page refresh
**Status:** CLOSED · 11 August 2026 · Session 3 (SSE Migration) · Collapsed 3 polling connections/operator to 1 persistent SSE stream. 1, 2, and 3-operator 10-min soaks completed cleanly with 0 stream reconnections (`conn_opens=0`) and 0 socket oversubscriptions.

**Cause: the W5500 was accessed from two threads with nothing serialising them.**
`Poll()` runs on the loop thread; `WriteToClient()` and `CloseClient()` run on
the Bridge thread via `net_tx` / `net_shutdown`. Six sockets, but **one chip and
one SPI bus** — so the two threads interleaved mid-transaction. There was no
mutex anywhere in `sketch/src/`.

The candidates listed below were all wrong, and cheaply eliminated:

- **Chunk size — not the cause.** Still 128 on both sides. Untested as a
  *throughput* question; see D6.
- **Slot exhaustion — not the cause.** Drops reproduced with slots free.
- **Slot lifecycle — not the cause.** `Poll()` implements relay rules 1, 2 and 4
  correctly. Those rules govern ordering *within* one thread; this was
  contention *between* threads, which none of them covered.

**Fix:** a `k_mutex` around every W5500 touch, sinks dispatched outside the lock
(holding it across a sink deadlocks against `net_tx`), and a bounded 50 ms wait
on the Bridge side so a busy chip fails a write instead of hanging the RPC
thread. New rule 7 in `RELAY_NOTES.md`.

**Measured, same board, same UI, before and after:**

| | before | after |
|---|---|---|
| Sampler gaps in the 10–12 s band | 3 | 0 |
| Longest gap | 11.00 s | 2.00 s |
| Fabricated positions stored | 7 | 0 |

416 samples over 6.9 minutes of live driving. Operator report: "feels calmer
than the chaos of before."

**Why not closed (original reasoning, still correct):** seven minutes is not
a soak, and a race that stops reproducing has not been proved absent.

**What Session 2's soak found, night of 8 August 2026 — two runs:**

| | 3 operators, ~22 min (Ctrl-C'd) | 1 operator, 15 min (completed) |
|---|---|---|
| MCU connections rejected | 1462 | 49 |
| `servo_read` timeout episodes | continuous, 18:23–18:38 UTC, **never self-recovered** — required an app restart | 2 (20:33:33, 20:33:44 UTC), **self-recovered**, run continued clean |
| Sampler stall | — | one 30 s gap (worse than the original 11 s signature) |
| Fabricated position (`counts <= 0`) | 1 | 1 |
| MCU write-lock timeouts (the mutex fix's own counter) | **0** | **0** |

**The headline: this reproduces at 1 operator, nowhere near the 6-slot
ceiling** — so it is not purely a connection-oversubscription problem, and
raising `kMaxRelaySockets` or tuning `timeout_keep_alive` alone will not
close it. **`write_lock_timeouts` stayed at zero through both runs**,
including the fully-latched 15-minute episode — the diagnostic the mutex
fix added to prove itself never fired once. Either the trigger for this
stall is a different path through the W5500 than the one the mutex
serialises, or the counter itself has a gap.

**Two live hypotheses, neither confirmed:**
1. **Load-correlated persistence, not load-correlated onset.** The stall
   happens regardless of load; how long it *lasts* (self-recovers in
   seconds vs. latches until restart) may scale with concurrent churn.
2. **`DiagLog` heap exhaustion under sustained rejection traffic.**
   `BridgeApi::DrainDiagLog()` allocates two `String`s per record on a
   device `App.cpp` documents as otherwise heap-free (flagged, unmeasured,
   in the Batch 3 note below) — 1462 rejections is a lot of allocation
   churn; 49 is much less, which is at least consistent with (but does not
   prove) a fragmentation threshold.

**Correction, 10 August 2026 — both runs in the table above were run with an
extra real browser open and watching, undocumented at the time.** Neither
the 3-operator nor the 1-operator run was actually operator-count-clean: a
real browser (its own poll timers, per D27) was open throughout both. So
"reproduces at 1 operator, nowhere near the 6-slot ceiling" overstates the
isolation — true load was closer to 2 operators' worth. The qualitative
finding (`write_lock_timeouts` stays 0, this is not purely oversubscription)
still holds, since even 2 operators' worth stays under the 6-slot ceiling.
Caught before it could affect a third run — see below.

**2 operators, 15 min, clean — run 10 August 2026, 14:22:20–14:37:20 local,
no browser open:**

| | |
|---|---|
| Requests / transport failures (client side) | 1518 / 58 |
| `move` rejections | 50 of 66 attempted — the ceiling refusing real commands |
| Sampler gaps > 2 s | 7, of which 2 in the 9–13 s stall band |
| Worst gap | **23.06 s** (14:27:39) — worse than both prior signatures (11 s, 30 s) |
| Other stall-band gaps | 12.07 s ×2 (14:29:33, 14:33:04) |
| Fabricated positions | 0 |
| MCU connections rejected | 12 |
| MCU write-lock timeouts | **0** — fourth run in a row at zero |
| Board after the run | healthy, no restart needed — self-recovered every time |

**The stall reproduced three times in this one 15-minute run, exactly at the
ceiling, with far less rejection churn (12 vs. 1462) than the run that
produced hypothesis 2.** That weakens hypothesis 2 (`DiagLog` heap exhaustion
under rejection churn) — 12 rejections is little allocation pressure —
without confirming hypothesis 1 either: three episodes here is more
*frequent*, not clearly longer, than the single 30 s gap at the
(uncorrected) ~1-operator run. **Neither hypothesis is confirmed or
eliminated.**

**Hypothesis 3, found reading the code 10 August 2026, not yet measured:**
**the yield is fixed, the work it is yielding around is not.** `App::Tick()`
(`App.cpp:78-92`) calls `g_relay.Poll()` then a single `delay(1)` —
regardless of how much real work `Poll()` just did. `RELAY_NOTES.md` rule 3
already documents this exact failure shape (`loop()` starves the Bridge RPC
thread, `servo_read` misses its 10 s deadline, "Response for unknown
msgid") and the `delay(1)` is its fix — but rule 3's own framing is
`Poll()` busy-spinning on *nothing to do*. Under real load `Poll()` is not
idle: step 3 (`NetworkRelay.cpp:191-203`) takes and releases `chip_lock_`
**once per slot**, up to 6 times a pass, each a real SPI read, with **no
yield between slots** — only the one `delay(1)` at the very end of `Tick()`.
`write_lock_timeouts` cannot see this: that counter only fires inside
`net_tx`'s bounded wait, and this path never touches it. That is consistent
with **all four runs to date reading zero** on that counter while the stall
still occurs, and with the stall getting *more frequent*, not necessarily
longer, as socket count rises — more slots with real data means more
back-to-back chip work with no yield in between, every single pass.

**Distinct from hypotheses 1 and 2 — neither assumed anything about
`Tick()`'s own timing, both stayed near the mutex/heap.** Not yet measured:
whether `Poll()`'s wall-clock cost per pass actually grows the way this
predicts under 2-operator load, and whether it correlates with the three gap
timestamps already captured (14:27:39, 14:29:33, 14:33:04). Cheapest way to
find out: instrument `Tick()`'s own duration (`millis()` before/after),
log it via `DiagLog` only when it crosses a threshold (say 20 ms), and
correlate against the next run's sampler gaps — measurement before any code
change, same discipline as Batch 1's own title.

**1 operator, 10 min, clean — run 10 August 2026, 14:45:03–14:55:03 local, no
browser open:**

| | |
|---|---|
| Requests / transport failures (client side) | 646 / 6 |
| `move` refused (client-reported) | 15 — **board's own count for the same window is 0**, an unexplained discrepancy, not yet investigated |
| Sampler gaps > 2 s | 1, **none in the stall band** |
| Fabricated positions | 0 |
| MCU connections rejected | 0 |
| MCU write-lock timeouts | 0 |
| `soak_report.py` verdict | **`clean` — no stall signature at all** |

**This overturns the headline conclusion at the top of this entry.** "D4
reopened — the stall reproduces even without socket contention" was written
from the two contaminated runs. The genuinely clean 1-operator baseline shows
**zero** stall-band gaps in 10 minutes, against **three** in the clean
2-operator run's 15 minutes. Read plainly: **the stall's onset looks
load-correlated after all** — it just takes more than one real operator's
worth of traffic to trigger it, which the contamination was masking by
adding roughly one operator's worth of hidden load to what looked like a
"1-operator" test.

**This makes hypothesis 3 the strongest of the three**, not weaker: it is
exactly a load-scaling mechanism (`Poll()` doing proportionally more real
work as active sockets carry more traffic, against a fixed 1 ms yield that
does not scale with it), and it is the only hypothesis that predicted *onset*
scaling with load rather than just persistence. Hypotheses 1 and 2 remain
open but now weaker: hypothesis 1 assumed onset was load-independent, which
this data contradicts; hypothesis 2 (heap exhaustion) has no mechanism for
why 12 rejections in 15 minutes would matter but a session with effectively
zero rejections (1-operator, clean) would not.

**Hypothesis 3 confirmed by direct measurement, 10 August 2026.** Added
`kSlowPollThresholdMs` (20 ms, `Config.h`) and a timer around `Poll()` in
`App::Tick()` (`App.cpp:78-92`), logged via `DiagLog` as
`mcu.relay.slow_poll` (arg1 = pass duration in ms) whenever crossed.
Rebuilt and reflashed clean (143368 bytes program/18%, 54693 bytes RAM/20%),
`tools/soak_report.py` updated to tally it.

**3 operators, 10 min, clean — run 10 August 2026, 15:14:57–15:24:57 local,
freshly reflashed:**

| | |
|---|---|
| Requests / transport failures (client side) | 596 / 495 (83%) |
| Worst request latencies | `state` max 16.3 s, `events_poll` max 13.8 s, `zeros_poll` max 12.8 s |
| **MCU slow `Poll()` passes** | **2200, worst pass 1000 ms** |
| MCU write-lock timeouts | 0 |
| MCU bus-refresh stalls | 0 |
| MCU connections rejected | 0 |
| Sampler gaps > 2 s | 1, none in the stall band |
| Fabricated positions | 1 (`counts=-1` at 15:20:17) |
| Board after the run | intermittently reachable, not fully wedged — recovered without a restart |

**This is no longer circumstantial.** `Poll()` genuinely took up to a full
second in a single pass, 2200 times in ten minutes, while
`write_lock_timeouts` and `bus_stalls` both stayed at zero — direct proof
the mutex diagnostic cannot see this failure mode, because it isn't chip
contention. A `Poll()` pass that long, with only a fixed 1 ms yield after
it, starves everything downstream: the Bridge RPC thread (`servo_read` and
friends) and every client HTTP request queued at the relay, which is the
likely explanation for this run's 83% client-side failure rate — a
different-looking symptom (mass request failure, not sampler gaps) from the
*same* mechanism, this time not clustering into the classic 9–13 s sampler
signature.

**Not yet known: which step inside `Poll()` costs the second** — disconnect
detection, accept, or the per-slot bulk read (`NetworkRelay.cpp:191-203`,
the prime suspect since it is the one step scaling with active-socket
count). `DiagLog::dropped_total()` read 0 after the run, so the 2200 figure
is complete, not undercounted by ring overflow.

**Done, 10 August 2026 — result: dominated by probe frequency (~1600
lock acquisitions/sec across all 6 slots), not one slow call. The fix built
from that finding (batch step 3 into 1 lock acquisition) made client
failures worse, not better, combined with an independently-real Python
async/blocking fix (see Session 2 log, steps 8-11). Both reverted; root
cause of the regression itself was not established.** A shield swap does
not raise the 6-socket ceiling (W5500/W6100 both cap at 8 hardware sockets)
— **decided instead: replace the 3-connections-per-operator polling model
with one SSE stream per operator**, next session, before re-attempting any
C++-side fix. See the Session 2 log above for the full sequence and numbers.

**Also found, not yet filed as its own item:** a single truncated/malformed
JSON body from `/api/v1/system/events` during the 1-operator run, and a
robustness gap in `synthetic_operator.py` itself — `get()` catches
`http.client.HTTPException`/`OSError` but not `json.JSONDecodeError`, so one
malformed reply permanently kills that operator's poll thread for the rest
of the run instead of retrying like every other failure path.

**Remaining, separate:** the UI declares a disconnection on a *single* failed
poll — see D11.

**Original report follows.**

**Severity:** high · **Needs investigation**

After a handful of commands the UI loses its connection and only a refresh
restores it. Reproduces **with a single UI instance open**, so this is not purely
a concurrency-limit problem.

Candidate causes, none confirmed:
- **Relay chunk size is half the proven value.** `RELAY_NOTES.md` §5 states
  plainly: *"256 is the value the working relay used."* The code ships
  `kRelayChunkBytes = 128` (`sketch/src/Config.h:43`) and `RELAY_CHUNK_BYTES=128`
  (`python/.env.example:10`). The two sides agree with each other, so the contract
  checker is happy — but both differ from the reference implementation. Chunk size
  is bytes per Bridge message, so **halving it doubles the number of Bridge round
  trips for identical payload.** Given that the Bridge starving is already a known
  failure mode (rule 3, the `loop()` yield), doubling its traffic is a plausible
  contributor to both this and D6. Cheapest experiment on the list: set it to 256
  on both sides and re-run.
- Relay slot exhaustion. `kMaxRelaySockets = 6` (`sketch/src/Config.h:45`) is the
  **only** connection limit in the system — there is no Python-side cap. A single
  browser opens up to 6 connections per host on its own, and `app.js` polls
  continuously, so one operator can plausibly occupy every slot if slots are not
  released promptly.
- Slot lifecycle bugs of the class already documented in `RELAY_NOTES.md`.

**Acceptance:** a single operator can drive the UI indefinitely without a
refresh. Determine and document the true concurrent-connection ceiling.

**Related:** D5, R1.

---

### D18 — A failed CSV export navigates the operator out of the application
**Status:** done · 11 August 2026 · **Severity:** medium · **Found by:** operator lens, 8 August 2026

`doExport()` (`app.js:522`) sets `window.location.href` to the export endpoint.
That is not a request the page can observe: there is no `catch`, no status, no
notice. If the endpoint errors, or the relay refuses the connection, the browser
replaces the control UI with its own error page and the operator has to find
their way back — from a machine-control screen.

It is also a **new connection** every time, spending from the same six-slot
budget as D13, taken at the moment an operator is most likely to also be driving.

**Sharpened by the twin-review of Batch 1, 8 August 2026.** D15's in-flight
guard went into `bind()`, and `doExport()` is the one handler it cannot hold:
it is **synchronous**, so `await handler()` resolves on the next microtask and
the control is released before the operator can see it was ever busy. Three
presses therefore start three concurrent exports, each a `StreamingResponse`
holding a relay socket — and the endpoint sets `Content-Disposition:
attachment`, so the browser does not cancel the previous one the way it cancels
a navigation. **The slowest, heaviest request in the application is the only
command with no press guard.** Making it a background fetch fixes both halves
at once.

**Acceptance:** export fetches in the background, reports success or failure like
every other command, never navigates away from the control page, and is covered
by the same in-flight guard as every other control.

**Related:** D13, D14, R5 — the export is the seed of the benchmarking pack, so
it will be used more, not less.

---

### D22 — The only export control is fixed at 24 hours
**Status:** done · 11 August 2026 · **Severity:** high · **Raised by:** the operator, 8 August 2026

`doExport()` (`app.js:522`) hardcodes the window:

```js
const from = now - 24 * 3600;
```

**The handover benchmark is the receiving team running the system for several
days unattended, after which the record is loaded and read.** With a 24-hour
button, four days of a five-day run cannot be retrieved from the UI at all —
they exist in the database and are reachable only by someone with `adb` or the
sshfs mount, which is not the receiving team.

The data is there: telemetry is sampled (twice a second, retained 30 days as
of 23 August 2026) and `torque_kgcm` is already stored, same as every other
field. **The gap is purely the operator's route to it**, and it defeats the
primary reason R5 exists.

**Scope confirmed and widened by the operator, 8 August 2026.** Two deliverables,
not one, and **both must exist on the backend *and* in the UI** — a tool that
only runs from a shell is unreachable for the team who ran the test:

1. **Export over a chosen range, as XLSX** (revised 10 August 2026 — see R5;
   was CSV). The operator picks start and end. The backend endpoint already
   takes `from` and `to`; it is the UI that hardcodes 24 hours. So the range
   control is mostly unchanged — but the range picker has to cope with a
   five-day window without the operator typing epoch seconds.
2. **The chart set, embedded in that same workbook.** Same range. **Decided
   10 August 2026 (R5): native Excel chart objects, not server-rendered
   images** — avoids exactly the sampler-contention risk this entry used to
   flag as the open question, since writing chart objects isn't rasterising
   a plot.

**Acceptance:** from the UI, the operator picks a time range spanning days and
gets one XLSX file, data and charts together, for exactly that range; it does
not navigate away from the control page (D18); the export is reachable from
the backend alone for anyone working over `adb`.

**Related:** R5 (this is its delivery path), D18 (same control, silent failure),
T9 (a multi-day pull must not exhaust memory — stream it, same discipline as
the current CSV export).

---

### D31 — Telemetry export drops instantly on the frontend with "controller busy"
**Status:** CLOSED · 23 August 2026 · **Severity:** high · **Found 11 August 2026**

The operator reported that downloading a 24-hour telemetry export (via the new binary stream route) failed instantly with the toast: "the controller is busy or did not answer — wait a moment and try again". The download progress bar stayed at 0%.

**Fixed 11 August 2026: the 22-second SQLite timeout**, unchanged from the original entry — a flat `COUNT(*)` replaced a sorting subquery, 22s → 0.01s.

**The 16-second-Pydantic-packing hypothesis was wrong, board-measured, 23 August 2026.** Reproduced the export live on the board at full scale (42,152–45,990 rows) with Pydantic *still in the loop*, unchanged: server-side packing took 4.4–11s, never the bottleneck. The actual "controller busy" toast traced to a real, unrelated client-side bug — `app.js`'s `generateExcelXlsxZip()` called two functions, `makeChartXml`/`makeDrawingXml`, that were never written (`ReferenceError`, 100% reproducible, confirmed by replaying the exact captured payload through the real code). `sayError()`'s generic "no HTTP status = unreachable" fallback misreported that client-side crash as a controller problem.

**The real transport bottleneck, found the same session**: not Pydantic, not the relay chunk size alone — **gzip compression was never enabled for actual export requests** (`GZipMiddleware` is registered and correct, but nothing had exercised it at scale). Enabling it: **5.3x faster** (120.2s → 22.8s for a 15-day/45,990-row export, board-measured), because the real fixed cost is the Bridge's ~11.5 KB/s physical link (LPUART1 @ 115200 baud — see `RELAY_NOTES.md` §5), and gzip cuts the bytes that have to cross it by ~81%. Pydantic bypass was never implemented and is no longer worth pursuing — it was optimizing a cost that was never the dominant one.

**Closed by**: `relay_chunk_bytes` 128→224 (D6/RELAY_NOTES §5), gzip enabled on the export path, and the client-side XLSX generator rebuilt correctly (R5) — `makeChartXml`/`makeDrawingXml` now exist, verified against a real generated reference file rather than guessed. **Update, same day: "rebuilt correctly" overclaimed — a separate zip-structure corruption bug survived this closure and was found live via a real OnlyOffice failure; see R5 in `BACKLOG.md` for that fix.**

**New finding folded into the ADR**: `app.js` runs `pollState` on an
independent 1 s timer and `pollZeros`/`pollEvents` on independent 15 s
timers, not sequential awaits — so a single browser can transiently open two
connections, not one. The real margin under the 7-socket wall is smaller
than `OPEN_QUESTIONS.md` Q2's answer assumed.

**Raised, not fixed:** D27 — `tools/synthetic_operator.py`'s load pattern
does not reproduce that concurrent-fetch behaviour, so R1 measured against it
as written would undercount real demand.

Full reasoning: `docs/adr/0009-connection-ceiling.md`.

**Original report follows.**

**Severity:** high · **Measured 7 August 2026**

**This is the "first press does nothing, press it again" symptom**, and it now
reproduces on demand. Identical requests, from one machine, differing only in
spacing:

| pattern | requests | failures |
|---|---|---|
| back to back, new connection each | 10 | **5** |
| paced at 1 s, as the UI polls | 10 | **0** |

**The ceiling, measured:** `kMaxRelaySockets = 6` slots, each held for about
five seconds after use by uvicorn's `timeout_keep_alive=5` (`main.py:172`, set
deliberately so idle sockets do not park a slot). That is a sustained ceiling of
roughly **one new connection per second**, with a burst tolerance of six.

A browser hides this while it is only polling, because it reuses one socket. It
surfaces the moment an action needs a *new* connection and every slot is busy —
the request is refused, the operator sees nothing happen, and pressing again
works because a slot has freed by then.

**This is what R1 has to be measured against.** The target is roughly three
remote operators plus one local session. A single browser may open up to six
connections to one host on its own, so the slot budget can be spent by one
person before the second connects.

Not a race, and not fixed by the W5500 mutex: the relay is refusing politely and
correctly (`Poll()` calls `fresh.stop()` and increments `rejected_total_`). The
question is whether six is enough, and what should happen when it is not — a
refusal is currently indistinguishable from a failure at the browser.

**`rejected_total()` already counts these and cannot be read from the board**,
exactly like `write_lock_timeouts()`. Two diagnostics, both unreachable; see D3.

**Acceptance:** the ceiling is stated in numbers here (done above), the target in
R1 is either met or the limit is raised deliberately, and a refused connection
produces something an operator can understand rather than silence.

**Promoted and reframed, 8 August 2026 (operator lens).** This is the most
demo-damaging behaviour in the product: in a room of people deciding whether to
procure a full project, "press it twice" is what they will remember. Two things
follow.

**First, it is a decision, not a fix.** The measurement is done. What is missing
is a choice between raising `kMaxRelaySockets`, dropping uvicorn's
`timeout_keep_alive=5`, pooling connections on the client, or accepting the
ceiling and surfacing refusals honestly — each with a different cost, and the
choice changes what R1 can possibly measure. **It needs an ADR**, or it will be
re-argued at every future connection bug, exactly as the chunk-size question was.

**Second, the operator half is now two separate defects**, because "the operator
sees nothing" turned out to be two mechanisms, not one:

- **D14** — when the refusal *does* reach the client, it is shown as the browser
  string "Failed to fetch".
- **D15** — nothing marks a command as in flight, so the operator presses again,
  opening another connection and spending another slot. **The UI's reaction to
  the symptom feeds the cause.**

Fix both before measuring R1, or the measurement includes the operator's
double-presses as load.

---

### D10 — `logger.exception` swallows the exception; the sampler's real fault was a thread-safety bug in the SQLite layer
**Status:** CLOSED · 24 August 2026 · **Severity:** medium · **Found by:** a
live board run, 7 August 2026

**Fixed 7 August 2026: the logging.** The cause was the Logger461 stand-in in
`main.py`: its `exception()` was a straight copy of `error()`, and attaching
the exception is the entire difference between the two. It now records the
exception type, message and traceback. **The test stub in `conftest.py` had
the identical gap** — fixed together, the twin-path pattern for the fourth
time in this repository.

**It happened again, 23 August 2026, twice (13:02:22, 13:39:55).** The
backlog's original follow-up quoted a two-line traceback and guessed "a race
around `ZeroStore.get_active()` returning a reference mid-mutation (a zero
being changed/replaced)." **Both halves of that guess were wrong, found
24 August 2026 by re-reading the actual JSONL log records instead of the
paraphrase:** the real traceback is one call path only —
`TelemetryService._run` → `_sample_once` → `ServoStateStore.snapshot` →
`_to_output_deg` (`servo_state.py:276`) — the quoted `_active_counts()` frame
was never in either real stack. And there was no zero-table write anywhere
near either timestamp, so nothing was "being changed" — the active zero
(`raw_counts=2046`) was untouched and still is.

**Root cause, reproduced empirically:** `Database` holds one shared
`sqlite3.Connection` (`check_same_thread=False`) across every thread — the
sampler and every API request. Writes were serialized through `write_lock`;
reads were not. A stress script against the real repository classes (four
reader threads calling `get_active()` in a loop, two threads doing ordinary
telemetry inserts — **no zero writes at all**) reproduced a `None` in the
`raw_counts` column (`NOT NULL` in the schema) within about a second, and, in
a second run, an outright `IndexError: tuple index out of range` from a torn
`sqlite3.Row` — a failure mode no theory about stored data can produce. Two
threads issuing statements on the *same* Python connection object without a
shared lock is undefined, regardless of what's actually stored; "SQLite
permits concurrent readers" (the class's own prior docstring) is true of
separate connections and false of this one shared, unsynchronized object.
Serializing every statement — reads included — through `write_lock`
eliminated it across a 185,000-read stress run with zero failures.

**Fixed by routing every statement through the lock, not just writes** —
the identical twin-path gap existed in four more places, found by grepping
both repository files rather than stopping at the one call site in the
traceback: `SqliteZeroRepository.list_all/get/get_active` were unlocked, and
`set_active`'s own verification `SELECT` sat *outside* its `with` block,
half-protecting itself. `SqliteTelemetryRepository.count_range` was unlocked;
`query()` streamed rows via a generator holding no lock at all across
`yield` — rewritten to fetch the matching rows while holding the lock, then
yield from that list, so a caller consuming results slowly doesn't hold
`write_lock` open for the duration. `Database`'s docstring is rewritten to
state what was actually measured instead of the assumption that caused this.

**Regression test:** `test_database.py::TestConcurrentAccess::test_reads_survive_concurrent_writes`
— the same reader/writer stress shape, run against the real `Database` and
both repositories for a bounded 2 seconds. Confirmed **RED** on the pre-fix
code (reproduced both the `None` and the `IndexError`, plus a third mode:
`set_active`'s own half-protected tail read breaking under its own writer
thread), confirmed **GREEN** after. Suite: 222 → 223. Native checks (194) and
the bridge contract are untouched — pure Python fix, nothing in `sketch/`
changed, no board needed to close this.

**One more artifact, noted so a future session doesn't chase it as a second
bug:** the 13:39:55 log record's traceback shows nonsensical source lines for
two of its frames (`_run` printing `try:`, `_sample_once` printing a bare
docstring line). That's `linecache` reading whatever was on disk *at
exception-format time*, not at import time — a known side effect of editing
files under a running process on the sshfs-mounted dev copy (§6,
`CLAUDE.md`). The line *numbers* in that traceback are accurate to what was
actually running; only the printed source text is stale.

**Related:** D2, D9 (the repository's other twin-path defects). Does not
block or interact with R2 — Session 6's second half proceeds independently.

**Original report follows.**

One `ERROR telemetry sampling failed` was recorded at 21:37:58 on 7 August 2026.
It cost one skipped sample — the only sampler gap over 2 s in the whole run.

**The cause cannot be determined, because the record contains no exception text
and no traceback.** `telemetry_service.py:91` calls `logger.exception(...)`, and
what reached both the JSONL file and the container log was the message alone
with `extra: {}`.

So the system logged that something failed, and nothing about what. That is
worse than not logging it: it looks like diagnosis.

**Two things to do, and they are separate:**

1. Fix the logging so an exception carries its type, message and traceback. Then
   check every other `logger.exception` call site for the same loss.
2. **Find the actual error.** It is still unexplained, and a sampler that throws
   once in seven minutes will throw during a demo.

**Acceptance:** an exception in the sampler produces a record from which the
fault can be identified without reproducing it; and the 21:37:58 failure is
explained.

---

### D32 — Speed field snaps to the angle's step grid, not its own
**Status:** CLOSED · 24 August 2026 · **Severity:** low · **Raised by:** the
operator, 24 August 2026

**The angle half was not a defect — confirmed, closed without a code change.**
`89.94` is `90 - ANGLE_STEP` exactly (`app.js:24`, `ANGLE_STEP = 0.06`): the
arrow key steps by one servo count in output degrees, working as designed,
same number as the documented rounding decision (`PROJECT_STATE.md`'s
gear-ratio audit).

**The speed half was a real, root-caused bug, fixed.** The SPEED field's step
buttons carry `data-d="5"` (`index.html:100,102`), but `nudge()`
(`app.js:1960-1968`) rounded *every* field it was bound to against the same
hardcoded `ANGLE_STEP`: `30 + 5` → `Math.round(35 / 0.06) * 0.06` = `34.98`.
Fixed by making `nudge()` snap only when `inputId === "inAngle"`; every other
field (speed) now just takes its own delta.

**A third piece, found investigating the nudge buttons and fixed the same
session — the angle field's typed path silently rewrote what the operator
typed.** `doMove()` sent `Math.round(target / ANGLE_STEP) * ANGLE_STEP`
regardless of what was typed — type `0.08`, it silently became `0.06` with no
indication anything changed. The backend already had the real guard for this
(`_validate_step`, `motion_service.py`, raises `StepError`), already tested
at the API level (`test_servo_routes.py::TestStepRefusalStatesTheEnforcedStep`)
and already displayed correctly by the client (`check_client_behaviour.js`'s
D21 check) — but the client's silent pre-snap meant neither had ever actually
been connected to the other from a browser. Fixed by deleting the client-side
snap in `doMove()`; the existing guard and display path now do their job,
confirmed live on the board during this session (an accidental test POST of
`72.07` was rejected with the real backend message before the fix landed).

**Verified:** `check_client_behaviour.js` (new: speed nudge does not snap to
0.06; a typed non-multiple angle reaches the backend unmodified and the
refusal displays). Board-confirmed live.

**Related:** D21 (built the display path this reconnected), D35 (the
speed-step *enforcement* this investigation originally intended to add,
pulled out and postponed after a board measurement raised doubt about the
unit conversion it would have relied on).

---

### D33 — Recent Activity timestamps display in UTC, not local time
**Status:** CLOSED · 24 August 2026 · **Severity:** low · **Raised by:** the
operator, 24 August 2026

`EventService.record()` (`python/app/core/events.py`) stamped
`datetime.now().isoformat(timespec="seconds")` with no UTC offset, on a
container whose system clock is UTC (same fact D30's fix documented).
`app.js`'s `eventTime()` parses an offset-less string as already-local, so no
conversion happened and the raw UTC clock showed as if it were local time.
Same species as D30, different code path.

**Fixed:** `datetime.now(timezone.utc)`, so the stamped string carries an
explicit offset and the browser's own `toLocaleTimeString` converts it
correctly.

**Also found, left alone deliberately:** `zero_service.py`'s `created_at` on
captured zeros has the identical bug — currently not rendered anywhere in the
UI, so out of scope; worth its own entry if that field is ever surfaced.

**Verified:** `test_events.py::test_timestamp_carries_an_explicit_utc_offset`
(new). Board-confirmed live (app restarted, Recent Activity checked).

**Related:** D30 (same UTC/local class, different code path).

---

### D34 — Angle displays truncate to 1 decimal, losing the 0.06° step
**Status:** CLOSED · 24 August 2026 · **Severity:** low · **Raised by:** the
operator, 24 August 2026 (move log); widened to every angle readout the same
session, at the operator's direction

Not D21 resurfacing — D21 was stale UI copy; this was display precision.
`ANGLE_STEP = 0.06` is the real minimum step, but every angle-facing display
formatted at 1 decimal place, which cannot distinguish two adjacent steps
(0.06 and 0.12 both read "0.1"). The backend already computed and sent
2-decimal precision (`servo_state.py`, `round(..., 2)`); the loss was
entirely client/message-formatting, throwing away precision the backend
already provided. 2 decimals was also already the established precision
elsewhere in this exact codebase (the angle input's own typed-value
stepping; the out-of-travel error message), so this fix brought the rest
into line with existing precedent.

**Every location fixed, all to 2 decimals:**

| File:line | What |
|---|---|
| `app.js:415` | current position (`posN`) |
| `app.js:454` | target readout |
| `app.js:464` | delta (Δ) readout |
| `app.js:608` | saved-zero list angle |
| `motion_service.py:87` | `from_deg` in the move-accepted event's structured data |
| `motion_service.py:89` | move-accepted event message |
| `motion_service.py:112` | `at_deg` in the stop event |
| `motion_service.py:218-219` | fine-approach event message + `overshoot_deg` |
| `motion_service.py:242` | out-of-travel error's `low`/`high` (was inconsistent with the `.2f` already on `target_deg` in the same sentence) |

**Verified:** `test_motion_service.py` (2 new tests: message precision,
`from_deg` precision) and `check_client_behaviour.js` (5 pre-existing
1-decimal assertions updated to 2 decimals — the same sweep-every-copy
discipline this project's own history exists to enforce). Board-confirmed
live.

**Related:** D21 (closed, different bug — stale copy, not this).

---

## Requirements captured but not yet designed

