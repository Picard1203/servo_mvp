# Project state

Where the project is right now. Updated as reality changes.

**This file does not list open work** — that is `BACKLOG.md`. It does not explain
decisions — that is `docs/adr/`. It does not define terms — that is `CONTEXT.md`.

---

## What this is

Arduino UNO Q + Waveshare ST3215 serial-bus servo. A FastAPI backend and an
LCARS-themed web UI served from the board: operators open
`http://<board-ip>:8000`, several at once, nothing installed on their machines.

The network path runs through the MCU, not the Linux side — production boards
have the WiFi/Bluetooth chip desoldered (ADR-0001).

## Where it is heading

A **delivered MVP**. Other teams will judge it and decide whether to procure a
full project. So the bar is not "feature complete" — it is **stable, benchmarkable
and conventionally built**.

Post-MVP, additional servos will be added as mechanical restraint (backlog R4).

## Status

Everything exists — backend, UI, sketch, tests — and `tools/verify.py`
(one command, `CLAUDE.md` §3) reports ALL GREEN:

```
244 Python tests, coverage of app/ gated at 99% (99.45% measured, D24)
194 native sketch checks, -Wall -Wextra -Wpedantic -Werror
Bridge contract checker: both sides agree
75 client-behaviour assertions (T12, promoted to a real check 25 Aug 2026)
```

(as of Session 8, 25 August 2026 — `tools/verify.py` is the source of truth
going forward, not this snapshot; run it rather than trust this number)

**26 August 2026 — Session 13: `twin-review` restructured (T16), not just extended, and `ruff` added (T19).** T16 went beyond its two scoped changes once it was clear the skill was diff-only and would not survive session 14's whole-app pass unchanged: a fifth lens (general correctness, composed via `code-review`), a diff/inventory scope split with directory chunking (never hand a reviewer the whole codebase), a `docs/REVIEW_FINDINGS.md` output contract for session 15 (which has no memory of the run), and lens 4 itself fixed — it referenced three verification numbers, `verify.py` runs four now. Cost control was deliberately moved from output-trimming ("cap yourself") to input-narrowing, checked against current practice first: each lens now names a concrete tool to build its candidate list before any reviewer reads source. T19 (raised the same session, not originally scoped): `ruff` wired in as that narrowing tool for the backend chunk — `python/ruff.toml`, adapted from the operator's own standard (found at `~/Coding Projects/Krusty-Crab/pyproject.toml`, unreachable on the air-gapped network) with two real corrections (Google docstring convention set explicitly; `UP` deliberately excluded, since it would fight `CONVENTIONS.md`'s `Optional[X]` rule). Advisory only — not part of `verify.py`'s gate; baseline 50 findings, all plausible. R1's stale "blocked on D4" note fixed — D4 closed 11 August; R1 is unmeasured against the current architecture, not blocked, pending session 16's re-measurement. `tools/verify.py`: 293/99.46%/194/96, unchanged.

**Session 3 landed 11 August 2026** — SSE migration complete. Collapsed 3 polling connections/operator to 1 persistent SSE stream (`GET /api/v1/stream`). Closed D4 (3-operator 10-min soak clean, 0 socket drops, 1,955 requests handled, 0 reconnects). Re-applied D29 async-def fix across 13 FastAPI handlers.

**23 August 2026 — R5 (XLSX export) rebuilt, and D31 closed for the real reason.** The 11 August attempt (Batch 4) never worked at all — `app.js` called two chart-building functions that were never written, guaranteed `ReferenceError` on every export, misreported by the UI as "controller busy." The 16-second-Pydantic hypothesis in the old D31 entry was wrong (board-measured: Pydantic was never the bottleneck). Rebuilt: XLSX generation is client-side (by design — the browser is stronger than the board, and the Bridge link is the real constraint, not the browser), one worksheet per day, native charts via a hidden formula-fed sheet, min-max downsampling for charts only. The real transport fix was enabling gzip on the export (5.3x faster, board-measured) plus raising `relay_chunk_bytes` 128→224 (see D6/`RELAY_NOTES.md` §5 — the old "256 vs 128" dispute is closed with a cause: 256 overflows the vendored Bridge library's own 256-byte RPC message buffer). Also this session: sampler cadence 1.0s→0.5s, retention 60d→30d (new requirement), and the display's SSE push cadence — previously a second, hardcoded, undocumented "1.0s" living beside the real setting — now reads the same config value.

**A real corruption bug shipped with the first "done" claim, same session.** The rebuilt export's zip central directory had two fields at swapped byte offsets — every generated `.xlsx` opened fine in lenient tools (`unzip -t`) but was rejected outright by strict ones (Python's `zipfile`, `openpyxl`) and, live, by the operator's own OnlyOffice. Found because the operator actually opened a real export rather than trusting "board-validated," fixed the same session, re-verified with the strict tools this time. **R5's mechanism is now genuinely validated cross-app — but real UX gaps remain (unreadable timestamp column, no actual day/range selector despite the interactivity mechanism existing, an over-compressed flags column, no LCARS styling) and are deferred to next session, see BACKLOG.md R5's gap table.**

**23 August 2026 — Session 5 closed that whole gap table, plus two new fields the operator asked for live, mid-session: target angle and servo (pre-ratio) angle, both captured, persisted, and shown in the UI's own target marker/Δ readout and in the export.** Also shipped: angle-correlated charts (mechanical team's request — a genuine `c:scatterChart`, verified against a reference, because a category axis cannot carry a real numeric angle axis), a typed chart-range selector confirmed live to actually narrow the charts, decoded flags, full column widths, LCARS styling, and a per-day summary table. One real regression happened and was caught the same session: an automatic date-axis tick spacing that looked fine against synthetic test data produced an illegible label smear against real board data — reverted to an explicitly computed tick interval, re-verified live. R5's remaining gap (no persisted move/event narrative) is now the only open row in its table. Full detail in `BACKLOG.md`'s R5 entry — this is the distilled version.

**24 August 2026 — Session 6, first half: D10 closed for the real reason.** The prior writeup's theory (a race on the active zero being edited) didn't survive a check of the actual logs — no zero write happened near either crash, and the schema rules out a stored `NULL`. The real cause: `Database` shares one SQLite connection across every thread and only serialized writes, not reads; reproduced with a stress test that broke the *unlocked reads* using nothing but ordinary telemetry writes, then confirmed the fix (every statement, not just writes, through the same lock) holds under 185k+ concurrent reads. Full record, including the twin-path sweep that found the same gap in four more places, is in `CLOSED.md`.

**25 August 2026 — Session 8: all eight items closed** (D24, D26, D30, T12, D8, D29, D23, D25) **— `ServoStateResponse` is now the settled shape R2 designs against.** `tools/verify.py` replaces the three-plus-one separate verification commands with one call, gated on a checked-in baseline instead of a number quoted in prose (D24's own lesson, applied to itself). The real finding of the session: chasing an unrelated coverage warning surfaced that `TelemetryService`'s sampler thread had no stop mechanism at all, and closing a shared database connection while one of these leaked threads was mid-statement on it could segfault the interpreter outright — very likely D26's actual mechanism (reproduced the segfault at the original's rate pre-fix, gone after), closed on that evidence rather than left open indefinitely. D8 and D29 close two silent-default bugs of the same species (a setting that looks configured and does nothing): the board can no longer boot into the simulator by accident, and `LOG_LEVEL` is now real on the Logger461 stand-in — both confirmed live on the board, not just in tests. D23 nulls `moving` and the six fault flags on a failed read (amends ADR-0008); D25 keeps a reported alarm visible through the reading going unknown, with recover disabled-and-explained rather than hidden. Repo hygiene pass same session: stale soak artifacts and a pre-git-era file registry removed, `.gitignore` gaps closed.

**26 August 2026 — Session 11: T15 closed (both halves), and `BACKLOG.md` restructured into an index.** Q10 answered: docstring summaries and typed `Args:`/`Returns:`/`Raises:`/`Attributes:` blocks stay, the explanatory paragraph and every inline comment move to `docs/` when not already written there. Two Antigravity runs against exact prompts (`docs/handoff/`), each followed by a full manual diff review rather than trusting the run's own completeness claim — the standing lesson from this session, now written into the prompts themselves. T15a (`python/app/`) needed real correction: real content silently dropped in several files, most seriously `isolation_service.py`'s torque-inversion fix comment and `servo_state.py`'s `_baseline_counts()` (the flagship D9 example this project's own docs already cited); restored to `docs/DESIGN_NOTES.md`, with the two safety-critical cases kept as one-line inline pointers. `python/static/app.js` was reverted whole — its diff was pure comment removal with zero other contribution, and `CONVENTIONS.md` has no JS section to strip against; that becomes **T18**. T15b (`sketch/src/`) held up far better: most of what it removed was already documented in `skills/uno-q-st3215/SKILL.md`/`RELAY_NOTES.md`, confirming that reference file is doing its job; real gaps were narrower (a few deleted doc-comment summaries, the servo payload-format table, minor provenance facts). T1 closed alongside T15a. `BACKLOG.md` itself split from 1,406 lines into a ~150-line index plus `docs/backlog/{D,R,T}.md`, read only for the item being worked — the same context-cost reasoning driving T15. New backlog item **T18** (front-end conventions, found while scoping T15). `tools/verify.py`: 293/194/96, unchanged both runs.

**26 August 2026 — Session 10: R2's board verification found two real bugs, both fixed and confirmed at the register level; R2 is now CLOSED.** `IsolationService._reconcile()` had the boolean backwards — passed isolated-intent straight into `set_torque()`, whose contract means the opposite (restore torque); fixed by negating it. `ServoController.cpp` checked the wrong failure sentinel on every torque and move write (`Begin()`, `SetTorque()`, `Move()`) — `EnableTorque`/`WritePosEx` return the SCServo library's own Ack() convention (0 fail/1 success), never -1, so a write the servo never acknowledged was silently reported as a success; fixed `!= -1` → `!= 0`. Found via a new diagnostic-only Bridge command (`servo_read_torque`) that reads register 0x28 back directly, independent of the write's own ack — added specifically because the write ack alone had turned out not to be trustworthy. Verified live, repeatably, in both directions, including through an unplanned mid-session board restart that also confirmed ADR-0010's boot re-apply. A small hand-felt nudge test (roughly 0.1°, the most the current bare-servo bench allows) corroborated the same result physically. Suite 283→293, client-behaviour checks 91→96. Three smaller UI/refusal gaps closed in the same delivery on `feature/motor-isolation-fixes`: a LOCKED state added to the movechip, the `isoHint` countdown scoped to when it's actually live, and a combined `locked_isolated` refusal so a servo that is both doesn't hide one reason behind the other. **T17 opened**: the full-range, multi-turn-under-load scenario still needs an actual mechanical rig on the bench, which does not exist yet.

**25 August 2026 — Session 9: R2 (motor isolation) implemented, on branch `feature/motor-isolation`.** Design settled first by a doc-grounded `/grilling` pass plus an `operator-lens` pass, both grounded in the actual code rather than a prior session's paraphrase — see `BACKLOG.md`'s R2 entry and `docs/adr/0010-motor-isolation-state-survives-a-reboot.md`. Built as one reconciler (`IsolationService`), not three features: boot re-apply, the idle-timeout auto-isolate backup, and retry-after-a-failed-write all converge acknowledged hardware state on persisted operator intent, and `isolated` is only ever reported True once the servo has acknowledged the write — reporting it on intent alone would be a false safety claim. New: an `app_state` table (the project's first persisted-across-reboot operator intent — nothing needed this before), a `servo_set_torque` Bridge command using the SDK's `EnableTorque` helper (never a raw register write, since 0x28 also means "re-centre" at value 128), and the binary telemetry format's spare bit (`target_valid_flags` bit1) rather than a struct-widening change. Suite 244→283, client-behaviour checks 75→91, native checks unchanged (the torque command is not natively testable — `ServoController`/`ServoBus` need `Arduino.h`). **`/twin-review` deliberately skipped this delivery** (operator's call, token budget) — runs later on the whole app, alongside `T16`'s planned enhancement of the skill itself. **Board verification happened 26 August (Session 10) and found two real bugs along the way — R2 is now CLOSED, see `CLOSED.md` and the entry immediately below.**

**24 August 2026 — Session 7: T14 (the maintenance triage) closed, and three operator-found UI defects closed with it, ahead of R2 rather than after — the operator's call, inverting the order the docs had planned.** Every previously-unslotted backlog item now has a real session or a stated reason it doesn't (see `BACKLOG.md`'s START HERE table); the Closed index gained three items it had silently dropped (D3, D27, D13). **D32, D33, D34 closed same-session, board-tested and board-verified** (app restarted, changes checked live): the speed nudge no longer snaps to the angle's step grid, a typed angle that isn't a clean 0.06° multiple is refused with the backend's own message instead of being silently rewritten, Recent Activity timestamps read correctly in local time, and every angle-facing display now shows 2 decimals instead of 1 (the backend already computed that precision — the loss was purely in formatting). **D35 opened, not closed**: bench-testing D32's originally-planned speed-step enforcement, a live timed move measured the servo running at roughly 1.5-2x the commanded speed. Ruled out cheaply: the Python-side position/speed conversions share the same stored constants and cannot disagree with each other; the firmware has a second speed-conversion function but it is dead code, never called from the live move path. Not yet ruled out — the operator's own suspicion — is that the servo's `GoalSpeed` register does not actually share position's encoder-count unit the way the structural evidence (shared register block, matching official Feetech library layout) suggested; the belt ratio (1.4667) and its square (2.15) both sit inside the measured range. The planned speed-step enforcement was pulled rather than shipped on that unverified assumption. **Session 8 is next, not R2** — one batch of eight smaller items (D24, D26, D30, T12, D8, D29, D23, D25), deliberately ending with D23+D25 so R2 designs against a settled `ServoStateResponse` shape instead of one about to move under it. **R2 (motor isolation) is Session 9**, after that — see `BACKLOG.md`'s START HERE table; the `/grilling` pass on its open design questions is queued first and can run as a fresh session.

**Batch 2 landed the same day** — D3, D13 closed, desk work only (see "Known
gaps" below: the sketch side of D3 has never been compiled or flashed). It
raised D27.

**It has now been run on real hardware, driving the real servo** (7 August 2026,
backlog T8). That run changed the picture more than any amount of reading could
have.

**Closed by it:** D1, D2, D9, and the cause of D4. **Opened by it:** D10, D11,
D12 — none of which anyone had thought to look for.

**The system is materially calmer but not yet stable.** What the run proved, in
numbers, before and after the W5500 fix:

| | before | after |
|---|---|---|
| Sampler stalls in the 10–12 s band | 3 | 0 |
| Longest sampler gap | 11.00 s | 2.00 s |
| Fabricated positions written to the database | 7 | 0 |
| Bridge timeouts logged (`servo.bridge.error`) | 3 | 0 |
| Fabricated positions logged as such | not recorded at all | 0 to record |

Coverage this high still means every line ran, not that every assumption was
questioned. It did not prevent the six defects in `AUDIT.md`, and it did not
prevent D9 — where the correct rule and its violation sat twelve lines apart in
one file, both covered, both green.

**And the figure was not what the documents said.** It is 99%; seven documents
quoted 100% because nothing ran coverage (backlog **D24**). The two uncovered
statements are the `InvalidReadingError` guards in `ZeroService.capture()` and
`ServoStateStore.read_counts()` — one of them the exact line D2 was filed about.
The guard went in; its test did not.

**10 August 2026 — Session 2 continued, D4 still open.** The soak's original
mutex fix does not explain the stall; two candidate fixes were built,
measured, and **both reverted** — see backlog D4 for the numbers. The
session's one durable finding: the relay's 6-socket ceiling is a property
of the whole Wiznet chip family (W5500 and its successor W6100 both cap at
8 hardware sockets) — a shield swap cannot raise it. The real lever is that
each operator's browser holds **3** persistent connections (state/zeros/
events polling), not 1, so 3 operators structurally want 9 sockets against
a hard 6. **Decided: replace polling with one SSE stream per operator**,
next session, before any further relay changes. Code is reverted to the
last commit; the board was stopped, not left running. See `BACKLOG.md`
"Session 2" and "Session 3" for the full sequence and the plan.

## The cut line

**What ships, what slips, what does not go.** Set 8 August 2026. This is the
scope statement the project did not have — `BACKLOG.md` said what the work *is*,
in what order, and nothing said what happens when there is not time for all of
it. Scaling down is a decision to be taken deliberately, in this table, not by
running out of week.

Batch numbers refer to the ordering in `BACKLOG.md`.

### Must ship — no handover without these

| | Why it is non-negotiable |
|---|---|
| **D13 decided** — **done** 8 Aug 2026, **ADR-0009** (D14, D15 also done) | "Press it twice" is what a procurement audience remembers. Both the operator halves and the ceiling decision are closed; the real lever stays unmeasured until Session 2 |
| **D4 closed** | Reopened by Session 2's soak, deepened 10 Aug — not a chip-mutex race, now believed to be socket-count pressure; SSE was the next attempt and closed it for real, 11 Aug — see `docs/CLOSED.md` D4 |
| **R1 answered** | The one capacity number anyone will ask for |
| **R2** motor isolation | Scoped in MVP explicitly *so MVP testing exercises it* |
| **R5** metrics export, **torque included** | Without it there is nothing to judge, and R6 cannot be written |
| **D22** export over any range | The benchmark is a multi-day unattended run at the receiving team's site; a 24-hour button cannot retrieve it |
| **R6** "stable" as numbers | The delivery is judged against it |
| **D8** made impossible to get wrong | A silent fallback to the simulator at handover is the worst failure available |
| **D16** — **done** 8 Aug 2026 | The operator must not be shown 0.00 V as a measurement. Schema and client both; the API half for the fault flags is now **D23** |
| **T10** the recovery runbook | The receiving team runs it unattended for days. They must know what to do when it misbehaves, and the site is three hours away |
| **T11** the operations manual | Nothing in the repo tells anyone how to *operate* this. Every document is written for whoever is building it |
| **Docs true** | Cheap, and the project's own standard |

### Should ship — cut only under real pressure, and say so out loud

**D6** (first paint measured), **T3** (on-target run), **T5** (diagrams),
**D7** (operator screen — *blocked on Q1*), **D12**, **D17**, **D18**, **T9**
(storage confirmed over hours), **D5**.

Cutting any of these means handing over something that works but cannot be
explained, measured or diagnosed by the people receiving it. That is a real cost
— it is simply not a reason to miss a date.

### Will not ship — decided, not forgotten

**T1, T6, T7** — the mechanical conventions pass. The MVP was written "dirty" on
purpose. It is the right work and it is invisible to the people judging this;
if it collides with the date, it loses. **R3, R4, R8, D19** — post-MVP or
pending an answer, by decision. (**D20** was on this list and is now done — it
was two minutes' work inside Batch 1, so it was cheaper to close than to keep
listing.)

### The branch that is not ours to choose

**T2** (air-gapped bundle) depends on adapter delivery — see R7 and Q7.

- **Adapters arrive in time** → T2 moves to *must ship*, and the system is boxed
  into the secure network for handover.
- **They do not** → ship on the single coloured adapter, and **state plainly in
  the handover that the air-gapped path has never been exercised.** It must not
  be discovered by the receiving team.

**Assume the second until told otherwise** (Q7).

### What this line assumes

That there is a date. Nothing in this repository states one — see Q8. Until it
is answered, this table is a priority ordering rather than a schedule.

---

## Environment right now

- Development runs on a **WiFi-mounted board**, not an air-gapped one. There is
  one servo bus adapter and it sits on a "coloured" internet-facing network that
  cannot be introduced to the secure network.
- **The air-gapped path has therefore never been exercised** (backlog T2, R7).
- More adapters are expected within the month. If they arrive before the MVP is
  finished, the system gets boxed into the secure network for handover; if not,
  it ships with the single coloured adapter.
- **This version now runs on the board.** `python/.env` exists, the backend logs
  `backend=hardware` at boot, and the database is populated. The app is started
  headlessly with `arduino-app-cli app start user:servo_mvp`, which is also how
  App Lab starts it — App Lab opens its Python and serial monitors when it does.
- **The database is `ArduinoApps/servo_mvp/servo_mvp.db`, inside the network
  mount** (CIFS/Samba — see `CLAUDE.md` §6). `.env.board` sets a relative
  `DB_PATH` on purpose, because the Python
  side runs in a container where `HOME` is `/home/app`. Earlier docs claimed it
  sat outside the mount and needed `adb`; that is true only of the default.
- The active datum is count 2049, captured mid-travel by the operator, and ±90
  is reachable in both directions from it.

## Hardware facts, all bench-verified

- 4096 counts per servo turn, 44:30 belt → **0.06° per count** at the output
  (true value **0.059925**; 0.06 is a deliberate rounding, see the audit below)
- ±90° = **3004 counts**; the datum must sit **mid-travel (~2048)**
- **A datum at count 0 makes the negative half unreachable** — the servo clamps
  below 0 silently and still reports success
- direction **+1**; deadband **0**; speed saturates ~**1100 counts/s**;
  acceleration has no effect above ~**50**
- **Not yet in this list, and it should be:** what one `GoalSpeed` register
  unit is actually worth in real deg/s. Assumed equal to one position count
  (0.06°) by symmetry with position — structurally plausible (same register
  block, same packet, same official library layout) but a live timed move
  measured the servo running ~1.5-2x faster than that assumption predicts
  (backlog D35). Don't build anything on the 0.06 speed-step assumption
  until D35 closes it with an actual measurement.
- Serial1 @ 1 Mbps is reliable (200/200 reads, 220 µs)
- Ethernet shield needs **SpiRemap** — SPI2 sits on D11–D13 but the shield takes
  SPI from ICSP (PD1/PC2/PC3). Apply it after `SPI.begin()` **and again** after
  `Ethernet.init()`
- Ethernet 2.0.2 needs an `IPAddress((uint32_t)0)` cast patch on this core
- `kMaxRelaySockets = 6` is the **only** connection limit in the system
- **The W5500 is one chip on one SPI bus, reached from two threads.** `Poll()`
  runs on the loop thread, `net_tx` / `net_shutdown` on the Bridge thread. They
  must be serialised — `RELAY_NOTES.md` rule 7. Six sockets are not six
  resources.
- Sketch libraries need explicit versions in `sketch.yaml`; an unversioned
  reference fails with `Invalid Library Reference`. The **platform** is still
  unpinned and needs `arduino:zephyr` ≥ 0.56.0 (backlog T2)

## Gear-ratio audit — 8 August 2026

**All three sides agree on the ratio.** Checked because angle maths crossing two
processors and a browser is exactly where a twin-path defect would hide, and
because D9 was a baseline disagreement of this shape.

| | counts/turn | belt | counts per output degree |
|---|---|---|---|
| Python | `config.py:94` = 4096 | `config.py:95` = 44.0/30.0 | `servo_state.py:33,120,151` → **16.6874** |
| C++ | `AngleMath.h:27` | `AngleMath.h:23` = 44/30 | `AngleMath.h:53` → **16.6874** |
| Browser | `app.js:17` `4096 * (44/30) / 360` | — | **16.6874** |

Both derived checks hold: ±90° = **3004 counts** total span, and one count =
**0.059925** output degrees. No side hardcodes a pre-computed constant — each
derives from `counts_per_turn` and the belt ratio, so retuning either propagates.

**Two things the audit found, both recorded:**

- **`output_step_deg = 0.06` is a rounding of 0.059925**, used consistently by
  both sides (`config.py:106`, `app.js:27`) and documented at `config.py:103`.
  It means a commanded step is 1.0012 counts, so roughly one nudge in 800 moves
  two counts instead of one — under 0.12° across the full ±90 range.
  **The operator is aware of the rounding and has not decided whether to change
  it (8 August 2026).** Recommendation: leave it. 0.06 is a number an operator
  can read and type; 0.059925 is not, and the error it buys is a tenth of a
  degree across the whole travel window on a mechanism whose datum was captured
  by hand. Revisit only if a requirement appears that needs count-exact
  addressing from the UI — and if it does, the fix is to command *counts* rather
  than to print more decimals.
- **The UI tells the operator the step is 0.1°** while config and backend both
  enforce 0.06 — filed as **D21**. The ratio is right everywhere; the sentence
  describing it to the operator is not.

## Decisions on record

Nine ADRs in `docs/adr/`. Do not re-litigate these without reopening the ADR:

| ADR | Decision |
|---|---|
| 0001 | Network path runs through the MCU |
| 0002 | Plain HTML/CSS/JS — no framework, no build step |
| 0003 | Travel window ±90 output degrees; multi-turn off but configurable |
| 0004 | Repository abstraction with a simulated backend |
| 0005 | Develop as if already air-gapped |
| 0006 | Bridge payloads are CSV strings |
| 0007 | Moves are permitted while position is unverified |
| 0008 | A failed read is reported as unknown, never as a number |
| 0009 | Connection ceiling stays at 6 this batch; timeout_keep_alive is the real lever, unmeasured |

## Known gaps, stated honestly

- **The relay and controller have no automated coverage.** Every bug in this
  project has lived there. The native tests cover pure maths only. The W5500
  mutex (`docs/CLOSED.md` D4) was verified by compiling, running and measuring on the
  board — **not by a single test**, because no test in this repository can
  reach it.
- **`sketch/tests/OnTarget/` has never been uploaded** (backlog T3).
- **The C++ side now logs (backlog D3, done 8 Aug 2026) and is built,
  flashed and running on the board.** `get_status`'s `diag_dropped` counter
  is confirmed live. **But `mcu.jsonl` itself has never been seen** — the
  one boot-time event that should be unconditional (`mcu.relay.ready`) was
  lost to a startup race (backlog D28). Whether steady-state events survive
  it is untested; confirm with a real rejection or timeout before trusting
  `soak_report.py`'s MCU-side numbers.
- **"Stable" is not yet defined by numbers.** It gets defined by measurement —
  backlog R5 and R6.
