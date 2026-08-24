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

### Q1 — What screen will you actually use? `half answered`
**Blocks:** D7, and the layout half of D17. **No longer blocks D15.**

**The touch half is answered by the operator, 8 August 2026: it is not a touch
screen.** D15 was therefore designed for a pointer — the busy control uses
`disabled` plus a hover-safe pulse, and `style.css` carries a note saying what
to revisit if that ever changes. Recorded because it is the kind of assumption
that gets silently inherited.

**The viewport half is still open, and D7 is still blocked on it.** The
mechanical/ops discussion mentioned an iPad-class size; the exact model was
never recorded, and "not touch" does not settle the pixels — a wall-mounted
panel and a laptop are both pointer-driven and lay out nothing alike. The
layout has still only ever been eyeballed through devtools.

*Still needed:* the device, or failing that the viewport in pixels.

### Q2 — How many operators at once, really, and doing what? `answered`
**Answered by the operator, 8 August 2026.**

> *"It would be open on the operator remote screen, and if I go and connect on
> site I would see the same site, and then headroom for one more."*

**The target: the remote screens, plus one on-site session, plus one spare.**
They are *watching* — screens left open — with driving as the occasional act.
That is the cheap case: a browser that is only polling reuses one connection.

**The hardware ceiling, now established.** `sketch/src/Config.h:44` already
recorded it, and it answers the operator's question about whether the limit can
be raised:

> *"The W5500 has 8 hardware sockets and the listener consumes one."*

So **7 concurrent client connections is a hard ceiling** and the code takes 6.
Raising `kMaxRelaySockets` buys **exactly one more slot**. It is not a tunable —
it is a wall one step away.

**Which means the socket count is not the lever.** The real one is uvicorn's
`timeout_keep_alive=5` (`main.py:142`), which holds each slot for five seconds
after use — set deliberately so idle sockets do not park a slot, and the direct
cause of the measured ceiling of about one new connection per second. Tuning
that moves capacity far more than the single spare socket does.

**Follow-up raised — see Q9.** The on-site answer may take that session off the
relay budget altogether, which would change this arithmetic completely.

### Q3 — When the machine misbehaves on site, what do you want to be able to do? `answered`
**Answered by the operator, 8 August 2026.**

> *"On site seems to me the same way a remote one can see, but with access to
> `adb` because they are USB-C connected and not through the relay."*

**So the on-site session is the same UI, plus `adb`.** Whoever is on site can
read logs, restart the app, and query the database directly — the full
diagnostic surface, which the remote operators do not have.

**Consequences:**

- The recovery procedure has two halves, and only one of them is a document.
  Remote: what the operator can do from the UI alone. On site: the `adb`
  commands, in order, with what is safe to run while a mechanism is attached.
  **Neither is written down** — this is now a build item, not a question.
- **On-site is the diagnostic seat.** D10's unexplained sampler exception, and
  anything the soak surfaces, will be caught by whoever is holding the USB-C
  cable. Give them the commands in advance rather than at the moment.

**Raises Q9**, below.

### Q4 — Should motor isolation survive a reboot? `answered — engineering decision`
**Decided 8 August 2026**, at the operator's instruction to make the call on
tradeoffs. **Wants an ADR before R2 is built.**

**Decision: isolation latches. It survives a reboot, and is re-applied at
startup before the servo is commanded to do anything.**

The reasoning, and the tradeoff it turns on:

- **Isolation is a protective act, so its safe state is the one that persists.**
  A watchdog restart, a power blip or an App Lab redeploy silently re-energising
  a mechanism somebody chose to make safe is the failure that hurts people. The
  competing risk — a reboot leaving the system dead — hurts a schedule.
- **The ADR-0007 argument does not transfer, and that is the crux.** ADR-0007
  refuses to gate movement on calibration because clearing that state needs
  somebody *physically present*, three hours away. **Clearing isolation does
  not.** It is one click in the same UI the remote operator already has open. A
  latched state that can be cleared remotely costs a click; an unlatched one
  costs a surprise.
- **It must be visible, not merely stored.** On boot the UI has to say the drive
  is isolated and that it was isolated *before the restart* — an operator who
  does not know why the machine is dead will power-cycle it, which under this
  decision changes nothing and wastes the trip.
- **The register is not the record.** `kTorqueSwitch = 0x28` re-enables on servo
  power-up regardless, so the latch lives in the database as operator intent and
  is re-applied at startup. That ordering matters: re-apply **before** any move
  can be accepted, or a queued command wins the race.

**Reopen this if** R8 (emergency stop) or R4 (unified Lock) changes the model —
an e-stop almost certainly latches too, and the two should agree.

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

### Q9 — What can the on-site person do? `answered`
**Answered by the operator, 8 August 2026.**

> *"The on-site should be able to do everything a dev — either there or at home
> base — tells him to do, just like we are developing now."*

**So on-site has the full development surface**, not a restricted operator
subset: `adb`, the sshfs mount, logs, the database, app start and stop — the
same access this project is being built with. The runbook (T10) can therefore
assume a competent pair of hands taking instructions, which makes it a
*reference* rather than a script that must anticipate everything.

**One half of this is not a preference and stays open as measurement, not as a
question:** whether USB-C traffic actually bypasses the W5500 is a fact about
the hardware. If it does, the on-site session costs **zero relay sockets** and
the budget is the remote screens alone — the difference between a comfortable
margin and none. It gets settled during the soak by reading the MCU counters,
which is one more reason the logging work comes first. **Until measured, R1 must
not be reported as met on the strength of it.** Tracked in R1, not here.

### Q8 — Is there a date? `open`
**Blocks:** the cut line's usefulness.

Nothing in this repository states when the MVP is due. The one-to-two month test
run mentioned in T9 implies one exists.

*Needed:* the date, or confirmation that there is not one. A cut line without a
date is a preference; with one it is a plan.
