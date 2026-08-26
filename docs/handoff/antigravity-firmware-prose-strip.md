# Task: strip explanatory prose from sketch/src/

STYLE ONLY. No behaviour changes. No test added, removed or edited.
Do not touch `python/`, `sketch/tests/`, or `tools/`.

**Read `sketch/src/RELAY_NOTES.md` in full first. It is non-negotiable — its
content must not be weakened, shortened, or moved by this task, even where
it appears as a comment near code you are otherwise editing.**

Read `CONVENTIONS.md` in full next — its C++ section was extended
26 August 2026 with the comment standard this task follows. If it disagrees
with anything below, STOP and report.

## Scope

`sketch/src/**/*.h` and `sketch/src/**/*.cpp` only. 500 comment lines in
1,884 total — a far higher ratio than the Python side, and there is no type
system underneath to carry meaning the prose currently carries, so read
each one before deleting it rather than pattern-matching Part A of the
Python task.

## A — Doxygen doc comments (`///` and `/** */` blocks)

**KEEP, and complete:**
- The one-line `@brief`-equivalent summary (the first line of the block).
- `@param` and `@return` lines, one per parameter and return value, each
  with a short description of what the value is (not a restated type — C++
  signatures already carry types, unlike the Python docstring blocks in the
  sibling task). **Omit `@return` entirely for a `void` function** — same
  exception as the Python task's `Returns:` block, nothing to describe.
  **Each `@param`/`@return` line is ONE line.** A wrapped, multi-line entry
  should be rare, not routine as it is today — shorten the description
  rather than wrapping it; only let one run past a line when shortening
  genuinely fails.

**REMOVE:** explanatory paragraphs after the summary — the mechanism
narrative, the reasoning, the incident history, cross-references to other
functions or documents.

Example, the shape to produce:

```cpp
/// Cuts or restores drive torque while the servo's electronics and
/// telemetry stay powered.
/// @param enabled True to restore drive torque, false to cut it.
/// @return True when every step the servo answered to succeeded.
bool SetTorque(bool enabled);
```

— not the current, longer version with the re-command-before-enabling
rationale and the register-128-collision warning in the doc comment. That
content is relocated per Part C, not deleted.

**Per the researched C++ convention now in `CONVENTIONS.md`: doc comments
belong on the declaration in the header (`.h`), not on the definition in the
`.cpp`.** Where a function's doc comment is currently duplicated or split
across both files, keep the header copy in the reduced form above and remove
the `.cpp` copy entirely (after relocating anything in it per Part C).

## B — inline comments

Delete every `//` line comment and `/* */` block comment that is not a
Doxygen doc-comment block per Part A.

Exceptions that stay: any `RELAY_NOTES.md`-referencing comment that flags a
non-negotiable hardware constraint (e.g. rule 7's threading requirement) —
these get **relocated**, not deleted, per Part C, and the one-line pointer
that remains at the call site should say what the rule is and name
`RELAY_NOTES.md`, not restate the full reasoning inline.

"Every" means every, including ones that look important. Part C is how they
survive.

## C — relocate what is not already written down

For each explanatory paragraph and each inline comment you remove, first
search `docs/` and `skills/uno-q-st3215/SKILL.md` for its content.

- **Already covered there** — delete it and move on.
- **Not covered** — relocate it, in distilled form (`CLAUDE.md` §4: facts,
  decisions, numbers, not narrative):
  - servo, register, or board hardware behaviour →
    `skills/uno-q-st3215/SKILL.md` (its Symptom→Cause table, or a new row)
  - a design or architecture decision → the relevant `docs/adr/` entry
  - a past defect or its lesson → `docs/AUDIT.md` or the item's entry in
    `docs/CLOSED.md`
  - anything that fits none of these → `docs/DESIGN_NOTES.md`, creating it
    if it does not exist, one `## sketch/src/<file>` section per source file

**When in doubt, relocate rather than delete.** Hardware rules in this
codebase have previously stopped real recurring defects (see
`skills/uno-q-st3215/SKILL.md`'s existing table) — losing one is a worse
outcome here than an extra line in a doc.

Do not create any other new file. List every relocation in your report.

## D — two comment classes that need special handling, found the hard way

The Python sibling run (session 11) reported every file as complete, but a
manual check afterward found real content silently deleted in files the
report never even listed — not relocated, not flagged, just gone, in the
one file with the most safety-critical comment in the codebase. Two classes
of comment caused this, and both exist in `sketch/src/` too:

**1. Contract-mismatch / sentinel-convention warnings** — a value or call
whose meaning is the *opposite* of what it looks like, or a magic number
that collides with a different meaning elsewhere. `ServoController.cpp`
already has exactly this: the `EnableTorque`/`WritePosEx` comments noting
their return convention is Ack()'s own (0 fail / 1 success, **never** -1),
fixed this session after a real inversion bug shipped. **These do not get
silently relocated to docs and left bare at the call site — collapse them
to ONE inline line that states the trap** (e.g. `// EnableTorque: 0 fail /
1 success, never -1.`), and relocate any fuller reasoning behind them
separately. Losing the one-line warning at the call site is exactly the
failure mode that shipped a bug this session.

**2. Twin-path / defect-precedent warnings** — a comment explaining *why* a
specific check, guard, or comparison exists, where the reason is that
skipping it once already caused (or would cause) a defect recorded
elsewhere in this project. These must be relocated in full, even in a file
that looks purely mechanical (a repository, a struct, a register table) —
do not assume a file's low narrative density means it has nothing
load-bearing in it. If you are not sure whether a comment is this class,
relocate it; the cost of an extra `docs/DESIGN_NOTES.md` line is much lower
than the cost of losing the second one of these that saved a real repeat.

**Before your final report, re-read every file you have already finished**
specifically hunting for these two classes — do not rely on having caught
them the first time through. State plainly, per file, either "no comment of
either class found" or the classes found and what was done — do not let a
summary claim completeness that a per-file check would contradict.

## Verification — after every file, not only at the end

```
cd sketch/tests/native && make
python3 tools/verify.py
```

- Both must stay **ALL GREEN**.
- The native test count must **NOT change**.
- If a single change breaks either, **REVERT** that one change and report
  it. Do not guess a fix, do not disable a test.

## Constraints

- No `git` commands. No branch, commit, stash, or reset.
- Do not edit `tools/verify_baseline.json`.
- Do not edit anything under `sketch/tests/`, `python/`, or `tools/`.
- Do not change `RELAY_NOTES.md` itself.
- Do not change any log message, diagnostic string, or any text that
  reaches the operator through `mcu_log`/`DiagLog`.

## Report back

1. Every file changed, with counts: doc-comment blocks reduced, inline
   comments removed, duplicated header/`.cpp` doc comments collapsed.
2. Total lines removed.
3. Every relocation made — source, destination.
4. **Per file, a one-line completeness statement per Part D** — either "no
   contract-mismatch or twin-path comment found" or what was found and how
   it was handled. Not a single overall claim of completeness — one line
   per file.
5. Any `RELAY_NOTES.md`-adjacent comment you were unsure about — list it
   rather than guessing.
6. The final `make` and `tools/verify.py` summary blocks, pasted verbatim.
