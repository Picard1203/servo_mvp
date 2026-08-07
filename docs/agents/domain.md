# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: single-context

```
/
├── CONTEXT.md              description + ## Language glossary + project constraints
├── docs/
│   ├── adr/                architecture decision records (0001-slug.md, ...)
│   ├── AUDIT.md            full-system audit — why the system is shaped this way
│   ├── PROJECT_STATE.md    point-in-time snapshot
│   └── FILE_REGISTRY.md    catalogue of every file ever delivered
├── python/
├── sketch/
├── libraries/
└── tools/
```

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — the `## Language` glossary first, then the
  locked decisions, hardware facts and known gaps.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.
- **`docs/AUDIT.md`** — read before touching the relay or the calibration path.
- **`sketch/src/RELAY_NOTES.md`** — the five relay rules; read before changing
  `NetworkRelay`.

If `docs/adr/` is empty, proceed silently. Decisions currently live in
`CONTEXT.md`'s "Locked decisions" table until one is pulled out into its own ADR;
`domain-modeling` creates ADRs lazily, when a decision actually crystallises.

## Prefer the knowledge graph over raw browsing

`graphify-out/` holds a graph fusing the AST with the docs' rationale. Run
`graphify query "<question>"` before grepping or reading source files — it returns
a scoped subgraph at a fraction of the token cost. See the root `CLAUDE.md` for
the full command set. Grep remains correct for editing or debugging specific lines.

## Use the glossary's vocabulary

When your output names a domain concept (an issue title, a refactor proposal, a
hypothesis, a test name), use the term as defined in `CONTEXT.md`'s `## Language`
section, and avoid the synonyms listed under each term's `_Avoid_` line —
`timestamp` never `ts`, `count` never `tick`, `datum` never `home`.

If the concept you need isn't in the glossary yet, that's a signal: either you're
inventing language the project doesn't use (reconsider), or there's a real gap —
note it for `domain-modeling`.

## Related skills

- **`domain-modeling`** — maintains the `## Language` glossary and writes ADRs.
  Formats: `~/.claude/skills/domain-modeling/CONTEXT-FORMAT.md` and `ADR-FORMAT.md`.
- **`grilling`** — stress-tests a plan or decision in rounds.
- **`grill-with-docs`** — runs a grilling session that maintains the docs as it goes;
  delegates to both of the above.

## Flag ADR conflicts

If your output contradicts an existing ADR or a locked decision in `CONTEXT.md`,
surface it explicitly rather than silently overriding:

> _Contradicts the "Plain HTML/CSS/JS, no framework" decision — but worth reopening because…_
