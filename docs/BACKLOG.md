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
| **2 — IN PROGRESS, 8 + 10 Aug 2026** | **D4 still open.** The soak found a reopened D4 (8 Aug); two fixes tried and reverted 10 Aug — see below. **Next: SSE (Session 3), not another relay tweak.** | yes |
| **3** | **SSE first** (collapse 3 poll connections/operator to 1 — see D4), **then Batch 4** — motor isolation, and the export as XLSX with embedded charts | yes, throughout |

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

### D29 — `LOG_LEVEL` is inert: the Logger461 stand-in logs everything regardless
**Status:** open · **Severity:** medium · **Found prepping Session 2's soak,
8 August 2026**

The real `Logger461` wheel is not installed on this board — `main.py`'s
fallback (`_ensure_logger461()`) is active, the same gap T9 already named for
rotation. Its stand-in's `setup(**kwargs)` reads only `kwargs.get("file")`;
`level` and `serialize` are accepted and silently discarded. Every level
method (`debug()` through `critical()`) calls `_emit()` unconditionally —
there is no level filter anywhere in the stand-in.

**So `LOG_LEVEL` has never done anything on this board.** Confirmed directly:
`.env` carried a leftover `DEBUG` from the W1 board run; changing it to
`INFO` and restarting the app still produced `relay.conn.open`/
`relay.conn.close` DEBUG lines immediately after boot.

**Revises two existing entries:**
- **D5's closing claim — "at INFO the lines are already silent" — is false
  on this board.** True of the real Logger461/loguru; not true of the
  stand-in actually running.
- **T9's storage table should treat the DEBUG rate as the operative number,
  not a worst case**, until the real wheel is installed (T2, air-gapped).

**Acceptance:** the stand-in's `_emit` gates on a level ordering matching the
real library, or the gap is stated plainly in D5/T9 rather than assumed.
Cheap either way — found, not designed around.

**Related:** D5, T9, T2.

---

### D30 — `soak_report.py` compared a local cutoff string against UTC logs,
### and reported a catastrophic run as clean
**Status:** code fixed 8 August 2026 · **regression test still needed**
· **Severity:** high · **Found running Session 2's soak**

Both JSONL logs are written in **UTC** (`mcu_log.py` uses `time.gmtime()`
explicitly; the Linux-side stand-in's `datetime.now()` is also UTC because
the container's system clock is UTC — confirmed against `date -u`).
`parse_since()` correctly converts a **local**-time `--since` string to an
absolute unix timestamp. The bug was one step later: `report_log()` and
`report_mcu_log()` each rebuilt a cutoff *string* from that timestamp with
`datetime.fromtimestamp(since).isoformat()` — local again — then compared
it directly against the logs' UTC-stamped strings. A 3-hour local/UTC gap
(IDT) meant every real record from the run sorted as "before the cutoff."

First report after the 3-operator soak (1462 MCU rejections, 11+ minutes of
continuous `servo_read` timeouts) printed:
```
VERDICT: clean - no stall signature, no fabricated positions, no errors.
```
**The D24 species again — a number nobody checked, reporting the opposite
of what happened** — on the one tool whose entire job is catching this.

**Fixed:** both call sites now use a new `_utc_cutoff()` helper
(`datetime.fromtimestamp(since, tz=UTC).replace(tzinfo=None).isoformat()`)
instead of the local reformat. `--since` itself is still typed in the
operator's own local time, matching what `synthetic_operator.py` itself
prints — that half was never the bug. Re-running both of tonight's soaks
with the fix produced the real numbers now in D4 and R1.

**Not yet done:** a regression test — a record just outside a
local-timezone cutoff but inside the UTC one, asserting it's still counted.

**Related:** D24, D3 (introduced the MCU log this bug hides).

---

### D31 — Telemetry export drops instantly on the frontend with "controller busy"
**Status:** CLOSED · 23 August 2026 · **Severity:** high · **Found 11 August 2026**

The operator reported that downloading a 24-hour telemetry export (via the new binary stream route) failed instantly with the toast: "the controller is busy or did not answer — wait a moment and try again". The download progress bar stayed at 0%.

**Fixed 11 August 2026: the 22-second SQLite timeout**, unchanged from the original entry — a flat `COUNT(*)` replaced a sorting subquery, 22s → 0.01s.

**The 16-second-Pydantic-packing hypothesis was wrong, board-measured, 23 August 2026.** Reproduced the export live on the board at full scale (42,152–45,990 rows) with Pydantic *still in the loop*, unchanged: server-side packing took 4.4–11s, never the bottleneck. The actual "controller busy" toast traced to a real, unrelated client-side bug — `app.js`'s `generateExcelXlsxZip()` called two functions, `makeChartXml`/`makeDrawingXml`, that were never written (`ReferenceError`, 100% reproducible, confirmed by replaying the exact captured payload through the real code). `sayError()`'s generic "no HTTP status = unreachable" fallback misreported that client-side crash as a controller problem.

**The real transport bottleneck, found the same session**: not Pydantic, not the relay chunk size alone — **gzip compression was never enabled for actual export requests** (`GZipMiddleware` is registered and correct, but nothing had exercised it at scale). Enabling it: **5.3x faster** (120.2s → 22.8s for a 15-day/45,990-row export, board-measured), because the real fixed cost is the Bridge's ~11.5 KB/s physical link (LPUART1 @ 115200 baud — see `RELAY_NOTES.md` §5), and gzip cuts the bytes that have to cross it by ~81%. Pydantic bypass was never implemented and is no longer worth pursuing — it was optimizing a cost that was never the dominant one.

**Closed by**: `relay_chunk_bytes` 128→224 (D6/RELAY_NOTES §5), gzip enabled on the export path, and the client-side XLSX generator rebuilt correctly (R5) — `makeChartXml`/`makeDrawingXml` now exist, verified against a real generated reference file rather than guessed.

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
**Status:** half done — **the logging is fixed; the fault itself named itself,
23 August 2026** · **Severity:** medium · **Found by:** a live board run

**Fixed 7 August 2026.** The cause was the Logger461 stand-in in `main.py`:
its `exception()` was a straight copy of `error()`, and attaching the exception
is the entire difference between the two. It now records the exception type, its
message and the traceback, and the console prints the traceback under the record
instead of flattening it into the single-line format.

**The test stub in `conftest.py` had the identical gap**, so a test asserting on
a cause would have passed against a stub that dropped it exactly as production
did. Both fixed together — this is the twin-path pattern for the fourth time in
this repository.

**It happened again, 23 August 2026, twice (13:02:22, 13:39:55) — this time with
a full trace, exactly as this entry predicted:**

```
TypeError: unsupported operand type(s) for -: 'int' and 'NoneType'
  servo_state.py:276  servo_deg = ((raw_counts - self._baseline_counts(active))
  servo_state.py:263  _active_counts() -> self._baseline_counts(self._zeros.get_active())
```

`_baseline_counts()` is typed `-> int` and both its branches (`active.raw_counts`
or `self._counts_per_turn // 2`) return one — the type hint is not a lie, so
`active.raw_counts` itself was `None` at the moment of the call. **Checked the
live `zeros` table: the active zero ("datum") has `raw_counts=2046`, a valid
int, not null.** So this is not corrupted stored data — it is a transient
in-memory state, most likely a race around `ZeroStore.get_active()` returning
a reference mid-mutation (a zero being changed/replaced) rather than a stable
snapshot. Not investigated further this session — the sampler skips the sample
and continues, which is the correct degrade, but every skip is a gap in
exactly the data R5's export exists to deliver.

**Still open: the actual fault, now with a real lead instead of no evidence.**
Next step is reading `ZeroStore`'s active-zero mutation path for a window where
a `ZeroReference` can be read with a still-unset `raw_counts`, not reproducing
blind.

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
`LOG_LEVEL` inert per D29 so this is effectively the DEBUG rate regardless
of setting): db 0.27 MB/hr → 196 MB/month, log 0.19 MB/hr → 137 MB/month,
mcu log 0.10 MB/hr → 75 MB/month. Broadly in the range this table already
expected, but a run dominated by connection-rejection churn is not a clean
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
**Scope:** in MVP · **Status:** done · 23 August 2026

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
