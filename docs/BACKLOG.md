# Backlog

**The work queue. This is the only list of open work in the repo.**

Restructured 26 August 2026 for context cost: this file is now an **index**,
read in full every session. Full entries moved whole into
`docs/backlog/D.md` (defects), `docs/backlog/T.md` (tasks), `docs/backlog/R.md`
(requirements/build items) — open only that file, only for the item you are
picking up.

Two other files hold the past tense and must not be merged into this one:
`docs/history/CLOSED.md` (items that entered this backlog and left it, including the
full session-by-session record of the MVP build, sessions 1–10) and
`docs/history/AUDIT.md` (defects found before the backlog existed, frozen).

---

# START HERE — the session plan

**Path-to-first-demo milestone (sessions 11–14) closed 26 August 2026** — full
record in `docs/history/CLOSED.md`. **"Session" means a Claude Code chat session**
(context-reset unit), not a calendar day — the numbering below reflects
sessions actually spent, not the ones originally planned.

| # | Session | Board? |
|---|---|---|
| **15** | **DONE, 27–30 Aug 2026.** The demo moved up unexpectedly, ahead of the originally-planned 15–19 sequence — ran anyway. Presenter walkthrough produced live (was 18's job). Hit and fixed a live-blocking bug (**D37**, now closed — part of 15's original triage job; the rest of that triage did not happen, see deferred list below). Client feedback gathered, decided into **R9**/**R10** with the team lead. Backlog reorganized and closed out — **D12**, **D19** also closed (superseded by R10's decision, not deferred). Full account: `docs/PROJECT_STATE.md`. | no |
| **16** | **DONE, 30 Aug 2026.** **R9 closed** (speed → global, off the operator UI). **R10 closed** (calibration collapses into `app_state`; zeros replaced by full-CRUD saved positions, scope grown mid-session past the original design note). Opportunistic bonus: T6's exception hierarchy restructured (half-done, metadata population left). One new defect filed, D38 (dismissing a stale saved-position's advisory tag). D7's 768px collapse corroborated, not fixed. | no |
| **17** | **DONE, 30 Aug 2026.** Soak tooling modernized and executed across 5 structured runs (Run 0–4; >70m soak time, >20k samples). R1 software capacity target verified (3 remote + 1 local USB-C). Q9 proven true. D4 11s stall regression verified absent (0 stalls). T9 storage budget measured empirically and closed. Mechanical rig protocol documented in `docs/sprint/RIG_TESTING_PROTOCOL.md` ahead of T17. | yes |
| **18** | **DONE, 30 Aug 2026.** Board DB and logs wiped to a clean state following Session 17 soak suite. Preflight probe confirmed pristine hardware boot, 0 telemetry rows, fresh 32KB schema, unverified datum ready for Rig Day calibration. Closes the experimental development phase. | yes |
| **19** | **DONE, 1 Sept 2026 (sprint continuation, not a new sprint — began Sun 30 Aug).** Rig assembled 31 Aug produced four hands-on findings; Session 14's `/twin-review` (`docs/REVIEW_FINDINGS.md`) triaged into the backlog for the first time — **D39–D46, T20, T21, R11, R12** filed, four of its HIGHs absorbed directly into the rig findings rather than filed separately. `REVIEW_FINDINGS.md` retired (content preserved in the entries above and in git history). Sprint plan and capacity written to `docs/sprint/SPRINTS.md`. **D39** (direction reversed) fixed and board-confirmed. Full sprint plan: `/home/egrisaru/.claude/plans/snuggly-growing-gosling.md`. | yes |
| **20** | **DONE, 1 Sept 2026.** **D40a** — three CR-flagged HIGH prerequisites fixed and verified: ack surfacing on `command_move`/`command_stop`, fine-approach thread generation-token cancellation and isolation-abort, `None`-guard on a failed position read. **D40b** — live investigation with the operator holding the rig: false ack ruled out, firmware edge-triggering tested directly and ruled out, `MinStartForce` register found unconfigured and partially fixed, root cause identified as genuine position-dependent mechanical stiction/backlash in the belt-and-gear drivetrain. Full findings and caveats: `docs/backlog/D.md` D40. | yes |
| **21** | **DONE, 1 Sept 2026.** **D40c** — fine approach activated (was built, never switched on), hardened (re-opened and re-closed D40a's ack-surfacing gap on the fine-approach path), register readback and a live tuning campaign added: `MinStartForce` swept 0→150, closing at every one of 55 real moves within 0.00-0.03°, including a real oscillation found and fixed at the travel extremes. **D35 closed as a side effect** (`PRESENT_SPEED` sampling resolved the commanded-vs-actual speed question). Full findings: `docs/backlog/D.md` D40, `docs/history/CLOSED.md` D35. All numbers unloaded. | yes |
| **22** | **DONE, 2 Sept 2026.** **D40d** — set out to verify `MinStartForce=150` under hand-held load; instead found it does not hold reliably (worst at −60°, not the ±90° extremes expected), root-caused (evidence-based) to likely mechanical resonance rather than stiction, fixed the settle-detection instrumentation gap that was masking it, landed one real permanent improvement (`P` 32→24, matches published community guidance for this servo family), tried and deliberately reverted a dead-zone tradeoff (operator's own call: accept residual jitter risk over an accuracy cost). **D40 closed** on that honest, non-clean basis; **D47** opened for real-rig verification. Two independent deep-research passes (Claude, Gemini) run the same evening converged on the same diagnosis and surfaced three untried levers (D gain, a softened fine-approach final leg, deeper P reduction) plus the instrumentation gap in D40d's own method (no fast current logging, inadequate repeat counts against a ~40-60% intermittent failure) — captured as **D48**, a properly designed experiment, explicitly slotted for the next session rather than run tonight. R11 and the rig protocols did not run this session — the D40d investigation used the full session. | yes |
| **23** | **DONE, 3 Sept 2026.** Tooling session ahead of D48, not D48 itself — no register was touched, no trial was run. Vendored the SCServo library into `libraries/SCServo/` (was documented, never actually present; confirmed via its own source that D48's gain registers are not in Feetech's/Waveshare's own library). Installed 8 skills from cold storage into `~/.claude/skills/`, woven into `skills/deliver/SKILL.md` by phase (experiment-design rigor for D48-shaped items, debugging, verification, skill-writing discipline), with 2 explicitly excluded for conflicting with standing rules. Built and live-fire-tested 3 `PostToolUse` hooks (`docs/WORKFLOWS.md` W9) that surface `docs/CONVENTIONS.md`'s Python/C++ rules and the glossary/no-backlog-ID rules on every edit, since they were previously advisory-only and unenforced. Full account: `docs/PROJECT_STATE.md`. | no |
| **24** | **IN PROGRESS, 3 Sept 2026, 12:47–16:45.** D48 itself, Steps 1–2 of 5 (plan revised twice with the operator first — characterisation before any fix, not the original straight-to-three-levers version). Instrument hardened and committed (period-based scoring, settle-short as its own outcome, CSV persistence, a real anchor parameter). Characterisation sweep done, fine approach on, rig attached: **±30° is a validated worst point** (3/3 reproduction both directions), asymmetric and patchy rather than tied to the travel extremes. A third pre-registered FAIL condition (current elevation) added mid-session on live evidence — position-only scoring missed a real case. Real finding: fine approach **off** measurably worsens jitter (43%→71% reproduction), the opposite of the plan's original hypothesis — restored to on. Most wall time went to board connectivity (mount, adb, a dropped wired-NIC link, a Docker container not publishing its port), documented in `docs/backlog/D.md` D48 so it isn't rediscovered. Resume point: Step 3 (mechanism read) at ±30°. Full account: `docs/backlog/D.md` D48, plan file `/home/egrisaru/.claude/plans/peaceful-whistling-candy.md`. | yes |
| **25** | **IN PROGRESS, 6 Sept 2026 — new sprint (Sun 6–Thu 10 Sept), six items.** Sprint set up in `docs/sprint/SPRINTS.md` with the previous sprint's retro filled in. **T17 closed** the same session (operator ran the real-rig hand-turn test directly: matched expectations) — see `docs/history/CLOSED.md`. Caught and fixed a stale `T22` ID collision (open one renumbered **T23**). **D48 resumed and ran Steps 3–5**: mechanism confirmed (quantisation-boundary limit cycle, not resonance); registers, fine-approach tuning, move-staging and dead-zone all tried, none reliably passed — full trail in `docs/backlog/D.md` D48, a second deep-research prompt prepared but not yet run. A real hardware incident mid-session (Ethernet shield short, minor burn, unrelated to the servo code, resolved by replacement) moved all further hardware work to attended-only. **D41**, **R11**, **R12**, **D38**, **T20** in this sprint's committed scope have not started yet. | tbd |
| **26** | **DONE, 7 Sept 2026.** D48 continued. A re-analysis of Session 25's own archive invalidated part of its basis — every campaign trial had run at ~10Hz, not the fast path, so poll rate and time-of-day were perfectly confounded and its between-configuration comparisons were uninterpretable as they stood. New pre-registered regimen and a randomised-block campaign tool built (`docs/sprint/D48_S26_REGIMEN.md`, `tools/d48_s26_campaign.py`). B7 dose-response found the bifurcation between `min_start_force` 85 and 100; B8 crossed dead zone with the floor; multi-angle and bracket sweeps followed. Both deep-research answers came in and disagreed on cause while agreeing on the next experiment. | yes |
| **27** | **DONE, 8 Sept 2026, 08:48–~17:30.** B9 confirmatory (N=16, two angles) passed and `min_start_force=40` was baked into `Config.h` — then the operator's own manual sweep reopened it the same day: commanding −75° three times landed in three different places, exposing that the fine approach never had a fixed arrival side. `tools/d48_decisive.py` built and run: P1 proved arrival direction decides the miss and flips with the angle's sign; P2A found no floor passes alone; P3 showed a host-side verify-and-correct converges. Left deliberately unclosed for a fresh-eyes analysis. | yes |
| **28** | **DONE, 8 Sept 2026, 17:36–close. D48 CLOSED.** Analysis of the whole archive showed the two failure modes move in opposite directions with the floor, so no single value can pass — the fix had to be software. Floor **55** (highest never-oscillating value) baked into `Config.h`; arrival direction anchored to the target's sign; verify-and-correct loop added with three guards. Found and fixed a divergence in the correction rule itself (it re-derived its aim from the target each round and ping-ponged; now cumulative). Live on hardware: the same target from opposite sides lands identically, 0.00° spread. Four diagnostic-tool defects fixed, one filed as **T24**. | yes |
| **29** | **DONE, 8 Sept 2026, 20:30–21:17. D38 CLOSED.** Dismissing the "earlier reference" tag: a small drawn ✕ inside the tag itself for one position, a quiet header link ("clear N tags") for the batch, neither visible when nothing is tagged. Backed by a new `dismissed_at` column, compared against the datum rather than re-stamping `updated_at` (which would have looked like an edit and ejected another operator's open Edit dialog). Three heavier UI variants (a colour band, extra toolbar buttons, the whole tag as a button) were mocked up first and rejected by the operator for costing too much visual weight before this one was approved. Caught and fixed a real cross-cutting bug the same session: `routers/stream.py` built its own `SavedPositionResponse` rather than reusing the router's `_to_response()` helper, so the SSE push silently broke on the new required field — an existing stream test caught it. Full account: `docs/history/CLOSED.md` D38. Neither the 3.0h estimate nor the operator's own ~10-minute guess held — actual 47 minutes, see `docs/sprint/SPRINTS.md`'s sizing note. | no |

**R11 was pulled into committed scope 1 Sept, alongside T20 and the rig
protocols, then did not start** (D48/D40d's investigation used the full
remaining time) — carried forward rather than dropped. **R12 and D41**
similarly moved to stretch and also did not start. All three, plus **T20**
and the closed **D38**/**D48**, were the **6–10 Sept sprint's committed
scope** — see `docs/sprint/SPRINTS.md` for the capacity math and
per-story estimates. **T17 closed 6 Sept**, separately, ahead of this
sprint (see its own row above and `docs/history/CLOSED.md`). The remaining
rig protocols (R1's loaded sign-off) and D47 stay deferred past this sprint
too, unchanged.

**Still deferred from the original session-15 triage** — narrower now that
Session 19 pulled out everything the rig findings needed: **T10**, **T11**
(originally sessions 16/17's job), **T18**, T2, R7, and the D42–D46/T21
detail entries above (filed and ranked, not started).

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
| D28 | MCU boot-time `mcu_log` notify lost to a startup race | open · low |
| D36 | Several tests construct their own `Database` and never close it | open · low |
| D47 | Verify the anti-backlash fix holds once the servo carries its real load | open · medium |
| D41 | Firmware commands real moves off failed reads and malformed payloads | open · high · before real loaded rig day · **sprint committed, 6–10 Sept** |
| D42 | Errors that vanish: SSE stream, migration, sqlite writes | open · medium |
| D43 | Guards that fail open on an invalid read | open · medium |
| D44 | Operator-facing UI gaps found by the whole-app review | open · medium |
| D45 | Relay and firmware robustness gaps found by the whole-app review | open · medium |
| D46 | Backend robustness gaps found by the whole-app review | open · medium (ack-surfacing tracked via D40) |

**Tasks** (full entries: `docs/backlog/T.md`)

| | | Status |
|---|---|---|
| T2 | Package the air-gapped bundle | open · blocked on adapters |
| T3 | Run the on-target test suite | open |
| T5 | Add `design_diagrams/` with PlantUML | open |
| T6 | Restructure the exception hierarchy | open · half-done · structure built Session 16, metadata population left |
| T7 | Add the database abstraction | open |
| T10 | Write the recovery runbook, in two halves | open · high |
| T11 | Write the operations manual | open · high |
| T13 | Distil the remaining documents | open · opportunistic |
| T18 | Front-end conventions, and split `app.js` by feature | open · after the demo |
| T20 | Doc-truth sweep from the whole-app review (~25 verified fixes) | open · low · **sprint, Antigravity** |
| T21 | Constants and dead code with no shared source | open · low |
| T23 | Run graphify's semantic pass on the doc backlog it's never had | open · low |
| T24 | A screening filter judges only its first six trials, tainting the "futile" verdicts on the PID gains | open · low |

**R-items** (full entries: `docs/backlog/R.md`)

| | | Status |
|---|---|---|
| R1 | Determine the real concurrent-operator ceiling | open · software target met Session 17 · final sign-off Rig Day |
| R4 | Post-MVP: mechanical restraint servos, unified under Lock | post-MVP |
| R7 | Handover logistics depend on adapter delivery | delivery-shaping constraint |
| R8 | Emergency stop | post-MVP · can wait |
| R11 | Accept any typed angle; snap to nearest, show the delta | open · **sprint committed, 6–10 Sept** |
| R12 | Extended travel: soft limit ±90°, hard limit ±95°, confirmed between | open · **sprint committed, 6–10 Sept, after R11 lands** · needs ADR-0012 |

---

## Closed — the record is in `docs/history/CLOSED.md`

| | | closed |
|---|---|---|
| **D38** | A saved position's "earlier reference" tag has no way to dismiss it | 8 September 2026 · Session 29 · single and batch, no edit to name/description/angle — see `docs/history/CLOSED.md` |
| **D48** | Diagnose the settling oscillation properly rather than sweep registers again | 8 September 2026 · Sessions 24–28 · the register could never fix it — the two failure modes move in opposite directions with it. Closed by two software fixes (fixed arrival side, verify-and-correct) plus floor 55; live spread 0.00° from opposite sides — see `docs/history/CLOSED.md`; real-arm verification is D47 |
| **T17** | Get a mechanical rig on the bench so R2's hand-turn scenario can actually be tested | 6 September 2026 · operator-run on the real rig: matched expectations both ways, position tracking read correctly afterward — see `docs/history/CLOSED.md` |
| **D40** | A move settles short under load; re-commanding does not correct it | 2 September 2026 · Session 22 · closed with `P=24` kept permanently and an honest, unresolved loaded-jitter risk accepted — see `docs/history/CLOSED.md`; real-rig verification is D47 |
| **D35** | Commanded vs. actual servo speed disagree ~1.5–2x | 1 September 2026 · not a register bug — resolved by measuring `PRESENT_SPEED` correctly, see `docs/history/CLOSED.md` |
| **T22** | Reorganize docs: `CONTEXT.md`/`CONVENTIONS.md` into `docs/`, `CLOSED.md`/`AUDIT.md` into `docs/history/`, sprint docs into `docs/sprint/` | 1 September 2026 · `CLAUDE.md` stays at root |
| **D39** | A positive angle turned the mechanism the wrong way | 1 September 2026 · `SERVO_DIRECTION` flipped, board-confirmed both directions; exposed and fixed an 8-test `.env` coupling |
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
| **D4** | Connection drops after a few commands; requires a page refresh | 11 August 2026 · Session 3 (SSE) — full two-session soak saga kept whole in `docs/history/CLOSED.md` |
| **D17** | Position bar can't show the negative half of travel | 23 August 2026 · Session 5 · dynamic range scaling in app.js |
| **D18** | A failed CSV export navigates the operator out of the application | 11 August 2026 |
| **D22** | The only export control is fixed at 24 hours | 11 August 2026 · R5's delivery path |
| **D31** | Telemetry export drops instantly with "controller busy" | 23 August 2026 · real cause was a client-side `ReferenceError`, not the Pydantic hypothesis — see `docs/history/CLOSED.md` |
| **D10** | `logger.exception` swallows the exception; recurred as an unexplained sampler crash | 24 August 2026 · Session 6 · real cause was every read on the shared SQLite connection running unlocked, not a zero-table race — see `docs/history/CLOSED.md` |
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
| **R2** | Motor isolation — board verification found the isolate/un-isolate write was inverted and its ack check used the wrong sentinel, both fixed and confirmed at the register level; UI/refusal gaps closed alongside | 26 August 2026 · hand-turn scenario closed separately, see T17 |
| **T1** | `docs/CONVENTIONS.md` gap in `python/app/` (types, control-flow style) closed via T15a | 26 August 2026 · Antigravity, hand-verified against the diff |
| **T15** | Code-level documentation strip, both halves (T15a Python, T15b firmware) — Antigravity, hand-verified against the diff both times | 26 August 2026 · T15a needed real correction, T15b held up well |
| **T16** | `twin-review` restructured for a whole-app pass: fifth lens, scope modes, tool-narrowed dispatch, `REVIEW_FINDINGS.md` output | 26 August 2026 · running it (session 14) still open |
| **T19** | `ruff` added as an advisory Python lint pass (`python/ruff.toml`), wired into `twin-review`'s backend-chunk lenses | 26 August 2026 · not part of `verify.py`'s gate; baseline 50 findings |
| **D37** | `NetworkRelay.cpp` stray unmatched closing brace, build-breaking — found by Session 14's review, hit live blocking the client demo | 30 August 2026 · fixed and committed same session |
| **D12** | No way to return to the datum after activating a saved zero | 30 August 2026 · superseded by R10's decision, not fixed in place |
| **D19** | Saved positions listed against a baseline of 0 when no zero is active | 30 August 2026 · superseded by R10's decision, not fixed in place |
| **R9** | Speed becomes a global parameter, removed from operator control | 30 August 2026 · Session 16 |
| **R10** | Zeros replaced by a single datum and full-CRUD saved positions | 30 August 2026 · Session 16 · scope grew mid-session to full CRUD |
| **T9** | Put a measured storage budget in writing | 30 August 2026 · Session 17 (Software Soak) · ~590 MB 30-day footprint against 2.6 GB disk |
| **R3** | Confirm whether Bridge could carry a frontend framework | 30 August 2026 · Session 17 · decided/moot; air-gap rules out build pipeline; vanilla JS LCARS accepted |
| **R5** | Metrics export and benchmarking output | 23 August 2026 · Session 5 · full XLSX client export with native charts, verified under load in Session 17 |
| **R6** | Define "stable" by benchmark, not by adjective | 30 August 2026 · Session 17 · codified via `tools/soak_report.py` scorecard |
