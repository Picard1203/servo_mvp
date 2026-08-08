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
5. **Baseline the numbers** before touching anything:

```bash
cd python && pytest                      # expect 192
cd sketch/tests/native && make           # expect 164
python3 tools/check_bridge_contract.py   # expect "both sides agree"
```

If the baseline is already wrong, stop and say so. Do not start work on a repo
that does not match its own documentation.

---

## Phase 1 — Plan, then STOP

Use the `writing-plans` skill for the mechanics. The plan must state, in this
order and in plain language:

1. **What the operator will be able to do afterwards that they cannot do now** —
   or, for a defect, what stops happening. If you cannot write this sentence, the
   item is not understood yet.
2. **Which files change**, with paths.
3. **What gets tested, and what is only assumed.** Say it plainly. 100% line
   coverage did not prevent the six defects in `AUDIT.md`, nor D9, where the
   correct rule and its violation sat twelve lines apart in one file, both
   covered, both green.
4. **The twin-path question, answered**: *where is this rule's twin, and does it
   know?* Four defects in this repository are the same defect — a rule applied to
   one path and not its mirror (`AUDIT.md`'s originals, D2's `calibrate()` but not
   `capture()`, D9's two baselines, D10's production logger and its test stub).
   Answer this in the plan, not after the review.
5. **Anything that needs the board**, listed separately — see Phase 3.
6. **The numbers you expect afterwards**, so a change in them is visible.

**Then stop and present it.** This is the only checkpoint. Wait for go-ahead.

---

## Phase 2 — Run it, all of it

On go-ahead, execute the whole plan without further prompting. Use
`executing-plans` for batching and checkpoint discipline.

- **Test-first where the code is testable.** Use the `tdd` skill. RED must
  actually fail for the stated reason before you write GREEN.
- **Never bundle unrelated changes into a fix.** If you spot something else,
  write it into `BACKLOG.md` as a new item and carry on.
- **Use the glossary's words** (`CONTEXT.md`): `timestamp` never `ts`, `count`
  never `tick`, `datum` never `home`. In code, tests, commits and the backlog.
- **Follow `CONVENTIONS.md`.** Where it marks something undecided, ask rather
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

The working copy is usually an **sshfs mount of the board**, so edits are already
there — but `python/.env` must exist on the board or `use_hardware_servo` defaults
to false and the simulator runs while the UI moves convincingly (backlog D8).
Confirm `servo.backend backend=hardware` in the log before believing any hardware
observation.

Board runs are worth doing at `LOG_LEVEL=DEBUG` for the duration and INFO
afterwards. **Watch for D10's unexplained sampler exception on every run** — the
logging that lost it is fixed, so next time it will name itself.

---

## Phase 4 — Verify

```bash
cd python && pytest
cd sketch/tests/native && make
python3 tools/check_bridge_contract.py
graphify update .
```

**If the numbers moved, stop and say so.** Do not explain them away in passing.

---

## Phase 5 — Record, or it is not done

1. **Update the `BACKLOG.md` entry.** An item is not done until its entry says
   so, with the date and what closed it. Keep the original report below a
   *Original report follows* line — the reasoning is the record.
2. **Doc-truth sweep.** One fact lives in exactly one file. If the change moved a
   number or a path, find every copy and fix them together; two copies of one
   fact is a defect, not a housekeeping matter.
3. **Feed the skill.** If the item taught something general about this hardware,
   add it to `skills/uno-q-st3215/SKILL.md`. The docs explain *this* project; the
   skill travels to the next one.
4. **State plainly what was tested and what was assumed.**

---

## When to call the other two skills

- **`operator-lens`** — before planning any change the operator can see, and
  after any change to the UI or an error path. It asks what the *operator* sees,
  which is not what the API returns.
- **`twin-review`** — on demand, on the finished diff, when the change touches
  `sketch/src/`, an error path, or anything with a mirror. It spawns parallel
  reviewers; it costs tokens; it is not automatic.
