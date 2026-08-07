## Codebase navigation

This repo has a graphify knowledge graph at `graphify-out/`. It fuses the AST of
every source file with the rationale extracted from the docs, so a query returns
a scoped subgraph instead of a pile of grep hits.

**Use it before reading or grepping source.** It is the cheap path — a query
costs a fraction of the tokens that browsing `python/app/` or `sketch/src/` does.

- `graphify query "<question>"` — start here for any question about how something
  works, what calls what, or where a behaviour lives. Add `--budget <n>` when the
  answer is truncated.
- `graphify path "<A>" "<B>"` — how two things relate.
- `graphify explain "<concept>"` — a focused explanation of one node.
- `graphify-out/GRAPH_REPORT.md` — read only for a broad architecture review, or
  when query/path/explain do not surface enough.

Grep and full-file reads are still right for editing or debugging specific lines —
just let graphify orient you first.

After changing code, run `graphify update .` to keep the graph current
(AST-only, no API cost). A `PreToolUse` hook nudges toward this automatically.

Two known extraction gaps: graphify has no `.ino` or `.css` mapping, so
`sketch/sketch.ino`, `sketch/tests/OnTarget/OnTarget.ino` and
`python/static/style.css` are skipped unless routed to the C++ grammar manually.

## Agent skills

### Issue tracker

Issues live in GitHub Issues for `Picard1203/servo_mvp`, managed via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `CONTEXT.md` at the repo root plus `docs/adr/`. See `docs/agents/domain.md`.

`CONTEXT.md` carries the `## Language` glossary — the project's ubiquitous
language. Use its terms in issue titles, test names, and proposals, and prefer
them over the synonyms listed under `_Avoid_`. The `domain-modeling` skill
maintains the glossary and writes ADRs into `docs/adr/`.
