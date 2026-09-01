---
name: twin-review
description: Review a servo_mvp change, or the whole app in one sitting, from several lenses at once — twin-path correctness, operator impact, relay and hardware safety, doc truth, and general correctness — by dispatching parallel reviewers, only the lenses the scope calls for. On demand only, never automatic. Use when the user asks for a review, or before closing a change that touches sketch/src/, an error path, or anything with a mirror.
---

# Twin review

Several reviewers, one scope, in parallel. **Invoking this skill is the request
to spawn them** — it is never automatic, because it costs real tokens.

Named for what it hunts. Four defects in this repository are one defect: **a rule
applied to one path and not to its twin.**

| | the rule | the twin that did not know |
|---|---|---|
| `docs/history/AUDIT.md` | the originals | — |
| D2 | `calibrate()` raised on an invalid reading | `capture()` stored `0` |
| D9 | motion used a mid-travel baseline | display used `0` — 212.7° of wrong movement |
| D10 | production `exception()` dropped the traceback | the test stub dropped it identically |

D2's twin was found only by **deleting** the lying method, which exposed two
further call sites nobody had counted — including `recover()`, which on a stalled
bus would have commanded count 0 and driven the mechanism to the bottom of travel
in the name of not moving it.

Twin path is only one of the lenses below, not the whole skill — a plain logic
error with no "twin" shape needs lens 5.

---

## What this review is NOT gated on

**Coverage.** Do not report a coverage number as a verdict, and do not accept one
as evidence. This project gates `app/` at 99% line coverage (`tools/verify.py`).
That did not prevent the six defects in `docs/history/AUDIT.md`, and it did not prevent D9,
where the correct rule and its violation sat twelve lines apart in the same
file — the correct one carrying a six-line docstring explaining precisely why a
baseline of 0 is wrong, and the other doing it anyway. Both covered. Both green.

Report defects. Coverage is not one.

---

## Scope: diff or inventory

Two modes. State which one is running before dispatching anything.

**Diff mode (default).** `git diff` against the branch point, or the paths the
user names. One dispatch round, all applicable lenses, on that diff.

**Inventory mode (whole app, one sitting).** No diff — the target is the current
state of the codebase. **Never hand a reviewer "the whole codebase."** Split into
the chunks this repo already has, and dispatch lens × chunk:

| Chunk | Path |
|---|---|
| Backend | `python/app/` |
| Firmware | `sketch/src/` |
| Frontend | `python/static/` |
| Docs | `docs/`, `CLAUDE.md`, `docs/CONTEXT.md`, `docs/CONVENTIONS.md`, `docs/adr/` |

**Backend chunk has a deterministic pre-pass: `ruff`.** `python/ruff.toml`
encodes the machine-checkable subset of `docs/CONVENTIONS.md` (typing, docstring
shape, unused imports/args, import order). Run
`../.venv/bin/ruff check python/app --config python/ruff.toml` before
dispatching any reviewer at that chunk — advisory only, not part of
`tools/verify.py`'s gate, so a nonzero exit is informational, not a blocker.
**Where ruff and `docs/CONVENTIONS.md` disagree, `docs/CONVENTIONS.md` wins** — the
config was adapted from a general personal standard, not written for this
repo, and docs/CONVENTIONS.md is the authority (e.g. `UP` is deliberately not
selected: it would push `Optional[X]` toward `X | None`, the opposite of this
repo's Types rule).

State plainly what inventory mode did **not** look at, rather than silently
skipping it: `sketch/sketch.ino`, `sketch/tests/OnTarget/OnTarget.ino` and
`python/static/style.css` have no graphify extraction (`CLAUDE.md` §1) — a
reviewer relying on `graphify query` alone will miss them. Route these to the
C++/plain-text grammar manually, or name them explicitly as unreviewed. The
same "verified vs. read" honesty this skill asks of findings applies to
coverage of the scope itself: say what was not looked at.

Five lenses × four chunks is twenty dispatches, not one five-way parallel
message — see the token budget note below before running this.

---

## How to run it

1. **Fix the scope** (above) — diff, or inventory chunks.
2. **Pick the lenses.** In diff mode, generalize lens 3's existing rule to all
   five: a lens applies if the scope could plausibly trigger it, skip it if not.
   In inventory mode **skip nothing** — every chunk gets every lens that plausibly
   touches it (lens 3 still gates on whether the chunk is `sketch/`/relay/Bridge/
   timing at all; the rest apply to every chunk). Selection is a diff-mode cost
   control, not an inventory-mode one — chunking is what controls inventory cost.
3. **Dispatch in parallel**, one message per chunk (or one message total in diff
   mode): an `Agent` call per lens 1–4 that applies, and lens 5 via the `Skill`
   tool (`skill: "code-review"`, target = the chunk path in inventory mode or
   omitted in diff mode, effort `medium` unless raised — see lens 5). Give every
   `Agent`-dispatched reviewer the scope, its lens below, and **this instruction
   verbatim**:

   > **Narrow before you reason.** Before reading any source file, build your
   > candidate list with a tool, not by skimming: `graphify query "<question>"`
   > for a scoped subgraph, and/or a targeted `grep`/`git log` for the concept
   > this lens hunts (each lens below names one). Read whole files only for the
   > specific lines a tool pointed you at. If a check is answerable by running a
   > command instead of reasoning about it — the lens below may name one — run
   > the command and report its output; do not re-derive by inference what a
   > command already answers exactly and more cheaply.
   > Report every defect you can name a concrete failure for — inputs or state,
   > and the wrong result they produce. Do not report style, and do not report
   > coverage. **There is no cap on findings** — narrowing the input is how this
   > stays cheap; trimming the output is not, and would mean missing real
   > defects. What *is* forbidden: no restating the scope, no "checked and
   > clean" inventory of what you looked at, no methodology narration, no
   > re-verifying a fact this prompt already stated.

   A three-reviewer diff-scoped run has cost ~218k tokens by skipping exactly
   this discipline — re-derived context, self-run verification, long "checked
   and clean" prose, and reasoning across raw files a tool could have narrowed
   first. Inventory mode multiplies the reviewer count; hold this line strictly
   or the run eats the rest of the session's budget. The saving comes from
   *narrowing what each reviewer reads*, not from asking them to find less.
4. **Merge, dedupe, rank** by whether an operator or the mechanism is affected.
5. **Iteration cap: 2 — diff mode only.** If a finding is still contested after
   two passes, escalate it to the user with both positions stated. Inventory
   mode is **findings-only**: write what was found (see Reporting) and leave
   adjudication to whoever triages the file next session — do not loop there.

---

## The five lenses

### 1. Twin path
Every guard, conversion, baseline, validity check and error handler in scope:
**where is its mirror, and does it know?** Look for the same concept computed in
two places, a check on one branch of a pair, a stub that mimics production, a
method whose name promises less than it discards. Prefer deleting the lying
thing over guarding today's call site — that is what closed D2.

**Narrow with a tool first.** Don't read every file hunting for pairs by eye —
enumerate candidates mechanically, then reason only about the matches:
`graphify query` for the concept in play (`"baseline computation"`,
`"error handling"`, `"validity check"`) returns the nodes that touch it
pre-linked; a plain `grep -rn` for the keyword family (`baseline|calibrat|
capture|_verified|except |raise `) finds the rest in one pass. Every twin-shape
defect this project has found (D2, D9, D10) had two matching hits for the same
concept — the tool finds the pair, the reviewer only has to judge whether they
agree.

In `python/app/`, run `ruff check --select ARG,SIM,PLC0415` first — unused
arguments and suppressible exceptions are exactly the shape of a guard whose
twin was never wired up. Ruff finds the mechanical half; only the "does the
mirror agree" judgment is left to the reviewer.

### 2. Operator impact
What changes on screen? What happens on failure, on refusal, on slow? Can a
non-programmer act on what they are shown? Load the `operator-lens` skill for the
five questions. A correct API response that reads as "broken" is a defect here
(D11), and a correct refusal that reads as nothing at all is a worse one (D13).

### 3. Relay and hardware safety
Only if the scope touches `sketch/`, the relay, the Bridge or timing. Read
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

**Don't re-derive what a tool already guarantees.** `cd sketch/tests/native &&
make` runs `-Wall -Wextra -Wpedantic -Werror` — if it passes, type mismatches,
uninitialized reads and unused results are already ruled out; spend no
reasoning rediscovering them. Judgment is needed only for what the compiler
cannot see: cross-thread ordering around the W5500, timing budgets, and
protocol-level agreement between the two sides of the Bridge.

### 4. Doc truth
- Does `docs/BACKLOG.md` still describe reality? An item is not done until its
  entry says so.
- **One fact lives in exactly one file.** Two copies is a defect — find every
  copy of any number or path the scope moved.
- Does the change contradict an ADR? If so it must be surfaced, not silently
  overridden.
- Do the verification numbers quoted in the docs still match `tools/verify.py`
  and `tools/verify_baseline.json`? **Do not trust a count written in prose** —
  that is exactly how D24 sat wrong for months.

**This one is fully mechanical — don't eyeball it.** `grep -rnE '[0-9]+ (tests|
checks|assertions|defects)'` across the touched docs to pull every quoted
number, run `python3 tools/verify.py`, and diff the two sets programmatically.
Only a mismatch needs a judgment call (is it a stale doc, or a deliberate
change nobody wrote down); a match needs none.

For `python/app/`'s own docstrings, `ruff check --select D` checks the Google
convention directly (`[lint.pydocstyle] convention = "google"` in
`python/ruff.toml`) — missing `Attributes:`, a missing `__init__` docstring,
a summary that isn't one line. It does not check the type-in-parens or
no-explanatory-paragraph rules (`docs/CONVENTIONS.md` goes further than pydocstyle
there); those still need a reviewer's eye.

### 5. General correctness
The other four lenses are each specialised; none is a plain bug hunt, so a
logic error with no "twin" shape (wrong comparison, off-by-one, a leak with no
mirror) can pass all four uncaught.

For `python/app/`, run `ruff check python/app --config python/ruff.toml`
before dispatching this lens and hand its output to whatever runs `code-review`
below — unused imports, unnecessary casts (`RUF046`), unused arguments are
answered already; the `code-review` pass should spend its reasoning on what
ruff cannot see, not rediscover what it already reported.

Composed by reference, not reimplemented:
invoke the `code-review` skill directly via the `Skill` tool at effort `medium`
(raise it for a chunk already flagged risky by the other lenses), target = the
chunk path in inventory mode, omitted (current diff) in diff mode. Keep only its
correctness findings for this report — its reuse/simplification/efficiency
findings are cleanup, not defects, and out of this skill's mandate (see
"What this review is NOT gated on" — the same "report defects, not style" rule
applies here).

---

## Reporting

**Diff mode.** Findings ranked most-severe first, each with a concrete failure
scenario — inputs or state, and the wrong output. Use `ReportFindings` if the
host is rendering a review; otherwise report as prose grouped by lens.

**Inventory mode.** Write every finding to `docs/REVIEW_FINDINGS.md`, one entry
per finding, self-contained — the session that triages it has no memory of this
run. Fixed fields per entry: `file:line`, plain-language issue, why it matters,
severity, proposed fix. `REVIEW_FINDINGS.md` is a **transient triage input**,
not a second backlog — `BACKLOG.md` is still the only list of open work; once
an entry is triaged it either becomes a `D`/`T`/`R` item or is dropped, and the
file is not maintained as a permanent record.

Say plainly which findings were **verified by running something** and which are
**read from the code**. That distinction is the house rule, and in a repository
whose defects have all lived in four untested files it is the only honest way to
report.

---

## Not yet scoped

Folding this into `deliver`'s own pipeline (`skills/deliver/SKILL.md`) rather
than leaving it a manual on-demand step — raised, not decided. Do not bundle it
into this change.
