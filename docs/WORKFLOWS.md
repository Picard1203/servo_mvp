# Workflows

How to actually execute the work in `BACKLOG.md` — which skill drives each item,
and in what order.

Sources verified **7 August 2026**. The skills ecosystem moves fast; re-check
before trusting any version number here.

---

## Tooling to install first

### 1. superpowers — the methodology layer

```
/plugin install superpowers@claude-plugins-official
```

Last commit **28 July 2026**, ~40 commits that week. Actively maintained.

Four of its skills target defects this project actually has:

| Skill | Why it fits here |
|---|---|
| `defense-in-depth` | D2 *is* a defence-in-depth failure — the guard is on `calibrate()` and not `capture()`. The skill's question is "where else is one path hardened and its twin not?" |
| `testing-anti-patterns` | The suite, gated at 99% coverage, caught none of six past defects, and none of the eight the operator lens found. |
| `condition-based-waiting` | `wait_until()` (`python/tests/conftest.py:222`) is a **god node with 38 edges** — the third most connected node in the graph. That many tests hanging off one async wait is a flakiness surface. |
| `systematic-debugging` | Four phases: reproduce → isolate → identify → verify. D4, D5 and D6 all have unknown causes. |

Also provides `writing-plans` (bite-sized tasks with exact file paths and
verification steps) and `executing-plans` (batch execution with checkpoints).

**Cost warning:** superpowers is a full methodology. `subagent-driven-development`
and its parallel-agent dispatch burn tokens fast. Drive it skill-by-skill.

### 2. agentic-awesome-skills — the catalogue

2,005+ skills, v15.11.0, 2,477 commits. Cross-agent, and **it targets Google
Antigravity directly** — which matters given the split of thinking here and
execution there.

```bash
# never install the whole catalogue - see warning
npx agentic-awesome-skills --skills systematic-debugging,brainstorming --dry-run
npx agentic-awesome-skills --path .agents/skills --category development,backend --risk safe,none
```

Antigravity's skill target is `~/.agents/skills` (installer has an `--antigravity`
flag).

**Warning from the project itself:** installing the full catalogue can exhaust
context or crash the agent. Always select with `--skills`, `--category` or
`--tags`.

### 3. Arduino-Agent — the hardware seam

MCP server plus a skill. Install the skill by copying `skills/arduino-agent/`
into `~/.claude/skills/`. The MCP server runs on `http://127.0.0.1:3847` with a
bearer token, configured through `.mcp.json`.

Ships three slash commands, two of which map straight onto our backlog:

- `/bringup` — hardware initialisation
- `/debug-serial` — serial monitor debugging → **D3, T8**
- `/profile-board` — board performance → **D6**

Caveat: tested against ESP32-S3, and boards outside its USB vid/pid list need a
manual FQBN. The UNO Q is not a listed board, so expect to specify FQBN by hand.

### 4. IoT-SkillsBench — the evidence, and the argument for writing our own

A benchmark of **378 hardware-in-the-loop experiments** across 3 platforms, 23
peripherals and 42 tasks, validated on real hardware. It compared agents with no
skills, LLM-generated skills, and human-expert skills.

**Finding: human-expert skills achieved near-perfect success rates, without
retrieval or long-context reasoning.** LLM-generated skills did not.

The human-expert skills are published under `skills-human-expert/` and cover the
Arduino framework plus relays, sensors and displays.

**What this means for us:** the highest-value move is not installing a generic
servo skill — it is writing a project-specific one from the knowledge already in
`PROJECT_STATE.md`, `docs/history/AUDIT.md` and `RELAY_NOTES.md`. The bench-verified numbers,
the six fixed bugs and the five relay rules are exactly the "human-expert"
content the benchmark found decisive. See W7 below.

---

## The flows

### W1 — T8: the instrumented board run
**Drives:** D4, D5, D6, and confirms or kills D1. **Do this first.**

Skill: `systematic-debugging` (phase 1 is reproduce, which is what the run is
for). Optionally `/debug-serial` from Arduino-Agent.

1. Create `python/.env` on the board (`cp .env.board .env`) — D8.
2. Set `LOG_LEVEL=DEBUG` **for this run only**, so the relay's connect/disconnect
   lines at `bridge_relay.py:80,115` actually appear.
3. Boot, exercise the UI, and reproduce the drop from D4.
4. Pull logs over `adb`. The database is at `servo_mvp.db` in the app root —
   **inside** the sshfs mount, so it can be read directly. `.env.board` sets a
   relative `DB_PATH` deliberately; only the *default* `db_path` sits outside
   the mount. (An earlier version of this step said otherwise — see D8.)
5. Read the stored datum. If `raw_counts=0`, D1 is fully explained.

**Why first:** D4, D5 and D6 all have unknown causes. Planning over unknowns
produces a plan you throw away.

---

### W2 — D2 then D1: the linchpin
**Skills:** `test-driven-development`, then `defense-in-depth`.

1. **RED** — a test where `capture()` receives an invalid reading. It should
   fail, because nothing currently guards that path.
2. **GREEN** — remove `read_raw_counts()` from the `ServoRepository` contract so
   every caller must handle a snapshot and its `valid` flag. Guarding `capture()`
   alone fixes today's call site; deleting the lying method fixes every call site
   that will ever exist.
3. **Then `defense-in-depth`** — sweep for other guards applied to one path and
   not its twin. That pattern is what produced this bug and the six in `docs/history/AUDIT.md`.
4. Re-check D1 against a mid-travel datum.

Order matters: D1 is D2's symptom, and ADR-0007 means the travel window is the
only guard protecting a remote operator — a guard computed from the datum.

---

### W3 — D3: logging on the C++ side
**Skill:** none exists. Hand-rolled.

`ServoBus`, `ServoController`, `NetworkRelay` and `BridgeApi` have zero runtime
logging, and every defect in this project has lived in those four files.

Hard constraint from `RELAY_NOTES.md`: `loop()` must yield (`delay(1)`) or the
Bridge thread starves and `servo_read` hits its 10 s timeout. **Logging must not
break that.** Verify the yield still holds after adding output.

Do this before W1's deeper diagnosis if the run proves inconclusive — you cannot
debug what you cannot see.

---

### W4 — T1, T6, T7: the mechanical pass
**Skill:** `writing-plans` here, execute in Antigravity.

- **T1** — apply `docs/CONVENTIONS.md`. Measured gap: 67 `Args:` lines missing
  `(type)`, 4 implicit-truthiness checks, 3 `while True`, 3 list comprehensions,
  2 `break`.
- **T6** — three-tier exception hierarchy with dotted error codes and metadata.
- **T7** — abstract `Database` over concrete `SqliteDatabase`.

High volume, low reasoning — exactly the Antigravity split. `writing-plans`
produces exact file paths and verification steps, which is the handoff artifact.

**Do this after the defects close**, so mechanical edits do not collide with real
fixes.

---

### W5 — R5, R6: benchmarking and defining "stable"
**Skill:** `user-stories` (from the embedded skills set) to force acceptance
criteria, then build the export.

"Stable" is currently an adjective, not a number. R5 (time-range telemetry
pull exported as XLSX with native embedded charts, no server-side
matplotlib) is what turns it into one, and it is also what the receiving
teams need to judge procurement.

---

### W6 — T3: on-target tests
**Skill:** Arduino-Agent, or manual upload.

`sketch/tests/OnTarget/` has never been uploaded. It checks ping, configuration
writes, landing accuracy and stop-hold — things a host cannot. Run once with the
servo free-shafted and record the tally in `BACKLOG.md`.

On test frameworks: TinyTest was chosen to avoid dependencies on an air-gapped
machine, but that reasoning does not hold — anything we ship with is shipped, so
a better framework is fair game. `embedded-unit-tests` scaffolds Unity, CppUTest
and Google Test, and knows embedded edge cases worth stealing regardless:
**32-bit millisecond rollover at 49.7 days**, circular-buffer wraparound, and
register bit manipulation. The relay has a ring buffer and the sampler runs on a
timer — both are exposed to exactly those.

---

### W7 — Project-specific skill: **DONE**
**Status:** written, 7 August 2026 · `skills/uno-q-st3215/SKILL.md`

Installed with `cp -r skills/uno-q-st3215 ~/.claude/skills/`. The same `SKILL.md`
format works in Antigravity (`~/.agents/skills`).

Covers: why the UNO Q is not a normal Arduino (LLEXT, dual brain, core pinning,
`src/` compilation rules); the ST3215 register map with the four traps
(`0x37` is the EEPROM lock not a safety lock, `0x3C` is PWM duty not torque,
`0x28`=128 sets centre, SMS_STS never SCSCL); status bit4; sign-magnitude
decoding; the belt geometry and the datum-must-sit-mid-travel law; the six relay
rules; the Bridge contract; a symptom→cause table; and the deployment traps.

**Keep it current.** When a defect in `BACKLOG.md` closes and teaches something
general, add it to the skill. It is the durable form of what this repo knows —
the docs explain *this* project, the skill travels to the next one.

---

### W8 — The delivery layer: **DONE**
**Status:** written and installed, 8 August 2026 · `skills/deliver`,
`skills/operator-lens`, `skills/twin-review`

Three project-specific skills that turn the flows above into something
executable, rather than something to be read and re-derived each time. Installed
with `cp -r skills/<name> ~/.claude/skills/` (and `~/.agents/skills/` for
Antigravity).

| Skill | What it does |
|---|---|
| `deliver` | "We need X" → done. Orient on the graph → plan → **one stop for approval** → run the whole thing → verify → update the backlog entry and sweep for doc truth. Board-touching steps always stop and hand over the commands. |
| `operator-lens` | Walks the control surface as the operator or the receiving team, not the developer. Five questions per control; files findings into `BACKLOG.md` in house format. |
| `twin-review` | Parallel reviewers on a diff or the whole app (chunked) — twin path, operator impact, relay safety, doc truth, general correctness; lenses selected by scope, candidates narrowed by tool before any reviewer reasons. **On demand only.** Iteration cap 2 in diff mode; inventory mode is findings-only, written to `docs/REVIEW_FINDINGS.md`. |

**`grilling`** is not one of these three — it is a generic, non-project-specific
skill (stress-tests a plan or decision by questioning it relentlessly), used
once so far: **R2's session opens with it**, on R2's own open design questions
(operator-visible state when isolated, refuse-vs-queue a move, the new
`ServoStateResponse` field — see `docs/history/CLOSED.md`'s R2 entry), per the operator's
explicit request that R2 be grounded in the docs rather than a prior session's
paraphrase.

`deliver` borrows `writing-plans` and `executing-plans` for the
plan-and-checkpoint mechanics, plus, as of 3 September 2026, six more
skills woven in at the phase each applies to — full list and the two
skills deliberately left out (and why) are in `skills/deliver/SKILL.md`'s
own "When to call the other skills" section, not duplicated here.

**Why written rather than installed.** BMAD-METHOD (51.6k★), Spec-Kit (80k★) and
metaswarm were all evaluated. Each installs its own document skeleton, which
would duplicate `BACKLOG.md`, the ADRs and `docs/CONVENTIONS.md` — a direct violation
of *one fact lives in exactly one file*. metaswarm's blocking quality gate is a
coverage threshold, and this repository is the standing counter-example to
coverage as a gate. The same reasoning as W7, and the same evidence:
IoT-SkillsBench found human-expert project-specific skills decisive where
generic ones were not.

**What was borrowed anyway:** metaswarm's parallel design-review gate, with its
iteration cap, is where `twin-review` comes from. Reviewing in parallel is cheap
and catches the twin-path class; *implementing* in parallel across the four
files where every defect in this project has lived is not worth the collision
risk.

**Keep them current**, on the same terms as W7 — when a backlog item closes and
teaches something general, feed it back.

---

### W9 — Convention hooks: **DONE**
**Status:** written and wired, 3 September 2026 · `tools/hooks/`,
`.claude/settings.json`

`docs/CONVENTIONS.md` had a machine-checkable subset (`python/ruff.toml`) that
its own text admitted was "advisory only, not part of `tools/verify.py`'s
gate" — nothing ever ran it. Three `PostToolUse` hooks now fire on every
`Write`/`Edit`, advisory only (the edit already landed; they surface a
reminder, never block):

| Script | Fires on | Checks |
|---|---|---|
| `check_python_conventions.sh` | `python/**/*.py` | `ruff check` against `python/ruff.toml`; `Args:`/`Returns:` lines missing a `(type)` parenthetical |
| `check_cpp_conventions.sh` | `sketch/src/**/*.{h,cpp}` | doc comments (`///`, `/**`) added in a `.cpp` instead of the `.h`; `break`/`continue`/`while(true)` outside the `RELAY_NOTES.md` drain-loop exception |
| `check_glossary_and_ids.sh` | any `.py`/`.cpp`/`.h`/`.js`/`.css` | backlog-ID tags (`D12`, `ADR-0008`, …) inside a code comment; `ts`/`tick`/`home` where the glossary requires `timestamp`/`count`/`datum` |

The third one deliberately covers `.js`/`.css` too, ahead of the frontend work
already queued in the backlog — the glossary and no-ID rules are stated in
`CLAUDE.md` as universal, not Python/C++-specific, so the tooling shouldn't
lag the convention.

Modeled on the `PostToolUse` hook pattern already vendored in
`skills/phd-skills/plugin/scripts/` (`jargon_scrub.sh`, `citation_guard.sh`) —
found while researching experiment-design skills for D48, reused rather than
built from nothing. Each script pipe-tested against real repo content and
live-fire-proven (temporary sentinel file, per the `update-config` skill's own
verification steps) before being left in place.

**The glossary/ID check was run against the existing corpus before being
left in place, not just against synthetic trigger cases** — a first pass
matching any bare `D11-D13` (an SPI pin range in `SpiRemap.h`, not a
backlog ID) and any bare `ts`/`tick`/`home` (the real `tick()` heartbeat
method in `isolation_service.py`, `/home/arduino/...` paths in `config.py`,
chart-axis "tick-label" in `app.js`) turned up 16 false hits on the
glossary word alone out of 17 total. Narrowed to a pin-range exclusion for
the ID check and a declaration/assignment shape (`ts =`, `def f(ts`, a
bare param in a destructure) plus an explicit exclusion list for the
glossary check — re-run against the same corpus, down to the one hit that
is a real existing violation (`app.js`'s `ts: s.timestamp`). A hook that
fires on legitimate code is worse than no hook: it trains the next session
to ignore it.

**Why a hook and not a downloaded "coding conventions" skill.** Searched for
one first. Skills are model-invoked — they fire when Claude judges them
relevant, which is not a reliable trigger for "apply this on every edit"
(confirmed against Anthropic's own steering guidance, not just inferred). A
rule that must hold every time belongs in `CLAUDE.md` or a hook; this repo's
Python and C++ conventions are also deliberately non-generic (explicit
`Optional[X]` never `X | None`, doc comments required in the `.h` not the
`.cpp`), so an imported generic-language skill would have pushed back toward
the standard this project already rejected, not enforced its own.

---

## Every flow ends the same way

`verification-before-completion` (superpowers, now installed to
`~/.claude/skills/` — it was named here as if live before it actually was;
fixed 3 September 2026) — the mechanised form of the rule already in
`CLAUDE.md`:

```bash
python3 tools/verify.py   # source of truth, not a count quoted here (CLAUDE.md §3)
graphify update .
```

State plainly what was **tested** versus **assumed**. If the numbers moved, stop
and say so.

---

## Sources

- [obra/superpowers](https://github.com/obra/superpowers)
- [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)
- [iot-agent/iot-skillsbench](https://github.com/iot-agent/iot-skillsbench)
- [mixelpixx/Arduino-Agent](https://github.com/mixelpixx/Arduino-Agent)
- [lookfwd/arduino-cli-claude-plugin](https://github.com/lookfwd/arduino-cli-claude-plugin)
- [karanb192/awesome-claude-skills](https://github.com/karanb192/awesome-claude-skills)
- [Claude Code Skills: Embedded Developer Guide](https://www.beningo.com/claude-code-skills-embedded-developers/)
