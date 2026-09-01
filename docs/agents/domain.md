# Domain docs

How the engineering skills consume this repo's documentation.

The full reading flow is in the root `CLAUDE.md`. This file covers only what
skills need to know.

## Layout: single-context

```
/
├── CLAUDE.md               the router — read first (must stay at root)
├── docs/
│   ├── CONTEXT.md          glossary ONLY (no status, no decisions, no layout)
│   ├── CONVENTIONS.md      code style, including undecided items
│   ├── PROJECT_STATE.md    where the project is
│   ├── BACKLOG.md          open defects and tasks — the work queue
│   ├── adr/                architecture decision records (0001-slug.md, …)
│   ├── history/            CLOSED.md, AUDIT.md — frozen/closed record
│   └── sprint/             SPRINTS.md, RIG_TESTING_PROTOCOL.md
├── python/  sketch/  libraries/  tools/
```

## Prefer the knowledge graph over raw browsing

`graphify-out/` fuses the AST with the docs' rationale. **Run
`graphify query "<question>"` before grepping or reading source** — it returns a
scoped subgraph at a fraction of the token cost. Use `graphify explain "<node
id>"` rather than opening a file the graph has already described. Grep and full
reads are correct for editing or debugging specific lines, once the graph has
pointed you there.

Pass this rule into every sub-agent prompt that involves code exploration.

## Use the glossary's vocabulary

When naming a domain concept — an issue title, a refactor proposal, a hypothesis,
a test name — use the term as defined in `docs/CONTEXT.md`'s `## Language` section and
avoid the synonyms under each `_Avoid_` line: `timestamp` never `ts`, `count`
never `tick`, `datum` never `home`, `Lock` never `e-stop`.

Watch the four terms that are easily conflated: **zero reference** (the genus),
**datum** (the one absolute member), **baseline** (whichever is active), and the
servo's `kLock` register (EEPROM write lock — not the **Lock**).

If a concept is missing from the glossary, that is a signal: either you are
inventing language the project does not use, or there is a real gap — add it.

## Decisions

`docs/adr/` holds seven ADRs and is **not** empty. Read the ones touching your
area before working there. `docs/CONTEXT.md` no longer carries a decisions table —
that content moved into the ADRs.

If your output contradicts an ADR, surface it rather than silently overriding:

> _Contradicts ADR-0002 (no framework) — but worth reopening because…_

## Where open work lives

`docs/BACKLOG.md`, and nowhere else. There is no external issue tracker; the
`gh`-based workflow that was once described here was never used and has been
removed.

## Related skills

- **`domain-modeling`** — maintains the glossary and writes ADRs. Formats:
  `~/.claude/skills/domain-modeling/CONTEXT-FORMAT.md` and `ADR-FORMAT.md`.
- **`grilling`** — stress-tests a plan or decision in rounds.
- **`grill-with-docs`** — a grilling session that maintains the docs as it goes.
