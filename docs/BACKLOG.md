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
| **2 — DONE, 8 + 10 Aug 2026** | D4 closed via SSE in Session 3 | yes |
| **3 — DONE, 11 Aug 2026** | SSE migration, D4 closed | yes |
| **4 — DONE, 23 Aug 2026** | Sampler 0.5s/retention 30d, R5 (XLSX export) rebuilt from scratch (11 Aug attempt never worked at all), relay chunk-size dispute closed with a cause, D31/D10 closed or advanced with real board evidence. **R5's mechanism works and is cross-app validated — but real UX gaps found live and deferred, see next row.** | yes |
| **5 — DONE, 23 Aug 2026** | **R5's export, redirected live by the operator**: target angle + servo angle end to end (UI and export), angle-correlated charts, a typed chart-range selector (confirmed live to work), decoded flags, day-sheet and Overview column widths, LCARS styling, per-day summary table. One live regression (chart date-axis) caught and reverted same session. **D10 and R2 stayed out of scope**, as planned — deferred, see row 6. Full detail in R5's entry. | yes — used for a real live walkthrough this session, which is exactly what caught the regression and several width/spacing defects a local render alone had missed |
| **6 — D10 half DONE, 24 Aug 2026** | **D10 closed** — real cause was a thread-safety gap in the SQLite layer (every unlocked read on the shared connection, not the zero-table race the original writeup guessed), see `CLOSED.md`. **Batch 4's motor isolation (R2)** remains — pulled out of Session 5 by the operator, 23 Aug 2026, to keep that session scoped to the export. **Before planning R2: a `/grilling` pass on R2's open design questions** (operator-visible state/label when isolated, refuse-vs-queue a move while isolated, the new `ServoStateResponse` field, the ADR the reboot-latch decision still wants — see R2's entry) **grounded in the docs, not in a prior session's paraphrase — requested by the operator, 24 Aug 2026.** Nothing from Session 6's D10 work is a prerequisite for it, but **Session 8 now runs first** (inserted 24 Aug 2026 by T14's triage, see row 8) so R2 designs against a settled `ServoStateResponse` shape — R2 itself is Session 9, not a direct continuation of this row. | R2: yes, for the operator-visible part |
| **7 — DONE, 24 Aug 2026** | **T14 closed** — all fourteen unslotted items given a real session (rows above and below) or an explicit reason they don't get one (T13, T15 — see their entries); Closed index gained D3/D27/D13 (moved to `CLOSED.md` but never indexed). **D32, D33, D34 closed the same session** — board-tested, verified (suite 223→226), app restarted and checked live. **D35 opened** (speed-step enforcement postponed, see Session 10) — a board measurement during D32's work found commanded and actual servo speed disagree by ~1.5-2x, so the planned fix was not shipped on an unverified unit-conversion assumption. | yes — used to verify D32/D33/D34 live and to bench-test D35's measurement |
| **8 — DONE, 25 Aug 2026** | All eight closed: **D24** (coverage gated at 99%, two unexercised guards covered), **D26** (sampler-thread leak found and fixed — segfault reproduced pre-fix at ~1-in-10 to 1-in-20, gone after; closed on evidence, see `CLOSED.md`), **D30** (UTC/local cutoff regression test), **T12** (`check_client_behaviour.js` promoted to a real check, folded into new `tools/verify.py`), **D8** (deploy without `.env` now fails loud), **D29** (`LOG_LEVEL` now real on the Logger461 stand-in), **D23** (`moving`/fault flags null on a failed read, amends ADR-0008), **D25** (a reported alarm survives the reading going unknown; recover disabled-with-reason, not hidden). `ServoStateResponse` shape is now settled for R2. Repo hygiene pass same session: stale soak artifacts and `FILE_REGISTRY.md` removed, `.gitignore` gaps closed. | no — board confirmation of D8/D23/D25 still outstanding, first thing to do when the board is next up |
| **9 — DONE (implementation), 25 Aug 2026** | **R2** — motor isolation. `/grilling` + `/operator-lens` passes ran first, both doc-grounded. Implemented on `feature/motor-isolation`, merged to `dev`. **Board verification still outstanding** — see R2's own entry for the full list (torque actually cutting, un-isolate not snapping to a stale goal, multi-turn tracking under a hand-turned shaft). `/twin-review` deliberately skipped this delivery, deferred to a later whole-app pass (see `T16`). | yes, for the board-verification items — next session up |
| **10 — opportunistic, any time after 7** | **D28** (MCU boot-time `mcu_log` notify race — needs a flash to fix or confirm) + **D35** (commanded vs. actual speed disagree by ~1.5-2x, found bench-testing D32 this session — needs `PRESENT_SPEED` register-level readback, not just wall-clock timing). D32 itself closed this session (24 Aug) — its speed-step-enforcement piece split into D35 rather than shipped on an unverified assumption. Low severity, no dependency on anything above; ride along with any session that already has the board up. **R2's board-verification list (row 9) is now a natural co-passenger too** — same "board is already up" opportunity, different item. | yes |

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
| **D3** | The C++ side has no logging | 8 August 2026 · Batch 2 |
| **D27** | `synthetic_operator.py` does not reproduce `app.js`'s concurrent poll timers | 8 August 2026 · Batch 2 |
| **D13** | Requests arriving faster than slots free up are refused | 8 August 2026 · ADR-0009 |
| **D4** | Connection drops after a few commands; requires a page refresh | 11 August 2026 · Session 3 (SSE) — full two-session soak saga kept whole in `CLOSED.md` |
| **D18** | A failed CSV export navigates the operator out of the application | 11 August 2026 |
| **D22** | The only export control is fixed at 24 hours | 11 August 2026 · R5's delivery path |
| **D31** | Telemetry export drops instantly with "controller busy" | 23 August 2026 · real cause was a client-side `ReferenceError`, not the Pydantic hypothesis — see `CLOSED.md` |
| **D10** | `logger.exception` swallows the exception; recurred as an unexplained sampler crash | 24 August 2026 · Session 6 · real cause was every read on the shared SQLite connection running unlocked, not a zero-table race — see `CLOSED.md` |
| **D32** | Speed field snaps to the angle's step grid, not its own; typed angle silently rewritten before send | 24 August 2026 · Session 7 (T14) · speed-step enforcement split into D35 rather than shipped unverified |
| **D33** | Recent Activity timestamps display in UTC, not local time | 24 August 2026 · Session 7 (T14) |
| **D34** | Angle displays truncate to 1 decimal, losing the 0.06° step | 24 August 2026 · Session 7 (T14) · widened from the move log to every angle readout |
| **T14** | Triage the unslotted items; audit backlog and doc hygiene deliberately | 24 August 2026 · Session 7 |
| **D24** | Two `InvalidReadingError` guards unexercised; docs claimed 100% coverage | 25 August 2026 · Session 8 |
| **D30** | `soak_report.py`'s UTC/local cutoff bug — regression test | 25 August 2026 · Session 8 |
| **T12** | `tools/check_client_behaviour.js` promoted to a real verification command | 25 August 2026 · Session 8 |
| **D8** | Deploy without `.env` must fail loud, not silently default to the simulator | 25 August 2026 · Session 8 |
| **D29** | `LOG_LEVEL` was inert on the Logger461 stand-in | 25 August 2026 · Session 8 |
| **D23** | `moving`/fault flags reported as measured on a failed read | 25 August 2026 · Session 8 |
| **D25** | An overload alarm disappeared once the reading went unknown | 25 August 2026 · Session 8 |
| **D26** | Suite failed once in ten runs — cause found (sampler thread leak), closed on evidence not proof; reopen fresh if it recurs | 25 August 2026 · Session 8 |

---

## Defects

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

**Related:** D32 (the postponed enforcement this measurement blocks).

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


## Tasks

### T13 — Distil the remaining documents
**Status:** open · **Severity:** medium · **Raised by:** the operator, 8 August 2026

Docs are re-ingested at the start of every session, so their length is a
recurring tax on the work. Started 8 August 2026: closed items moved to
`docs/CLOSED.md` and Batch 1's own entries cut, taking `BACKLOG.md` from 15,223
words to ~10,600.

**Not yet done.** The remaining bloat is in entries written before this rule
(`D4` and `D22`, both previously listed here, were moved to `docs/CLOSED.md`
whole on 23 August 2026 rather than distilled in place — relocation, not this
item's kind of work; `D13` was already closed and moved before this table was
last checked, and was never actually bloat in *this* file at all. Both classes
of drift removed from this table accordingly):

| | words |
|---|---|
| `R2` | 520 |
| `R5`'s "use case" section | 459 |
| `T11` | 425 |
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

### T15 — Code-level documentation reads as unprofessional and costs tokens
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
**Status:** open · **Raised by:** the operator, 25 August 2026, during R2

Two changes to `skills/twin-review/SKILL.md` (and its installed copy at
`~/.claude/skills/twin-review/`), decided but not yet made:

1. **A fifth lens, general correctness, composed by reference to
   `/code-review`** at a chosen effort level (medium by default) — the same
   composition pattern lens #2 already uses for `operator-lens` ("Load the
   operator-lens skill for the five questions"). The current four lenses
   (twin path, operator impact, relay/hardware safety, doc truth) are each
   specialised; none of them is a general bug hunt, so a plain logic error
   with no "twin" shape (wrong comparison, off-by-one, a leak with no mirror)
   can pass all four uncaught.
2. **Lens selection, not a fixed four (or five).** A small change that
   touches none of `sketch/`, no error path, no mirror gets no value from
   the relay-safety or twin-path lenses; forcing every run through all of
   them regardless of the diff wastes tokens on lenses with nothing to say.
   Should default to "everything relevant to what changed," not an
   unconditional fixed set.

**Deliberately deferred, together with actually running the enhanced skill**
— on the whole app, in one sitting, rather than piecemeal per feature. Includes
retroactively covering R2's `feature/motor-isolation` diff, which shipped
without a `twin-review` pass by explicit operator decision (see R2's entry).

**Also raised, not yet scoped:** folding this into `deliver`'s own pipeline
(`skills/deliver/SKILL.md`) rather than leaving it a manual on-demand step.

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
does it fit?* Measured on the board on 7 August 2026, at the original 1 row/s:

| | rate | one month | two months |
|---|---|---|---|
| Telemetry database | ~80 bytes/row at 1 row/s → ~6.9 MB/day | ~208 MB | ~416 MB |
| Log at DEBUG | ~180 bytes/line, ~24 lines/min/operator → ~6.3 MB/day | ~188 MB | ~376 MB |

Free space on the board: **2.6 GB**. So a two-month run at DEBUG lands near
800 MB — it fits, but nothing enforces it and nobody had written it down.

**Recomputed, 23 August 2026 — `sampler_interval_seconds` is now 0.5, not
1.0.** The telemetry-database row doubles with it (log row is operator-poll
driven, not sampler-driven, unaffected): ~160 bytes/s → **~13.8 MB/day**.
`telemetry_retention_days` also dropped 60 → 30 the same session, so the
database no longer grows past that window — it plateaus at roughly
**13.8 MB/day × 30 days ≈ 414 MB**, not the ~416 MB two-month figure above,
which was for the old rate and window and no longer applies. Not
re-measured on the board at the new rate — this is arithmetic from the
7 August figures, flagged as such.

**Retention, corrected.** Telemetry purges at 60 days
(`telemetry_retention_days`), so the database plateaus rather than growing
without limit. The **real Logger461 rotates**, so production logging is bounded
too. What is *not* bounded is the **stand-in** in `main.py`, which is what runs
on any board without the wheel installed — including this one. It opens the file
and appends forever.

**Provisional numbers from Session 2's soak, 8 August 2026 — treat with
caution, both runs were abnormal (D4 reopened):** 3-operator run (~22 min,
`LOG_LEVEL` was inert at the time (D29, since closed 25 August 2026 — the
stand-in now actually filters), so this measured the DEBUG rate regardless
of the configured setting; a board on INFO from here on should log less
than this, not re-measured): db 0.27 MB/hr → 196 MB/month, log 0.19 MB/hr →
137 MB/month, mcu log 0.10 MB/hr → 75 MB/month. Broadly in the range this
table already expected, but a run dominated by connection-rejection churn
is not a clean
baseline — re-measure once D4 is actually closed.

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

**Measured, 8 August 2026 — target not met at 3 operators, cause still open.**
`synthetic_operator.py` models each operator as 3 independent poll streams
(state, zeros, events), matching what `app.js` actually does per-tab, not
the "one connection per screen" assumption above. 3 operators = up to 9
concurrent streams against 6 slots: **1462 rejections in ~22 minutes**,
ending in a stall that needed a restart to clear. **1 operator = 3 streams,
comfortably under the ceiling: only 49 rejections and no oversubscription
signature** — but the same D4 stall still occurred twice and self-recovered.
So the socket ceiling explains the rejection *count*, but not the stall
itself, which reproduces even without oversubscription (see D4). **R1
cannot be closed by tuning `timeout_keep_alive` alone until D4's reopened
cause is understood** — a faster slot turnover does not fix a fault that
also happens with slots to spare. Still unverified: the USB-C/Q9 question
above, unchanged by tonight's runs (no on-site session was part of either).

---

### R2 — Motor isolation: cut drive power, keep sensors alive
**Scope:** in MVP · **Priority:** feature, not critical — must ship with the MVP
so that MVP testing exercises it. **Status: implemented, 25 August 2026, on
branch `feature/motor-isolation`.**

**`/twin-review` deliberately skipped this delivery, not blocking it** — the
operator's call, 25 August 2026: it runs later, on the whole app, once T16
(below) has enhanced the skill. Merge proceeds through the normal `/deliver`
pipeline without it this time.

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

**The mechanism already exists today, manually.** Two butterfly screws clamp a
3D-printed arch onto the shaft, operated by hand — R4 is the mechanical team
adding servos to drive those screws so it's software-controllable and
sensed. Motivation (operator, 25 Aug 2026, during R2's design): once the
physical lock holds position by friction, the primary servo's motor can rest
(isolated) instead of being held energised for months at a field site — the
point of **R2**'s isolation feature in the first place. R8 (emergency stop)
is expected to engage isolation and the physical lock together for an
instant stop.

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
**Scope:** in MVP · **Status:** mechanism, UX gaps and operator-requested richness all shipped, 23 August 2026 (Session 5) · one gap genuinely still open, see table below

Pull telemetry for an arbitrary time range and chart it for delivery. The
point is that the MVP must be **benchmarkable**: the receiving teams need to
see whether the servo actually handles what it is asked to handle.

**Shipped, 23 August 2026 — architecture note.** The 10 August decision
below (XLSX not CSV, native charts, one data product) still holds exactly
as reasoned. What changed is **who builds the file**: not the export
endpoint (`openpyxl` was the original example) but the **browser**,
client-side, in `app.js` — decided deliberately, not a fallback. The server
stays a dumb byte pump per ADR-0001: it streams the existing compact binary
format (`GET /api/v1/telemetry/binary`, gzip'd) and never has to hold or
transmit a built `.xlsx`, which would be a far larger payload crossing the
same ~11.5 KB/s Bridge link that already dominates every other timing
number in this project. See D31 for the board measurements this rests on.

An 11 August session wrote most of this once already (`app.js`'s
`generateExcelXlsxZip`) and it never actually worked — two functions it
called, `makeChartXml`/`makeDrawingXml`, were never written at all,
guaranteed `ReferenceError` on every attempt. Rebuilt 23 August against a
real generated reference workbook (verified with `XlsxWriter`, unzipped, the
actual chart XML schema copied from there, not guessed a second time from
documentation) — see D31.

**Format decided 10 August 2026 (operator + team lead), revised same day.**
Export format is **XLSX (Excel), not CSV** — team lead's correction: a CSV
cannot carry a chart, and the point of this item is that it must. Charts are
native Excel chart objects, not rendered images — this still avoids the
original matplotlib/sampler-contention risk (D22's stated concern), because
writing chart-definition objects into the workbook is not rasterising a
plot. The data sheet is the raw form; the chart objects read from it
directly inside the same file, so there is still one data product, not two.

The standalone CSV export button was retired (operator decision, predates
this session) once XLSX existed as the one export artifact.

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

- **Every field gets the same chart treatment — position, torque, temperature,
  voltage, current.** No field is singled out over another. **Revised 10
  August 2026** (operator): the original text elevated torque above the
  others; corrected — the standard is "give the full picture," applied
  uniformly, and any field gets extra numeric detail (e.g. peaks/sustained
  figures) if it genuinely needs it to be read correctly, not because of
  which field it is. `torque_kgcm` is already sampled, stored
  (`sqlite_telemetry_repository.py:28`) and in the CSV columns
  (`telemetry_service.py:17`), same as the rest — the data layer needs
  nothing regardless of chart treatment.
- **Nobody is watching while it runs.** Anything not recorded is lost for good.
  Before that run, confirm the sampler survives days rather than minutes (D10's
  unexplained exception, T9's growth rates, and the stand-in logger in `main.py`
  that appends forever without rotation).
- **The window is days, not a session.** See D22 — the only export control in the
  UI is fixed at 24 hours, so after a five-day run an operator can retrieve the
  last day of it and no more.

**30-day telemetry retention (`telemetry_retention_days`, lowered from 60
this session) is the real upper bound on a single export now** — a full
30-day/0.5s-interval pull is 5.18M rows, board-tested at that exact scale
(see below), not just assumed to fit.

**Acceptance, made concrete — what actually shipped:**

- Given a start and end timestamp, the workbook carries every field with
  the same treatment: position, torque, temperature, voltage, current,
  sampler interval. Peak/sustained figures are computed once, from the
  full-resolution dataset, on the **Overview** sheet — never from a
  downsampled series.
- **Every field gets a native Excel line chart**, built from a hidden
  `ChartData` sheet whose cells are **live formulas** pointing back at the
  exact day-sheet cell each downsampled point came from (min-max binning,
  ≤2000 points/chart — keeps spikes/faults visible, not smoothed away).
  Editing a day sheet updates the chart. Every formula cell also carries a
  cached value (matching real Excel output, confirmed against a generated
  reference file) so a renderer that doesn't recalculate on open —
  OnlyOffice, some LibreOffice paths — still shows something correct.
- **One worksheet per calendar day** for the raw data, full resolution, no
  downsampling, no row cap — bounds every sheet far under Excel's
  1,048,576-row ceiling regardless of range length. This is also what
  closed the old silent-truncation defect: `export_max_rows` no longer
  needs to be a practical limit (raised 50,000 → 10,000,000, a defensive
  ceiling only — see `config.py`).
- **Must work over a multi-day window.** Board-tested at the real worst
  case: 30 days / 5.18M rows completes in ~73s and produces a 193MB file
  (client-side, in-browser) — down from an unoptimized first pass that
  either exhausted a 4GB heap (15 days) or produced a 349–475MB file,
  fixed by two changes: the zip writer now actually deflates its contents
  (it shipped uncompressed at first — a real gap, caught by testing at
  real scale, not assumed fixed because it "worked" at 2 days), and each
  day's XML is built, compressed and discarded one at a time instead of
  holding the whole range in memory at once. Further shrunk 45% (349MB →
  193MB) by dropping a redundant duplicate timestamp column (kept only a
  native Excel date, not a spelled-out text copy too), packing the 8
  boolean/fault columns into one bitmask byte (same encoding
  `export_binary_stream` already uses — one fact, one place), and rounding
  values to the 2 decimals the sensor data actually supports.
- Runs on the board *or* off it against a pulled database — generation is
  entirely client-side JavaScript, needs only the binary stream, never the
  servo attached.
- The standalone CSV export was retired (see above) — XLSX is the one
  export artifact now, its data sheets serving the role CSV used to.
- Chart XML verified against a real `XlsxWriter`-generated reference file,
  not written from documentation alone — the previous attempt's
  `makeChartXml`/`makeDrawingXml` were never implemented, see D31.

**A real corruption bug shipped with the first "done" claim, found by the
operator opening a real export in OnlyOffice, fixed the same session.**
The central directory's general-purpose-flag and compression-method
fields were at swapped byte offsets — `unzip -t` doesn't catch this,
`zipfile`/`openpyxl`/OnlyOffice do, and did. Fixed and re-verified against
the exact real board data with `zipfile.testzip()` and
`openpyxl.load_workbook()`, not just `unzip -t` again. **The lesson, not
just the fix: a file "opening" in one lenient tool is not proof it's
correct — validate with the strictest available reader, and test cross-app
compatibility for real, not by inspection.**

**Shipped, 23 August 2026 (Session 5) — the operator redirected this session
live, mid-plan, to two new fields plus the whole UX gap table at once.**
Decisions below are scoped to this one item, so recorded here rather than
as a standalone ADR.

- **Target angle and servo (pre-ratio) angle, end to end** — captured
  (`ServoStateStore.set_target`/`_to_servo_deg`, `servo_state.py`), persisted
  (`telemetry.target_deg`, nullable, idempotent migration), carried over the
  binary contract (header gains the gear ratio as a float so the client
  derives servo angle rather than re-declaring the constant — the exact
  duplication that caused D9), shown live (`.subline` under the big
  readout: target, signed Δ, servo angle, plus a target marker on the
  travel bar — the deviation is spatial, not arithmetic) and in the export
  (own columns, own line chart, an overlay chart plotting measured against
  target on one axis). Stop marks the target **stale, not cleared** — kept
  on screen dimmed, because "asked for 45, stopped at 27" is the reading
  the feature exists for.
- **Angle-correlated charts** — torque/voltage/current/temperature each
  plotted against **output angle** (mechanical team's request), line style,
  angle-sorted downsample. Real OOXML type is `c:scatterChart` with
  `scatterStyle="lineMarker"` (a category axis cannot carry a genuinely
  numeric, unevenly-spaced axis) — verified against an XlsxWriter reference
  before writing it by hand, same rule as everything else here.
- **Typed chart-range selector** — two date cells on Overview
  (`RANGE_FROM_CELL`/`RANGE_TO_CELL`); every `ChartData` formula gates on
  them (`IF(AND(...),value,NA())`, `dispBlanksAs="gap"`) rather than a
  per-day picker. Confirmed live against real board data: editing the
  dates narrows every chart.
- **Richer Overview**: a per-day table (samples, moving %, angle travelled,
  peak torque/current, temp/voltage range, stalls) below the chart grid,
  derived from data already grouped by day — no schema change.
- **Decoded flags** — the bitmask column is gone; `Moving`/`Locked` are
  their own columns, `Faults` is a decoded name list. Closes the old
  "flags too compact" complaint by construction rather than tuning the
  packing.
- **All day-sheet columns sized explicitly** (were unset entirely —
  `makeDaySheetXml` had no `<cols>` at all, not just a narrow date column).
- **LCARS styling** — real palette hex values from `style.css`, not
  re-guessed: tangerine header/title band, panel2 row banding (row-level
  `s=`+`customFormat="1"`, confirmed to render with no per-cell stamps —
  matters at 5.18M rows), alarm-bg fault rows, Bahnschrift SemiCondensed/
  Consolas fonts matching the app's own choices.

**Desired angle's earlier "defer to a later session" reasoning (retroactive
NULLs on existing rows) turned out not to be the operator's actual ask** —
they wanted it captured going forward and shown live too, not just charted
retroactively. Overridden on request; the retroactive-NULL fact is still
true and just doesn't matter for what was actually wanted.

**Five more defects found live on the real board, same session, fixed
before calling it done — the export's own standing lesson (found by
opening a real file, not assumed) held again:**

1. Travel bar scaled position as `deg/360` on a mechanism that travels
   −90..+90 — every negative angle rendered as 0%, indistinguishable from
   the datum. Found designing the target marker; fixed by sending the
   reachable range in the state response instead of a second hardcoded
   copy of it in `app.js`.
2. Binary format's documented types disagreed with the actual struct
   (`voltage_v`/`current_a` declared `H` in the comment and read as
   `getUint16` client-side, packed as signed `h` server-side). Harmless at
   real values; fixed since those exact lines were already being touched.
3. **A genuine regression, caught and reverted the same session**: `c:dateAx`
   with automatic tick spacing rendered cleanly against an isolated
   reference (500 evenly-spaced points) but produced an illegible
   per-second label smear against real, denser board data — worse than
   the original crowding it was meant to fix. Reverted to `c:catAx` with
   an explicitly computed `tickLblSkip` (we already know the point count;
   no reason to trust a renderer's heuristic on data it hadn't been tried
   against) plus restored diagonal label rotation, both re-verified
   against real board exports before shipping.
4. Overview's title band and its own value column (the range-selector
   dates) were both too narrow for their own content — same class of gap
   this whole item exists to close, just not caught until a real render.
5. The target/Δ/servo sub-line had uneven spacing (6px between a label
   and its own value, 18px between items) — visually lopsided around Δ
   specifically. Flattened to one uniform gap.

**Known gap, still genuinely open:**

| Gap | What was seen | What's needed |
|---|---|---|
| No narrative of *what happened* (moves, refusals, fault transitions over time) | R5's stated use case is reconstructing an unattended run; a table of instantaneous values requires the reader to re-derive events by eye. Root cause: the only place holding that narrative, `EventService` (`core/events.py`), is an **in-memory ring buffer** that does not survive past the SSE session it feeds live — there is nothing left to export by the time an operator requests a range | Needs a persisted move/event history — a real schema item, own session, not a same-session `app.js` patch |

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
