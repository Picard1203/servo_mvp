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

**Agreed with the operator, 26 August 2026.** Sessions 1–10 (the MVP feature
build, through R2's close) are done — the full record is in `docs/CLOSED.md`.
This table is the path from there to the **first client demo** — not MVP
delivery, a narrower earlier milestone. **"Session" means a Claude Code chat
session** (context-reset unit), not a calendar day.

| # | Session | Board? |
|---|---|---|
| **11** | **DONE, 26 Aug 2026.** T15a: prose strip on `python/app/`, plus T1 in full. Run by Antigravity; corrected by hand the same session after a full diff review found real content silently dropped — see T15's entry. `python/static/*.js` was descoped and reverted whole (no JS conventions exist yet — T18). | no |
| **12** | **DONE, 26 Aug 2026.** T15b: same rule on `sketch/src/`. Held up far better than session 11 — most of what it removed was already in `skills/uno-q-st3215/SKILL.md`/`RELAY_NOTES.md`; five deleted doc-comment summaries and a few minor facts (payload-format table, register provenance) restored. T15 fully closed — see `CLOSED.md`. | no |
| **13** | **DONE, 26 Aug 2026.** T16 closed — went further than scoped (see `CLOSED.md`): fifth lens, diff/inventory scope modes with chunking, tool-narrowed candidate-finding per lens (not output-trimming — checked against current industry practice for LLM review token cost first), `REVIEW_FINDINGS.md` output contract. R1's stale blocked-on-D4 note fixed (D4 closed 11 Aug; R1 is now unmeasured against the current architecture, not blocked). | no |
| **14** | **DONE, 26 Aug 2026.** Enhanced `/twin-review`, whole-app, first time — 5 lenses × 4 chunks (backend/firmware/frontend/docs), ~65 findings → `docs/REVIEW_FINDINGS.md`. Headline: a real build-breaking brace mismatch in `NetworkRelay.cpp` that no existing check catches (native suite doesn't compile that file). | no |
| **15** | **Claude.** Triage those findings; fix what matters before the demo; backlog the rest with a reason. | maybe |
| **16** | **Claude, board.** R1 re-measured (synthetic, one SSE stream/operator — no real multi-machine test exists yet). Soak sharpened for auto-isolate. Feature pass via `/operator-lens`. Fix live: **D17**, **D12**, **D19**. | yes |
| **17** | **Claude, desk.** **T10** (recovery runbook) and **T11** (operations manual), after 16 lands. | no |
| **18** | **Claude, desk.** Client walkthrough guide — a short UI script for the presenter, this meeting. | no |
| **19** | **Claude.** Dry run on the real presentation device. Final verify. Go/no-go. | depends |

**Not on this path:** T2, T9, R6's full bar, R7 (MVP-delivery arc). D5, D28
(low severity, unscheduled). D35 (live-demo talking risk). **T18** (front-end
conventions + `app.js` split, after the demo). **T17** (mechanical rig,
independent track near Monday's mechanical session — does not gate the demo).

**D7** is unblocked (Q1 answered 26 Aug — responsive range, not an exact
device) but still not on this path; it can be picked up whenever, independent
of the demo sessions.

Full reasoning for this sequence: see the plan this table was built from,
or ask — it is not re-derived here to keep this table short.

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
| D12 | No way to return to the datum after activating a saved zero | open · medium |
| D17 | Position bar can't show the negative half of travel | open · medium |
| D19 | Saved positions listed against a baseline of 0 when no zero is active | open · medium · needs confirmation |
| D28 | MCU boot-time `mcu_log` notify lost to a startup race | open · low |
| D35 | Commanded vs. actual servo speed disagree ~1.5–2x | open · medium · not yet investigated |
| D36 | Several tests construct their own `Database` and never close it | open · low |

**Tasks** (full entries: `docs/backlog/T.md`)

| | | Status |
|---|---|---|
| T2 | Package the air-gapped bundle | open · blocked on adapters |
| T3 | Run the on-target test suite | open |
| T5 | Add `design_diagrams/` with PlantUML | open |
| T6 | Restructure the exception hierarchy | open · later |
| T7 | Add the database abstraction | open |
| T9 | Put a measured storage budget in writing | open |
| T10 | Write the recovery runbook, in two halves | open · high |
| T11 | Write the operations manual | open · high |
| T13 | Distil the remaining documents | open · opportunistic |
| T17 | Get a mechanical rig on the bench for R2's hand-turn scenario | open · independent track |
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
