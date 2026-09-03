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

### Retro (fill in at sprint close)

- Planned capacity vs. actual hours spent:
- Committed vs. completed:
- Estimate misses worth remembering for the next sprint's scale:
