# Backlog

**The work queue. This is the only list of open work in the repo.**

Restructured 26 August 2026 for context cost: this file is now an **index**,
read in full every session. Full entries moved whole into
`docs/backlog/D.md` (defects), `docs/backlog/T.md` (tasks), `docs/backlog/R.md`
(requirements/build items) — open only that file, only for the item you are
picking up.

Two other files hold the past tense and must not be merged into this one:
`docs/CLOSED.md` (items that entered this backlog and left it, including the
full session-by-session record of the MVP build, sessions 1–10) and
`docs/AUDIT.md` (defects found before the backlog existed, frozen).

---

# START HERE — the session plan

**Path-to-first-demo milestone (sessions 11–14) closed 26 August 2026** — full
record in `docs/CLOSED.md`. **"Session" means a Claude Code chat session**
(context-reset unit), not a calendar day — the numbering below reflects
sessions actually spent, not the ones originally planned.

| # | Session | Board? |
|---|---|---|
| **15** | **DONE, 27–30 Aug 2026.** The demo moved up unexpectedly, ahead of the originally-planned 15–19 sequence — ran anyway. Presenter walkthrough produced live (was 18's job). Hit and fixed a live-blocking bug (**D37**, now closed — part of 15's original triage job; the rest of that triage did not happen, see deferred list below). Client feedback gathered, decided into **R9**/**R10** with the team lead. Backlog reorganized and closed out — **D12**, **D19** also closed (superseded by R10's decision, not deferred). Full account: `docs/PROJECT_STATE.md`. | no |
| **16** | **DONE, 30 Aug 2026.** **R9 closed** (speed → global, off the operator UI). **R10 closed** (calibration collapses into `app_state`; zeros replaced by full-CRUD saved positions, scope grown mid-session past the original design note). Opportunistic bonus: T6's exception hierarchy restructured (half-done, metadata population left). One new defect filed, D38 (dismissing a stale saved-position's advisory tag). D7's 768px collapse corroborated, not fixed. | no |
| **17** | **Claude + operator, no rig.** Pure software stress test — 10 min and 1 h soaks, varying operator counts — exercises connection/SSE/DB stability under load. **Not related to the mechanical rig.** First real measurement toward **R1**, replacing the synthetic remeasure originally planned here. | yes |
| **18** | **Claude + operator.** Wipe DBs and logs to a clean state, after the session 17 soaks and before the rig day — everything up to now was experiments; closes that phase. | maybe |

**After session 18, a separate day — mechanical rig assembly and R2's
hand-turn test (T17), operator/mechanical-team-led, Claude involvement
light.** Not one of the numbered sessions above; T17's own entry
(`docs/backlog/T.md`) tracks it.

**Deferred to the triage after session 18 (joint, and separately with the
team lead) — explicitly held, not dropped:** the rest of
`docs/REVIEW_FINDINGS.md` (originally session 15's full job — only D37 was
triaged out of it), **D17**, **T10**, **T11** (originally sessions 16/17's
job), **T18**, T9, T2, R6, R7. The originally-planned "dry run before the
demo" (old session 19) is moot — the demo already happened.

---

## How to pick up work

1. Read `../CLAUDE.md` — especially the graphify rules. Query the graph
   before reading source.
2. Run the verification commands in `CLAUDE.md` §3, note the numbers.
3. Find the item's `D`/`T`/`R` number in the index below, then open **only**
   its detail file (`docs/backlog/D.md`, `T.md`, or `R.md`) — not all three.
4. Update the entry as part of the change — an item is not done until its
   entry says so. Run `graphify update .` after changing code.
5. Re-run the verification commands. If the numbers moved, stop and say so.

---

## Open items — index

**Defects** (full entries: `docs/backlog/D.md`)

| | | Status |
|---|---|---|
| D5 | Log output dominated by connect/disconnect noise, phrasing not useful | open · medium |
| D6 | App load time is sometimes slow (chunk-size half closed) | open · medium |
| D7 | UI not verified on small operator screens | open · medium |
| D17 | Position bar can't show the negative half of travel | open · medium |
| D28 | MCU boot-time `mcu_log` notify lost to a startup race | open · low |
| D35 | Commanded vs. actual servo speed disagree ~1.5–2x | open · medium · not yet investigated |
| D36 | Several tests construct their own `Database` and never close it | open · low |
| D38 | A saved position's "earlier reference" tag has no way to dismiss it | open · low · R10 |

**Tasks** (full entries: `docs/backlog/T.md`)

| | | Status |
|---|---|---|
| T2 | Package the air-gapped bundle | open · blocked on adapters |
| T3 | Run the on-target test suite | open |
| T5 | Add `design_diagrams/` with PlantUML | open |
| T6 | Restructure the exception hierarchy | open · half-done · structure built Session 16, metadata population left |
| T7 | Add the database abstraction | open |
| T9 | Put a measured storage budget in writing | open |
| T10 | Write the recovery runbook, in two halves | open · high |
| T11 | Write the operations manual | open · high |
| T13 | Distil the remaining documents | open · opportunistic |
| T17 | Get a mechanical rig on the bench for R2's hand-turn scenario | open · scheduled after the DB/log cleanup |
| T18 | Front-end conventions, and split `app.js` by feature | open · after the demo |

**R-items** (full entries: `docs/backlog/R.md`)

| | | Status |
|---|---|---|
| R1 | Determine the real concurrent-operator ceiling | open · unmeasured since SSE migration |
| R3 | Confirm whether the Bridge could carry a frontend framework | open |
| R4 | Post-MVP: mechanical restraint servos, unified under Lock | post-MVP |
| R5 | Metrics export and benchmarking output | mechanism shipped · one gap open |
| R6 | Define "stable" by benchmark, not by adjective | open · blocked on R5 |
| R7 | Handover logistics depend on adapter delivery | delivery-shaping constraint |
| R8 | Emergency stop | post-MVP · can wait |

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
| **R2** | Motor isolation — board verification found the isolate/un-isolate write was inverted and its ack check used the wrong sentinel, both fixed and confirmed at the register level; UI/refusal gaps closed alongside | 26 August 2026 · hand-turn scenario left open, see T17 |
| **T1** | `CONVENTIONS.md` gap in `python/app/` (types, control-flow style) closed via T15a | 26 August 2026 · Antigravity, hand-verified against the diff |
| **T15** | Code-level documentation strip, both halves (T15a Python, T15b firmware) — Antigravity, hand-verified against the diff both times | 26 August 2026 · T15a needed real correction, T15b held up well |
| **T16** | `twin-review` restructured for a whole-app pass: fifth lens, scope modes, tool-narrowed dispatch, `REVIEW_FINDINGS.md` output | 26 August 2026 · running it (session 14) still open |
| **T19** | `ruff` added as an advisory Python lint pass (`python/ruff.toml`), wired into `twin-review`'s backend-chunk lenses | 26 August 2026 · not part of `verify.py`'s gate; baseline 50 findings |
| **D37** | `NetworkRelay.cpp` stray unmatched closing brace, build-breaking — found by Session 14's review, hit live blocking the client demo | 30 August 2026 · fixed and committed same session |
| **D12** | No way to return to the datum after activating a saved zero | 30 August 2026 · superseded by R10's decision, not fixed in place |
| **D19** | Saved positions listed against a baseline of 0 when no zero is active | 30 August 2026 · superseded by R10's decision, not fixed in place |
| **R9** | Speed becomes a global parameter, removed from operator control | 30 August 2026 · Session 16 |
| **R10** | Zeros replaced by a single datum and full-CRUD saved positions | 30 August 2026 · Session 16 · scope grew mid-session to full CRUD |
