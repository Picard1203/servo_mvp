# Sprints

What the backlog cannot hold: sprint membership, story points, estimate vs.
actual, in-progress state. Does **not** restate item status or detail — an
item is done when its own `docs/backlog/D.md`/`T.md`/`R.md` entry says so;
duplicating that here is the exact two-copies-of-one-fact defect this repo
treats as a bug. Updated as the sprint runs, not reconstructed at the end.

Points: Fibonacci, anchored on the operator's own calibration that a 5 is
about 7.5h: **1** ≈1–1.5h · **2** ≈3h · **3** ≈4.5h · **5** ≈7.5h · **8**
split it. Estimates, not commitments.

**Jira export convention** (the air-gapped Jira has no API access, so import
is copy-paste from a standalone file, regenerated on request — not this
file, which is the working record; current copy: `docs/sprint/JIRA_EXPORT.md`).
`D` → issue type Bug, `T` → Task, `R` → Story. Priority derives from the
item's own stated severity/urgency: `high` severity that is safety- or
delivery-blocking → Highest, other `high` → High, `medium` → Medium, `low`
→ Low, post-MVP → Lowest. A multi-part item (a lettered defect, a batched
review item) is one Jira story with its sub-items as subtasks, never split
into separate stories. **Every story and every subtask carries its own To
Do / In Progress / Done status.**

**The export must be fully self-contained — the operator's explicit
correction, 2 Sept, after a first draft leaned on this repo's own D/T/R
numbering.** The air-gapped Jira, and anyone reading it who isn't on this
project, has no access to this repo: no backlog IDs, ADR numbers, session
numbers, internal tool names (this project's own skill/agent names), or
cross-references to files in this repo anywhere in the export — every fact
a reader needs is written inline in plain language instead. Each item must
stand alone well enough to be deleted or edited in isolation without
breaking anything else in the file. **Subtasks appear only once an item is
actually pulled into a sprint** — an item still sitting in the general
backlog is one story with no subtask breakdown; that breakdown happens at
sprint-planning time, not backlog-grooming time. When asked to build a
sprint from specific backlog numbers, apply this same convention without
re-asking.

**Timestamp every item boundary, every session — non-negotiable, not a
per-conversation habit.** Get a real clock time from the operator or `date`
at the moment work on a story starts and again when it closes; write both
into that story's row. Session 19 had to reconstruct its first two rows from
a wrong estimate (elapsed time minus a forgotten lunch deduction), corrected
only because the operator supplied the real anchors by hand — a session that
skips this repeats that mistake blind. Do not infer a start/end time from
session start or from wall-clock "now"; deductions in the capacity table
(meals, cleaning, army, any declared-absent window) are not working time and
must not be counted as if they were.

The **To Do / In Progress / Done** snapshot the operator asks for
periodically is generated from this file plus the backlog entries — never
from memory or conversation scrollback — so it can't drift from what
actually landed.

---

## Sprint: 30 Aug – 3 Sept 2026 (continuation, not a fresh start)

Began Sunday 30 Aug with the client-feedback fixes (R9, R10, the soak suite,
T9, board wipe — see `PROJECT_STATE.md` Sessions 15–18). Rig assembly was
Monday. What follows is capacity for the **remaining three working days**,
Tue 1 – Thu 3 Sept. No Friday this sprint — anything left over is carry-over
into the sprint starting Sun 6 Sept, not weekend work.

**Capacity:** Tue 13:00–22:00 (8.0h raw) · Wed 09:00–17:45 (7.25h) · Thu
09:00–17:30 minus 1.25h office cleaning (5.75h) · minus 1.5h floating army
duty · **19.5h raw → 13.5h at 0.7 focus factor.**

**Tooling:** Claude and Antigravity, assigned per whole item, never
mid-item — a Claude quota cutoff moves the *next* item to Antigravity rather
than handing the current one over half-done.

### Committed (~13.25h claude/operator-serial / 13.5h capacity — pulled in
1 Sept from Stretch, see note below the table; ~98% of remaining capacity,
knowingly over the 85% discipline, the operator's explicit call)

| Story | Pts | Est. | Start | End | Actual | Session | Status |
|---|---|---|---|---|---|---|---|
| CR triage into the backlog | 1 | 1.5h | ~13:05 | not marked | combined ~40m, see note | 19 | Done |
| Sprint board + this file | 1 | 0.75h | ~13:05 | not marked | combined ~40m, see note | 19 | Done |
| D39 — direction reversed | 1 | 1.5h | ~13:05 | 13:45 | combined ~40m, see note | 19 | Done |
| D40a — 3 CR HIGH prerequisites (ack surfacing, thread cancellation, `None`-guard) | | ~0.75h | 14:47 | 15:44 | 57m | 20 | Done |
| D40b — investigation, operator holding the rig | | 1.25h | 15:44 | 17:19 | 1h35m | 20 | Done |
| D40c — activate and harden the existing anti-backlash fine approach (travel-limit clamp, overshoot resized to measured data, event diagnostics, tuning-register read/write, PRESENT_SPEED read, MinStartForce tuning campaign) | | ~2h | 18:53 | 23:20 | 4h27m | 21 | Done |
| D40d — verify MinStartForce=150 holds under hand-held load; retune only if it does not | | 1.0h | 14:52 | 16:55 | ~4h | 22 | Done |
| D40 total | 5 | ~5h | | | | 20–22 | Done |
| R11 — snap to nearest + delta | 2 | 3.0h | | | | 22 | To Do — did not start, see note |
| Rig protocols 1/2/3/5, hand-held | 1 | 1.5h | | | | 22 | To Do — did not start, see note |
| T20 — doc-truth sweep (Antigravity, parallel — not counted against the 13.25h above) | 1 | 1.5h | | | | — | To Do |
| D48 — characterise the settling jitter properly, then fix it (Steps 1-5, see plan file) | 5 | ~4h | 12:47 | 16:45 | 3h58m | 24 | In Progress — Steps 1-2 done, Steps 3-5 remain, see D48 entry |

**D40d actual, ~4h against a 1.0h estimate — an unexplained-mismatch case,
stated plainly.** The estimate assumed a single confirmation pass
(`MinStartForce=150` holds, or it doesn't). What actually happened: the
confirmation failed in a way the estimate did not anticipate (jitter at
−60°, not the ±90° extremes the prior session had flagged), which opened a
real investigation — instrumentation fixed, root cause hypothesis built and
evidence-gathered, several register combinations tried live, one kept
permanently (`P`), a deep-research prompt drafted for further external
work. **R11 and the rig protocols did not start this session** — D40d's
investigation used the full remaining time. Both carry forward exactly as
committed scope, not dropped.

**13:51 note, before D40a genuinely starts:** an earlier edit briefly marked
D40a "In Progress" with a 13:51 start — wrong, that time went to this retune
conversation, not to D40a's code. Reset to To Do; D40a gets its own real
Start mark the moment work on it actually begins, per the rule above.

**1 Sept retro, mid-sprint — corrected twice in place rather than left
wrong.** First attempt wrongly counted the operator's lunch as working time
(retracted). Second attempt, from real operator-given anchors: plan approved
**13:05**, D39 closed and pushed **13:45** — **~40 minutes** covering all
three rows above (CR triage, sprint board, D39 including the unplanned
8-test regression fix), against a **3.75h (225m) combined estimate**. Not
"ran over" — the opposite: roughly 5–6x faster than estimated. Real, not
guessed, and per-story rather than per-row is not separable from this one
anchor pair (the three ran back to back with no boundary marked between
them — exactly what timestamping from here on fixes).

**What this says about the point scale, tentatively — confirm on D40, don't
assume yet:** the hour-per-point anchors were calibrated on the human-Scrum
assumption that reading, writing and testing code costs human wall-clock
time throughout. Claude-executed work compresses the parts that are pure
analysis/editing/tool-calls; it does **not** compress parts gated on the
operator's own clock — physical board observation, confirming which way a
shaft turned, a live investigation with the operator holding the rig.

**D40 retuned 1 Sept, before starting, on that basis — split by what
actually gates it, not by a blanket multiplier.** D39's ~5–6x held only for
a near-cheapest-possible case (a one-line config flip); D40c is real code
with design decisions (a bounded retry, config, events, a new UI state), so
it gets a modest 3.5h→2h, not D39's ratio. D40a is pure code close to D39's
shape, so 2.0h→0.75h is defensible. **D40b and D40d are untouched** — they
are gated on the operator's physical clock (holding the rig, positioning,
settle waits, watching, discussing) and nothing about D39's evidence says
those compress. Total: **5h estimated for a 5-point story** — the point
stays (it is still the operator's own "biggest problem in the system," the
largest single item this sprint), only the hour mapping moves, and only for
the parts with actual evidence behind the change. **The header's "5 ≈
7.5h" anchor is not touched yet** — one data point (a 5 that ran ~5h) is not
enough to move a scale used sprint-wide; revisit the anchor line itself only
after a second point-5 story confirms the same shape, not on this one.

**D40c actual, 4h27m against a 2h estimate — an unexplained-mismatch case,
stated plainly rather than silently absorbed.** The estimate covered the
code (clamp, readback, register write, PRESENT_SPEED read); the overrun is
real hardware iteration the estimate did not price in: a genuine
measurement-tool bug found and fixed twice on real hardware (a settle race,
then a debounce too short for a slow hunt), and — the actual scope driver —
a live tuning campaign (three MinStartForce values, a dead-zone detour, a
real oscillation found and root-caused at the travel extremes) that the
original estimate filed under D40d, not D40c. Confirms the point-scale note
above: physical-clock-gated work does not compress, and this session's own
scope grew to include what was meant to be D40d's territory.

**R12's ordering constraint is unchanged even though its sprint tier moved
(see Stretch below).** It was never carried because of a feared overrun — it
was carried because R11 must land first: snapping changes what a valid
target is, and R12's confirmation threshold depends on that. Now that R11 is
committed rather than stretch, R12 can honestly sit as stretch instead of
next-sprint carry-over — the sequencing R11-then-R12 still holds, it is just
more likely both happen this sprint instead of neither.

### Stretch (attempted only if committed scope finishes with room left)

| Story | Pts | Est. | Why it's here, not committed |
|---|---|---|---|
| R12 — soft ±90° / hard ±95° limit | 3 | 4.0h | Ordering, not risk: needs R11 actually landed first (snapping changes what a valid target is; the confirmation threshold depends on it). R11 is committed now, so this is sequencing, not a carry-over fear — attempt it only once R11 is genuinely done. |
| D41 — firmware moves on failed reads | 2 | 3.5h | Safety item for the *loaded* rig, not blocking this sprint's software work. No ordering dependency — good stretch candidate if time opens up, and must land before real load regardless of which sprint it's in. |

**Moved here 1 Sept from "carry-over to 6 Sept"**, at the operator's
direction, after seeing committed scope had real slack. Nothing about
either item's own reasoning changed — R12 still cannot start before R11 is
actually done, D41 still has no dependency either way. If neither gets
touched this sprint, they carry to 6 Sept exactly as before; the only thing
that changed is that "if time opens up" is now a real possibility, not a
formality.

### Jira-pasteable blocks

Story name + points; subtasks as names only, matching what the air-gapped
Jira needs.

```
D39 — A positive angle turns the mechanism the wrong way          [1]
  - Flip SERVO_DIRECTION in python/.env and .env.board
  - Apply servo_direction in renderZeros() (app.js)
  - Tests: conversion round-trip both signs; renderZeros under -1
  - Board check: +5/-5 by eye, saved-position spot check

D40 — A move settles short under load; re-commanding doesn't correct it  [5]
  - Fix: surface non-ack Bridge replies as errors, not silent success
  - Fix: fine-approach thread gets a generation token + guarded body
  - Fix: None-guard start_deg in _needs_fine_approach
  - Investigate: which of the 3 candidates, operator holding the load
  - Build: bounded convergence retry, config-gated
    (superseded 1 Sept — the mechanism kept is activating and tuning the
    already-existing fine approach, not a new retry; see D40's own entry)
  - Tune: tolerance + attempt count against hand-held load

R11 — Accept any typed angle; snap to nearest, show the delta     [2]
  - Backend: _validate_step becomes a snap, response carries the delta
  - Frontend: remove ANGLE_STEP/COUNTS_PER_OUTPUT_DEG local copies
  - Tests + check_client_behaviour.js: delta display

R12 — Soft limit ±90°, hard limit ±95°                             [3]
  - ADR-0012: soft/hard model, amends ADR-0003
  - Backend: live Pydantic bounds, three-state _validate_reachable
  - Frontend: confirm modal reuse, remove hardcoded ANGLE_MIN/MAX
  - docs/CONTEXT.md: soft limit / hard limit glossary entries

D41 — Firmware commands real moves off failed reads                [2]
  - ReadRawCounts failure signal, guard the 3 callers that use it as "hold"
  - ReadSnapshot per-field validity
  - Malformed servo_move payload refused, not defaulted to 0

T20 — Doc-truth sweep from the whole-app review                    [1]
  (Antigravity handoff — exact paths, no judgment; see T.md entry)
```

### Retro (sprint closed 6 Sept 2026, on starting the next one)

- **Planned capacity vs. actual:** 19.5h raw / 13.5h at 0.7 focus (Tue–Thu)
  committed to ~13.25h of stories. Actual hours, where marked: CR
  triage+sprint board+D39 combined ~40m (est. 3.75h — the one clean,
  human-clock-free case); D40a 57m (est. 45m); D40b 1h35m (est. 1.25h);
  D40c 4h27m (est. 2h); D40d ~4h (est. 1h); D48 3h58m (est. ~4h, on time but
  only 2 of 5 steps done — a scope miss, not a rate miss).
- **Committed vs. completed:** D39, D40(a–d) done, D40 closed. D48 in
  progress, checkpointed not closed (Steps 1–2 of 5). R11 and the rig
  protocols did not start — carried forward, not dropped (R11 is
  re-committed below). R12 and D41 were pulled from carry-over into stretch
  mid-sprint and also did not start — same disposition, carried forward. T17
  (separately, operator-run outside a Claude session) closed 6 Sept, just
  ahead of the next sprint being set up.
- **Estimate misses worth remembering:** confirmed pattern, not a one-off —
  pure code/analysis work (D39) ran 5–6x under estimate; anything gated on
  the operator's own physical clock (D40b, D40d: holding the rig,
  positioning, watching a settle) ran 2–4x *over* estimate, and D48's Session
  24 miss was different again — the *hour* estimate held, the *step-count*
  estimate for what fits in that time did not (board-connectivity friction
  ate wall time that had nothing to do with the actual measurement work).
  Going forward: estimate board/rig-gated work on its own clock, not the
  code-work multiplier, and budget board-connectivity setup as its own line
  rather than folding it into the first story that happens to need the
  board.

---

## Sprint: 6–10 Sept 2026 (Sun–Thu, work week)

**Deliberately five items, no stretch tier** — the operator's own call,
after two sprints running near or over capacity on point-scale surprises:
"less this time so it actually gets done." All five already exist in the
backlog; this sprint pulls them in and breaks them into subtasks per the
convention above.

**Capacity.** Lunch 11:30–13:00 (1.5h) and dinner 17:45–18:45 (1h) deducted
wherever a day's window crosses them, same windows as last sprint. Start
times are approximate (operator's own: "more or less 9:00, sometimes 30
minutes late").

| Day | Window | Raw | Deductions | Net |
|---|---|---|---|---|
| Sun 6 Sept (today) | 14:00–17:30 | 3.5h | none (before lunch window, ends before dinner window) | 3.5h |
| Mon 7 Sept | ~09:00–17:45 | 8.75h | lunch 1.5h | 7.25h |
| Tue 8 Sept | ~09:00–17:45 | 8.75h | lunch 1.5h | 7.25h |
| Wed 9 Sept | ~09:00–17:45 | 8.75h | lunch 1.5h | 7.25h |
| Thu 10 Sept | ~09:00–17:45 | 8.75h | lunch 1.5h | 7.25h |

Baseline raw: **32.5h**. Minus **~2h** floating military-duty deduction
across the week (day not yet known — subtract from whichever day it lands
on once real) → **30.5h**. At the 0.7 focus factor → **~21.35h effective
capacity**. **One evening will likely extend to 20:00 or 22:00** (dinner
deduction would then apply too) — not counted in the baseline above since
which day and how late is still open; treat it as buffer, not committed
capacity.

**Tooling:** Claude, per the standing rule (assigned per whole item, never
mid-item).

### Committed (~17.5h est. / ~21.35h effective capacity — ~82%)

| Story | Pts | Est. | Start | End | Actual | Session | Status |
|---|---|---|---|---|---|---|---|
| D48 — finish the resonance experiment: mechanism read at ±30° (Step 3), noise-floor calibration (Step 4, still unrun — `R_max`/`C_max` unset), statistically-powered lever test and permanent fix (Step 5) | 5 (carried — Steps 1–2 already spent ~4h in Session 24) | ~4h for the remainder | 13:06 | 19:23 | 6h17m (includes ~1h lost to an unrelated Ethernet-shield hardware failure/replacement mid-session, not investigation time) | 25 | Still open — mechanism confirmed (M1), no fix found today reliably passes; see D48 entry for the full trail and tomorrow's resume point |
| D48 (cont.) — finer sweep, multi-angle validation, dead-zone factorial; the campaign tool built and its selector bug found | — (same 5 pts, carried) | — | not captured | ~18:43 | not captured | 26 | Done that day — reconstructed from artifact timestamps, see note below |
| D48 (cont.) — B9 confirmatory, floor 40 baked in, then reopened the same day by the operator's manual sweep; P1/P2A/P3 decisive run built and run | — (same 5 pts, carried) | — | 08:48 | ~17:30 | ~8h40m | 27 | Done that day — Start from the run's own `started_at`, End from the next session's start |
| D48 (cont.) — decide the floor from the archive, validate it on the board, build the three fixes, close | — (same 5 pts, carried) | — | 17:36 | 19:42 | 2h06m | 28 | **Done — D48 closed.** Floor 55 baked in; arrival direction and verify-and-correct shipped; live on hardware |
| D41 — firmware refuses a real move commanded off a failed sensor read or a malformed payload | 2 | 3.5h | | | | 25 | To Do |
| R11 — accept any typed angle, snap to the nearest reachable step, show the delta | 2 | 3.0h | | | | 25 | To Do — carried from last sprint, did not start there |
| R12 — soft limit ±90° / hard limit ±95°, confirmed in between | 3 | 4.0h | | | | 25 | To Do — needs R11 actually done first (ordering, not risk) |
| D38 — let an operator dismiss a saved position's "may be outdated" tag | 2 | 3.0h | 20:30 | 21:17 | 47m | 29 | **Done — D38 closed.** Neither the 3.0h estimate nor the operator's own ~10-minute guess held; see the note below |
| T20 — doc-truth sweep, ~25 verified stale citations (Antigravity, parallel — not counted against the 13.25h/17.5h Claude estimate above) | 1 | 1.5h | | | | — | To Do |

**Two sessions of D48 work (26 and 27) were never booked here at the time,
and were reconstructed on 8 Sept from what they left on disk** — findings
files' own `started_at`, per-trial timestamps and archive file times. Their
figures are marked accordingly and are weaker evidence than a clock time
written down as the work happened. Session 26's start was not recoverable
at all. The rule this breaks is already written down (mark Start before the
branch exists, End when it closes); what made it break was a multi-session
item that never reached a closing ceremony, so nobody ever wrote a row.
**An item spanning sessions needs its row per session, not per item.**

**Order, as originally given:** D48 continuation first (done, closed
Session 28), then D41 (highest severity of the five — a physical-safety
item once real load is on the mechanism), then R11, then R12 (blocked on
R11 landing), then D38. T20 runs in parallel via Antigravity, not
session-bound, so it has no place in that ordering.

**Re-prioritized by the operator, end of Session 28 (8 Sept, ~19:50):
D38 moves ahead of D41, R11 and R12.** Stated reason: banking a small,
completable win tonight, with two shorter working days ahead (Mon 9 Sept
until ~17:45, Tue 10 Sept until ~17:15/17:30) and wanting to finish the
sprint's committed scope on time regardless. **D41 stays the higher
severity item and is not deprioritized on merit** — this is a sequencing
call for the time remaining, not a re-ranking of what matters most.
D41 is next after D38, then R11, then R12 (still blocked on R11 landing).

**Sizing note the operator flagged before this ran:** D38 is estimated at
3.0h in this sheet, set the same session that wrote its acceptance
criteria (single dismiss, batch dismiss, no edit to name/description/angle,
tests for both). The operator's own estimate going in was closer to 10
minutes. Record whichever the actual turns out to be — if it lands near
10 minutes, the 3.0h estimate was wrong and worth understanding why for
future estimates of similarly-worded items; if it lands near 3.0h, say so
plainly rather than let a strained "quick win" framing stand uncorrected.
**Actual: 47 minutes — neither estimate held.** Closer to the operator's
order of magnitude than the sheet's, but for a reason neither guess
priced in: three design iterations against real visual mockups (the
first two shown and rejected for costing too much visual weight) before
any code, then a genuine cross-cutting bug the work itself surfaced (the
SSE stream built its own copy of the response the router already had a
helper for, missing the new field entirely — caught by the existing
stream test, not invented for this item). The lesson for next time: a
UI-facing item's estimate should price in a design pass, not just the
code.

**T17 closed 6 Sept, ahead of this sprint being set up** — the operator ran
the real-rig hand-turn test directly: matched expectations both ways
(freely hand-turnable while isolated including multi-turn, resists/corrects
when un-isolated, position tracking correct afterward). Full record:
`docs/history/CLOSED.md` T17.

**Explicitly deferred, not dropped:** the remaining rig protocols (R1's
final loaded-capacity sign-off) and D47 (real-arm verification of the
anti-backlash fix) — neither is touched by the six items above, and neither
was pushed out to make room for them.

### Jira-pasteable blocks

```
D48 — Diagnose and fix the load-induced settling oscillation (resuming from a prior session's characterisation work)          [5]
  - Log position and current together fast enough to tell a resonance signature from a stick-slip signature, at the confirmed worst test angle
  - Establish a noise-floor pass/fail threshold before testing any fix
  - Test the mechanism-appropriate fix candidates at real statistical power (not a small, inconclusive sample)
  - Write the kept configuration permanently once it passes its own pre-declared bar

D41 — Firmware commands real moves off failed reads and malformed payloads          [2]
  - Add a failure signal to the raw-position-read function, and update the places that currently treat a failed read as "hold here"
  - Make the full-status read report which individual fields actually succeeded, instead of one blanket valid/invalid flag
  - Reject a malformed incoming move command outright instead of silently treating it as a move to position zero

R11 — Accept any typed angle; snap to nearest, show the delta          [2]
  - Backend: _validate_step becomes a snap, response carries the delta
  - Frontend: remove ANGLE_STEP/COUNTS_PER_OUTPUT_DEG local copies
  - Tests + check_client_behaviour.js: delta display

R12 — Soft limit ±90°, hard limit ±95°          [3]
  - ADR-0012: soft/hard model, amends ADR-0003
  - Backend: live Pydantic bounds, three-state _validate_reachable
  - Frontend: confirm modal reuse, remove hardcoded ANGLE_MIN/MAX
  - docs/CONTEXT.md: soft limit / hard limit glossary entries

D38 — Let an operator dismiss a saved position's "may be outdated" tag          [2]
  - Add a dismiss action (single position, and a batch dismiss for one recalibration's worth of newly-stale positions)
  - Dismissal clears the tag without touching name/description/angle
  - Tests: dismiss clears the flag; a later recalibration can re-raise it

T20 — Doc-truth sweep from the whole-app review                    [1]
  (Antigravity handoff — exact paths, no judgment; see T.md entry)
```

### Retro (fill in at sprint close)

- Planned capacity vs. actual hours spent:
- Committed vs. completed:
- Estimate misses worth remembering for the next sprint's scale:
