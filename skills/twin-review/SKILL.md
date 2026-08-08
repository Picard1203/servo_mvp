---
name: twin-review
description: Review a servo_mvp change from four perspectives at once — twin-path correctness, operator impact, relay and hardware safety, and doc truth — by dispatching parallel reviewers. On demand only, never automatic. Use when the user asks for a review, or before closing a change that touches sketch/src/, an error path, or anything with a mirror.
---

# Twin review

Four reviewers, one diff, in parallel. **Invoking this skill is the request to
spawn them** — it is never automatic, because it costs real tokens.

Named for what it hunts. Four defects in this repository are one defect: **a rule
applied to one path and not to its twin.**

| | the rule | the twin that did not know |
|---|---|---|
| `AUDIT.md` | the originals | — |
| D2 | `calibrate()` raised on an invalid reading | `capture()` stored `0` |
| D9 | motion used a mid-travel baseline | display used `0` — 212.7° of wrong movement |
| D10 | production `exception()` dropped the traceback | the test stub dropped it identically |

D2's twin was found only by **deleting** the lying method, which exposed two
further call sites nobody had counted — including `recover()`, which on a stalled
bus would have commanded count 0 and driven the mechanism to the bottom of travel
in the name of not moving it.

---

## What this review is NOT gated on

**Coverage.** Do not report a coverage number as a verdict, and do not accept one
as evidence. This project runs 192 tests at 100% line coverage of `app/`. That
did not prevent the six defects in `AUDIT.md`, and it did not prevent D9, where
the correct rule and its violation sat twelve lines apart in the same file — the
correct one carrying a six-line docstring explaining precisely why a baseline of
0 is wrong, and the other doing it anyway. Both covered. Both green.

Report defects. Coverage is not one.

---

## How to run it

1. **Get the diff.** `git diff` against the branch point, or the paths the user
   names.
2. **Dispatch four reviewers in parallel**, one message, four `Agent` calls. Give
   each the diff scope, its lens below, and **this instruction verbatim**:

   > Run `graphify query "<question>"` before reading any source file.
   > `graphify-out/graph.json` exists; a query returns a scoped subgraph at a
   > fraction of the tokens. Read whole files only to inspect specific lines the
   > graph pointed you at. Report only defects you can name a concrete failure
   > for — inputs or state, and the wrong result they produce. Do not report
   > style, and do not report coverage.

3. **Merge, dedupe, rank** by whether an operator or the mechanism is affected.
4. **Iteration cap: 2.** If a finding is still contested after two passes,
   escalate it to the user with both positions stated. Do not loop.

---

## The four lenses

### 1. Twin path
Every guard, conversion, baseline, validity check and error handler in the diff:
**where is its mirror, and does it know?** Look for the same concept computed in
two places, a check on one branch of a pair, a stub that mimics production, a
method whose name promises less than it discards. Prefer deleting the lying
thing over guarding today's call site — that is what closed D2.

### 2. Operator impact
What changes on screen? What happens on failure, on refusal, on slow? Can a
non-programmer act on what they are shown? Load the `operator-lens` skill for the
five questions. A correct API response that reads as "broken" is a defect here
(D11), and a correct refusal that reads as nothing at all is a worse one (D13).

### 3. Relay and hardware safety
Only if the diff touches `sketch/`, the relay, the Bridge or timing. Read
`sketch/src/RELAY_NOTES.md` first — it is non-negotiable, and rule 7 exists
because there was no mutex anywhere in `sketch/src/` while two threads shared one
W5500 on one SPI bus. Check specifically:

- **`loop()` still yields.** Starve it and `servo_read` hits its 10 s timeout.
- **Every W5500 touch is inside the lock, and no sink is dispatched while
  holding it** — holding it across a sink deadlocks against `net_tx`.
- **Six sockets are not six resources.** One chip, one bus.
- **Log volume is budgeted** against T9 before it crosses the Bridge.
- Bridge payloads are CSV strings (ADR-0006) and both sides must still agree:
  `python3 tools/check_bridge_contract.py`.

### 4. Doc truth
- Does `docs/BACKLOG.md` still describe reality? An item is not done until its
  entry says so.
- **One fact lives in exactly one file.** Two copies is a defect — find every
  copy of any number or path the diff moved.
- Does the change contradict an ADR? If so it must be surfaced, not silently
  overridden.
- Do the three verification numbers quoted in the docs still match what the
  commands print?

---

## Reporting

Findings ranked most-severe first, each with a concrete failure scenario —
inputs or state, and the wrong output. Use `ReportFindings` if the host is
rendering a review; otherwise report as prose grouped by lens.

Say plainly which findings were **verified by running something** and which are
**read from the code**. That distinction is the house rule, and in a repository
whose defects have all lived in four untested files it is the only honest way to
report.
