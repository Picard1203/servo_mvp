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

### Q1 — What screen will you actually use? `answered`
**Blocks:** nothing now — see D7's updated acceptance criteria.

**The touch half is answered by the operator, 8 August 2026: it is not a touch
screen.** D15 was therefore designed for a pointer — the busy control uses
`disabled` plus a hover-safe pulse, and `style.css` carries a note saying what
to revisit if that ever changes. Recorded because it is the kind of assumption
that gets silently inherited.

**The viewport half, 26 August 2026: operator recalls iPad mini but isn't
sure, and decided the exact device isn't worth blocking on.** Verifying
against one unconfirmed model buys false precision; a responsive range covers
the uncertainty at no extra cost. D7's acceptance criteria changed
accordingly — see `docs/backlog/D.md`.

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
`timeout_keep_alive=5` (`main.py:172`), which holds each slot for five seconds
after use — set deliberately so idle sockets do not park a slot, and the direct
cause of the measured ceiling of about one new connection per second. Tuning
that moves capacity far more than the single spare socket does.

**Follow-up raised — see Q9.** The on-site answer may take that session off the
relay budget altogether, which would change this arithmetic completely.

**Update, 11 August 2026 (Session 3):** Replaced polling model with one persistent SSE stream per operator (`GET /api/v1/stream`). Reduced per-operator connection footprint from 4 sockets to 2 sockets (1 SSE + 1 mover). Three concurrent operators (6 sockets total) now fit 100% within the 6-socket ceiling with 0 connection drops.

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

### Q4 — Should motor isolation survive a reboot? `answered — promoted to ADR-0010`
**Decided 8 August 2026**, at the operator's instruction to make the call on
tradeoffs. **Full reasoning: `docs/adr/0010-motor-isolation-state-survives-a-reboot.md`**
(promoted from this entry 25 August 2026, ahead of R2's build).

Short answer: isolation latches, survives a reboot, and is re-applied at
startup before the servo can be commanded to do anything.

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

**Measured and confirmed, 30 August 2026 (Session 17):** USB-C access via `adb forward tcp:8001 tcp:8000` reaches Linux Uvicorn directly over the Docker bridge (`172.19.0.2:8000`). It bypasses the W5500 shield and SPI bus completely, consuming exactly **zero relay sockets**. Verified over 38.4 minutes of dual-link traffic in Run 3 (400+ commands over USB-C while 3 remote operators used the W5500, with zero socket drops and zero MCU relay counter impact). Tracked in R1, resolved.

### Q8 — Is there a date? `open`
**Blocks:** the cut line's usefulness.

Nothing in this repository states when the MVP is due. The one-to-two month test
run mentioned in T9 implies one exists.

*Needed:* the date, or confirmation that there is not one. A cut line without a
date is a preference; with one it is a plan.

### Q10 — Should code-level docs/comments carry rationale, or move to `docs/`? `answered`
**Answered by the operator, 26 August 2026.**

> *"Anything a function or a class wants to say is in the one-liner at the
> start of the function. If you can't put the description of the function
> in one line, consider splitting the function — under SOLID, and in
> general, functions should be single-responsibility. The logic behind* why
> *is more suited to the docs in the heavier manner, but removing the
> inline comments is something that 100% needs to happen, whether it goes
> to `docs/` or not."*

**Decided:** the docstring summary line and the typed `Args:`/`Returns:`/
`Raises:`/`Attributes:` blocks stay and get completed (types were never the
problem). The explanatory paragraph in between, and every inline comment,
go — **not deleted outright: relocated with judgment, and only where the
content is not already written down.** Each is checked against `docs/` (ADR,
`AUDIT.md`, `CLOSED.md`, or `skills/uno-q-st3215/SKILL.md`) first; genuinely
missing rationale is added there, distilled — content already covered is
simply deleted, not duplicated. This is not a naive copy-paste pass; see
T15's scope for how the Antigravity prompt states it. A docstring that
cannot fit one honest summary line is a signal worth reporting, weighed
under single-responsibility — not a rule that forces a split on its own.

`CONVENTIONS.md`'s Docstrings section and C++ section are rewritten to this
rule (26 August 2026). T15 unblocked; see its entry for the two-session
Antigravity split.
