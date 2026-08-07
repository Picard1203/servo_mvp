# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout: single-context

```
/
├── CONTEXT.md
├── docs/
│   ├── adr/
│   ├── AUDIT.md
│   ├── PROJECT_STATE.md
│   └── FILE_REGISTRY.md
├── python/
├── sketch/
├── libraries/
└── tools/
```

## Before exploring, read these

- **`CONTEXT.md`** at the repo root — architecture, locked decisions, hardware facts, known gaps.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.
- **`docs/AUDIT.md`** — full-system audit; read before touching the relay or controller.
- **`docs/PROJECT_STATE.md`** — point-in-time snapshot meant to replace prior chat history.

If `docs/adr/` is empty, proceed silently — decisions currently live in `CONTEXT.md`'s
"Locked decisions" table until one gets pulled out into its own ADR.

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids (e.g. `timestamp`, never `ts`).

## Flag ADR conflicts

If your output contradicts an existing ADR or a locked decision in `CONTEXT.md`, surface it explicitly rather than silently overriding:

> _Contradicts the "Plain HTML/CSS/JS, no framework" decision — but worth reopening because…_
