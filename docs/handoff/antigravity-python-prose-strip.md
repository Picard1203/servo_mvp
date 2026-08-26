# Task: strip explanatory prose from python/app/

**Already run once, 26 August 2026 (T15a) — this file is the historical
record of that prompt, not a live task.** If this is being re-run for any
reason, note two corrections made after the first run, from a full manual
diff review that found real content silently deleted despite this file's
existing Part C:
- `python/static/*.js` is **removed from scope**. The first run stripped it
  too; every line of that diff turned out to be comment removal with zero
  other contribution, and `CONVENTIONS.md` has no JavaScript section to
  strip *to* — it was reverted whole. See T18 and `docs/DESIGN_NOTES.md`'s
  final section.
- Before reporting any file complete, re-read it once more specifically for
  contract-mismatch/sentinel warnings and twin-path/defect-precedent
  comments (see `docs/handoff/antigravity-firmware-prose-strip.md` Part D
  for both classes, written after this run) — the first pass missed real
  instances of both, most seriously in `isolation_service.py` and
  `servo_state.py`.

STYLE ONLY. No behaviour changes. No test added, removed or edited.
Do not touch `sketch/`, `python/static/`, `python/tests/`, or `tools/`.

Read `CONVENTIONS.md` in full first — its Docstrings section was rewritten
26 August 2026 and is the authority here. If it disagrees with anything
below, STOP and report.

## A — docstrings (`python/app/**/*.py`)

242 docstrings, 197 multi-line, 1,756 body lines. If your count differs by
more than 5, STOP and report before changing anything.

**KEEP, and complete:**
- The one-line summary sentence.
- The `Args:` / `Returns:` / `Raises:` / `Attributes:` blocks, in full.
  **Every `Args:`, `Returns:` AND `Attributes:` entry must carry its type in
  parentheses** — this applies to all three equally, not just `Args:`/
  `Returns:` — taken from the signature (or, for `Attributes:`, from the
  attribute's own annotation) — `name (str):`, `Returns: Optional[ZeroReference]:`,
  `_servo (ServoRepository):`. About 67 `Args:`/`Returns:` entries are
  currently missing it; `Attributes:` has not been counted, so report
  whatever you find. **Do not remove or shorten these blocks. Do not omit
  the `(type)` parentheses because the signature is already annotated —
  this project deliberately keeps them in both places.**
  **Exception: omit the `Returns:` block entirely when the function returns
  `None`** — there is nothing to type or describe.
  **Every entry inside these blocks is ONE line** —
  `name (type): description.` A wrapped, multi-line entry should be rare,
  not routine as it is today. Where a description does not fit one line,
  shorten the description rather than wrapping it; only let it run past one
  line when shortening genuinely fails. Report your count
  of types added.

**REMOVE:** every explanatory paragraph between the summary and the first
block — rationale, mechanism narrative, project history, incident
references, cross-references to other code or documents.

The summary line itself: one sentence, imperative mood, ends with a period.
Reuse the summary already present — do not invent a new one.

Do NOT split, rename or restructure any function. Where a docstring's
explanatory paragraph is long enough that you suspect the function does too
much, note it in your report as a single-responsibility candidate for a
later human pass — do not act on that suspicion yourself.

## B — inline comments

Delete EVERY `#` comment in `python/app/**/*.py` (147 lines).

Exceptions that stay: tool directives (`# type: ignore`, `# noqa`,
`# pragma: no cover`), shebangs, encoding declarations, licence headers.

"Every" means every, including ones that look important. Part C is how they
survive.

**All of `python/static/` (`app.js`, `style.css`, `index.html`) is OUT OF
SCOPE for this task** — the front end has no conventions of its own yet;
see T18.

## C — relocate what is not already written down

For each explanatory paragraph and each inline comment you remove, first
search `docs/` for its content.

- **Already covered there** — which most of it is expected to be — delete it
  and move on.
- **Not covered** — add it, in distilled form (see `CLAUDE.md` §4: facts,
  decisions, numbers, not narrative), to the matching file:
  - a design or architecture decision → the relevant `docs/adr/` entry
  - a past defect or its lesson → `docs/AUDIT.md` or the item's entry in
    `docs/CLOSED.md`
  - a hardware or servo behaviour → `skills/uno-q-st3215/SKILL.md`
  - anything that fits none of these → `docs/DESIGN_NOTES.md`, creating it
    if it does not exist, one `## <module path>` section per source file

Do not create any other new file. Do not restructure existing docs beyond
appending to them.

List every relocation in your report — source `file:line`, destination file.

## D — the remaining style gaps (`python/app/` only)

Per `CONVENTIONS.md`, and only these:

1. Implicit-truthiness checks (`if x:` where `x` is not already a `bool`) →
   explicit comparison, matching the style already used in the same file.
   Expect 4.
2. `while True:` → an explicit loop condition. Expect 3.
3. List comprehensions → explicit `for` loops, matching the same file.
   Expect 3.
4. `break` → a restructured condition avoiding the early exit. Expect 2.

Any count that differs: report it, do not silently do more or fewer.

## Verification — after every file, not only at the end

Run from the repo root:

```
python3 tools/verify.py
```

- Must stay **ALL GREEN**.
- Test counts must **NOT change**. Adding or editing tests is out of scope;
  a changed count means behaviour or a test was touched.
- If a single change breaks the suite, **REVERT** that one change and report
  it. Do not guess a fix, do not disable a test, do not touch
  `tools/verify_baseline.json`.

## Constraints

- No `git` commands. No branch, commit, stash, or reset.
- Do not edit `tools/verify_baseline.json`.
- Do not edit anything under `python/tests/`, `sketch/`, `python/static/`, or `tools/`.
- Do not change any string literal, log message, error message, or any text
  the operator can see in the UI.

## Report back

1. Every file changed, with per-category counts: docstrings collapsed,
   `(type)` annotations added, inline comments removed, Part D fixes by type.
2. Total lines removed.
3. Any count that differed from the expected numbers above.
4. Every relocation made — source, destination.
5. Every single-responsibility candidate you noted but did not act on.
6. The final `tools/verify.py` summary block, pasted verbatim.
