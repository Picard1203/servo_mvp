---
name: deliver
description: Take a backlog item or a stated need in the servo_mvp project from "we need X" to done — orient on the graph, plan, stop once for approval, then run the whole thing including tests, verification, docs and the backlog entry. Use whenever the user names a backlog item (D3, T1, R5…) or says "we need to…" about this project.
---

# Deliver

The execution loop for this repository, made runnable instead of readable. It is
`docs/WORKFLOWS.md` with the checkpoints enforced.

**One stop, at the plan.** Everything before it is cheap orientation; everything
after it runs to completion without asking again.

---

## The rule that overrides your instincts

**Do not read source to orient yourself.** `graphify-out/` holds the AST of every
file fused with the rationale in the docs. A query returns a scoped subgraph at a
fraction of the tokens.

```bash
graphify query "<the question>"          # ALWAYS first
graphify query "<q>" --budget 3000       # when truncated
graphify explain "<node id>"             # beats opening the file
graphify path "<A>" "<B>"                # how two things relate
```

Read whole files only to **edit or debug specific lines**, after the graph has
pointed at them. Pass this rule to every sub-agent you dispatch.

---

## Phase 0 — Orient (cheap, no approval needed)

1. **Read the backlog entry verbatim.** `docs/BACKLOG.md` is the only list of open
   work. The entry's *Original report follows* section is usually where the real
   reasoning lives — read it, do not skim to the acceptance line.
2. **Read the flow** if the entry names one (`WORKFLOWS.md` W1–W7).
3. **Check for an ADR that governs it** (`docs/adr/`). If your change contradicts
   one, say so out loud — *"Contradicts ADR-000N because…"* — and do not silently
   override it.
4. **`graphify query`** for the code involved.
5. **Baseline the numbers** before touching anything — `tools/verify.py`, not
   a count quoted here, is the source of truth (a number written into this
   file is exactly what let a stale count survive for months, per
   `CLAUDE.md` §3):

```bash
python3 tools/verify.py   # compares against tools/verify_baseline.json
```

If the baseline is already wrong, stop and say so. Do not start work on a repo
that does not match its own documentation.

---

## Phase 1 — Plan, then STOP

**Plan inside Claude Code's plan mode** (`EnterPlanMode`, then
`ExitPlanMode` to present) — do not present the plan as chat prose instead.
Adopted 25 August 2026: a chat-prose plan on this batch described fixes
without explaining the problems, which made it unreviewable by anyone not
already holding the code in their head; the plan-mode file forced the
problem-first structure below and made the approval a real gate. Phase 0's
baseline commands run **before** entering plan mode — plan mode forbids
changing the system, and that includes running the verification commands.

Use the `writing-plans` skill for the mechanics inside the plan file. Every
item in the plan must state, **in this order and in plain language a
non-programmer stakeholder could act on**:

1. **What is wrong right now, described in plain language before any fix is
   mentioned** — what the operator or reader actually sees or experiences
   today, not the name of the broken function. A reviewer who has not read
   the code must be able to tell whether the plan solves their actual
   problem from this sentence alone.
2. **What the operator will be able to do afterwards that they cannot do now**
   — or, for a defect, what stops happening. If you cannot write this
   sentence, the item is not understood yet.
3. **Which files change**, with paths.
4. **What gets tested, and what is only assumed.** Say it plainly. 99% line
   coverage did not prevent the six defects in `docs/history/AUDIT.md`, nor D9, where the
   correct rule and its violation sat twelve lines apart in one file, both
   covered, both green.
5. **The twin-path question, answered**: *where is this rule's twin, and does it
   know?* Four defects in this repository are the same defect — a rule applied to
   one path and not its mirror (`docs/history/AUDIT.md`'s originals, D2's `calibrate()` but not
   `capture()`, D9's two baselines, D10's production logger and its test stub).
   Answer this in the plan, not after the review.
6. **Anything that needs the board**, listed separately — see Phase 3.
7. **The numbers you expect afterwards**, so a change in them is visible.

Use `AskUserQuestion` inside plan mode to settle a real judgment call before
writing the final plan — do not silently pick one and only mention it in
passing.

**If the item is a hardware experiment, not a code change** (a D-item shaped
like D48 — tuning a register, diagnosing a physical failure mode, anything
whose evidence is trial repeats rather than a test suite): the plan itself
must state, before Phase 2 starts, the same things D48's own protocol
required and D40d's post-mortem found missing — a pre-declared pass/fail bar
written down before any trial runs, the sample size behind it, and which
variable moves alone versus in a factorial. Use `experiment-design` for the
matrix shape (single-variable isolation, factorial vs. sequential
elimination) and `statistical-analysis` for the actual sample-size number
instead of a round one. `pre-registration-writing` and `hypothesis-building`
carry the same discipline from social-science methodology if the plan needs
a more formal falsifiable-claim structure — use them for the underlying
"declare the bar before you see the data" logic, not for their registry or
survey-specific apparatus, which doesn't apply here.

**Then call `ExitPlanMode`.** This is the only checkpoint. Wait for
go-ahead — and if it comes back as pushback rather than approval, use
`receiving-code-review`'s discipline: verify the specific objection against
the actual plan rather than performatively agreeing and rewriting.

---

## Phase 2 — Run it, all of it

On go-ahead, execute the whole plan without further prompting. Use
`executing-plans` for batching and checkpoint discipline.

- **If `docs/sprint/SPRINTS.md` exists, this item is in an active sprint — mark its
  Start time there before the branch is even created.** Get a real clock
  time (ask the operator, or `date`), not a wall-clock guess from session
  start — deductions in the sprint's own capacity table (meals, cleaning,
  any declared-absent window) are not working time and starting from
  session-start-minus-nothing double-counts them. This was skipped once
  (1 Sept 2026, D39) and produced a wrong retro that had to be corrected
  twice in the same session, once for exactly this reason.
- **First action, before any edit: create the feature branch.**
  `git checkout -b feature/<name> dev`, named for what the item does (see
  `docs/CONVENTIONS.md`'s Git section for the naming rule — one branch per
  feature, not per session). This was written down once already and
  ignored for 16 days because nothing enforced it (24 Aug 2026, T15); it is
  enforced here now so it does not need to be remembered by hand. Merge
  back into `dev` with `--no-ff` as the last step of Phase 5's commit, not
  before — the branch is where the work happens, not a label added after.
- **Test-first where the code is testable.** Use the `tdd` skill. RED must
  actually fail for the stated reason before you write GREEN.
- **Root cause before any fix, always.** Use `systematic-debugging` — read
  the error fully, reproduce it, form one hypothesis, test it minimally.
  Three failed fixes in a row means the architecture is wrong, not that a
  fourth attempt is due.
- **Never bundle unrelated changes into a fix.** If you spot something else,
  write it into `BACKLOG.md` as a new item and carry on.
- **Use the glossary's words** (`docs/CONTEXT.md`): `timestamp` never `ts`, `count`
  never `tick`, `datum` never `home`. In code, tests, commits and the backlog.
- **Follow `docs/CONVENTIONS.md`.** Where it marks something undecided, ask rather
  than choosing silently.
- **Before touching `sketch/src/`, read `sketch/src/RELAY_NOTES.md`.**
  Non-negotiable. In particular rule 7: the W5500 is one chip on one SPI bus
  reached from two threads, and `loop()` must still yield or the Bridge thread
  starves into a 10 s timeout.
- **High-volume, low-reasoning work goes to Antigravity.** `writing-plans` output
  with exact paths and verification steps is the handoff artifact. Its skill
  target is `~/.agents/skills`.

---

## Phase 3 — Hardware never runs unattended

Anything that touches the board **stops and hands you the commands**. Claude does
not drive the servo, and does not claim a hardware result it did not watch.

```bash
adb shell arduino-app-cli app start user:servo_mvp   # ~16s warm, ~7min cold
adb shell arduino-app-cli app logs  user:servo_mvp
```

The working copy is usually a **network mount of the board** (CIFS/Samba as of
25 August 2026 — check `CLAUDE.md` §6, the protocol has already changed once),
so edits are already there — but `python/.env` must exist on the board or
`use_hardware_servo` defaults
to false and the simulator runs while the UI moves convincingly (backlog D8).
Confirm `servo.backend backend=hardware` in the log before believing any hardware
observation.

Board runs are worth doing at `LOG_LEVEL=DEBUG` for the duration and INFO
afterwards. Exceptions in the sampler now name themselves in the log (D10,
closed) — read the JSONL record itself rather than a summary of it if one
appears; a paraphrase of a traceback is not the traceback.

---

## Phase 4 — Verify

```bash
cd python && pytest
cd sketch/tests/native && make
python3 tools/check_bridge_contract.py
graphify update .
```

**If the numbers moved, stop and say so.** Do not explain them away in
passing — `verification-before-completion`'s iron law is exactly this: no
completion claim without fresh evidence run in this message, "should pass"
is not a substitute for running it. For an experiment-shaped item's trial
data, use `statistical-analysis` to check the result against the plan's own
pre-declared bar rather than eyeballing a pass/fail from the raw numbers.

---

## Phase 5 — Record, or it is not done

1. **If `docs/sprint/SPRINTS.md` exists, mark this item's End time there, next to
   the Start from Phase 2** — same rule: a real clock time, not a guess.
   This is what makes the file's own estimate-vs-actual column real instead
   of aspirational; skipping it here is the same mistake as skipping it at
   the start, just discovered later.
2. **Update the `BACKLOG.md` entry, then move it to `docs/history/CLOSED.md` if it is
   fully done.** An item is not done until its entry says so, with the date and
   what closed it. Keep the original report below a *Original report follows*
   line — the reasoning is the record. A fully closed item does not stay in
   `BACKLOG.md`: cut the whole entry (status line through the closing `---`)
   and paste it into `docs/history/CLOSED.md`, matching the format already there (`**Status:**
   CLOSED · <date> · **Severity:** ...`, narrative, then the preserved *Original
   report follows* block). Add one row to `BACKLOG.md`'s own Closed index table
   pointing at it. This is for the next session's token budget as much as
   correctness — `BACKLOG.md` is re-read in full every session, `docs/history/CLOSED.md` is
   read on demand; a closed item left in the working file is paid for again
   every time regardless. Leave an item only half-closed (a mechanism fixed but
   a sub-part still open, a decision still pending) in `BACKLOG.md`, updated in
   place — don't move it until every part of it is actually done.
3. **Doc-truth sweep.** One fact lives in exactly one file. If the change moved a
   number or a path, find every copy and fix them together; two copies of one
   fact is a defect, not a housekeeping matter.
4. **Feed the skill.** If the item taught something general about this hardware,
   add it to `skills/uno-q-st3215/SKILL.md`. The docs explain *this* project; the
   skill travels to the next one. Use `writing-skills` for the edit itself —
   it is a skill file, not prose, and a bad edit degrades every future
   session that reads it.
5. **State plainly what was tested and what was assumed.**
6. **Commit on the feature branch from Phase 2, then merge into `dev`.**
   Message follows `docs/CONVENTIONS.md`'s Git section — plain English, grounded in
   the actual diff, no backlog codes, no hyphens in the prose, `add <thing> to
   <place>` / `fix <issue> in <place>` / `refactor <thing> in <place>`, never
   Conventional-Commits style. Stage only the files this item actually
   touched — review what's staged before committing, same as any commit in
   this repo. Then `git checkout dev && git merge --no-ff feature/<name>`.
   A `deliver` run reaching Phase 5 means it was approved and verified; commit
   and merge it as part of finishing, not as a separate step the user has to
   remember to ask for.

---

## When to call the other skills

- **`operator-lens`** — before planning any change the operator can see, and
  after any change to the UI or an error path. It asks what the *operator* sees,
  which is not what the API returns.
- **`twin-review`** — on demand, on the finished diff, when the change touches
  `sketch/src/`, an error path, or anything with a mirror. It spawns parallel
  reviewers; it costs tokens; it is not automatic.
- **`systematic-debugging`**, **`verification-before-completion`**,
  **`receiving-code-review`**, **`writing-skills`** — woven into Phases 2, 4
  and 5 above at the point each applies; named here too so they are not lost
  in the phase text. All four installed 3 September 2026, extracted
  individually from `skills/superpowers/` (cold storage) the same way
  `writing-plans`/`executing-plans` already were, not installed as the whole
  plugin.
- **`experiment-design`**, **`statistical-analysis`**, **`pre-registration-writing`**,
  **`hypothesis-building`** — Phase 1 only, and only for a hardware-experiment
  item (D48-shaped). Installed the same day from `phd-skills` and
  `open-science-skills`, added specifically because D48's own post-mortem on
  D40d found the missing discipline was exactly what these encode: a
  pre-declared pass bar, a real sample size, one variable at a time unless a
  factorial is deliberately chosen.

**Deliberately not installed, so the gap isn't rediscovered by accident:**
`finishing-a-development-branch` (superpowers) deletes the branch after
merge (`git branch -d`/`-D`) — this repo never deletes branches, even merged
ones, so Phase 5's own merge step stays the way to integrate, not this skill.
`using-git-worktrees` (superpowers) checks work out into a second directory —
incompatible with `CLAUDE.md` §6, where the working copy *is* the CIFS mount
of the board and a worktree would not be. Both stay in `skills/superpowers/`
cold storage; nothing about the case for excluding them expires.
