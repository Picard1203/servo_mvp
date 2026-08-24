# Backlog

**The work queue. This is the only list of open work in the repo.**

Two files hold the past tense and must not be merged into this one:
`docs/CLOSED.md` (items that entered this backlog and left it) and
`docs/AUDIT.md` (defects found before the backlog existed, frozen).

---

# START HERE — the session plan

**Agreed with the operator, 8 August 2026. Three sessions, in this order. Each
starts cold; everything needed is written down below so nothing is rediscovered.**

| Session | What it does | Board needed |
|---|---|---|
| **1 — Batch 1 & 2 DONE 8 Aug 2026** | **Session 2 next** — the soak | no (desk work both batches) |
| **2** | **The soak** — one long supervised run | yes |
| **3** | **Batch 4** — motor isolation, and the export with graphs | yes, at the end |

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
2. Run the verification commands in `CLAUDE.md` §3 and note the numbers.
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

- **T2** air-gapped bundle — **blocked on adapter delivery (R7)**, not on us.
- **D19** — needs a reachability answer first; see its entry.
- **R3, R4, R8** — post-MVP by decision, not by omission.

**What is not in any batch is as important as what is:** if a batch slips, the
cut line in `PROJECT_STATE.md` says what ships anyway.

**Status key:** `open` · `in progress` · `needs investigation` · `done`

---

## Closed — the record is in `docs/CLOSED.md`

| | | closed |
|---|---|---|
| **D1** | A move to a negative angle stops at 0 | 7 August 2026 · **Confirmed on hardware, both halves** |
| **D2** | `capture()` can store a failed read as position 0 | 7 August 2026 · commit `c903182` |
| **D9** | The display and the motion path used two different baselines | 7 August 2026 · commit `c903182` · **found on hardware** |
| **D11** | A single failed poll is presented as a disconnection | 7 August 2026 · **needs an operator's eye on the board** |
| **D14** | The most likely error in the system shows the operator "Failed to fetch" | 8 August 2026 · Batch 1 |
| **D15** | A command in flight looks identical to a command that did nothing | 8 August 2026 · Batch 1 |
| **D16** | On a failed read the operator is shown 0.0 V, 0.0 A, 0.0 °C as if measured | 8 August 2026 · Batch 1 · **the answer was "both sides"** |
| **D20** | `eventTime()` claims a compatibility fallback it does not implement | 8 August 2026 · Batch 1 |
| **D21** | The UI tells the operator the step is 0.1°; it is 0.06° | 8 August 2026 · Batch 1 |
| **T8** | Instrumented run on the board over adb | 7 August 2026 · **Flow:** `WORKFLOWS.md` W1 |
| **T4** | Moves while unverified: DECIDED, permitted | (decision) · **Recorded in:** ADR-0007 |

---

## Defects

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
**Status:** open · **Severity:** medium · **still blocked on Q1**

**Narrowed 8 August 2026: it is not a touch screen** (operator, answering the
touch half of Q1). That settles the *interaction* model — and D15 was designed
against it — but not the size. A wall panel and a laptop are both
pointer-driven and lay out nothing alike, so **the viewport is still the
blocker.**

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


### D12 — No way to return to the datum after activating a saved zero
**Status:** open · **Severity:** medium · **Reported:** operator, on hardware

Activating a saved zero replaces the active baseline, and there is then no
control that means "go back to the datum". The datum is a row in `zeros` like
any other and is flagged `is_datum`, so the information exists — the operator
route to it does not.

**Acceptance:** from any activated zero, one action returns the active baseline
to the datum, and it is obvious which one it is.

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

### D23 — `moving` and the fault flags are reported as measured on a failed read
**Status:** open · **Severity:** medium · **Raised by:** Batch 1, 8 August 2026

The sixth twin-path instance, where D16's entry said to look for it.

After Batch 1 six fields null on a failed read: `output_deg`, `raw_counts` and
the four telemetry floats. `moving` and the six fault booleans still come from
`_empty_snapshot()`, all `False` — so the API states that a servo which did not
answer is **not moving and has no faults**. The UI no longer renders it; every
other consumer still reads it, which after R5 and D22 is the point of the API.

Not fixed in Batch 1 because `bool | None` is a tri-state that ripples into the
CSV, `TelemetrySample`, the database schema and every client — an API-shape
decision, not a defect fix.

Three options, not equivalent:

1. **Null the booleans too.** Consistent with the six that already null; most work.
2. **Lean on `reading_valid`** and document it. Cheapest; relies on every future
   client reading a docstring — the assumption that failed in D16.
3. **Nest a `reading` object** that is null as a whole. Cleanest; biggest change
   to client and CSV.

**Acceptance:** one is chosen and written down, and no field of `/servo/state`
states a measurement that was not taken. If (2), say plainly it is a documented
convention, not an enforced one. **Amends ADR-0008.**

**Related:** D16, D2, D9, ADR-0008.

---

### D26 — The Python suite failed once in ten runs, unreproduced
**Status:** open · **needs investigation** · **Severity:** medium
· **Observed:** 8 August 2026

One run reported `1 failed, 197 passed`. Nine runs either side were clean and it
did not recur, so **which test failed is not known** — the run was chained into
one command and its traceback was consumed before it could be read. That was an
error in how it was run.

- It happened on the loaded run (pytest + `make` + two `node` invocations
  chained, on a machine also serving an sshfs mount).
- Batch 1's Python change is four conditional expressions and some type
  annotations — nothing concurrent, timed or ordered.
- The suite has timing-sensitive areas: the settle window, the sampler interval,
  `wait_until` in `conftest.py`. A deadline under load is the natural suspect.

**Acceptance:** run the suite in a loop with `--tb=long` captured to a file
until it recurs; then fix it or document the timing sensitivity that triggers
it. **Until then a single green run is not evidence** — any report of "198
passed" should say how many runs it took.

**Related:** D10 (a failure that destroyed its own evidence), T3.

---

### D25 — An overload that stops being readable disappears from the screen
**Status:** open · **Severity:** medium · **Found by:** twin-review, 8 August 2026

The servo trips overload; the banner reads `■ ALARM · Overload` and the recover
control appears. Reads then start failing — what a strained servo on a busy bus
does. After three failures D16's rule blanks the lamps, the banner switches to
"Position unknown", and the recover control is hidden. **The servo is still
overloaded and the screen no longer says so.**

Not a regression — before D16, `overload:false` hid the button from the *first*
failed read. Filed because D16 rewrote these lines: blanking a fault that **was**
reported differs from blanking a lamp that never was.

**Hiding recover is arguably correct**, and that is the tension: `recover()`
raises `InvalidReadingError` when the position is unknown, so the control could
only refuse. The defect is that the alarm stops being *stated*.

**Acceptance:** a fault reported and never reported cleared stays visible while
the reading is unknown, marked last-known. Decide at the same time whether
recover is reachable or explained as unavailable — hidden and refused teach the
operator different things.

**Related:** D16, D11, D12, R2.

---

### D24 — Two `InvalidReadingError` guards are unexercised; the docs claimed 100%
**Status:** open · **Severity:** medium · **Found by:** Batch 1, 8 August 2026

Coverage of `app/` is **99%, not 100%**. Two statements never execute:

| | |
|---|---|
| `zero_service.py:49` | the guard in **`ZeroService.capture()`** |
| `servo_state.py:225` | the guard in **`ServoStateStore.read_counts()`** |

**`capture()`'s guard is the line D2 exists about.** D2 states it "now raises
`InvalidReadingError` exactly as `calibrate()` always did" and that six tests
were added. The guard is correct; the test that runs it does not exist.
`calibrate()`'s twin **is** covered — the twin-path shape, this time in the
tests.

Measured identically before and after Batch 1 (929 statements, 2 missed), so it
pre-dates it. It survived because **nothing measures it**: the verification
commands do not run coverage and `pytest.ini` sets no threshold.

**Acceptance:** both guards exercised by a test that fails without them, and the
quoted figure is one the suite enforces (`--cov-fail-under`) or is not quoted.

**Related:** D2, ADR-0008, `AUDIT.md`.

---

## Tasks

### T12 — Decide the status of `tools/check_client_behaviour.js`
**Status:** open · **Severity:** medium · **Raised by:** Batch 1, 8 August 2026

Written during Batch 1 because four of its five items were client-side and the
repository could check none of them. Loads `python/static/app.js` into a stubbed
DOM under `node` and runs 44 assertions across D14, D15, D16, D20, D21. Passes.
Deliberately **not** a fourth verification command yet.

**For:** every UI defect here — D14, D15, D16, D17, D18, D19, D21 — lives in one
600-line file with no automated coverage, and it needs nothing beyond `node`, in
the spirit of `tools/check_bridge_contract.py`.

**Against:** it makes `node` a development prerequisite, which touches ADR-0005
(air-gapped by default) — it must never become something fetched from a network.
And a stubbed DOM proves logic, not rendering: nothing about layout, CSS, or
whether `disabled` really blocks a click.

**Acceptance:** either it becomes a fourth command and `CLAUDE.md` §3 says so
with its count, or it is recorded as a one-off with a reason. **Do not leave it
undecided** — a checker nobody runs is D20's species.

**Related:** ADR-0005, D7, R6.

---

### T13 — Distil the remaining documents
**Status:** open · **Severity:** medium · **Raised by:** the operator, 8 August 2026

Docs are re-ingested at the start of every session, so their length is a
recurring tax on the work. Started 8 August 2026: closed items moved to
`docs/CLOSED.md` and Batch 1's own entries cut, taking `BACKLOG.md` from 15,223
words to ~10,600.

**Not yet done.** The remaining bloat is in entries written before this rule:

| | words |
|---|---|
| `D4` | 687 |
| `D13` | 522 |
| `R2` | 520 |
| `R5`'s "use case" section | 459 |
| `T11` | 425 |
| `D22` | 388 |
| `D10`, `D8`, `T10`, `D5`, `T9` | ~300 each |

Also worth a pass: `docs/WORKFLOWS.md` (1,754) and `CONVENTIONS.md` (1,350).

**Do it opportunistically** — distil an entry when you are already working on
that item, not as a sweep of its own. A sweep costs the tokens it is meant to
save, and rewriting reasoning you have not just re-derived is how facts get
dropped.

**Acceptance:** no open entry states the same thing twice, and every one keeps
its numbers, paths, decisions and honest statements of what was not tested. The
rule itself is in `CLAUDE.md` §4.

---

### T1 — Apply `CONVENTIONS.md` across the codebase
**Status:** open · **Flow:** `WORKFLOWS.md` W4 · suited to an executing agent

The MVP was written "dirty" on purpose. Measured gap in `python/app/`: 67 `Args:`
lines missing `(type)`, 4 implicit-truthiness checks, 3 `while True`, 3 list
comprehensions, 2 `break`, 0 `continue`, 0 `X | None` unions.

**Acceptance:** the gap table in `CONVENTIONS.md` reads zero across the board,
and the suite (207 tests as of Batch 2) still passes.

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
