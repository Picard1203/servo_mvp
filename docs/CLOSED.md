# Closed items

**The past tense of `BACKLOG.md`.** Every entry here is done; the reasoning is
kept because it is the record, not because it is pending. Nothing in this file
is work.

`AUDIT.md` is a different thing again: defects found *before* this backlog
existed, frozen. This file is items that entered the backlog and left it.

Split out of `BACKLOG.md` on 8 August 2026 — closed entries were 25% of the
file every session has to read.

---

### D37 — `NetworkRelay.cpp` had a stray unmatched closing brace, build-breaking
**Status:** done · 30 August 2026 · found by Session 14's `/twin-review`,
hit live blocking the client demo

`sketch/src/NetworkRelay.cpp:170` had a bare `}` immediately before the
real `}  // namespace net` closer, with nothing left to close — a real
compiler rejects the file. Session 14's whole-app review found and flagged
this HIGH/build-breaking (`docs/REVIEW_FINDINGS.md`, firmware #1); it went
untriaged into the client demo, which hit it live — `arduino-app-cli app
start` failed with the exact compile error. Neither `tools/verify.py`
check catches this class of bug: the native suite never compiles this
file (needs `Arduino.h`/`Ethernet.h`), and the bridge contract checker
reads source text, not a build. Fixed by deleting the stray line;
confirmed by restarting the app clean.

**Prevention added the same session, not deferred:**
`tools/check_brace_balance.py` — a small standalone script checking brace
balance (comments/string literals stripped) across every
`sketch/src/*.cpp`/`*.h` file the native suite can't compile — wired into
`tools/verify.py`'s gate as its 5th check the same session, not left as a
manual-only script or a separate backlog item.

**Related:** `docs/REVIEW_FINDINGS.md` firmware #1.

---

### D12 — No way to return to the datum after activating a saved zero
**Status:** closed, 30 August 2026 · superseded, not fixed in place

The activate/baseline model this defect depends on is being removed
entirely by **R10** (zero service overhaul, decided the same day). Once
"activating a zero" no longer exists, there is nothing to need a way back
from. Closed on the decision, not deferred until R10's build lands — the
old model was never going to get a "return to datum" button written for
it.

**Related:** R10.

---

### D19 — Saved positions are listed against a baseline of 0 when no zero is active
**Status:** closed, 30 August 2026 · superseded, not fixed in place

Same reasoning as D12: **R10** removes the baseline concept entirely, so a
saved point is always shown against the one datum, never a possibly-absent
active zero. The state this defect describes stops being reachable, by
design, not by patching `renderZeros()`'s fallback.

**Related:** D9, D12, R10.

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

### T14 — Triage the unslotted items; audit backlog and doc hygiene deliberately
**Status:** CLOSED · 24 August 2026 · **Severity:** medium · **Raised by:**
the operator, 23 August 2026

All fourteen unslotted items given a real session (D24, D26, D30, T12, D8,
D29, D23, D25 in Session 8; D28, D35 in Session 10) or an explicit reason
they don't get one (T13 stays deliberately opportunistic per its own entry;
T15 is blocked on an operator decision, moved to `OPEN_QUESTIONS.md` Q10).
The Closed index table gained the three items it had silently dropped (D3,
D27, D13). **D33 and D34 were pre-diagnosed going into this session and
closed immediately after, rather than slotted** — see their own entries.

**Two further instances of the same drift class, caught closing this item
out rather than by accident, same as the two it was opened to fix:**
`CLAUDE.md` §3's quoted Python test count was stale (222, actual 223 at the
time — confirmed by running the suite; later 226 after this session's own
fixes and their tests); and two live references to "R2 next" (`BACKLOG.md`'s
Session 6 row, `PROJECT_STATE.md`'s own Session 7 paragraph — the second one
introduced by this very session, in the act of writing this item's own
closure) had gone stale the moment Session 8 was inserted ahead of R2.

**Acceptance held:** every open item in `BACKLOG.md` now has a batch or a
stated reason it doesn't; every index table matches what it indexes.

**Related:** T13 (overlaps in spirit, not in scope).

---

### D24 — Two `InvalidReadingError` guards were unexercised; the docs claimed 100%
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

Coverage of `app/` was 99%, not the 100% seven documents quoted — nothing
measured it. The two unexercised statements were the guards in
`ZeroService.capture()` (the exact line D2 was filed about) and
`ServoStateStore.read_counts()`. Both now have a test that fails without
them, verified RED then GREEN. Coverage is measured and gated at 99% in
`pytest.ini`; `tools/verify.py` (T12) reports it every run.

**Related:** D2, ADR-0008, T12.

---

### D30 — `soak_report.py` compared a local cutoff string against UTC logs, and reported a catastrophic run as clean
**Status:** CLOSED · 25 August 2026 (code fixed 8 August 2026; regression
test was the missing half) · **Severity:** high

Both JSONL logs are UTC; `report_log()`/`report_mcu_log()` rebuilt the
`--since` cutoff back into local time before comparing, so on this
project's 3-hour offset every real record sorted as "before the cutoff" —
the first report after a genuinely catastrophic soak (1,462 rejections, 11+
minutes of timeouts) printed `VERDICT: clean`. Fixed the same day with a
`_utc_cutoff()` helper both call sites share. The regression test
(`test_soak_report.py`) forces `TZ=Asia/Jerusalem` and `time.tzset()` so it
actually exercises the gap — this machine's own clock is UTC, so a naive
test would pass even with the bug reinstated. Verified RED against the
original buggy expression before being accepted.

**Related:** D24 (the same species — a number nobody checked).

---

### T12 — Decided: `tools/check_client_behaviour.js` is a real verification command
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

Promoted to a fourth verification check, folded into `tools/verify.py`.
Node is present on the development machine and the checker fetches nothing
over a network, so ADR-0005 (air-gapped by default) is not touched — the
concern that kept this undecided. Assertion count is 63 now (grown from 44
since Batch 1, covering D32 too), read live by `verify.py` rather than
quoted in a doc that can go stale.

**Related:** ADR-0005, D7, R6.

---

### D8 — `.env` must be created before the first run of this version
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

Without `.env`, `use_hardware_servo` defaulted to `False`, the backend ran
the simulator, and the UI moved convincingly while the real servo never
twitched — silent, and the worst failure available at a handover. Checking
whether `.env` merely exists was not enough (a file present but missing or
misspelling the key would pass that check and still run the simulator), so
`main.py` now refuses to start when nothing *explicitly* chose a backend —
gated on `Settings.model_fields_set`, which distinguishes an explicitly-set
value (file or environment variable) from one that fell back to its
default. A deliberate `USE_HARDWARE_SERVO=false` for laptop development
still starts fine. Scoped to `main.py`; `run_dev.py` is a separate
dev-PC entry point, unaffected.

**Related:** `run_dev.py`, ADR-0004.

---

### D29 — `LOG_LEVEL` was inert: the Logger461 stand-in logged everything regardless
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

The real Logger461 wheel is not installed off the air-gapped network, so
`main.py`'s stand-in ran instead — and its `setup(level=...)` accepted the
level and silently discarded it, so every message printed no matter what
`LOG_LEVEL` was set to. Confirmed directly: setting `INFO` and restarting
still produced DEBUG lines. Fixed: the stand-in stores the level it is
given and gates on it (`_level_enabled()`, matching the real library's
ordering). Revised two entries that had assumed this worked: D5's closing
claim ("at INFO the lines are already silent") was false on this board and
is true now; T9's storage table treated the DEBUG rate as operative
regardless of setting, which no longer holds going forward.

**Related:** D5, T9, T2.

---

### D23 — `moving` and the fault flags were reported as measured on a failed read
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

The sixth twin-path instance D16's own entry said to look for: after D16
closed, six fields nulled on a failed read (`output_deg`, `raw_counts`, the
four telemetry floats), but `moving` and the six fault booleans still came
from `_empty_snapshot()`, all `False` - the API stated a servo that did not
answer was "not moving and has no faults." Fixed the way the entry's own
option 1 proposed: all seven now null on a failed read, gated in
`ServoStateStore.snapshot()`, typed `Optional[bool]` in `ServoStateResponse`
and `ServoStateView`. Cheaper than feared: a failed read writes no telemetry
row at all (ADR-0008's own rule), so the CSV and database schema are
untouched, and `app.js` already rendered these flags as tri-state before the
API caught up - this was a contract fix for the *other* consumers (exports,
direct API callers), not a client rewrite. Amends ADR-0008.

**Related:** D16, D2, D9, ADR-0008, D25.

---

### D25 — An overload that stopped being readable disappeared from the screen
**Status:** CLOSED · 25 August 2026 · **Severity:** medium

The servo trips overload, the banner correctly reads `ALARM · Overload`;
reads then start failing (what a strained servo on a busy bus does), and
after three failures D16's rule blanked the readings and switched the
banner to "Position unknown" - taking the still-active alarm with it.
Fixed in `app.js`'s `renderState()`: a fault reported `true` is now sticky
and survives the reading going unknown, marked "(last known — position
unknown)"; a fault reported `false` is *not* carried forward past the
known-window, deliberately asymmetric with (not a relaxation of) D16's
own rule - claiming "still OK" from stale data is exactly what D16
prevents. The paired question is answered: recover stays visible but
`disabled` with the reason stated on the control (`title`), matching D15's
existing pattern for a control that must refuse - hidden would have taught
"the alarm is over," which is not true.

**Related:** D16, D11, D12, D15, D23, R2.

---

### D26 — The Python suite failed once in ten runs, unreproduced
**Status:** CLOSED · 25 August 2026 (closed on evidence, not proof — see
below) · **Severity:** medium · **Observed:** 8 August 2026

Root cause found while chasing an unrelated `ResourceWarning`, not by
reproducing the original report: `TelemetryService.start_sampler()` had no
stop mechanism at all, so a background thread it started kept running
forever, reading state and logging into the shared test `_logger_stub`
whenever the scheduler next ran it. Worse than a confusing assertion:
closing the shared `Database` connection while one of these zombie threads
was mid-statement on it segfaulted the interpreter outright, confirmed
reproducible — `sqlite3`'s C extension is not safe against a connection
closing mid-use. Fixed: `TelemetryService` gains `stop_sampler()`; `Database`
gains `close()`; `_clear_all_caches()` stops any cached sampler before
closing the database it reads through.

**Closed on:** a ~20-run loop against the pre-fix code segfaulted at
roughly 1-in-10 to 1-in-20 — close enough to the original "1 in 10" to
call it the same mechanism; two deterministic tests
(`TestSamplerLifecycleIsolation`) induce it directly rather than relying on
luck; a ~30-run loop against the fixed code ran clean. The original
report's exact failing test was never identified, and the clean loop ran
on local disk rather than the original's loaded machine — genuinely not
proof of identity, closed as a judgment call rather than left open
indefinitely. **If this recurs, it is a new defect, not a reopening** — file
it fresh with whatever evidence the recurrence provides.

**Related:** D10 (a failure that destroyed its own evidence), T3.

---

### R2 — Motor isolation: cut drive power, keep sensors alive
**Status:** CLOSED · 26 August 2026 · **Confirmed on hardware, register level
and hand-felt**

Board verification (the item R2 was left open for since Session 9) found two
real bugs on the way, both fixed and confirmed against the real servo:

- **`IsolationService._reconcile()` had the boolean backwards.** Pressing
  Isolate reported the motor as isolated while the write actually sent to
  the servo asked it to *restore* torque, and un-isolating cut it — the raw
  isolated-intent flag was passed straight into `set_torque()`, never
  negated against that method's own contract (`enabled=True` means
  restore). Caught by reading register 0x28 back directly — a new
  diagnostic-only Bridge command, `servo_read_torque` — rather than
  trusting the write's own acknowledgement.
- **`ServoController.cpp` checked the wrong failure sentinel on every
  torque and move write** (`Begin()`, `SetTorque()`, `Move()`):
  `EnableTorque`/`WritePosEx` return the SCServo library's own Ack()
  convention (0 fail / 1 success), never -1 — that sentinel belongs to this
  file's *read* calls, not its writes. A torque write the servo never
  acknowledged was silently reported as a success regardless. This is why
  the inversion above was invisible from the UI: isolating still logged a
  clean acknowledged event no matter what the servo actually did with the
  write.

Both fixed (`!= -1` → `!= 0`; `set_torque(intent)` → `set_torque(not
intent)`). Verified live, repeatably, in both directions: register reads 0
after isolate, 1 after un-isolate — including through an unplanned
mid-session board restart, which also confirmed ADR-0010's boot re-apply
(`reason: "boot"` event, torque re-cut before any move could reach the
servo).

**Also corroborated by hand, at small scale:** a full free-spin test isn't
possible on this bench (bare servo, no rig, not enough leverage to turn the
shaft at all - see below), but a small nudge (roughly a tenth of a degree,
about the most the current setup allows) showed the expected qualitative
difference repeatably: un-isolated, the shaft resists and corrects back;
isolated, it stays wherever it was moved. Felt, not measured with an
independent instrument - real corroboration, not the rigorous multi-turn
test R2's board-verification list originally wanted.

Also closed in the same delivery, found reviewing the UI live against the
board:
- The status chip beside the live angle readout had no LOCKED state
  (indistinguishable from idle-unlocked); added, ranked below ISOLATED and
  above MOVING/SETTLING/HOLDING.
- The `isoHint` countdown text was a permanent line under all three control
  cubes regardless of state; scoped to show only while locked and not yet
  isolated, and now names Isolate explicitly.
- `MotionService.move_to()` checked `is_locked()` before
  `is_isolated_intent()` and raised immediately, so a servo that was both
  never told the operator about the isolation half until the lock was
  cleared and the move retried. New `LockedAndIsolatedError` /
  `reason="locked_isolated"` names both at once.

**R2's own stated acceptance is now fully confirmed on real hardware**: drive
power cuts and is visibly shown, telemetry keeps reading throughout, a move
while isolated is refused with a reason, state is reported correctly, and
reboot behaviour matches ADR-0010.

**Left explicitly open — see new backlog item T17:** the full-range,
multi-turn scenario (position tracking surviving a hand-turned shaft under
real mechanical load) stays untested. The current bench is a bare servo
with no belt, arm, or lever attached; the small-scale nudge above is real
evidence but not a substitute for that test. Not the same as "passed" -
stays open until a rig exists.

**Original report follows.**

**Scope:** in MVP · **Priority:** feature, not critical — must ship with the MVP
so that MVP testing exercises it.

**Motivation, from the operator directly (25 Aug 2026) — sharper than "the
mechanical team wanted it":** the board runs at field sites for months.
Holding the servo energised the whole time costs continuous power and wear
for no reason once movement isn't needed. Post-MVP (**R4**) the mechanical
team adds a physical lock — two butterfly screws clamping a 3D-printed arch
onto the shaft; it already exists today as a manual, unsensed mechanism —
that holds position by friction, so the motor can rest whenever it's
engaged. R8 (emergency stop, post-MVP) is expected to compose isolation with
the digital Lock and the physical lock together for an instant stop.

**Feasible in firmware, no hardware change needed.** `ServoRegisters.h:53`
defines `kTorqueSwitch = 0x28` — writing 0 disables drive torque while the
servo's electronics remain powered, so telemetry keeps reading. (Note 128 is
already used on that register as the set-centre-position command.)

**Relationship to Lock: separate control, but Lock now *triggers* isolation.**
Digital Lock and motor isolation stay two distinct controls (R4 unifies them
post-MVP with the physical restraint; R8 may compose them for e-stop) — but
isolation is not only a direct button press:

- **Manual isolate** — operator presses the isolate cube directly. Executes
  immediately; motion state does not gate it, deliberately, because this is
  meant to double as R8's future stop mechanism and refusing it mid-move
  would defeat that.
- **Auto-isolate (backup only)** — fires after the digital Lock has been
  engaged *and* idle for a configurable timeout (`config.py` convention, not
  hardcoded — D21's lesson). Placeholder default **15 min**, untuned until
  real-hardware testing with the mechanical team (the dev rig doesn't have
  the belt mounted yet). Never fires while unlocked — isolating a still-movable
  servo risks catching the operator mid-task.
- Not mutually exclusive: pressing isolate manually satisfies the goal
  immediately; the idle timer only covers "locked but forgot to isolate."

**Un-isolating is always an explicit action** — releasing Lock does not
auto-clear isolation (would silently re-energise a motor rested on purpose),
and a move request does not implicitly wake it either.

**Move command while isolated: refused**, mirroring `locked` exactly — new
`IsolatedError` (`exceptions.py`), checked in `MotionService.move_to()`
alongside `is_locked()`; `REFUSALS["isolated"] = "refused — motor is
isolated"` (`app.js`, D14's mechanism).

**Operator-visible state:**
- Third `.cube`, same pattern as `lockCube`/`calCube` — `Isolate` idle,
  `Isolated` engaged.
- Every isolate action (manual or auto) shows a transient notice via the
  existing `say()` (`app.js:196`), because the software has no way to know
  the physical lock is actually engaged: *"Motor isolated — physical lock is
  manual, confirm it's engaged."* (auto variant: *"Motor isolated after
  idle — physical lock is manual, confirm it's engaged."*)
- A persistent indicator, not just the transient notice, is also needed so
  the state isn't missed on a screen that's mostly left open — exact
  placement against the existing layout is `/deliver`'s to design.

**`ServoStateResponse` — new `isolated: bool` field**, following `locked`'s
shape exactly: never null on a failed read, since it's DB-stored operator
intent rather than a servo measurement — the same situation `locked` is
already in. Recorded in telemetry (own column, like `moving`) and in the R5
export. The null-on-failed-read question **for the telemetry/export column
specifically** is left open, deliberately — decide it in `/deliver`'s
functional-design step, not here.

**Reboot behaviour: latches — see `docs/adr/0010-motor-isolation-state-survives-a-reboot.md`**
(was `OPEN_QUESTIONS.md` Q4; promoted 25 August 2026).

**Explicitly out of scope for R2 (confirmed 25 August 2026):** sensing the
physical lock — no hardware exists yet, that's R4. Back-drive/self-locking
behaviour of the belt under load is the mechanical team's concern, not
something R2's software hedges against — the existing calibration-on-boot
flow (ADR-0007) is the safety net for any drift, same as it already is for
every other source of position doubt.

**Acceptance:** the operator can cut drive power from the UI (manually or via
the idle backup) and see plainly that it is cut; telemetry keeps reading
throughout, proving the sensors stayed alive; a move while isolated is
refused with a message that says why; the state is reported in
`/servo/state` and recorded in telemetry; reboot behaviour is `ADR-0010`.

**Blocks:** MVP handover. **Wants first:** D14 (done, Session 1 — so the
refusal reads properly).

---

## Requirements captured but not yet designed


---

## MVP feature build — sessions 1-10 (26 August 2026, dated record)

Moved whole from `BACKLOG.md`'s START HERE table and session logs when the
backlog was restructured for context cost — every session below is DONE, kept
as a record of how the batches actually ran, not as work.

# START HERE — the session plan

**Agreed with the operator, 8 August 2026. Three sessions, in this order. Each
starts cold; everything needed is written down below so nothing is rediscovered.**

| Session | What it does | Board needed |
|---|---|---|
| **1 — Batch 1 & 2 DONE 8 Aug 2026** | **Session 2 next** — the soak | no (desk work both batches) |
| **2 — DONE, 8 + 10 Aug 2026** | D4 closed via SSE in Session 3 | yes |
| **3 — DONE, 11 Aug 2026** | SSE migration, D4 closed | yes |
| **4 — DONE, 23 Aug 2026** | Sampler 0.5s/retention 30d, R5 (XLSX export) rebuilt from scratch (11 Aug attempt never worked at all), relay chunk-size dispute closed with a cause, D31/D10 closed or advanced with real board evidence. **R5's mechanism works and is cross-app validated — but real UX gaps found live and deferred, see next row.** | yes |
| **5 — DONE, 23 Aug 2026** | **R5's export, redirected live by the operator**: target angle + servo angle end to end (UI and export), angle-correlated charts, a typed chart-range selector (confirmed live to work), decoded flags, day-sheet and Overview column widths, LCARS styling, per-day summary table. One live regression (chart date-axis) caught and reverted same session. **D10 and R2 stayed out of scope**, as planned — deferred, see row 6. Full detail in R5's entry. | yes — used for a real live walkthrough this session, which is exactly what caught the regression and several width/spacing defects a local render alone had missed |
| **6 — D10 half DONE, 24 Aug 2026** | **D10 closed** — real cause was a thread-safety gap in the SQLite layer (every unlocked read on the shared connection, not the zero-table race the original writeup guessed), see `CLOSED.md`. **Batch 4's motor isolation (R2)** remains — pulled out of Session 5 by the operator, 23 Aug 2026, to keep that session scoped to the export. **Before planning R2: a `/grilling` pass on R2's open design questions** (operator-visible state/label when isolated, refuse-vs-queue a move while isolated, the new `ServoStateResponse` field, the ADR the reboot-latch decision still wants — see R2's entry) **grounded in the docs, not in a prior session's paraphrase — requested by the operator, 24 Aug 2026.** Nothing from Session 6's D10 work is a prerequisite for it, but **Session 8 now runs first** (inserted 24 Aug 2026 by T14's triage, see row 8) so R2 designs against a settled `ServoStateResponse` shape — R2 itself is Session 9, not a direct continuation of this row. | R2: yes, for the operator-visible part |
| **7 — DONE, 24 Aug 2026** | **T14 closed** — all fourteen unslotted items given a real session (rows above and below) or an explicit reason they don't get one (T13, T15 — see their entries); Closed index gained D3/D27/D13 (moved to `CLOSED.md` but never indexed). **D32, D33, D34 closed the same session** — board-tested, verified (suite 223→226), app restarted and checked live. **D35 opened** (speed-step enforcement postponed, see Session 10) — a board measurement during D32's work found commanded and actual servo speed disagree by ~1.5-2x, so the planned fix was not shipped on an unverified unit-conversion assumption. | yes — used to verify D32/D33/D34 live and to bench-test D35's measurement |
| **8 — DONE, 25 Aug 2026** | All eight closed: **D24** (coverage gated at 99%, two unexercised guards covered), **D26** (sampler-thread leak found and fixed — segfault reproduced pre-fix at ~1-in-10 to 1-in-20, gone after; closed on evidence, see `CLOSED.md`), **D30** (UTC/local cutoff regression test), **T12** (`check_client_behaviour.js` promoted to a real check, folded into new `tools/verify.py`), **D8** (deploy without `.env` now fails loud), **D29** (`LOG_LEVEL` now real on the Logger461 stand-in), **D23** (`moving`/fault flags null on a failed read, amends ADR-0008), **D25** (a reported alarm survives the reading going unknown; recover disabled-with-reason, not hidden). `ServoStateResponse` shape is now settled for R2. Repo hygiene pass same session: stale soak artifacts and `FILE_REGISTRY.md` removed, `.gitignore` gaps closed. | no — board confirmation of D8/D23/D25 still outstanding, first thing to do when the board is next up |
| **9 — DONE, 25-26 Aug 2026** | **R2 — motor isolation, CLOSED** (see `CLOSED.md`). Implemented 25 Aug on `feature/motor-isolation`, merged to `dev`. Board verification 26 Aug found two real bugs — `IsolationService`'s write was inverted and its ack check used the wrong sentinel, both fixed and confirmed at the register level — plus three UI/refusal gaps closed alongside on `feature/motor-isolation-fixes`. Hand-turn/multi-turn-under-load scenario left genuinely untested (no rig on the bench) — see **T17**. `/twin-review` deliberately skipped this delivery, deferred to a later whole-app pass (see `T16`). | yes — used for the full board-verification pass |
| **10 — opportunistic, any time after 7** | **D28** (MCU boot-time `mcu_log` notify race — needs a flash to fix or confirm) + **D35** (commanded vs. actual speed disagree by ~1.5-2x, found bench-testing D32 this session — needs `PRESENT_SPEED` register-level readback, not just wall-clock timing). D32 itself closed this session (24 Aug) — its speed-step-enforcement piece split into D35 rather than shipped on an unverified assumption. Low severity, no dependency on anything above; ride along with any session that already has the board up. | yes |

**T14 (`CLOSED.md`) has the full reasoning behind this slotting** if it is
ever needed again — this row is just a pointer to the outcome.

**The venv is at `.venv/` in the working copy** — the suite runs, no setup.
**Verification commands and their numbers: `CLAUDE.md` §3**, not repeated here:
the suite figure was stale in nine documents for a month because it was copied
into all of them (D24).

Use **`/deliver`** to run a batch: it plans, **stops once** for approval, then
runs the whole thing. **`/operator-lens`** before changing anything the operator
sees; **`/twin-review`** on the finished diff, scoped to named paths with a
findings cap.

## Session 1, Batch 1 — DONE, 8 August 2026

D14, D15, D16, D20, D21 closed. Suite 193 → 198; native checks and the bridge
contract unmoved (nothing in `sketch/` changed). Detail in `docs/CLOSED.md`.

`/twin-review` on the diff found a hole in D15's fix (Enter bypassed the
guard), a CSS regression it introduced, two false-notice bugs, and eight untrue
statements in the docs. All fixed. **It cost ~218k tokens across three
reviewers — scope them to named paths with a findings cap next time.**

Raised, not fixed: **D23** (fault flags still reported as measured — API-shape
decision), **D24** (two uncovered guards; coverage is 99%, not the 100% seven
documents claimed), **D25** (an overload stops being displayed once unreadable),
**D26** (one unreproduced suite failure in ten runs), **T12** (what to do with
`tools/check_client_behaviour.js`, written because four of the five items had no
other way to be verified).

**Q1's touch half answered: mouse, not touch.** The viewport half is open, so
D7 stays blocked.

**Wants an operator's eye on the board**, none of it blocking Batch 2: D15's
busy state, D14's message under a real refusal, D16's blanking during a real
stall — and **D11**, unconfirmed since 7 August in the same render path. One
sitting closes all four.

## Session 1, Batch 2 — DONE, 8 August 2026

D3, D13 closed. Suite 198 → 207; native checks 164 → 194; bridge contract gains
`mcu_log` (MCU → Linux) and still agrees. Detail in `docs/CLOSED.md`.

New: a `DiagLog` singleton (`sketch/src/DiagLog.h/.cpp`) — a bounded ring
buffer (`LogRing.h`, its own native tests) fed by `NetworkRelay`, `ServoBus`
and `ServoController`, drained by `BridgeApi::DrainDiagLog()` over a new
`mcu_log` Bridge notify. Received on the Python side
(`app/relay/mcu_log.py`) into `logs/mcu.jsonl` — a file separate from the
main log, with its own rotation, so a volume spike on either side cannot
evict the other's history. `tools/soak_report.py` now pulls and reports it,
including the D4 write-lock-timeout signature.

**ADR 0009**: `kMaxRelaySockets` stays at 6. The wall is fixed (7 sockets,
hardware); the real lever (`timeout_keep_alive`) stays unmeasured, and this
batch does not tune it blind — see the ADR for why. New finding folded in:
`app.js` runs independent poll timers, so a single browser can transiently
open two connections, meaning the real margin under the 7-socket wall is
smaller than `OPEN_QUESTIONS.md` Q2's answer implied.

**Built, flashed, and checked on the real board the same day.** Compiled
clean (143224 bytes program/18%, 54649 bytes RAM/20%), flashed via
OpenOCD/SWD, app started. `Arduino_RouterBridge`'s `notify()` read directly
off the board: a variadic template with no fixed argument ceiling — the
six-argument `mcu_log` concern is resolved, not assumed. Live health check
via the relay IP (`192.168.10.60:8000` — the board's own OS network does not
expose the port at all, per ADR-0001) returned
`diag_dropped=0` in `get_status`, confirming the counter works end to end.

**D27 fixed**, not just raised — `tools/synthetic_operator.py` rewritten
around kept-alive persistent connections (fixing a bigger, related fidelity
gap: the old `urllib`-based version opened a fresh connection on *every*
poll, not just missing the concurrent-timer pattern) and now reproduces
`app.js`'s three independent timers exactly. Detail in `docs/CLOSED.md`.

**D28 raised, real not hypothetical**: the boot-time `mcu.relay.ready`
notify was lost on the actual board — confirmed by its total absence after
several minutes of uptime. Likely a startup race (Python registers the
`mcu_log` handler after the MCU has already sent it), likely confined to
boot-time events only. See `docs/CLOSED.md`'s D3 entry and D28 in this file
for the detail and the two possible next steps.

## Session 2 — The soak — IN PROGRESS

Planned as one run closing four things (D4, R1, T9, D10). What actually
happened, night of 8 August 2026 — **read D4 and R1 first, this is the
short version:**

1. **Ran 3 operators, 120 min planned.** Relay slot ceiling (6) hit
   immediately — 1462 rejections in ~22 min — ending in a `servo_read`
   stall that never self-recovered. Ctrl-C'd; the board stayed wedged
   (unreachable) until restarted.
2. First `soak_report.py` reading said `VERDICT: clean` — **it was wrong**,
   a timezone bug (**D30**, now code-fixed) silently excluded the whole run.
3. **Restarted, ran 1 operator, 15 min, completed clean-ish** — no
   oversubscription, but the *same stall* happened twice anyway (self-
   recovered this time) plus a 30 s sampler gap and a fabricated position.
4. **Conclusion at the time: D4 is reopened, not closed by the original
   mutex fix** — the stall reproduces even without socket contention, and
   the mutex fix's own diagnostic (`write_lock_timeouts`) stayed at zero
   through both runs. **Overturned by step 7 below** — both runs turned out
   to be contaminated. Two hypotheses raised here are still live; see D4.

5. **10 August 2026 — ran the 2-operator diagnostic step.** First attempt was
   contaminated within 3 minutes (a real browser was open watching, on top of
   the 2 synthetic operators) and killed before it mattered. **That surfaced
   a bigger problem: both runs above (steps 1 and 3) were also watched with a
   real browser open, undocumented at the time** — neither was actually
   operator-count-clean. Corrected in D4's entry.
6. **Re-ran clean, no browser, 15 min, 2 operators exactly at the ceiling.**
   The stall reproduced **three times** (23.06 s, 12.07 s ×2), self-recovered
   every time, board healthy afterward, `write_lock_timeouts` still 0.
   Reading the code the same day found a third hypothesis: `App::Tick()`
   yields a fixed 1 ms regardless of how much real work `Poll()` just did —
   full detail in D4.
7. **Ran a true 1-operator clean run, 10 min, no browser — `VERDICT: clean`,
   zero stall-band gaps.** This overturns step 4's headline: the stall's
   *onset*, not just its duration, now looks load-correlated. That makes the
   `Tick()`-timing hypothesis from step 6 the strongest of the three — full
   reasoning in D4.

8. **Instrumented `Poll()` (lock-wait/work/sink breakdown + bailout count),
   confirmed by measurement: it's cheap-and-frequent per-slot chip-lock
   probing (~264 passes/sec, ~1600 probes/sec), not one slow call.** Batched
   step 3's 6 per-slot lock acquisitions into 1 (matching step 1's existing
   pattern). **Made client failures worse, not better**, at both 3 and 2
   operators.
9. **Found and fixed a second, independent bug: every Bridge-touching
   FastAPI route was `async def` calling synchronous blocking code** —
   textbook Starlette footgun, confirmed by FastAPI's own docs. A single
   blocking Bridge call freezes the *entire* server, explaining why
   unrelated endpoints (even `/health`) failed together. Converted the 13
   affected handlers to plain `def` (FastAPI auto-threads these).
10. **Combined (8+9), re-tested at 3 then 2 operators: both worse than the
    original untouched baseline**, not just unhelped — 2-operator failure
    rate went from 3.8% (58/1518) to 26% (154/593), worst `Poll()` pass back
    to ~1000 ms, `write_lock_timeouts` non-zero again. Root cause of *why*
    combining them regressed things is not established — not investigated
    further this session.
11. **Reverted all of it** (`sketch/src/{App.cpp,BridgeApi.cpp,Config.h,
    NetworkRelay.{h,cpp}}`, the 4 router files, `tools/soak_report.py`) back
    to the last commit. Board redeployed on the reverted code, then stopped
    for the session.

**Session's real finding, kept regardless of the revert:** the 6-socket
ceiling is a property of the whole Wiznet hardwired-stack chip family
(W5500/W6100 alike — confirmed by web search) — a shield swap will not
raise it. The actual lever is that each operator's browser opens **3**
persistent connections (state/1s, zeros/15s, events/15s), so 3 operators
structurally want 9 sockets against a hard 6. **Decided: replace polling
with one SSE stream per operator** (plain HTTP, no protocol upgrade, reuses
the `StreamingResponse` pattern the CSV export already proves out) — cuts
socket demand 3x, sized **M**, next session, before anything else in Batch 4.

**Next session, in order:** (1) SSE — collapse the 3 poll connections into
one stream per operator; re-run the 2-operator and 3-operator soaks clean
against *that* to see whether D4 was ever really about `Poll()` timing at
all, or just socket pressure the whole time. (2) Batch 4 proper — motor
isolation (ADR first) and the XLSX export. Use `--since` in **local** time
(D30) for any soak.

R1, T9, D10 are not closed either; see R1's entry for what changed there.
D10 specifically was not reproduced — a different, now-explained sampler
`TypeError` was, see D4's entry.

**Update 11 August 2026:** The UI export button failed repeatedly with "controller busy or did not answer". Two backend bottlenecks caused the Arduino proxy to drop the connection during export. See **D31** below.

## Session 3 — SSE first, then Batch 4

**New, decided 10 August 2026 — before anything else:** replace `app.js`'s
3-connections-per-operator polling with one SSE stream per operator (plain
HTTP, no protocol upgrade). Sized M. See D4's entry and the Session 2 log
above for why. Re-run the D4 soaks against it before touching the relay
again.

Then Batch 4: motor isolation (**latching, decided — see
`OPEN_QUESTIONS.md` Q4; write the ADR first**), and the export: time-range
selection plus the chart set, **both on the backend and in the UI**, all
telemetry fields charted the same way, exported as **XLSX with embedded
native charts, no server-side matplotlib** (decided under R5, 10 August
2026).

## Not in these three sessions

The handover pack (defining "stable", the recovery runbook, the **operations
manual**, diagrams, on-target tests), and the mechanical conventions pass. See
the batch list further down.

## Suggested order — SUPERSEDED 8 August 2026

> **Do not work from this section.** It is kept for its reasoning, which is
> sound. The live ordering is **"Ordering, rewritten 8 August 2026"** below.

**`WORKFLOWS.md` gives a flow per item** — which skill drives it, in what steps,
with the constraints that apply. Read the flow before starting the item.

**Rewritten 7 August 2026, after the T8 board run.** D1, D2, D4's cause, D9 and
T8 itself are closed; the ordering below replaces the pre-run one.

**D10 and D11 are done** (7 August 2026), except that D10's underlying fault is
still unexplained and will only reappear on a board run — the logging that lost
it is fixed, so next time it will name itself.

**D3 next** (MCU logging). Its case is stronger than when it was written: the
W5500 fix added `write_lock_timeouts()`, a number that says whether `loop()` is
starving the Bridge, **and there is no way to read it from the board.** The
diagnostic exists and cannot be reached.

Then the measurement pass, in this order because each depends on the last:
**D4's soak** (a long multi-operator run, which is also R1's measurement) →
**D6** (first paint, then the 128 vs 256 experiment on a board that no longer
races) → **R5/R6** (benchmarks, and turning "stable" into numbers).

**D12** and **T3** can slot in anywhere. **T1** (conventions) is mechanical and
suits an executing agent; do it once the defects are closed so it does not
collide with real fixes.

Summary: **D3 → D4 soak/R1 → D6 → R5/R6 → T1/T6/T7 → D12/T3**, with D10's
unexplained fault watched for on every board run until it shows itself.

---

## Ordering, rewritten 8 August 2026 — by session, with sizes

**The ordering above is superseded. It is kept because its reasoning is sound;
what it got wrong was the unit and the scope.**

Two corrections drive this rewrite:

1. **The unit of work here is a session, not an item.** T8 proved it: one board
   run settled four items and found four more that were on nobody's list.
   Ordering items individually schedules work that cannot actually be done
   individually.
2. **The only two unbuilt MVP features were invisible.** R2 and R5 are both
   scoped *in MVP*, both not started, and neither appeared in the order above.
   Unbuilt features carry far more schedule risk than known defects, because
   their effort is unknown. Both are now written up as build items.

Sizes are **S / M / L**, meaning roughly: S = under a session; M = one focused
session; L = more than one, or needs the board and a human watching.

### Batch 1 — Desk work, no board — **DONE 8 August 2026**

| | Item | Size | Outcome |
|---|---|---|---|
| 1 | **D14** network errors read as "Failed to fetch" | S | done — one `request()` door, `unreachable` reason code, no browser text can reach the screen |
| 2 | **D15** no in-flight feedback | S | done — guard in `bind()`, the one place all nine controls pass through |
| 3 | **D16** telemetry rendered as 0.0 on a failed read | S | done — **schema and client both**; raised **D23**, the sixth instance |
| 4 | **D21** UI states the wrong step size (0.1° vs 0.06°) | S | done — reason codes split by who owns the words |
| 5 | **D20** dead `eventTime` branch | S | done |

**The rationale held.** All five were client-side or schema-level, none needed
hardware, and three of them change what the next board session can observe. The
instrument is fixed before the measurement is taken.

**What it cost that the plan did not predict:** the batch had no way to check
four of its five items, so `tools/check_client_behaviour.js` was written to
execute them rather than reporting them as read. That tool is now an open
decision — **T12**.

### Batch 2 — Make the machine diagnosable — **DONE 8 August 2026** (desk work)

| | Item | Size | Outcome |
|---|---|---|---|
| 5 | **D3** C++ side has no logging | M | done — `DiagLog` ring + `mcu_log` Bridge notify; both counters now visible; detail in `docs/CLOSED.md` |
| 6 | **D13** decision: is six slots enough? | M | done (decided) — **ADR-0009**: stays at 6, real lever unmeasured until Session 2 |

D13's decision is recorded in `docs/adr/0009-connection-ceiling.md`: the wall
is fixed by hardware, `timeout_keep_alive` is the real lever and is left
unmeasured rather than tuned blind, and Session 2 measures it as the first
experiment.

**Built and flashed the same day, after this batch's desk work landed** —
see the note above. `check_bridge_contract.py`'s "both sides agree" is
backed by reading the actual `Arduino_RouterBridge` source now, not just a
comma count.

### Batch 3 — The measurement session (board, supervised, one long run)

**Firmware built, flashed, and running — done 8 August 2026.** The relay and
`get_status`/`diag_dropped` path are confirmed live (see Batch 2 above).
**Not yet confirmed: `mcu.jsonl` and `mcu.*` log lines** — see D28. Trigger a
real rejection or write-lock timeout early in Session 2 and check whether
that specific event arrives, before trusting `soak_report.py`'s MCU-side
numbers for anything that matters. Also watch for heap fragmentation over a
long run: the drain allocates two `String`s per diagnostic record on a
device `App.cpp` documents as otherwise heap-free — unmeasured, not assumed
safe.

| | Item | Size |
|---|---|---|
| 7 | **D4** soak — closes the race, and is **R1's measurement** | L |
| 8 | **R1** concurrent-operator ceiling | — same run |
| 9 | **T9** storage growth over hours, not minutes | — same run |
| 10 | **D10** watch for the unexplained sampler exception | — same run |
| 11 | **D6** first paint, then the 128 vs 256 chunk experiment | M |

**One session, four items.** Tooling exists (`tools/synthetic_operator.py`,
`tools/soak_report.py`), so this is two commands and a person watching. Run it
supervised — an unattended failure at 03:00 is a gap in a log; a watched one is
an observation.

### Batch 4 — The two unbuilt MVP features

| | Item | Size | Why here |
|---|---|---|---|
| 12 | **R2** motor isolation | L | Must ship *and be exercised by MVP testing*. Design first — see its entry |
| 13 | **R5** metrics export and graphs, **torque first-class** | L | Blocks R6 entirely; the receiving teams have nothing to judge without it |
| 14 | **D22** export any time range, not a fixed 24 h | S | R5's delivery path. A multi-day unattended run cannot be retrieved through a 24-hour button |

**These are the schedule risk.** Everything above is bounded by known causes;
these two are unbounded until designed. If the calendar slips, it slips here.

### Batch 5 — The handover pack

| | Item | Size |
|---|---|---|
| 14 | **R6** define "stable" from Batch 3's numbers | M |
| 14b | **T10** the recovery runbook, both halves | M |
| 14c | **T11** the operations manual — **after** batches 1 and 4 land | M |
| 15 | **T5** architecture diagram + ERD | M |
| 16 | **T3** on-target test suite, run once | S |
| 17 | **D7** UI at the operator screen size | S — **blocked, see `OPEN_QUESTIONS.md`** |
| 18 | **D12** route back to the datum | S |
| 19 | **D17** position bar covers the travel window | S |
| 20 | **D18** export without navigating away | S |
| 21 | **D5** log reads as a narrative | S |

### Batch 6 — Mechanical, suits an executing agent

**T1** (conventions) → **T6** (exception hierarchy) → **T7** (database
abstraction), in that order, once the defects are closed so mechanical edits do
not collide with real fixes. High volume, low reasoning — the Antigravity split.

### Not scheduled

- **T2** air-gapped bundle, **R7** the logistics behind it — **blocked on
  adapter delivery**, not on us.
- **D19** — needs a reachability answer first; see its entry.
- **R3, R4, R8** — post-MVP by decision, not by omission.

**T14 closed, 24 August 2026 (full record in `CLOSED.md`) — every item that had
no batch now has one, or an explicit reason it doesn't.** The fourteen from the
23 August audit (D8, D23, D24, D25, D26, D28, D29, D30, T12, T13, D32, T15,
D33, D34): nine are slotted, in Session 8 or Session 10 above; **D32, D33 and
D34 were closed the same session as this triage** (all three pre-diagnosed or
diagnosed going in, see the Closed index); **T13 stays deliberately
unscheduled** — its own entry says do it opportunistically, not as a sweep;
**T15 is blocked on an operator decision**, moved to `OPEN_QUESTIONS.md` Q10.

**What is not in any batch is as important as what is:** if a batch slips, the
cut line in `PROJECT_STATE.md` says what ships anyway.

---

### T1 — Apply `CONVENTIONS.md` across the codebase
**Status:** done · 26 August 2026 · via T15a's Antigravity run, hand-corrected same session

Measured gap in `python/app/`: 67 `Args:` lines missing `(type)`, 4
implicit-truthiness checks, 3 `while True`, 3 list comprehensions, 2 `break`.
Folded into T15a's prose-strip prompt rather than run separately, since both
touch the same docstrings.

Antigravity's run matched every expected count exactly (4/4 truthiness, 3/3
`while True`, 3/3 list comprehensions, 2/2 `break`; `Args:`/`Returns:` types
completed, matching the ~67 baseline) — confirmed by a full manual diff
review after the run, not taken on the self-report alone (see T15's entry).
`Attributes:` blocks were also completed with types, a gap T1's own count
never measured. `tools/verify.py` unchanged (293/194/96, all green).

**Original report follows.**

**Status:** open · **Flow:** `WORKFLOWS.md` W4 · suited to an executing agent

The MVP was written "dirty" on purpose. Measured gap in `python/app/`: 67 `Args:`
lines missing `(type)`, 4 implicit-truthiness checks, 3 `while True`, 3 list
comprehensions, 2 `break`, 0 `continue`, 0 `X | None` unions.

**Acceptance:** the gap table in `CONVENTIONS.md` reads zero across the board,
and the suite (207 tests as of Batch 2) still passes.

---

### T15 — Code-level documentation reads as unprofessional and costs tokens
**Status:** done · 26 August 2026 · **Decided:** `OPEN_QUESTIONS.md` Q10

Split into T15a (`python/app/`) and T15b (`sketch/src/`), each an Antigravity
run against its own exact prompt (`docs/handoff/`), with T1 folded into T15a
since both touch the same docstrings.

**T15a needed real correction, not just review.** Antigravity's own report
claimed every file's relocations were complete; a full manual diff read
found genuine load-bearing content silently deleted with no relocation at
all in several files — most seriously `isolation_service.py` (this
session's own torque-inversion fix comment) and `servo_state.py`'s
`_baseline_counts()` (the flagship D9 example this entry already cited by
name). Restored to `docs/DESIGN_NOTES.md`, with the two safety-critical
cases kept as one-line inline pointers (the operator's call, not a blanket
exception). `python/static/app.js` was reverted whole — its entire diff was
comment removal with zero other contribution, and `CONVENTIONS.md` has no
JavaScript section to strip against; that was a scoping mistake, not a
judgment failure, and waits for **T18**.

**T15b held up far better.** Nearly everything it removed was already
documented in `skills/uno-q-st3215/SKILL.md` and `RELAY_NOTES.md` — built in
an earlier session, and evidently working as the "check first" reference it
was meant to be. Real gaps: five Doxygen summaries deleted outright rather
than kept (process violation of the prompt's own rule, not a judgment
call), the servo command payload-format table (had no other home), and a
handful of minor provenance/tuning facts — all fixed, in `SKILL.md` and
`docs/DESIGN_NOTES.md`.

**Standing lesson from both runs, now written into the prompts themselves:
verify against the actual diff, never take a self-reported "complete" at
face value.** A derived constant also lost a term during relocation on the
Python side (a wrong number, not just a missing one) — the firmware prompt
now warns about this specifically.

`tools/verify.py`: 293/194/96, unchanged, both runs. Native suite: 194
checks, 0 failures.

**Related:** T1 (folded in, closed alongside), T18 (front-end conventions,
`app.js`'s own future pass).

**Original report follows.**

**Status:** blocked on an operator decision — see `OPEN_QUESTIONS.md` Q10 ·
**Raised by:** the operator, 24 August 2026

The operator's read on the current docstrings/comments: too long, contains
inline comments (disapproved of), and carries "insider information" — project
history, rationale, incident narrative — that belongs in `docs/` markdown, not
in the source. Beyond style, this has a real cost: every session re-reads this
code, so verbose in-code narrative is paid for out of the same token budget as
the actual work, every time.

**This contradicts current, deliberate policy, and that must be resolved
first, not silently overridden either way:** `CONVENTIONS.md` (Docstrings,
~L30) currently says the opposite — "if a docstring needs three sentences of
prose to explain the mechanism, the explanation belongs in a comment at the
relevant line, not in the docstring" — and the repo's own defect history
(`AUDIT.md`, D2, D9) is full of cases where exactly this kind of in-line
"why" comment (e.g. `_baseline_counts`'s note about the 212.7°-on-90°
incident) is what stopped the same mistake recurring nearby. A wholesale
"move it to docs/" pass needs an explicit decision on which of those two
failure modes the project would rather risk, not just a style pass.

**Scope, once decided:** a full-repo pass — `CONVENTIONS.md`'s own Docstrings
section rewritten first if the decision changes it, then every docstring and
inline comment in `python/app/` and `sketch/src/` brought into line, with any
genuinely load-bearing rationale relocated to the matching `docs/adr/` entry,
`AUDIT.md`, or `CLOSED.md` record rather than deleted.

**Related:** T1 (mechanical `CONVENTIONS.md` gaps, different axis), CLAUDE.md
§4's "write every document distilled" rule (same cost, different location).

---

### T16 — Enhance `twin-review`: a fifth lens, and lenses made selectable
**Status:** CLOSED · 26 August 2026 · **Severity:** open (enhancement)

Went further than the two scoped changes once it became clear the skill, as
written, was diff-only and would not survive being pointed at the whole app in
session 14 — restructured, not just extended:

- **Lens 5, general correctness**, composed by reference (`Skill` tool,
  `code-review`, medium effort) rather than reimplemented — catches
  non-twin-shaped bugs the other four can't.
- **Scope: diff or inventory mode**, the latter chunked (`python/app/`,
  `sketch/src/`, `python/static/`, `docs/`) so no reviewer is ever handed the
  whole codebase; graphify's known `.ino`/`.css` blind spots are named, not
  silently skipped.
- **Lens selection** generalized from lens 3's existing conditional — a
  diff-mode cost control; inventory mode runs every applicable lens per chunk.
- **Lens 4 was stale and fixed**: it pointed at "the three verification
  numbers in the docs," but `verify.py` runs four now and the counts live in
  `verify_baseline.json` — exactly the D24 rot this lens exists to catch.
- **Cost control moved from output-trimming to input-narrowing**, after a web
  check of current practice confirmed the approach (deterministic pre-filter,
  then LLM judgment only on what's left) over the first draft's "cap yourself"
  instruction, which risked losing real findings on session 14's first-ever
  whole-app pass. Each lens now names a concrete `grep`/`graphify`/existing-tool
  query to build its candidate list before any reviewer reads source.
- **Output contract added**: inventory mode writes to `docs/REVIEW_FINDINGS.md`
  (file:line, issue, why it matters, severity, fix) — session 15 has no memory
  of the run, so findings must be self-contained; the file is a transient
  triage input, not a second backlog.
- Iteration cap 2 scoped to diff mode only; inventory mode is findings-only.
- Synced to `~/.claude/skills/twin-review/` and `~/.agents/skills/`; "four" /
  "one diff" wording dropped from `CLAUDE.md` and `WORKFLOWS.md`'s summaries
  per D24 (don't quote a count that will go stale).

**Deferred, unchanged:** actually running it on the whole app (session 14,
`BACKLOG.md`), and folding it into `deliver`'s pipeline (not yet scoped).

**Related:** D24, R2 (raised it), session 14/15 (`BACKLOG.md`).

---

### T19 — Add `ruff` as an advisory Python lint pass, wired into `twin-review`
**Status:** CLOSED · 26 August 2026 · **Severity:** open (enhancement)

Raised alongside T16: the user has a personally-refined ruff standard on the
air-gapped network, unexportable; the closest reachable copy was found in
`~/Coding Projects/Krusty-Crab/pyproject.toml` (most recent of three near-
identical copies across `Eyal-FastAPI-Project`, `Krusty-Crab`, `Krusty-Crab-
backup` — the same lineage `CONVENTIONS.md` itself was derived from).

**Adapted, not copied verbatim** — two real corrections against this repo:
- `[lint.pydocstyle] convention = "google"` added; the source config never
  set it, so `D`-rules would not actually validate the Google format
  `CONVENTIONS.md` declares.
- `UP` (pyupgrade) deliberately **not** selected — it would push
  `Optional[X]` toward `X | None`, the opposite of `CONVENTIONS.md`'s Types
  rule. Dropped the Krusty-Crab-specific `[project]` table, its per-file
  `logging/__init__.py` ignore (no such module here), and the misplaced
  `fixable = ["ALL"]` (nested under `per-file-ignores`, a no-op in the
  source; also unwanted while advisory-only means no default auto-fix).

**Advisory only, not part of `tools/verify.py`'s gate** (per the operator) —
runs against `python/app/`, baseline is 50 findings (`ruff check python/app
--config python/ruff.toml --statistics`), all plausible (13 `D107`
undocumented `__init__`, matching `CONVENTIONS.md`'s own noted gap; 11 `D104`
undocumented packages; 10 `ARG001` unused arguments; the rest cleanup-shaped).
**Where ruff and `CONVENTIONS.md` disagree, `CONVENTIONS.md` wins** — stated
in both `CONVENTIONS.md` and the skill.

Wired into `twin-review` (lenses 1, 4, 5) as a pre-pass for the backend
chunk — narrows what needs LLM judgment, same principle T16 already applied.
`ruff` added to `python/requirements-dev.txt`; config at `python/ruff.toml`.

**Related:** T16, CONVENTIONS.md.
