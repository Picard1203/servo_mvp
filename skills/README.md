# Skills archive

Every skill this project may want, vendored **on disk** so it survives the move
to the air-gapped network. Downloaded 7 August 2026; three more added 3
September 2026 (below) to close the gap D40d's own post-mortem found: ad hoc
tuning with too few repeats and no pre-declared pass bar, the exact method
error D48 exists to not repeat.

This is the cold store — most of it is not installed, and stays here until it
is. A handful of individual skills (never a whole vendored collection) have
been extracted into `~/.claude/skills/`, one at a time, as a real need
surfaced: `writing-plans`/`executing-plans` from `superpowers/` (W8), four
more from `superpowers/` plus four from `phd-skills/`/`open-science-skills/`
(W8 update, 3 September 2026). See `docs/WORKFLOWS.md` for which skill drives
which piece of work, the full installed roster, and install commands.

## What's here

| Directory | Size | Tracked in git | What it is |
|---|---|---|---|
| **`uno-q-st3215/`** | 20K | yes | **Ours.** The board-and-servo skill this project needed and nobody had written. Install with `cp -r skills/uno-q-st3215 ~/.claude/skills/`. |
| `_global-claude-skills/` | 296K | yes | Copy of `~/.claude/skills` — `graphify`, `grilling`, `grill-with-docs`, `domain-modeling`, `tdd`, `to-tickets`, `improve-codebase-architecture`. The ones already in use. |
| `superpowers/` | 2.2M | yes | obra/superpowers — 14 skills. `test-driven-development`, `systematic-debugging`, `defense-in-depth`, `condition-based-waiting`, `testing-anti-patterns`, `writing-plans`, `executing-plans`, `verification-before-completion`. The methodology layer. |
| `iot-skillsbench/` | 692K | yes | Human-expert embedded skills from the HIL benchmark, in `skills-human-expert/` (plus `skills-llm-generated/` for comparison and `tasks/`). Docs and source stripped. |
| `Arduino-Agent/` | 1.3M | yes | The `arduino-agent` skill and MCP server. IDE-extension bulk stripped. |
| `arduino-cli-claude-plugin/` | 128K | yes | Thin arduino-cli wrapper skill. |
| `agentic-awesome-skills/` | 105M | **no — gitignored** | 1,916 skills, cross-agent including Antigravity. Too large to track; it travels with the folder, not with git. |
| `phd-skills/` | 264K | yes | fcakyon/phd-skills — `experiment-design` (single-variable isolation, factorial vs. sequential-elimination matrices, pre-declared analysis plan before running) is the direct match for D48's own protocol shape. Also carries `reproduce`, `compare`, `paper-review-lite`; the ML-training-run skills (`compare`'s wandb/epoch alignment) don't apply here and are left unused. |
| `claude-statistical-analysis-skill/` | 148K | yes | terryfyl/claude-statistical-analysis-skill — diagnoses assumptions before picking a test; includes a power/sample-size workflow, which is what turns D48's "N≥10" into a computed number instead of a round one. |
| `open-science-skills/` | 2.1M | yes | scdenney/open-science-skills — `pre-registration-writing`, `hypothesis-building` (falsifiable claims via DAGs/counterfactuals) and `research-grill` carry the "declare the bar before you see the data" discipline D48 asks for, from social-science methodology rather than engineering. **CC BY-NC 4.0 — noncommercial only** — fine as an internal methodology aid on an MVP not yet sold, but don't let its wording end up verbatim in anything delivered to the client. `codex/` (duplicate Codex-format distribution) and `assets/hero.jpg` stripped as redundant. |

Total ~111.5M, of which 105M is the untracked library.

## Why the big one is not tracked

It travels by folder copy (`adb push`, or the shipped zip), which is how this
project reaches the board and the secure network anyway. Tracking 105M would
make every clone of this repo slow for no gain, since git is not the transfer
mechanism to the air gap.

**If the transfer method ever becomes a git bundle rather than a folder copy,
this decision must be revisited** — a gitignored directory will not be in the
bundle.

## What was stripped, and why

Downloaded repos were trimmed to skill content only:

- `.git` directories from all (50M+34M+8M).
- `iot-skillsbench/docs` (35M), `src`, `scripts`.
- `Arduino-Agent/docs` (13M), `arduino-ide-extension` (5.6M), `i18n`,
  `electron-app`, `static`.
- `agentic-awesome-skills/plugins` (180M — a duplicate distribution of
  `skills/`), `data` (23M), `assets`, `apps`.

452M as cloned → 109M as stored.

## The gap this archive does not fill

**None of it is Arduino UNO Q specific.** Every embedded skill here targets AVR,
ESP32, STM32 or Nano 33 BLE. The UNO Q is a different animal — Qualcomm QRB2210
running Debian alongside an STM32U585 on Zephyr, with sketches loaded as a
relocatable ELF via LLEXT, plus this project's Bridge RPC. A skill that
confidently drives `arduino-cli` against a classic board will be wrong here.

In `agentic-awesome-skills`, 1,916 skills yielded three loose embedded matches
and no Arduino, serial or firmware skill at all.

That is why **W7 in `docs/WORKFLOWS.md` — writing our own UNO Q / ST3215 skill —
is the highest-leverage item**, and it is backed by the benchmark these skills
come from: human-expert skills achieved near-perfect success on real hardware
where LLM-generated ones did not.

## Sources

- [obra/superpowers](https://github.com/obra/superpowers)
- [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)
- [iot-agent/iot-skillsbench](https://github.com/iot-agent/iot-skillsbench)
- [mixelpixx/Arduino-Agent](https://github.com/mixelpixx/Arduino-Agent)
- [lookfwd/arduino-cli-claude-plugin](https://github.com/lookfwd/arduino-cli-claude-plugin)
- [fcakyon/phd-skills](https://github.com/fcakyon/phd-skills) (MIT)
- [terryfyl/claude-statistical-analysis-skill](https://github.com/terryfyl/claude-statistical-analysis-skill) (MIT)
- [scdenney/open-science-skills](https://github.com/scdenney/open-science-skills) (CC BY-NC 4.0)

## Considered and left out

**jamestjsp/control-skills** (`control-theory`, `pid-loop-tuning`, `ctrlsys-control`) —
classical continuous-loop industrial process control: FOPDT identification,
lambda tuning, bump tests on a flow/pressure/temperature loop with a
controllable OP. The ST3215 is tuned through discrete on-servo registers
(P/I/D, `MinStartForce`, velocity-loop gains) with no access to that kind of
open-loop step-test signal — different enough in kind, not just degree, that
the methodology doesn't transfer. Also has no `LICENSE` file at all (default
all-rights-reserved) and depends on an unclear/possibly-unpublished `ctrlsys`
package. Revisit only if a future servo generation exposes real continuous
control access.
