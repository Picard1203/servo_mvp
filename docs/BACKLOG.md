# Backlog

**The work queue. This is the only list of open work in the repo.**

`AUDIT.md` is the *past* tense (bugs already fixed). This file is the *present*
tense. Do not merge them.

## How to pick up work

1. Read `../CLAUDE.md` if you have not — especially the graphify rules. **Query
   the graph before reading source; it costs a fraction of the tokens.**
2. Run the three verification commands and note the numbers (186 / 164 / agree).
3. Take an item below in the suggested order.
4. Update this file as part of the change — an item is not done until its entry
   says so.
5. Run `graphify update .` after changing code.
6. Re-run the three commands. If the numbers moved, stop and say so.

## Suggested order

**`WORKFLOWS.md` gives a flow per item** — which skill drives it, in what steps,
with the constraints that apply. Read the flow before starting the item.

**Rewritten 7 August 2026, after the T8 board run.** D1, D2, D4's cause, D9 and
T8 itself are closed; the ordering below replaces the pre-run one.

**D10 first.** The sampler threw once in seven minutes and the log cannot say
why. Everything after this is measurement, and an unexplained exception that
destroys its own evidence corrupts every measurement taken near it. It is also
small.

Then **D11** — the UI over-reacts to a single blip, on both the connection
banner and the position readout. Cheap, and it is what the operator sees; the
end users are not programmers.

Then **D3** (MCU logging). Its case is stronger than when it was written: the
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

Summary: **D10 → D11 → D3 → D4 soak/R1 → D6 → R5/R6 → T1/T6/T7 → D12/T3.**

**Status key:** `open` · `in progress` · `needs investigation` · `done`

---

## Defects

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

### D3 — The C++ side has no logging
**Status:** open · **Severity:** high · **Flow:** `WORKFLOWS.md` W3

Only `App.cpp` produces any output (13 `Serial.print` calls). `ServoBus`,
`ServoController`, `NetworkRelay` and `BridgeApi` have **zero** logging — and
every bug in this project has lived in exactly those four files.

There is currently no way to tell from the board what the MCU side is doing.

**Acceptance:** each of the four files logs its significant transitions and every
failure path, at a level that can be turned down. Log volume must not starve
`loop()` — see `RELAY_NOTES.md` on the yield requirement.

---

### D4 — Connection drops after a few commands; requires a page refresh
**Status:** cause found and fixed · **needs a longer soak before it is closed**
· 7 August 2026

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

**Why not closed:** seven minutes is not a soak, and a race that stops
reproducing has not been proved absent. Close it after a long run under
multi-operator load, which is also R1's measurement.

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
lines are already silent, and the work is to make the default level read as a
narrative of what the system *did* — moves, calibrations, faults — rather than
what its sockets did. The phrasing complaint stands unchanged.

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
**Status:** open · **Severity:** medium · **Needs investigation**

Occasional slow first paint. Cause unmeasured. Suspected inefficiency in the
serving path, plausibly interacting with D4.

**First thing to try:** the halved relay chunk size described under D4. Every
byte of the UI crosses the Bridge in `kRelayChunkBytes` chunks, so a first paint
is exactly the workload that a doubled round-trip count would slow down.

**Update, 7 August 2026.** Now worth testing properly, because until the D4 race
was fixed any chunk-size result was meaningless — a larger chunk means longer
SPI transactions, so it changed the size of the race window rather than
measuring throughput.

**Caution before raising it.** `RELAY_NOTES.md` §5 says "256 is the value the
working relay used", but the operator recalls **256 failing at the very first
demo**. Those two statements cannot both be the whole truth. Treat 256 as an
experiment with a measured result, not as a known-good value to restore.

Numbers already in hand: a warm app restart is 15.8 s, a cold one ~7 minutes
(empty `.cache/`); a `/api/v1/servo/state` call served in 0.117–0.134 s. First
paint itself is still unmeasured.

**Acceptance:** load time measured and stated; a number to hold against.

---

### D7 — UI is not verified on small operator screens
**Status:** open · **Severity:** medium

Operator screens may be small; the mechanical/ops discussion mentioned an
iPad-class size (exact model not recorded). The layout has only been eyeballed
through devtools.

**Acceptance:** target viewport size confirmed with the operators and written
down here, then the UI verified and fixed at that size.

---

### D8 — `.env` must be created before the first run of this version
**Status:** open · **Severity:** medium · **Found by:** inspection of the live board

There is no `python/.env` on the board, and no `servo_mvp.db` — this version has
not been run yet, so this is a **pending deploy step, not a live
misconfiguration**.

It still matters, because omission is silent: without `.env`,
`use_hardware_servo` defaults to `False` (`python/app/core/config.py:113`), the
backend runs the simulator, and the UI moves convincingly while the servo never
twitches.

`config.py:75-81` already carries a comment about having been burnt by exactly
this — a relative `env_file` that quietly fell back to defaults. The absolute
path anchoring was the fix; the missing file is a separate instance of the same
hazard.

**Update, 7 August 2026 — the manual step is done, the acceptance is not.**
`python/.env` now exists on the board and the backend logs
`servo.backend backend=hardware` at boot, so it is driving the real servo. But
nothing stops the next clean deployment repeating the omission, which is what
this item is actually about.

**Correction to this entry.** The claim that the database is unreachable from
the sshfs mount was wrong, and it was repeated in `CLAUDE.md` §6. It is true of
the *default* `db_path`, but `.env.board` deliberately overrides it with a
**relative** `DB_PATH=servo_mvp.db`, with a comment explaining why: the Python
side runs in a container where `HOME` is `/home/app`. The database therefore
lands at `ArduinoApps/servo_mvp/servo_mvp.db` — **inside the mount**, readable
directly. Both files have been corrected.

The stored datum was read this session and is not 0: the operator calibrated at
count 2049, mid-travel, and it behaves correctly. The `AUDIT.md` warning that it
"is still 0" refers to a database that no longer exists.

**Acceptance:** the deployed board cannot run against the simulator by accident.
Either the manual step is removed, or startup refuses to proceed silently — a
warning in a log nobody reads is what allowed this to persist.

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

### D10 — `logger.exception` swallows the exception
**Status:** open · **Severity:** medium · **Found by:** a live board run

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

### D11 — A single failed poll is presented as a disconnection
**Status:** open · **Severity:** medium · **Reported:** operator, on hardware

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

### D12 — No way to return to the datum after activating a saved zero
**Status:** open · **Severity:** medium · **Reported:** operator, on hardware

Activating a saved zero replaces the active baseline, and there is then no
control that means "go back to the datum". The datum is a row in `zeros` like
any other and is flagged `is_datum`, so the information exists — the operator
route to it does not.

**Acceptance:** from any activated zero, one action returns the active baseline
to the datum, and it is obvious which one it is.

---

## Tasks

### T1 — Apply `CONVENTIONS.md` across the codebase
**Status:** open · **Flow:** `WORKFLOWS.md` W4 · suited to an executing agent

The MVP was written "dirty" on purpose. Measured gap in `python/app/`: 67 `Args:`
lines missing `(type)`, 4 implicit-truthiness checks, 3 `while True`, 3 list
comprehensions, 2 `break`, 0 `continue`, 0 `X | None` unions.

**Acceptance:** the gap table in `CONVENTIONS.md` reads zero across the board,
and 186 tests still pass.

---

### T5 — Add `design_diagrams/` with PlantUML
**Status:** open

Both reference projects (`Krusty-Crab`, `Eyal-FastAPI-Project`) carry
`design_diagrams/pumls/` — architecture diagram, ERD, project UML — plus rendered
images. This repo has none, and it is the more complex of the three: it spans two
processors, a serial bus, a relay and a browser.

**Acceptance:** at minimum an architecture diagram showing the MCU/Linux split
and the byte path from browser to servo, plus an ERD for the SQLite schema.

---

### T6 — Restructure the exception hierarchy
**Status:** open · **Priority:** later, but agreed

Adopt the three-tier hierarchy from `CONVENTIONS.md`: service base
(`ServoMvpException`) → general category (`NotFoundException`) → concrete
(`ServoNotFoundError`). Each class carries its FastAPI status code; error codes
accumulate with `+=` into `SERVO_MVP.NOT_FOUND.SERVO_NOT_FOUND`.

Exceptions must **carry metadata**, passed uniformly and logged at the top level.
They do not today.

The payoff is one handler on the service base exception instead of a handler per
type.

Current state: a flat set under `DomainError`, no error codes, no metadata.

**Acceptance:** one exception handler covers the service; every raised exception
carries a dotted error code and metadata.

---

### T7 — Add the database abstraction
**Status:** open

The abstract/concrete split used for repositories is missing for the database
itself. `python/app/db/database.py` is a concrete `Database` with no contract
above it; it should be an abstract `Database` with a concrete `SqliteDatabase`.

This is the gap meant by "database separation" — not the repository layer, which
already has it.

**Acceptance:** nothing outside the concrete implementation names SQLite.

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

### T2 — Package the air-gapped bundle
**Status:** open

Production runs on a secure isolated network. The wheelhouse
(`--platform manylinux2014_aarch64`) and the vendored patched `Ethernet`/`SCServo`
libraries must be present and verified before delivery.

Current development runs on a WiFi-mounted board instead, because there is only
one servo bus adapter and it sits on a "coloured" network that cannot be
introduced to the secure one. **The air-gapped path is therefore untested.**

**Acceptance:** a clean board with no network provisions and runs from the bundle
alone.

---

### T3 — Run the on-target test suite
**Status:** open · **Flow:** `WORKFLOWS.md` W6

`sketch/tests/OnTarget/` has never been uploaded. It covers ping, configuration
writes, landing accuracy and stop-hold — the things a host cannot check.

**Acceptance:** uploaded once with the servo free-shafted, tally recorded here.

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

## Requirements captured but not yet designed

### R1 — Determine the real concurrent-operator ceiling
Target: roughly three remote operators plus one local USB-C session, all
connected at once without failure. This requirement appears in no other document.
The only enforced limit anywhere is `kMaxRelaySockets = 6`.

**Open question:** can the Bridge sustain that load at all? Unknown.

---

### R2 — Motor isolation: cut drive power, keep sensors alive
**Scope:** in MVP · **Priority:** feature, not critical — must ship with the MVP
so that MVP testing exercises it.

From the mechanical team: it must be possible to kill drive power to the servo
while its sensors stay energised, so the cards are not burnt.

**Feasible in firmware, no hardware change needed.** `ServoRegisters.h:53`
defines `kTorqueSwitch = 0x28` — writing 0 disables drive torque while the
servo's electronics remain powered, so telemetry keeps reading. (Note 128 is
already used on that register as the set-centre-position command.)

**Relationship to Lock: DECIDED — separate controls.** Motor isolation gets its
own control. The two may be composed into a flow, and the dependency may run one
way (engaging the Lock triggers isolation) without running the other, but they
are **not** made one and the same.

Deliberately so: emergency stop (R8) is coming, and if Lock and isolation were
fused there would be no room left to express it.

---

### R3 — Confirm whether the Bridge could carry a frontend framework
The no-framework decision was justified partly on the assumption that the Bridge
relay could not carry a framework's payloads. **That assumption is unverified**
and may be wrong.

It does not change the current decision — the air gap independently rules out a
build pipeline — but the reasoning must not be written into an ADR as fact until
it is tested. See `docs/adr/` when written.

---

### R4 — Post-MVP: mechanical restraint servos, unified under one Lock
After the MVP is accepted, additional servos will be added to physically restrain
the primary servo. At that point the digital Lock, motor isolation and the
mechanical restraint are meant to become a **single** Lock concept rather than
three separate controls.

Out of scope for delivery; recorded so today's decisions do not foreclose it —
in particular, the Lock's API and UI should not be shaped as if "digital only"
were permanent.

---

### R8 — Emergency stop
**Scope:** post-MVP · **Can wait**

A single operator action that engages the Lock **and** removes motor power at
once, rather than requiring the two to be composed by hand. Requested by the same
discussion that produced R2.

This is the reason Lock and motor isolation are kept as separate controls — see
R2. Fusing them now would leave no distinct meaning for emergency stop later.

---

### R5 — Metrics export and benchmarking output
**Scope:** in MVP · **Not started**

Pull telemetry for an arbitrary time range and render graphs (matplotlib or
similar) for delivery. The point is that the MVP must be **benchmarkable**: the
receiving teams need to see whether the servo actually handles what it is asked
to handle.

CSV export exists today and is the seed of this, but it is not enough on its own.

**Acceptance:** given a start and end timestamp, produce the graphs that go in
the handover pack.

**Related:** this is also how "stable" gets defined — see R6.

---

### R6 — Define "stable" by benchmark, not by adjective
"Stable enough to hand over" cannot currently be written down as a checklist.
The plan is to measure first, then set the bar from what the measurements show.

Agreed elements of the bar so far: all defects closed; `CONVENTIONS.md` applied
(T1); air-gapped bundle built and booted on a clean board (T2); on-target tests
run (T3); concurrent-operator ceiling measured and meeting roughly 3 remote plus
1 local (R1); UI verified at the operator screen size (D7); the C++ side
diagnosable (D3); docs true. Numbers for the rest come from R5.

The existing tests run and pass, but are judged not to cover enough — coverage of
the relay and controller is the known hole (see `AUDIT.md`).

---

### R7 — Handover logistics depend on adapter delivery
More servo bus adapters are expected to arrive this month. The current adapter is
on a "coloured" (internet-facing) network and cannot be introduced to the secure
isolated network, which is why development runs on a WiFi-mounted board and the
air-gapped path stays untested (T2).

- **If the adapters arrive before the MVP is finished:** box the system into the
  secure network and hand it over there.
- **If they do not:** hand over with the single existing coloured adapter.

This is a delivery-shaping constraint, not a task.
