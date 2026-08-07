# Servo MVP — start here

Arduino UNO Q + Waveshare ST3215 serial-bus servo. FastAPI backend and an
LCARS-themed web UI served from the board.

**This file is the router. Read it, then follow the flow below.** Everything the
project knows is written down — do not rebuild context by reading source.

---

## 1. Use graphify. It is not optional.

`graphify-out/` holds a knowledge graph fusing the AST of every source file with
the rationale extracted from the docs. A query returns a scoped subgraph instead
of a pile of grep hits, **at a fraction of the token cost of browsing
`python/app/` or `sketch/src/`.**

```bash
graphify query "<question>"      # start here for ANY question about the code
graphify query "<q>" --budget N  # when the answer is truncated
graphify path "<A>" "<B>"        # how two things relate
graphify explain "<concept>"     # one focused node
graphify update .                # after changing code (AST-only, no API cost)
```

**Rules, learned the expensive way:**

- Run `graphify query` **before** grepping or reading any source file.
- `graphify explain "<node id>"` beats reading a whole file. When a query returns
  a node id, use it — do not open the file to find what the graph already told
  you.
- Read full files only to **edit or debug specific lines**, after the graph has
  pointed you at them.
- Pass this rule to any sub-agent you dispatch. It applies to them too.
- Run `graphify update .` after changing code. A `PreToolUse` hook nudges you.

Two known extraction gaps: no `.ino` or `.css` mapping, so `sketch/sketch.ino`,
`sketch/tests/OnTarget/OnTarget.ino` and `python/static/style.css` are skipped
unless routed to the C++ grammar manually.

---

## 2. The document flow

Read in this order. Each answers a different question.

| # | File | Answers |
|---|---|---|
| 1 | `CLAUDE.md` (this) | How do I work here? |
| 2 | `docs/PROJECT_STATE.md` | Where is the project right now? |
| 3 | `docs/BACKLOG.md` | **What do I do next?** ← the work queue |
| 3b | `docs/WORKFLOWS.md` | **How do I do it?** ← skill + flow per item |
| 4 | `CONTEXT.md` | What do the words mean? (glossary only) |
| 5 | `CONVENTIONS.md` | How must the code look? |
| 6 | `docs/adr/` | Why is it built this way? |
| 7 | `docs/AUDIT.md` | What went wrong before? (frozen, historical) |
| 8 | `sketch/src/RELAY_NOTES.md` | Before touching the relay. Non-negotiable. |

**To pick up work: go to `docs/BACKLOG.md`.** It is the only file listing open
items. Nothing else in the repo is a to-do list.

One fact lives in exactly one file. If you find the same fact in two places, that
is a defect — fix it rather than updating one copy.

---

## 3. Before you change anything

Run all three. Note the numbers.

```bash
cd python && pytest                      # 192 tests
cd sketch/tests/native && make           # 164 checks
python3 tools/check_bridge_contract.py   # "both sides agree"
```

Run them again after. **If the numbers do not match, stop and say so.**

The Python suite needs `pip install -r python/requirements-dev.txt` in a venv;
the board's own environment is provisioned by App Lab.

---

## 4. How to work on this repo

- **Read the written reasoning before rewriting anything.** Several bugs came
  from re-deriving solved behaviour instead of porting it.
- **Never bundle unrelated changes into a fix.**
- **Say plainly what was actually tested versus assumed.** 100% line coverage did
  not prevent any of the six defects in `AUDIT.md`.
- **Use the glossary's words** (`CONTEXT.md`) in commits, tests and issues —
  `timestamp` never `ts`, `count` never `tick`, `datum` never `home`.
- **If your change contradicts an ADR, surface it** rather than silently
  overriding: _"Contradicts ADR-0002 (no framework) — worth reopening because…"_
- **Follow `CONVENTIONS.md`.** Where it marks something undecided, ask; do not
  choose silently.

## 5. Two traps that cost real time

- **`python/.env` must exist on the board.** Without it `use_hardware_servo`
  defaults to false, the simulator runs, and the UI moves convincingly while the
  servo never twitches. `cp .env.board .env` on the board only. (Backlog D8.)
- **`adb push` never deletes.** Wipe the target directory first, or renamed and
  deleted files linger and get picked up instead of the new ones.

## 6. Environment note

The working copy is usually an **sshfs mount of the board itself**
(`arduino@192.168.1.192:/home/arduino/ArduinoApps/`), so edits land on the board
directly and there is no push step during development. That is a convenience for
development only — it is not the deployment path. See `README.md` for real
deployment.

The database is at `servo_mvp.db` in the app root — **inside** the mount, so it
can be read directly. `.env.board` sets a relative `DB_PATH` deliberately: the
Python side runs in a container where `HOME` is `/home/app`, so an absolute
`/home/arduino/...` path would not persist where you can reach it. Only the
*default* `db_path` sits outside the mount.

`adb` is still how you **start and stop** the app without App Lab:

```bash
adb shell arduino-app-cli app start user:servo_mvp     # ~16s warm, ~7min cold
adb shell arduino-app-cli app logs  user:servo_mvp
```
