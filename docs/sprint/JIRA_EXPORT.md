# Jira Import — Servo MVP

Generated 2 September 2026. A snapshot for copy-paste import into Jira.
Self-contained by design: every item carries whatever context is needed to
understand and act on it, written into the item itself — nothing here
depends on any other document. Delete or edit any single item freely; none
of them reference each other by an ID that would break.

**What the system is**, for context: an Arduino UNO Q single-board computer
(a Linux-capable processor paired with a real-time microcontroller on one
board) drives a Waveshare ST3215 serial-bus servo motor through a
belt-and-gear reduction. A web backend and a browser-based control screen
run on the board; operators connect over the local network to move the
mechanism, calibrate it, and save named positions. The finished system will
run at a deployment site with no internet access at all.

**Issue types used:** Bug (a defect in existing behavior) · Task
(engineering or documentation work with no user-facing defect) · Story (a
new capability or requirement).

**Priority:** Highest (safety-critical or blocks delivery) · High
(important, not currently blocking) · Medium (should be done, no urgency) ·
Low (nice to have) · Lowest (deferred, out of current scope).

**Story points:** Fibonacci scale, calibrated against this team's own past
work: **1** ≈ 1–1.5 hours · **2** ≈ 3 hours · **3** ≈ 4.5 hours · **5** ≈
7.5 hours · **8** = too large, split it before starting. Estimates, not
commitments.

**Status:** To Do / In Progress / Done, tracked independently for a story
and for each of its subtasks — a partly-finished story shows exactly which
pieces remain. Subtasks are only broken out once an item has actually been
pulled into a sprint; items still sitting in the general backlog are listed
as a single story with no subtask breakdown, since that breakdown is
sprint-planning work, not backlog-grooming work.

---

## Section A — Current Sprint (30 August – 3 September 2026)

### Committed

---

**Summary:** Triage a full codebase review's findings into individually tracked work items
**Type:** Task · **Priority:** Medium · **Points:** 1 · **Status:** Done
**Started/Closed:** 1 September, roughly 13:05–13:45 (combined with the two items below — worked as one continuous block, no clean boundary between them)

**Description:** A comprehensive automated review of the whole codebase
surfaced roughly 25 individual findings — gaps in error handling, rough
edges in the operator-facing screen, robustness issues in the
microcontroller firmware, and a few pieces of duplicated or dead code. This
work converted that raw review output into separately described,
separately prioritized entries (several of them appear later in this same
document) instead of leaving it as one undifferentiated report nobody would
work through end to end.

---

**Summary:** Set up a sprint-tracking document, separate from the backlog
**Type:** Task · **Priority:** Medium · **Points:** 1 · **Status:** Done
**Started/Closed:** 1 September, roughly 13:05–13:45 (combined, see above)

**Description:** Created a document to track which items are committed to
the current working period, their point estimates, actual time spent, and
in-progress state — kept separate from the general list of open work so
that list stays a clean backlog rather than turning into a mixed
backlog-plus-tracker.

---

**Summary:** A positive angle typed by the operator turned the mechanism the wrong physical direction
**Type:** Bug · **Priority:** Highest · **Points:** 1 · **Status:** Done
**Started/Closed:** 1 September, roughly 13:05–13:45 (combined, see above)

**Description:** Commanding a positive angle drove the servo in the
negative physical direction — a sign error in the configuration value that
maps a typed angle to a motor direction. Fixing the sign also exposed and
required fixing an unrelated set of eight automated tests that had come to
depend on the wrong value being present. Confirmed correct on the real
hardware in both directions (moved +5° and −5° and visually verified the
direction matched what was typed), plus a spot check that saved positions
still moved to the right place afterward.

---

**Summary:** A commanded move settles short of its target under mechanical load, and repeating the same command does not correct it
**Type:** Bug · **Priority:** Highest · **Points:** 5 · **Status:** In Progress
**Started:** 1 September, roughly 14:47 · **Not yet closed** — one piece remains, described in the last subtask below

**Description:** Under load, commanding the mechanism to a target angle
(for example 90°) could settle a fraction of a degree short (around 89°);
pressing the same target again produced no corrective movement, though
commanding several degrees further did move it. This was the operator's own
top-priority problem with the system — the number on screen could not be
trusted as the number actually achieved.

Investigation, done live with the operator holding the mechanism, ruled out
two suspected software causes (a false "move accepted" signal being sent
before the servo actually moved, and the servo silently ignoring a repeated
command to the same target) and identified the real cause as ordinary
mechanical stiction and backlash in the belt-and-gear drive — the kind of
static friction that has to be overcome before the mechanism will move at
all from a dead stop.

The fix reuses an anti-backlash technique that existed in the code already
but had never been turned on: instead of driving straight to the target,
the mechanism deliberately overshoots slightly and then approaches the
final target from one consistent direction, which cancels out backlash the
same way it's cancelled by hand on a manual instrument. This was switched
on, made to work approaching from either direction (it previously only
worked approaching from one), and then tuned against the real hardware: a
servo configuration value controlling minimum startup force was swept from
0 up to 150 (on a 0–1000 scale), and 150 produced consistent, repeatable
landings within 0.00–0.03° of the target across 55 real test moves,
including fixing a separate oscillation problem that was found at the
extreme ends of the mechanism's travel range at an earlier value in that
sweep.

**Important caveat:** every number above comes from testing with no load on
the mechanism. The remaining subtask exists specifically to confirm the fix
still holds once there's a real hand-applied load on the mechanism, which
is what actually matters for the finished use case.

**Acceptance:** a commanded move converges to its target within a stated
tolerance, or the system plainly reports that it could not — it must never
silently settle short of the target while reporting success.

**Subtasks:**
- [Done] Make the three main move/stop commands report failure honestly if the servo never actually acknowledges them, instead of assuming success
- [Done] Live investigation with the operator holding the mechanism: ruled out a false-success signal and a "repeated command ignored" theory; identified genuine mechanical stiction as the cause
- [Done] Turn on and tune the existing overshoot-and-return anti-backlash technique; run a live tuning sweep of the servo's minimum-startup-force setting and fix an oscillation found at the extreme ends of travel
- [To Do] Re-verify the tuned result holds with a real hand-applied load on the mechanism (not just the unloaded bench); retune only if it does not

---

**Summary:** Commanded and actual servo speed disagreed by roughly 1.5–2x
**Type:** Bug · **Priority:** Low · **Points:** 0 — resolved as a side effect of the tuning work above, no separate cost · **Status:** Done
**Closed:** 1 September

**Description:** Not an actual bug. While adding live readback of the
servo's real, measured speed (a hardware register the firmware wasn't
reading before) during the tuning work described above, the measured speed
matched the expected value closely at low-to-medium speeds. At the highest
tested speed it only reached the expected value on long moves; short moves
simply don't have enough distance to accelerate all the way up to that
speed before they're already decelerating — a normal physical
acceleration-distance effect, not a bug in the software or the hardware
configuration. Resolved by measuring correctly, not by any code change.

---

**Summary:** Reorganize project documentation for long-term navigability
**Type:** Task · **Priority:** Low · **Points:** 2 (no time estimate was recorded for this item at the time; actual time spent was well under what a fresh estimate would suggest) · **Status:** Done
**Closed:** 1 September

**Description:** The project's internal documentation had grown into a mix
of loose files at the top level and a single folder with everything else.
Reorganized into clearly separated groups — historical/closed-item records
in one place, active planning documents in another, general reference
material in a third — and updated every cross-reference between documents
so nothing pointed at a moved file's old location. Two hand-drawn diagrams
were redrawn by hand to match.

---

**Summary:** Accept any typed angle; automatically snap it to the nearest position the mechanism can actually reach, and show the operator the difference
**Type:** Story · **Priority:** High · **Points:** 2 · **Status:** To Do
**Requested by:** the client, through the operator, during hands-on testing on 1 September

**Description:** The mechanism moves in fixed steps of about 0.06° and
today the system refuses any typed angle that isn't an exact multiple of
that step — forcing the operator to do the arithmetic themselves before
typing a number in. The new behavior: accept whatever angle the operator
types, silently work out the nearest angle the mechanism can actually
reach, move there, and show both the requested angle and the actual target
on screen along with the difference between them, so nothing is hidden.

A stricter version of this was tried once before and rejected: it rewrote
the typed value on screen with no indication anything had changed, which
was confusing. This design is different specifically because the
difference is always shown, never hidden.

This must be built and working before the extended-travel confirmation
feature described later in this document (in the stretch section) — because
once angles get silently snapped to the nearest reachable step, that
changes which values actually cross the extended-travel confirmation
threshold, so that feature has to be built already knowing this behavior
exists.

**Acceptance:** any typed angle within the mechanism's travel range is
accepted; the screen shows the requested angle, the actual (snapped)
target, and the difference; no separate copy of the step size is
duplicated in the browser-side code — it always reflects what the backend
returns.

**Subtasks:**
- [To Do] Change the backend's angle validation from rejecting an invalid angle to snapping it to the nearest valid one, and have it return the requested angle, snapped angle and delta
- [To Do] Remove the hardcoded step-size value from the browser-side code; display whatever the backend returns instead
- [To Do] Update automated tests to check the delta is displayed correctly

---

**Summary:** Verify, under a real hand-applied load, that the mechanism can be freely turned by hand while motor power is isolated, and that position tracking survives it
**Type:** Task · **Priority:** High · **Points:** 1 · **Status:** To Do

**Description:** The system has a feature to electrically isolate the
servo's motor power (for maintenance or safety) while leaving the rest of
the system running. It was previously confirmed at the electrical/register
level that power genuinely cuts and restores correctly, but one part was
never actually tested: whether a person can freely turn the mechanism by
hand while isolated, and whether the system's internal position tracking
still shows the correct position afterward, given that the shaft moved
without the motor driving it. A bare test rig without a belt or lever
attached couldn't support this test properly; a proper mechanical rig with
the actual belt-and-gear drive is now assembled and available for it.

---

**Summary:** Correct a batch of outdated facts accumulated across the project's documentation
**Type:** Task · **Priority:** Low · **Points:** 1 · **Status:** To Do

**Description:** Roughly 25 individually-verified stale references have
built up across the project's written documentation over time: test counts
quoted from before the test suite grew, a configuration value mentioned as
correct that a later fix actually changed, a mention of a file that no
longer exists, an example command that no longer works as written given a
later environment change, and a similar volume of outdated line-number and
section references scattered elsewhere. This is a mechanical, no-judgment
correction pass — no new writing, just fixing facts that have gone stale —
so it's well suited to being handed off to an automated pass or a
less-experienced contributor working from a list of what changed and when.

**Acceptance:** every stale reference corrected to its current, real value;
nothing added beyond the corrections themselves.

---

### Stretch (attempted only if the committed work above finishes with time left)

---

**Summary:** Allow the mechanism to travel further than its normal range, with an explicit confirmation step before going past the normal limit
**Type:** Story · **Priority:** Medium · **Points:** 3 · **Status:** To Do
**Requested by:** the operator, during hands-on testing on 1 September, for an occasional special-purpose need

**Description:** Today the mechanism has one fixed travel limit
(approximately ±90°) with no way to deliberately go further. New design,
three states: within the normal ±90° range, behavior is unchanged, no
prompt. Between the normal limit and an absolute hard limit of ±95°, a
move is only carried out after the operator explicitly confirms it on
screen (reusing an existing confirmation dialog already used elsewhere in
the interface). Past ±95°, a move is always refused outright, the same way
an out-of-range move is refused today — no confirmation makes it possible.
The ±95° hard limit is a deliberate, unmoving safety backstop, not
adjustable through this feature.

This changes an existing design decision that treated the travel limit as
a single fixed window; that decision is being formally revised in writing,
not silently overridden. It also must be built after the angle-snapping
feature described earlier in this document, because that feature changes
which values actually land in the confirmation zone.

It is not yet proven that ±95° is mechanically safe to reach under a real
working load — this work only builds the software gate that enforces the
limit; a separate hardware verification under load is still needed before
the limit is trusted in practice.

**Acceptance:** a move to 89.9° happens with no prompt; a move to 92°
requires confirmation first; a move to 96° is refused outright with no way
to override it; declining the confirmation prompt results in no movement;
a typed value that gets snapped into the confirmation zone by the
angle-snapping feature still triggers the prompt.

**Subtasks:**
- [To Do] Write up the new soft-limit/hard-limit design as a formal decision record, explicitly revising the earlier single-limit decision
- [To Do] Backend: make the travel-limit check read its bounds live from configuration rather than a value fixed at startup, and add the three-state (normal / confirm / refuse) logic
- [To Do] Frontend: reuse the existing confirmation dialog for the middle zone; remove the hardcoded travel-limit values duplicated in the browser-side code
- [To Do] Add "soft limit" and "hard limit" as defined terms in the project's glossary of terminology

---

**Summary:** Prevent the microcontroller firmware from commanding a real move based on a failed sensor read or a malformed incoming command
**Type:** Bug · **Priority:** Highest · **Points:** 2 · **Status:** To Do
**Must be completed before the mechanism is ever tested under real load with people or equipment near it**, regardless of which sprint it lands in

**Description:** The same category of bug already found and fixed on the
application/backend side of the system also exists in the microcontroller
firmware. When a position sensor read fails, the firmware's read function
returns a plain zero with no indication the read actually failed — and
three places in the firmware currently treat that zero as a legitimate
"hold here" position and act on it as a real move command, meaning a
momentary communication glitch during a stop or a power-related command
could silently drive the servo toward position zero while still reporting
success. Separately, the function that reads the servo's full status
doesn't check whether each of its six individual sensor reads actually
succeeded before marking the whole status as valid. And separately again,
an empty or malformed incoming move command is currently treated the same
as a command to move to position zero (because the parsing code's default
for a missing value happens to be zero, and zero is also a legitimate real
target), rather than being rejected outright.

Not urgent for this sprint's software-only work, but once there is a real
working load and enclosure around the mechanism, a communication glitch
silently driving the servo toward position zero becomes a physical safety
event, not just an incorrect reading.

**Acceptance:** a failed sensor read is never used as a move target; a
malformed incoming command is rejected outright rather than silently
defaulted to a real value; the full-status read reflects which individual
values actually succeeded, matching how the backend side already works.

**Subtasks:**
- [To Do] Add a failure signal to the raw-position-read function, and update the places that currently treat a failed read as "hold here"
- [To Do] Make the full-status read report which individual fields actually succeeded, instead of one blanket valid/invalid flag
- [To Do] Reject a malformed incoming move command outright instead of silently treating it as a move to position zero

---

## Section B — Backlog (not yet scheduled into a sprint)

Quick-reference list, priority order. Full descriptions follow below —
pull any item into a future sprint and break it into subtasks at that
point; items here are intentionally left as single stories with no subtask
breakdown, since that breakdown is sprint-planning work.

| Summary | Type | Priority | Points |
|---|---|---|---|
| Package a self-contained software bundle for delivery to a fully disconnected network | Task | High | Blocked — see description |
| Write a recovery runbook for when the system misbehaves | Task | High | 3 |
| Write a day-to-day operations manual | Task | High | 5 |
| Reduce log noise from routine connection housekeeping | Bug | Medium | 2 |
| Measure and fix occasional slow first-load time | Bug | Medium | 3 |
| Verify and fix the interface on small screens | Bug | Medium | 2 |
| Stop several classes of failure from being silently swallowed with no trace | Bug | Medium | 3 |
| Fix safety checks that default to "safe" when their input is actually unknown | Bug | Medium | 3 |
| Fix a batch of rough edges in the operator-facing screen | Bug | Medium | 5 |
| Fix a batch of robustness gaps in the network-relay and firmware layer | Bug | Medium | 5 |
| Fix a batch of robustness gaps in the backend | Bug | Medium | 3 |
| Final sign-off of the maximum number of simultaneous operators, under real mechanical load | Story | Medium | 1 |
| Run the on-hardware test suite at least once | Task | Medium | 1 |
| Write front-end coding conventions and split one large interface file into smaller modules | Task | Medium | 5 |
| Add architecture and data-model diagrams | Task | Low | 3 |
| Finish populating structured error detail on the exceptions that don't have it yet | Task | Low | 2 |
| Add a proper abstraction layer above the database, matching the pattern already used elsewhere | Task | Low | 2 |
| Ongoing: trim verbose, outdated documentation as it's encountered | Task | Low | 1 |
| Remove duplicated constants and settle one piece of unused, untested code | Task | Low | 3 |
| Fix a startup-timing race that can silently drop the first boot-time log message | Bug | Low | 1 |
| Fix several automated tests that open a database file and never close it | Bug | Low | 2 |
| Let an operator dismiss a "may be outdated" warning on a saved position | Bug | Low | 2 |
| Post-launch: motorize the manual mechanical safety clamp | Story | Lowest | Not sized — future phase |
| Post-launch: single-button emergency stop | Story | Lowest | Not sized — future phase |

---

**Summary:** Package a self-contained software bundle for delivery to a fully disconnected network
**Type:** Task · **Priority:** High · **Points:** Blocked — cannot be sized until the blocker below clears · **Status:** To Do

**Description:** The system will eventually run at a secure site with no
internet access at all. All required software packages and two
custom-patched third-party libraries need to be bundled and verified to
install and run on a clean machine with zero network access, before
delivery. Currently, development happens on a board connected to a
regular network, because the only available hardware adapter for
programming the servo bus is on that regular network and can't be
connected to the secure one — so this disconnected-install path has never
actually been tested. More adapters are expected to arrive at some point,
which would remove this blocker; if they don't arrive before delivery,
handover happens with the one existing adapter instead.

**Acceptance:** a clean machine with no network access at all successfully
runs the complete system from the bundle alone.

---

**Summary:** Write a recovery runbook for when the system misbehaves
**Type:** Task · **Priority:** High · **Points:** 3 · **Status:** To Do
**Requested by:** the operator

**Description:** The deployment site is roughly three hours from anyone
who can fix a software problem, and there is currently no written
procedure for what to do when something goes wrong. Two audiences need two
different documents: one for whoever only has the browser interface
available remotely (what does an "offline" indicator actually mean, how
long before it's a real problem rather than a brief hiccup, what does a
refused command look like versus an actual fault, and when to stop trying
things and call someone); and one for whoever is physically on site with a
direct cable connection to the board (the exact sequence of commands to
check and restart the system, what's safe to run while a person or
mechanism is nearby, how to confirm the system is actually talking to the
real hardware rather than a software simulation, and explicitly what is
never safe — for example, restarting the system while someone's hands are
on the mechanism is not a neutral action, since the mechanism can be moved
by hand while unpowered).

**Acceptance:** both halves are written; the on-site half has been
followed once, successfully, by someone who did not write it.

---

**Summary:** Write a day-to-day operations manual
**Type:** Task · **Priority:** High · **Points:** 5 · **Status:** To Do
**Requested by:** the operator · scheduled for after a round of error-message improvements elsewhere in the system finishes, so it doesn't describe messages that are about to change

**Description:** Distinct from the recovery runbook above: this is the
document for routine, everyday use, not for when something's wrong.
Nothing currently exists to tell a new operator how to actually run the
system day to day. At minimum it needs to cover: the startup routine
(moving the mechanism to the middle of its range and calibrating, and why
that specific step matters); what every control on screen does, including
why motor isolation, position lock and emergency stop are three separate
controls rather than one; what a saved position is and how to get back to
the calibrated reference point; how to honestly read the on-screen status
indicators; the mechanism's travel range and step size; and how to pull
exported data off the system.

**Acceptance:** someone who has never seen the system before can run a
normal working session using only this document, with no one to ask.

---

**Summary:** Reduce log noise from routine connection housekeeping
**Type:** Bug · **Priority:** Medium · **Points:** 2 · **Status:** To Do

**Description:** The cause is already identified and it isn't actually a
bug: the network relay deliberately closes and reopens idle connections
every five seconds to free up a scarce hardware connection slot, and that
housekeeping produces roughly 24 log lines per minute per connected
operator at the more detailed logging level (already hidden at the normal
default level). What remains is a presentation problem — at the normal
logging level, the log should read as a plain narrative of what the system
actually did (moves, calibrations, faults), not a transcript of its network
connection housekeeping.

**Acceptance:** at the default logging level, the log reads as a useful
narrative of system activity; the detailed connection housekeeping stays
available at the more verbose logging level only.

---

**Summary:** Measure and fix occasional slow first-load time
**Type:** Bug · **Priority:** Medium · **Points:** 3 · **Status:** To Do

**Description:** The page occasionally takes noticeably longer to first
load than usual. One contributing factor (the size of data chunks sent
over the connection to the microcontroller) has already been identified
and fixed, with a measured throughput improvement. The remaining,
still-unmeasured factor is the page's own first-paint time in the browser.

**Acceptance:** first-load time is actually measured and a number is put
in writing to compare future work against.

---

**Summary:** Verify and fix the interface on small screens
**Type:** Bug · **Priority:** Medium · **Points:** 2 · **Status:** To Do

**Description:** The operator screen has a confirmed layout bug at a
narrow tablet-sized width (roughly 768 pixels wide): a section of the page
collapses to zero height under a specific responsive-layout rule and the
lower half of the page renders blank. Two wider widths (a larger tablet
size and a typical laptop width) already render correctly.

**Acceptance:** verified at the narrow tablet width, the larger tablet
width, and a typical laptop width using a browser's device-simulation
mode; the blank-page bug at the narrow width is fixed.

---

**Summary:** Stop several classes of failure from being silently swallowed with no trace
**Type:** Bug · **Priority:** Medium · **Points:** 3 · **Status:** To Do

**Description:** Four related gaps, all with the same shape — a failure
that a developer or operator genuinely needs to see currently produces no
log entry and no visible trace at all: the live-status data stream to the
browser catches every internal error with no logging, unlike an equivalent
piece of code elsewhere in the system that does log its errors correctly;
the database upgrade routine that runs on startup treats every possible
database error as "already up to date" and logs nothing, which means a
genuinely failed upgrade is indistinguishable from a successful one that
already ran; none of the code that reads or writes the database has any
error handling for a "database temporarily locked" condition (a real,
reproducible condition on this project's development setup), so it
surfaces to the operator as a generic, unhelpful server error instead of a
clear message; and one diagnostic reading returns an ambiguous "no value"
result for two very different situations (the hardware not responding at
all, versus the hardware responding with something unexpected) with no way
to tell which happened.

**Acceptance:** each of the four either logs and clearly surfaces its
failure, or there's a written reason why the current behavior is
acceptable as-is.

---

**Summary:** Fix safety checks that default to "safe" when their input is actually unknown
**Type:** Bug · **Priority:** Medium · **Points:** 3 · **Status:** To Do

**Description:** Three related gaps where a safety check silently assumes
the reassuring answer at exactly the moment its input data is least
trustworthy: the check that guards against locking the mechanism while it
is moving reports "not moving" whenever the underlying sensor read fails,
rather than reporting genuinely unknown; the general status readout blanks
every telemetry and fault value to unknown after a single failed sensor
read, with no distinction between one momentarily dropped reading and a
genuinely sustained problem; and the calibration screen's "off-center"
warning uses its own separate, simplified reachability calculation instead
of the same shared calculation used everywhere else in the system, and has
been confirmed to actually disagree with the real calculation in
asymmetric setups.

**Acceptance:** each safety check reflects genuine uncertainty rather than
defaulting to the reassuring answer; the calibration screen's check is
changed to reuse the same shared calculation as the rest of the system, by
construction, rather than happening to agree with it by coincidence.

---

**Summary:** Fix a batch of rough edges in the operator-facing screen
**Type:** Bug · **Priority:** Medium · **Points:** 5 · **Status:** To Do

**Description:** Eight smaller frontend issues found in one review pass,
none individually large enough to justify a separate ticket each: the
fault-warning banner can simultaneously show a real measured position and
a "last known position, may be stale" warning, which is contradictory; five
out of six fault types have no on-screen way to acknowledge or recover
from them, only one type does; a date-range input error is shown to the
operator as a generic "controller busy" message instead of the actual
problem; the speed adjustment control has no upper or lower bound and
shows a raw, unfriendly error message with no indication of which field
was wrong; exporting a time range with no data in it silently downloads an
empty file that looks structurally valid; the "connecting" status
indicator uses the identical color as "confirmed healthy," making them hard
to tell apart at a glance; an empty recent-activity list renders as a
blank panel with no explanation; and a legitimate zero-value reading is
treated identically to "no reading at all" in one export path.

**Acceptance:** each of the eight either gets fixed or has a written reason
why the current behavior is acceptable — no closing this out as a batch
without addressing each one individually.

---

**Summary:** Fix a batch of robustness gaps in the network-relay and firmware layer
**Type:** Bug · **Priority:** Medium · **Points:** 5 · **Status:** To Do

**Description:** Six related firmware-level issues found in one review
pass: the network relay's bulk-read loop exits its entire scan early on a
single lock timeout instead of skipping just that one connection slot,
which can deterministically starve later connection slots on every single
pass; a lock is held across a potentially slow network write, and the
equivalent code on the software side does something similar, meaning one
slow or stalled connection could plausibly stall every other connected
operator (this specific risk hasn't been fully confirmed, since the
relevant third-party networking library isn't available for direct
inspection in this environment); two low-level write functions to the
servo bus have no retry logic and no error logging at all, unlike every
read function; a failed write to the servo silently logs nothing while a
harmless, expected refusal logs clearly — the signal-to-noise ratio is
backwards; a diagnostic log buffer used specifically for debugging
high-load conditions isn't rate-limited and can overflow during exactly
the high-load condition it exists to help diagnose; and a partially
successful startup sequence currently reports "ready" identically to a
fully successful one, with no distinction visible anywhere.

**Acceptance:** each of the six either gets fixed or has a written reason
why the current behavior is acceptable.

---

**Summary:** Fix a batch of robustness gaps in the backend
**Type:** Bug · **Priority:** Medium · **Points:** 3 (a fourth, higher-severity finding from the same review — commands reporting success without real hardware confirmation — has already been fixed separately; this covers the remaining three) · **Status:** To Do

**Description:** Three remaining issues found in a review pass: the code
path that talks to the real hardware servo has no fallback if the
hardware-support software package isn't installed, unlike three other,
similar code paths elsewhere in the system that all degrade gracefully —
so enabling real-hardware mode without that package installed crashes the
whole system on startup instead of failing cleanly; input-validation
errors (for example, an invalid speed value) return a generic, differently
shaped error response compared to every other error in the system, meaning
the single most likely mistake an operator will actually make looks
different from every other error they might see; and one specific command
can block and produce no response for over a second under certain timing
conditions, which reads to the operator as an unresponsive button press.

**Acceptance:** each of the three either gets fixed or has a written
reason why the current behavior is acceptable.

---

**Summary:** Final sign-off of the maximum number of simultaneous operators, under real mechanical load
**Type:** Story · **Priority:** Medium · **Points:** 1 · **Status:** To Do

**Description:** Target: roughly three remote operators plus one person
connected directly by cable on site, all using the system at once with no
failures. This has already been measured and confirmed met on a bare test
bench with no mechanical load attached — three simultaneous remote
operators produced zero failures over a sustained test, and adding a
fourth simultaneous connection was also tested to establish exactly where
the system's real ceiling is. What remains is reconfirming this same
result now that there's a real mechanical load on the system, not further
software measurement.

**Acceptance:** the same simultaneous-operator scenarios reconfirmed with
the mechanism under real load, or a written reason why the bench result is
accepted as sufficient on its own.

---

**Summary:** Run the on-hardware test suite at least once
**Type:** Task · **Priority:** Medium · **Points:** 1 · **Status:** To Do

**Description:** There is a dedicated set of automated tests designed to
run directly on the real microcontroller hardware — covering basic
communication, configuration writes, landing accuracy and stop/hold
behavior — that has been written but never actually uploaded and executed
on real hardware, because it needs the servo disconnected from the
mechanism to run safely.

**Acceptance:** uploaded and run once with the servo disconnected from the
mechanism; the pass/fail results recorded.

---

**Summary:** Write front-end coding conventions and split one large interface file into smaller modules
**Type:** Task · **Priority:** Medium · **Points:** 5 · **Status:** To Do
**Requested by:** the operator · scheduled for after the next client demo unless brought forward

**Description:** The backend code has a written style guide; the
browser-side code does not. The main browser-side interface file has grown
to over two thousand lines with no internal module boundaries, which makes
it harder to navigate and to safely change one feature without risking
another. Two halves of work: write the missing style guide for the
browser-side code (comment style, function documentation conventions,
matching the shape already used in the backend guide); and split the large
file into smaller files organized by feature, using the browser's native
module support rather than a build tool (a build step isn't viable given
the fully disconnected deployment target). This is expected to help with
long-term maintainability and caching; it's explicitly not expected to
meaningfully change page load time on a local network, and shouldn't be
sold as a performance fix.

**Acceptance:** the style guide covers the browser-side code; the large
file is split into feature modules with no behavior change, confirmed by
actually using the interface on the real board afterward; existing
automated interface tests still pass unmodified.

---

**Summary:** Add architecture and data-model diagrams
**Type:** Task · **Priority:** Low · **Points:** 3 · **Status:** To Do

**Description:** The project currently has no visual diagrams at all,
despite spanning two separate processors, a serial communication bus, a
network relay layer and a browser interface — genuinely more moving parts
than a typical single-process project, where a diagram earns its keep more
than usual.

**Acceptance:** at minimum, one diagram showing the split between the two
processors and the path data takes from the browser to the servo, plus one
diagram of the database's table structure.

---

**Summary:** Finish populating structured error detail on the exceptions that don't have it yet
**Type:** Task · **Priority:** Low · **Points:** 2 · **Status:** To Do
**Roughly half-done already**

**Description:** The system's internal error-handling structure (a
three-tier hierarchy of error types, each carrying a distinct error code,
with one central handler instead of many scattered ones) is already built
and working. What's left is populating additional structured detail
(beyond just the error code) on several specific error types that don't
have it filled in yet, matching the pattern already used on the ones that
do.

**Acceptance:** every error type raised anywhere in the system carries
both a distinct error code and populated structured detail, not just the
code alone.

---

**Summary:** Add a proper abstraction layer above the database, matching the pattern already used elsewhere
**Type:** Task · **Priority:** Low · **Points:** 2 · **Status:** To Do

**Description:** Most of the system's data-access code already follows an
abstract-interface-plus-concrete-implementation pattern, except for the
database connection itself, which is currently a single concrete
implementation with no abstraction above it. Bringing it in line with the
rest of the codebase would make it possible to swap the underlying
database technology without touching anything outside that one
implementation.

**Acceptance:** nothing outside the one concrete implementation file
references the specific database technology by name.

---

**Summary:** Ongoing: trim verbose, outdated documentation as it's encountered
**Type:** Task · **Priority:** Low · **Points:** 1 (deliberately small and ongoing — do this only while already working on a document for some other reason, never as its own dedicated sweep, since a dedicated sweep costs about as much effort as it saves) · **Status:** To Do
**Requested by:** the operator

**Description:** Project documentation is read in full at the start of
every work session, so its length is a real, recurring cost. Several
documents predate a "keep everything concise" rule that now applies and
are still noticeably verbose.

**Acceptance:** no document states the same fact in two places; every
trimmed document keeps its actual numbers, decisions, and honest
statements of what has and hasn't been tested.

---

**Summary:** Remove duplicated constants and settle one piece of unused, untested code
**Type:** Task · **Priority:** Low · **Points:** 3 · **Status:** To Do

**Description:** Several small instances of the same value or the same
conversion logic existing independently in two places with nothing
enforcing that they stay in agreement: one geometric constant defined
separately in two firmware files; one string constant defined separately
in the backend and in the firmware; one configuration field that's stored
but never actually read anywhere; one hardcoded array size that isn't tied
to the configuration value it's supposed to match, which could silently
become an out-of-bounds bug if that configuration value is ever raised;
and one small conversion utility duplicated in two programming languages
that neither production code path actually calls. One of these carries a
real decision that needs to be made rather than just a fix: a geometry
conversion utility exists in the firmware but is never actually used by
the real firmware code path (only by its own test), while the backend
maintains its own separate, actively-used copy of the same math — either
wire the firmware copy into the real code path, or delete it along with
its test, since leaving an unused, untested second implementation lying
around is worse than either alternative.

**Acceptance:** each duplicated value either gets a single shared source,
or there's a written reason duplication is acceptable there; the unused
geometry-utility question is explicitly decided one way or the other, not
left unresolved.

---

**Summary:** Fix a startup-timing race that can silently drop the first boot-time log message
**Type:** Bug · **Priority:** Low · **Points:** 1 · **Status:** To Do
**Found while testing on real hardware**

**Description:** The microcontroller sends a "ready" notification within
milliseconds of finishing its own startup, but the backend software's
listener for that notification registers itself later in its own startup
sequence — and the underlying notification mechanism has no
acknowledgment or retry, so a notification sent before the listener is
ready is silently lost forever. Confirmed missing on a real board after
several minutes of uptime with nothing else lost. Currently believed to
only affect this one startup-time message, though whether the same
mechanism could drop a message later during normal operation hasn't been
tested, since nothing else has triggered the same failure mode yet.

**Acceptance:** either move the listener registration earlier in the
backend's startup sequence to shrink the timing window, or deliberately
trigger a similar notification later during normal operation to confirm
the same problem doesn't happen once the system is fully up.

---

**Summary:** Fix several automated tests that open a database file and never close it
**Type:** Bug · **Priority:** Low · **Points:** 2 · **Status:** To Do
**Found while chasing an unrelated, already-fixed test-suite issue**

**Description:** Nine places across the automated test suite create their
own direct database connection instead of going through the shared,
properly-managed connection the rest of the tests use — so none of the
nine get cleaned up automatically, and each one produces an unpredictable
"unclosed resource" warning somewhere later in the test run. Doesn't cause
any test to fail; simply hasn't been worth the time to fix nine separate
call sites yet.

**Acceptance:** each of the nine either properly closes its connection
when done, or there's a written reason the current pattern is fine as-is.

---

**Summary:** Let an operator dismiss a "may be outdated" warning on a saved position
**Type:** Bug · **Priority:** Low · **Points:** 2 · **Status:** To Do
**Found by:** the operator

**Description:** A saved position shows a small warning tag whenever it
was saved before the most recent time the mechanism was recalibrated. The
only current way to clear that warning is to fully re-save the position,
which isn't why someone would normally open that position's edit screen.
The predictable concern: after one recalibration, every position saved
before it carries the warning permanently, whether the actual drift is
meaningful or not, which starts to read as background noise rather than
useful information.

**Acceptance:** an operator can dismiss the warning on an individual saved
position, or on a whole batch of positions that just became stale from one
recalibration, without having to edit the position's name, description or
angle to do it.

---

**Summary:** Post-launch: motorize the manual mechanical safety clamp
**Type:** Story · **Priority:** Lowest · **Points:** Not sized — future phase, out of scope for the current delivery · **Status:** To Do

**Description:** After the current system is accepted, additional small
motors are planned to be added to physically restrain the main mechanism —
motorizing a clamp that currently has to be tightened and loosened by hand
with two screws. Once that exists, the intent is for the software's
position-lock control, the motor-isolation control, and this new physical
clamp to become a single unified "lock" concept rather than three separate
controls, since holding the physical clamp closed would let the main
motor's power be safely cut for long unattended stretches instead of being
kept energized continuously. Recorded now purely so the current lock
feature's design doesn't accidentally assume "digital-only" is permanent.

---

**Summary:** Post-launch: single-button emergency stop
**Type:** Story · **Priority:** Lowest · **Points:** Not sized — future phase, can wait · **Status:** To Do

**Description:** A single operator action that would engage the physical
safety lock and cut motor power at the same time, instead of requiring the
two to be triggered separately by hand. This is deliberately not being
built into the current position-lock and motor-isolation controls, so that
emergency stop still has a distinct, single meaning once it is added
later.

---
