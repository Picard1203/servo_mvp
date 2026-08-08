# Open questions

**Questions only a human can answer.** Not work — answers. Everything here blocks
or reshapes something in `BACKLOG.md`, and none of it can be resolved by reading
code, running tests or thinking harder.

Ask these **in one go**. They have been trickling out one at a time across three
documents, and each trickle costs a round trip to people who are not sitting
here.

Created 8 August 2026.

**Status key:** `open` · `answered` — when answered, write the answer here, move
the consequence into the item it blocks, and say who answered.

---

## For the operators

### Q1 — What screen will you actually use? `open`
**Blocks:** D7, and the layout half of every UI defect (D14, D15, D17).

The mechanical/ops discussion mentioned an iPad-class size; the exact model was
never recorded. The layout has only ever been eyeballed through devtools.

*Needed:* the device, or failing that the viewport in pixels, and whether it is
touch. Touch changes D15's answer — a busy control that cannot be pressed again
is a different design with a finger than with a mouse.

### Q2 — How many operators at once, really, and doing what? `open`
**Blocks:** R1, and the D13 decision that precedes it.

R1 says "roughly three remote plus one local USB-C session". Two things are not
stated: whether they are *watching* or *driving*, and whether they are on the
same site.

*Why it matters:* the measured ceiling is about **one new connection per
second** (six W5500 slots, each held ~5 s by `timeout_keep_alive`). A watching
operator costs almost nothing — the browser reuses one socket. A driving one
costs a slot per action. Three watchers and one driver is comfortable; four
drivers is not. **The answer changes whether D13 needs a fix or only a message.**

### Q3 — When the machine misbehaves on site, what do you want to be able to do? `open`
**Blocks:** nothing yet — **this is a gap, not a task.**

The site is roughly three hours away. That distance is the whole argument of
ADR-0007 (moves stay permitted while position is unverified, because refusing
turns a signal loss into a site visit). But there is **no written recovery
procedure**: no "if the UI will not load, do this", no way to restart the app
without `adb` or App Lab, and no statement of what is safe to do with a
mechanism attached.

*Needed:* who is on site, what they are allowed to touch, and whether a power
cycle is acceptable. Then it becomes a runbook item.

### Q4 — Should motor isolation survive a reboot? `open`
**Blocks:** R2.

Torque enable is a servo register (`kTorqueSwitch = 0x28`). A power cycle
re-energises the drive. If an operator isolated the motor deliberately and walks
away, the machine coming back energised is a surprise with a mechanism attached
— but *latching* it means a reboot cannot recover a stuck system remotely.

*Needed:* which surprise is worse in your setting. This is a safety judgement,
not a code decision.

---

## For whoever receives the MVP

### Q5 — What would convince you it is stable? `open`
**Blocks:** R6, and therefore the shape of R5.

R6 currently says "stable" cannot be written as a checklist and the plan is to
measure first and set the bar from what the measurements show. That is sound —
but the bar is being set by the people building it rather than the people
judging it.

*Needed:* the numbers or the demonstration that would satisfy the receiving
team. Hours of continuous operation? A count of failed commands out of N? A
recovery from a deliberately induced fault? **R5 should draw the graphs they
want to see, not the graphs we find easy.**

### Q6 — Are the handover artifacts we are planning the ones you need? `open`
**Blocks:** T5, R5.

Planned: an architecture diagram and ERD (T5), telemetry graphs over a chosen
window (R5), the on-target test tally (T3), and this document set.

*Needed:* confirmation, plus anything missing. Cheaper to ask now than to
discover at handover.

---

## For the programme

### Q7 — When do the extra servo bus adapters arrive? `open`
**Blocks:** T2, and the entire air-gapped path.

Stated as "within the month" (recorded 7 August 2026). The single existing
adapter sits on a coloured, internet-facing network and cannot be introduced to
the secure one, which is why the air-gapped path has **never been exercised**.

*Needed:* a date, or a decision to ship without it. The branch is already
written down in R7: adapters before the MVP is finished → box into the secure
network for handover; otherwise → hand over on the single coloured adapter. The
cut line in `PROJECT_STATE.md` assumes the second unless told otherwise.

### Q8 — Is there a date? `open`
**Blocks:** the cut line's usefulness.

Nothing in this repository states when the MVP is due. The one-to-two month test
run mentioned in T9 implies one exists.

*Needed:* the date, or confirmation that there is not one. A cut line without a
date is a preference; with one it is a plan.
