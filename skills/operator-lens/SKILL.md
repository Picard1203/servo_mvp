---
name: operator-lens
description: Look at the servo_mvp system as the operator or the receiving team sees it, not as the developer does — walk the control surface, find what is unexplained, unreachable or silently wrong, and file findings into docs/BACKLOG.md. Use before planning operator-visible work, after UI or error-path changes, and when organising the backlog by product value rather than by code.
---

# Operator lens

**The end users are not programmers, and the receiving teams are deciding whether
to procure this.** Both judge the system by what it does on screen, not by what
its API returns.

This skill exists because of a measurable pattern: **the defects that matter most
here were found by an operator on hardware, not by 192 tests.** D9, D10, D11, D12
and D13 all came out of one board session. None were on any list beforehand.

---

## Rule zero

`graphify query` before reading source. Same rule as everywhere in this repo —
see `CLAUDE.md` §1. Pass it to any sub-agent.

---

## The control surface

Everything the operator can do, and where it lives:

| Control | Front end | Back end |
|---|---|---|
| Move to angle, at speed | `doMove()` `python/static/app.js` | `POST` move, `routers/servo.py` |
| Stop | `doStop()` | `routers/servo.py` |
| Lock / unlock | `toggleLock()` | `routers/servo.py` |
| Calibrate (set the datum) | `doCalibrate()` | zeros |
| Save a named zero | `doSave()` | zeros |
| Activate a saved zero | `doUse()` | zeros |
| Recover from overload | `doRecover()` | motion |
| Position + status readout | polling `state`, `renderState` | `GET` state |
| CSV export | export control | `routers/telemetry.py` |

`apiPost()` and `asApiError()` in `app.js` are where every failure the operator
ever sees is shaped. Look there when the question is "what did they actually
see?"

---

## The five questions, per control

Ask all five. The interesting answers are almost never in the success path.

1. **On success, what changes on screen?** Is it enough to believe it worked?
2. **On failure, what does the operator see — and can a non-programmer act on
   it?** "Error" is not an answer. Neither is silence.
3. **On refusal, is it distinguishable from failure?** *D13: it is not.* The
   relay refuses politely and correctly when all six W5500 slots are busy; the
   operator sees nothing happen and presses again. "First press does nothing" is
   the single most damaging behaviour in a procurement demo.
4. **On slow, what holds the screen?** A first paint of unknown duration (D6) and
   a poll that used to shout OFFLINE at one dropped packet (D11) are the same
   question asked twice.
5. **Is there a route back?** *D12: from an activated saved zero there is no
   control meaning "return to the datum".* The information exists — the datum is
   a row in `zeros` flagged `is_datum` — the operator route to it does not.

---

## The four failures worth memorising

They are the evidence that this lens finds things tests do not.

- **D9 — the screen said 0.0, the machine moved 212.7°.** Nothing malfunctioned.
  Motion used a mid-travel baseline, display used 0. Both internally consistent,
  against different baselines, twelve lines apart in one file. The operator
  commanded 90 from a screen reading 0 and watched seven seconds of wrong
  movement.
- **D13 — a correct refusal, presented as nothing at all.**
- **D12 — a state the operator can enter and not leave.**
- **D11 — one lost packet presented as "connection lost".** Honest at the API
  (`reading_valid: false`, per ADR-0008), and it reads as *broken* to the person
  in front of it. Now paced at three consecutive failures; the split between an
  honest contract and a calm surface is deliberate.

**The pattern:** every one is a gap between what is *true* and what is *shown*.
That gap is this skill's entire search space.

---

## Also wear the client's hat

The receiving teams judge whether to procure a full project. Ask what they will
ask:

- **"Show me it is stable."** Can we? R6 says "stable" is still an adjective. R5
  (time-range telemetry pull and graphs) is what turns it into a number, and it
  is **in MVP and not started.**
- **"How many operators at once?"** R1 targets ~3 remote plus 1 local. The only
  enforced limit anywhere is `kMaxRelaySockets = 6`, and one browser can open six
  connections by itself.
- **"Show me the architecture."** T5 — no diagrams exist, in the most complex of
  the three sibling projects.
- **"Run it for two months — does it fit?"** T9 measured it: ~208 MB/month
  telemetry, ~188 MB/month log at DEBUG, against 2.6 GB free. It fits; nothing
  enforces it.
- **"What do we do when it misbehaves?"** The site is ~3 hours away (ADR-0007's
  central argument) and there is no written recovery procedure.
- **"Can we cut drive power without losing sensors?"** R2 — feasible in firmware
  via `kTorqueSwitch = 0x28`, **in MVP, and not designed.**

---

## Output — file it, do not just say it

Findings go into `docs/BACKLOG.md`, in the house format, and nowhere else.
`BACKLOG.md` is the only list of open work in the repo; a finding that lives in a
chat transcript does not exist.

```markdown
### D<n> — <what the operator experiences, in their words>
**Status:** open · **Severity:** high|medium|low · **Found by:** operator lens

<What they see. What is actually happening underneath. Why the gap matters.>

**Acceptance:** <observable from the operator's seat, not from the API>

**Related:** <other items>
```

Rules for filing:

- **Title it by symptom, not by cause.** "First press does nothing" outranks
  "connection refused when slots are exhausted" — the cause belongs in the body.
- **Acceptance must be observable from the operator's seat.** "Returns 409" is
  not acceptance; "the operator is told the system is busy and to try again" is.
- **Separate questions from work.** Anything that needs a human answer — target
  screen size (D7), real operator count (R1), adapter ETA (R7) — is a question
  for the operator, not a task. Collect them and ask in one go rather than
  trickling.
- **Do not invent severity.** High means it damages a demo or endangers the
  mechanism. Say which.
