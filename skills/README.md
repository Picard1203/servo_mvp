# Skills archive

Every skill this project may want, vendored **on disk** so it survives the move
to the air-gapped network. Downloaded 7 August 2026.

Nothing here is installed. This is the cold store. See `docs/WORKFLOWS.md` for
which skill drives which piece of work, and for install commands.

## What's here

| Directory | Size | Tracked in git | What it is |
|---|---|---|---|
| `_global-claude-skills/` | 296K | yes | Copy of `~/.claude/skills` — `graphify`, `grilling`, `grill-with-docs`, `domain-modeling`, `tdd`, `to-tickets`, `improve-codebase-architecture`. The ones already in use. |
| `superpowers/` | 2.2M | yes | obra/superpowers — 14 skills. `test-driven-development`, `systematic-debugging`, `defense-in-depth`, `condition-based-waiting`, `testing-anti-patterns`, `writing-plans`, `executing-plans`, `verification-before-completion`. The methodology layer. |
| `iot-skillsbench/` | 692K | yes | Human-expert embedded skills from the HIL benchmark, in `skills-human-expert/` (plus `skills-llm-generated/` for comparison and `tasks/`). Docs and source stripped. |
| `Arduino-Agent/` | 1.3M | yes | The `arduino-agent` skill and MCP server. IDE-extension bulk stripped. |
| `arduino-cli-claude-plugin/` | 128K | yes | Thin arduino-cli wrapper skill. |
| `agentic-awesome-skills/` | 105M | **no — gitignored** | 1,916 skills, cross-agent including Antigravity. Too large to track; it travels with the folder, not with git. |

Total 109M, of which 105M is the untracked library.

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
