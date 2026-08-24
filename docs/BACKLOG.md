# Backlog

**The work queue. This is the only list of open work in the repo.**

`AUDIT.md` is the *past* tense (bugs already fixed). This file is the *present*
tense. Do not merge them.

---

# START HERE — the session plan

**Agreed with the operator, 8 August 2026. Three sessions, in this order. Each
starts cold; everything needed is written down below so nothing is rediscovered.**

| Session | What it does | Board needed |
|---|---|---|
| **1 — next** | **Batch 1 then Batch 2** — fix the instrument, then make the MCU diagnosable | Batch 2 only |
| **2** | **The soak** — one long supervised run | yes |
| **3** | **Batch 4** — motor isolation, and the export with graphs | yes, at the end |

Use **`/deliver`** to run a batch: it plans, **stops once** for approval, then
runs the whole thing. Use **`/operator-lens`** before changing anything the
operator sees, and **`/twin-review`** on the finished diff — every item in
Batch 1 has a twin somewhere.

**Do not run the Python suite looking for 192.** There is no venv on the
development machine and this is known, not a failure — `pip install -r
python/requirements-dev.txt` in a venv if you want it, otherwise verify with the
other two commands and **say plainly that the suite did not run.** The native
checks (164) and `tools/check_bridge_contract.py` ("both sides agree") both work
with no setup.

## Session 1, Batch 1 — Fix the instrument before taking the measurement

Five fixes, all client-side or schema-level, **no board required.** Three of
them change what Session 2 is able to observe, which is why they come first.
Every location below is verified as of 8 August 2026.

| # | Item | Where | The fix, in one line |
|---|---|---|---|
| 1 | **The most likely error shows "Failed to fetch"** (D14) | `app.js:220` `sayError()` | A network-level rejection has no `reason` code and never reaches `asApiError()` — give it its own branch and a sentence an operator can act on |
| 2 | **A command in flight looks like one that did nothing** (D15) | `app.js:539` `bind()`; handlers `:441-528` | Mark the control busy and refuse a second press until it answers. **Design it touch-safe** — Q1 is unanswered, so assume a finger |
| 3 | **A failed read shows 0.0 V as if measured** (D16) | `schemas/servo.py:106-116`; `app.js:286-289` | One rule, five fields. Either the schema nulls them all or the client blanks them all — decide once, apply to both |
| 4 | **The UI says the step is 0.1°; it is 0.06°** (D21) | `app.js:224`; backend is right at `motion_service.py:255-258` | Stop discarding the backend's message. Confirmed leftover from an earlier design |
| 5 | **`eventTime()` claims a fallback it does not implement** (D20) | `app.js:411-412` | Both branches identical. Delete the dead one and its comment |

**Test-first where it is testable.** Items 3 and 4 have backend halves that can
have failing tests written before the fix; items 1, 2 and 5 are browser-side and
this repository has no browser test harness — **say so rather than claiming
coverage.**

**Then `/twin-review` the diff.** Item 3 is the fifth instance of the twin-path
class in this repository; the sixth is the one nobody has found yet.

## Session 1, Batch 2 — Make the machine diagnosable

| # | Item | Where |
|---|---|---|
| 6 | **The C++ side has no logging** (D3) | `ServoBus`, `ServoController`, `NetworkRelay`, `BridgeApi` in `sketch/src/` |
| 7 | **Decide the connection ceiling** (D13) | An ADR in `docs/adr/`, not a code change |

**Read `sketch/src/RELAY_NOTES.md` before touching any of it.** The hard
constraint: `loop()` must keep yielding or the Bridge thread starves into a 10 s
timeout. Size the log volume against T9's budget *before* adding it — relay
chatter is the highest-rate traffic in the system.

**Two counters already exist and cannot be read from the board**:
`write_lock_timeouts()` and `rejected_total()`. Exposing them is the point of
this batch, because Session 2 needs them — including to settle whether the
USB-C session bypasses the relay (R1).

**The ceiling decision is a choice, not a fix.** The measurement is done. The
W5500 has 8 hardware sockets and the listener takes one (`Config.h:44`), so **7
is a wall** and raising `kMaxRelaySockets` from 6 buys exactly one slot. The
real lever is `timeout_keep_alive=5` (`main.py:142`). Write the ADR before
Session 2, or the soak measures a system nobody has decided the shape of.

## Session 2 — The soak

One long supervised run closing four things at once: the connection-drop defect
(D4), the operator ceiling (R1), storage growth over hours rather than minutes
(T9), and a watch for the unexplained sampler exception (D10). Tooling exists:

```bash
python3 tools/synthetic_operator.py --host <board> --minutes 120 \
    --operators 3 --report soak.json
python3 tools/soak_report.py --since <ISO timestamp>
```

Run it **supervised**. An unattended failure at 03:00 is a gap in a log; a
watched one is an observation.

## Session 3 — Batch 4

Motor isolation (**latching, decided — see `OPEN_QUESTIONS.md` Q4; write the ADR
first**), and the export: time-range selection plus the matplotlib graph set,
**both on the backend and in the UI**, with torque first-class.

## Not in these three sessions

The handover pack (defining "stable", the recovery runbook, the **operations
manual**, diagrams, on-target tests), and the mechanical conventions pass. See
the batch list further down.

---

## How to pick up work

1. Read `../CLAUDE.md` if you have not — especially the graphify rules. **Query
   the graph before reading source; it costs a fraction of the tokens.**
2. Run the three verification commands and note the numbers (192 / 164 / agree).
3. Take the next **batch** from "Ordering, rewritten 8 August 2026" — not a
   single item. The unit of work here is a session; T8 proved it.
4. Update this file as part of the change — an item is not done until its entry
   says so.
5. Run `graphify update .` after changing code.
6. Re-run the three commands. If the numbers moved, stop and say so.

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

### Batch 1 — Desk work, no board (do now, in parallel with nothing)

| | Item | Size | Why here |
|---|---|---|---|
| 1 | **D14** network errors read as "Failed to fetch" | S | Every later board session produces these; unreadable errors waste the session |
| 2 | **D15** no in-flight feedback | S | Makes D13 worse by inviting a second press. Fix before measuring D13 |
| 3 | **D16** telemetry rendered as 0.0 on a failed read | S | Twin-path, fifth instance. One rule, five fields |
| 4 | **D21** UI states the wrong step size (0.1° vs 0.06°) | S | Same handler as D14; a number shown to the operator that is simply wrong |
| 5 | **D20** dead `eventTime` branch | S | Two minutes; it is a comment that lies |

**Rationale:** all four are client-side or schema-level, none need hardware, and
three of them change what the *next* board session is able to observe. Fixing
the instrument before taking the measurement.

### Batch 2 — Make the machine diagnosable (board present)

| | Item | Size | Why here |
|---|---|---|---|
| 5 | **D3** C++ side has no logging | M | `write_lock_timeouts()` and `rejected_total()` both exist and **cannot be read from the board.** Two diagnostics, unreachable |
| 6 | **D13** decision: is six slots enough? | M | Not a bug — an architectural limit. **Wants an ADR**, see below |

D13's numbers are already measured. What is missing is a *decision*: raise
`kMaxRelaySockets`, drop `timeout_keep_alive`, pool on the client, or accept the
ceiling and surface refusals properly. That decision changes R1's answer, so it
comes before R1 is measured — and it belongs in `docs/adr/` because it will
otherwise be re-litigated on every future connection bug.

### Batch 3 — The measurement session (board, supervised, one long run)

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

- **T2** air-gapped bundle — **blocked on adapter delivery (R7)**, not on us.
- **D19** — needs a reachability answer first; see its entry.
- **R3, R4, R8** — post-MVP by decision, not by omission.

**What is not in any batch is as important as what is:** if a batch slips, the
cut line in `PROJECT_STATE.md` says what ships anyway.

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

**Tooling for that run exists** (7 August 2026), so the soak is two commands:

```bash
python3 tools/synthetic_operator.py --host <board> --minutes 120 \
    --operators 3 --report soak.json     # drives it like people do
python3 tools/soak_report.py --since 2026-08-08T09:00   # what the board saw
```

The first simulates operators — polling once a second like the UI, moving,
waiting for the move to arrive, thinking, locking, occasionally pulling an
export — with randomised think time so they do not act in lockstep. The second
pulls the database and log over `adb` and states a verdict: gaps in the 9–13 s
stall band, positions the servo cannot have reported, logged failures, and the
growth rates T9 needs.

Run it supervised rather than overnight. An unattended failure at 03:00 is just
a gap in a log; a watched one is an observation.

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
**Status:** half done — **the logging is fixed; the fault itself is still
unexplained** · **Severity:** medium · **Found by:** a live board run

**Fixed 7 August 2026.** The cause was the Logger461 stand-in in `main.py`:
its `exception()` was a straight copy of `error()`, and attaching the exception
is the entire difference between the two. It now records the exception type, its
message and the traceback, and the console prints the traceback under the record
instead of flattening it into the single-line format.

**The test stub in `conftest.py` had the identical gap**, so a test asserting on
a cause would have passed against a stub that dropped it exactly as production
did. Both fixed together — this is the twin-path pattern for the fourth time in
this repository.

**Still open: the actual fault.** The sampler exception of 21:37:58 remains
unexplained, and its evidence is gone. It can only be caught if it happens
again — but now, when it does, the record will say what it was. **Watch for it
on the next board run.**

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

### D13 — Requests arriving faster than slots free up are refused
**Status:** open · **Severity:** high · **Measured 7 August 2026**

**This is the "first press does nothing, press it again" symptom**, and it now
reproduces on demand. Identical requests, from one machine, differing only in
spacing:

| pattern | requests | failures |
|---|---|---|
| back to back, new connection each | 10 | **5** |
| paced at 1 s, as the UI polls | 10 | **0** |

**The ceiling, measured:** `kMaxRelaySockets = 6` slots, each held for about
five seconds after use by uvicorn's `timeout_keep_alive=5` (`main.py:142`, set
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

### D12 — No way to return to the datum after activating a saved zero
**Status:** open · **Severity:** medium · **Reported:** operator, on hardware

Activating a saved zero replaces the active baseline, and there is then no
control that means "go back to the datum". The datum is a row in `zeros` like
any other and is flagged `is_datum`, so the information exists — the operator
route to it does not.

**Acceptance:** from any activated zero, one action returns the active baseline
to the datum, and it is obvious which one it is.

---

### D14 — The most likely error in the system shows the operator "Failed to fetch"
**Status:** open · **Severity:** high · **Found by:** operator lens, 8 August 2026

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
**Status:** open · **Severity:** high · **Found by:** operator lens, 8 August 2026

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
**Status:** open · **Severity:** high · **Found by:** operator lens, 8 August 2026

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

### D17 — The position bar cannot show the negative half of travel
**Status:** open · **Severity:** medium · **Found by:** operator lens, 8 August 2026

`app.js:283` computes the bar as `(deg / 360) * 100`, clamped to 0–100.

Travel is **±90 output degrees** (ADR-0003). So the whole positive half of travel
occupies the first **25%** of the bar, and every negative angle clamps to **0%** —
an operator at −45°, at −90° and at 0° sees an identical empty bar. Half the
travel window is invisible on the only spatial indicator in the UI.

The numeric readout is correct; this is the picture beside it disagreeing with
it. Given D9 — where the operator commanded a move from a readout they trusted —
an indicator that silently agrees with itself across a third of the range is
worth fixing before the demo.

**Acceptance:** the bar maps the configured travel window, `output_min_deg` to
`output_max_deg`, with the datum visible as a marked centre.

---

### D18 — A failed CSV export navigates the operator out of the application
**Status:** open · **Severity:** medium · **Found by:** operator lens, 8 August 2026

`doExport()` (`app.js:522`) sets `window.location.href` to the export endpoint.
That is not a request the page can observe: there is no `catch`, no status, no
notice. If the endpoint errors, or the relay refuses the connection, the browser
replaces the control UI with its own error page and the operator has to find
their way back — from a machine-control screen.

It is also a **new connection** every time, spending from the same six-slot
budget as D13, taken at the moment an operator is most likely to also be driving.

**Acceptance:** export fetches in the background, reports success or failure like
every other command, and never navigates away from the control page.

**Related:** D13, D14, R5 — the export is the seed of the benchmarking pack, so
it will be used more, not less.

---

### D19 — Saved positions are listed against a baseline of 0 when no zero is active
**Status:** open · **Severity:** medium · **Needs confirmation on hardware**
· **Found by:** operator lens, 8 August 2026

`renderZeros()` (`app.js:367`):

```js
const base = active ? active.raw_counts : 0;
```

Every saved position's displayed angle is `(raw_counts - base) / counts_per_deg`.
**With no active zero, `base` is 0** — so a position stored at count 2049 lists
as ≈150°, not 0°, and the list becomes a set of plausible-looking wrong numbers.

**This is D9's exact line of code, in a third location.** D9 was a display
baseline of 0 where motion used mid-travel; `_baseline_counts()` is now the
single definition on the Python side — and this client-side copy did not learn.
It is the twin-path pattern again, across the API boundary this time.

Marked *needs confirmation* rather than confirmed: it requires a state with saved
zeros and none active, which may not be reachable if the datum is always active.
**Determine whether that state is reachable before deciding the fix** — if it is
not reachable, the defect is that a fallback exists at all for a state that
cannot happen, and it should be an error rather than a silent 0.

**Related:** D9, D12.

---

### D20 — `eventTime()` claims a compatibility fallback it does not implement
**Status:** open · **Severity:** low · **Found by:** operator lens, 8 August 2026

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
**Status:** open · **Severity:** medium · **Found by:** the gear-ratio audit,
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

### D22 — The only export control is fixed at 24 hours
**Status:** open · **Severity:** high · **Raised by:** the operator, 8 August 2026

`doExport()` (`app.js:522`) hardcodes the window:

```js
const from = now - 24 * 3600;
```

**The handover benchmark is the receiving team running the system for several
days unattended, after which the record is loaded and read.** With a 24-hour
button, four days of a five-day run cannot be retrieved from the UI at all —
they exist in the database and are reachable only by someone with `adb` or the
sshfs mount, which is not the receiving team.

The data is there: telemetry is sampled once a second, retained 60 days, and
`torque_kgcm` is already stored and already a CSV column. **The gap is purely
the operator's route to it**, and it defeats the primary reason R5 exists.

**Scope confirmed and widened by the operator, 8 August 2026.** Two deliverables,
not one, and **both must exist on the backend *and* in the UI** — a tool that
only runs from a shell is unreachable for the team who ran the test:

1. **CSV over a chosen range.** The operator picks start and end. The backend
   endpoint already takes `from` and `to`; it is the UI that hardcodes 24 hours.
   So this is mostly a control, not a feature — but the range picker has to
   cope with a five-day window without the operator typing epoch seconds.
2. **The graphs, generated on request and downloadable.** Same range, the
   matplotlib set described under R5, produced by the board and delivered to the
   browser. **This is the part that does not exist at either layer.** Decide
   deliberately whether rendering happens on the board (simple, but matplotlib
   on the MPU during a live run competes with the sampler) or the endpoint
   serves data that the client plots — and record the choice, because it is the
   kind of decision that gets re-argued.

**Acceptance:** from the UI, the operator picks a time range spanning days and
gets both the CSV and the graph set for exactly that range; neither navigates
away from the control page (D18); and both are reachable from the backend alone
for anyone working over `adb`.

**Related:** R5 (this is its delivery path), D18 (same control, silent failure),
T9 (a multi-day pull must not exhaust memory — stream it, as the CSV export
already does).

---

## Tasks

### T1 — Apply `CONVENTIONS.md` across the codebase
**Status:** open · **Flow:** `WORKFLOWS.md` W4 · suited to an executing agent

The MVP was written "dirty" on purpose. Measured gap in `python/app/`: 67 `Args:`
lines missing `(type)`, 4 implicit-truthiness checks, 3 `while True`, 3 list
comprehensions, 2 `break`, 0 `continue`, 0 `X | None` unions.

**Acceptance:** the gap table in `CONVENTIONS.md` reads zero across the board,
and 192 tests still pass.

---

### T9 — Put a measured storage budget in writing
**Status:** open · **Raised by:** the operator, planning a one-to-two month test

The question is simple and nobody could answer it: *run this for two months —
does it fit?* Measured on the board on 7 August 2026:

| | rate | one month | two months |
|---|---|---|---|
| Telemetry database | ~80 bytes/row at 1 row/s → ~6.9 MB/day | ~208 MB | ~416 MB |
| Log at DEBUG | ~180 bytes/line, ~24 lines/min/operator → ~6.3 MB/day | ~188 MB | ~376 MB |

Free space on the board: **2.6 GB**. So a two-month run at DEBUG lands near
800 MB — it fits, but nothing enforces it and nobody had written it down.

**Retention, corrected.** Telemetry purges at 60 days
(`telemetry_retention_days`), so the database plateaus rather than growing
without limit. The **real Logger461 rotates**, so production logging is bounded
too. What is *not* bounded is the **stand-in** in `main.py`, which is what runs
on any board without the wheel installed — including this one. It opens the file
and appends forever.

Still to do:

- Confirm the telemetry purge actually plateaus the file. SQLite reuses freed
  pages rather than shrinking, so the size should level off, not fall — verify
  rather than assume.
- Measure the message rate with several operators, not one.
- **Size any MCU-side logging against this budget before adding it** (D3). Debug
  chatter from the relay is the highest-rate traffic in the system, and if it
  crosses the Bridge into the same log file it spends from the same allowance.
  If the stand-in is what will be running, give it rotation first.

**Acceptance:** a table like the one above, verified over a multi-hour run, with
a stated maximum footprint the board cannot exceed.

---

### T10 — Write the recovery runbook, in two halves
**Status:** open · **Severity:** high · **Raised by:** the operator answering
`OPEN_QUESTIONS.md` Q3, 8 August 2026

The site is roughly three hours away and **there is no written procedure for
what to do when the system misbehaves.** ADR-0007's entire argument rests on not
turning a signal loss into a site visit — and then nothing says what the person
who did travel should actually do.

The operator's answer defines the shape: **on site is the same UI as remote,
plus `adb`, because they are USB-C connected rather than coming through the
relay.** So there are two audiences and two documents:

**Remote half** — what an operator with only the browser can do. The UI says
OFFLINE: what does that mean, how long to wait before it is real (three failed
polls, about three seconds), what a refusal looks like versus a fault, and when
to stop pressing and call someone.

**On-site half** — the `adb` sequence, in order, with what is safe to run while
a mechanism is attached:

```bash
adb shell arduino-app-cli app logs  user:servo_mvp
adb shell arduino-app-cli app start user:servo_mvp   # ~16 s warm, ~7 min cold
```

Plus: reading the database directly, confirming `servo.backend backend=hardware`
rather than the simulator (D8), and **what is never safe** — the mechanism can
be moved by hand with power off, so a restart with somebody's hands in it is not
a neutral act.

**On-site is also the diagnostic seat.** Whoever holds the USB-C cable is the
only person who can catch D10's unexplained sampler exception, or anything the
soak surfaces. Give them the commands before the trip, not during it.

**Acceptance:** both halves written, and the on-site half rehearsed once by
somebody who did not write it.

**Related:** Q3, Q9, D3 (the MCU counters they will want and cannot read), D8.

---

### T11 — Write the operations manual
**Status:** open · **Severity:** high · **Raised by:** the operator, 8 August 2026

**The everyday document. Nothing in this repository tells someone how to operate
the system.** Every document here is written for whoever is *building* it —
`CLAUDE.md`, the ADRs, the conventions, this backlog. The person who sits down
in front of the UI to do a day's work has nothing.

That gap ships with the MVP unless it is closed: the receiving team runs this
unattended for days, and the benchmark is only as good as their ability to
operate it correctly for those days.

**Distinct from T10, and the split is deliberate:**

| | T11 — operations manual | T10 — recovery runbook |
|---|---|---|
| When it is read | every day | when something is wrong |
| Audience | the operator | the operator, then whoever is on site |
| Content | how to do the work | how to get back to working |

One fact in one file: **the manual does not repeat the runbook.** It points at
it.

**Contents, at minimum:**

- **The startup ritual.** Drive the mechanism to mid-travel, press Calibrate —
  and *why*, because the mechanism can be moved by hand while power is off, and
  because a datum that is not mid-travel strands half the travel window
  (ADR-0003, and the original cause behind D1).
- **What every control does**, including the ones whose meaning is not obvious:
  Lock versus motor isolation versus emergency stop, and why they are separate
  controls (R2, R8).
- **Saved positions**: what a zero is, what activating one changes, and how to
  get back to the datum (D12).
- **Reading the screen honestly**: what MOVING, SETTLING and HOLDING mean; what
  the unverified-reference warning means; what a blank position means and what
  it does not.
- **The travel window**: ±90 output degrees, 0.06° per step, and what a refusal
  as out-of-travel is telling them.
- **Pulling the data**: the export, the time range, and the graphs — the thing
  the receiving team will be doing at the end of their run.
- **What not to do**, with reasons rather than prohibitions.

**Write it after the batch-1 and batch-4 work, not before** — several of the
things it must describe are the things being changed. A manual describing the
current error messages would be wrong within a week.

**Acceptance:** somebody who has never seen the system can run a normal working
session from this document alone, without asking a developer.

**Related:** T10 (the emergency half), D12, D17, R2, R5.

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

**Sharpened by the operator, 8 August 2026** (`OPEN_QUESTIONS.md` Q2, Q3, Q9):

- **The sessions are screens left open, not people driving.** That is the cheap
  case — a polling browser reuses one connection. Driving is occasional.
- **The on-site session is the same UI plus `adb`**, connected over USB-C.
- **7 is a hard ceiling, not a setting.** `Config.h:44` already recorded why:
  the W5500 has 8 hardware sockets and the listener takes one. Raising
  `kMaxRelaySockets` from 6 buys **exactly one more slot**, then stops.
- **So the lever is `timeout_keep_alive=5`, not the socket count.** Five seconds
  of slot retention per connection is what produces the measured ceiling of
  about one new connection per second. That is the number to tune.
- **And the arithmetic may not be what it looks like** — if the USB-C session
  reaches uvicorn without crossing the W5500 (Q9), it costs no relay socket at
  all and the budget is the remote screens alone. **Unverified. Do not report
  R1 as met on the strength of it.**

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

**Elevated to a build item, 8 August 2026.** This is one of only two unbuilt
things scoped *in MVP*, and it had no design, no acceptance and no place in the
suggested order — it was a requirement paragraph sitting behind thirteen
defects. The firmware half is a single register write; **the operator half does
not exist at all**, and that is the work.

**Still to decide before any code** — these are design questions, not
implementation details:

- **What the operator sees.** A third cube beside Lock and Calibrate? What does
  it read when engaged — "Motor off"? The state must be unmistakable, because a
  de-energised servo that still reports telemetry looks exactly like a working
  one on this UI.
- **What happens to a move command while isolated.** Refuse it with a reason
  code (the `sayError()` path, which needs D14 first), or accept and queue it?
  Refusing is the honest answer and matches `locked`.
- ~~**Whether it survives a reboot.**~~ **DECIDED 8 August 2026 — it latches.**
  Isolation persists across a restart and is re-applied at startup *before any
  move can be accepted*. Reasoning in `OPEN_QUESTIONS.md` Q4, in short: a
  protective state should be the one that survives, and unlike calibration
  (ADR-0007) clearing isolation needs no one on site — it is one click in the
  UI the remote operator already has open. The latch lives in the database as
  operator intent, because the servo register re-enables on power-up regardless.
  **Wants an ADR before build**, and it must agree with R8's emergency stop.
- **What `state` reports**, so the UI can render it and telemetry can record it.
  A new field on `ServoStateResponse` — and per D16, decide its behaviour on an
  invalid read *at the same time*, not afterwards.

**Acceptance:** the operator can cut drive power from the UI and see plainly that
it is cut; telemetry keeps reading throughout, proving the sensors stayed alive;
a move while isolated is refused with a message that says why; the state is
reported in `/servo/state` and recorded in telemetry; and the behaviour across a
reboot is documented, whichever way it is chosen.

**Blocks:** MVP handover. **Wants first:** D14 (so the refusal reads properly).

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

**Elevated to a build item, 8 August 2026.** The second of the two unbuilt
in-MVP items. Its absence is not a missing feature — it is the reason R6 cannot
be written, the reason the soak run has no output format, and the reason the
receiving teams have nothing to judge. **Everything measured so far has been
read out of an ad-hoc query or a log.**

### The use case this actually serves — stated 8 August 2026 by the operator

**The receiving team runs the system for several days on their own, unattended.
Afterwards we load what it recorded and see what happened.** That is the
benchmark. It reframes R5 from "graphs for a handover slide" into **a forensic
record of a run nobody watched**, and three consequences follow:

- **Torque is first-class, not a nice-to-have.** It is the measurement that says
  whether the servo actually handled what it was asked to handle — the question
  R5 exists to answer. `torque_kgcm` is **already sampled, already stored**
  (`sqlite_telemetry_repository.py:28`) **and already in the CSV columns**
  (`telemetry_service.py:17`), so the data layer needs nothing. **The graphs must
  name it explicitly**, plotted against commanded motion so load is readable
  against what was asked, with its peaks and sustained levels called out — not
  buried as a fourth line on a shared axis.
- **Nobody is watching while it runs.** Anything not recorded is lost for good.
  Before that run, confirm the sampler survives days rather than minutes (D10's
  unexplained exception, T9's growth rates, and the stand-in logger in `main.py`
  that appends forever without rotation).
- **The window is days, not a session.** See D22 — the only export control in the
  UI is fixed at 24 hours, so after a five-day run an operator can retrieve the
  last day of it and no more.

**60-day telemetry retention (`telemetry_retention_days`) comfortably covers a
multi-day run** — verify it plateaus rather than assume it, per T9.

**Acceptance, made concrete:**

- Given a start and end timestamp, produce a PNG set: position against time with
  commanded target overlaid; **torque against time, with commanded motion
  overlaid, plus peak and sustained figures stated in numbers**; sampler
  interval distribution, with the 9–13 s stall band marked (that band is what
  `tools/soak_report.py` already judges); temperature, voltage and current
  against time; and a count of invalid readings over the window.
- **Must work over a multi-day window**, not just a session — that is the
  handover benchmark. Downsample for the plot if needed, but never for the
  stated numbers.
- Runs on the board *or* off it against a pulled database — the graphs must not
  require the servo to be attached, or nobody can produce them during a review.
- One command, with the time range as arguments, documented in `README.md`.
- The existing CSV export stays and remains the raw form; this sits on top of it.
- **Reuses `tools/soak_report.py`'s verdict logic** rather than restating it —
  one definition of "a stall", not two. See D9 on what two definitions cost.

**Related:** this is also how "stable" gets defined — see R6. D18 — the export
is the seed of this and currently fails silently. T9 — the storage numbers this
must not contradict.

**Blocks:** MVP handover, and R6 entirely.

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
