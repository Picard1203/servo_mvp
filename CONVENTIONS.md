# Conventions

The coding standard for this repo. Written to be handed to an executing agent
verbatim — every rule is checkable without judgement calls.

Status: **draft**. Derived from the standard used in `Eyal-FastAPI-Project` and
`Krusty-Crab`, with two deliberate updates noted under *Types*.

**The machine-checkable subset of the Python rules below is encoded in
`python/ruff.toml`** — run via `ruff check python/app --config
python/ruff.toml`, advisory only (not part of `tools/verify.py`'s gate).
Where the two disagree, this file wins — the config is adapted from a general
personal standard, not written for this repo.

---

## Types

- **Every** signature is fully typed — every parameter and the return.
- Use **lowercase builtin generics**: `list[str]`, `dict[str, int]`, `tuple[int, int]`.
  _Updated._ The older standard mandated `List[str]` from `typing`; this repo uses
  lowercase.
- Use **`Optional[X]`**, never `X | None`. Import it from `typing`.
  This is the one place the old standard still holds — `Optional` is explicit at a
  glance in a way `| None` is not.
- Combined, the canonical optional collection is `Optional[list[str]]`.

```python
def find_zeros(self, name: str, limit: int) -> Optional[list[ZeroReference]]:
```

## Docstrings

Google format. **`Args:` and `Returns:` always carry the type in parentheses
— never omit `(type)` on the theory that the signature is already annotated.
This project deliberately keeps the type in both places**, against the
letter of Google's own style guide (which permits dropping it when PEP 484
annotations are present) — decided 26 August 2026, so it does not get
"corrected" back to that guidance later.

**Exception: omit the `Returns:` block entirely when the function returns
`None`.** There is nothing to type or describe, so the block is noise.

**Every entry inside `Args:` / `Returns:` / `Raises:` / `Attributes:` is one
line** — `name (type): description.`, same reasoning as the summary line
above. A wrapped, multi-line entry should be rare, not the routine it is
today; if a description genuinely cannot fit one line, shorten the
description rather than wrapping it, and only let it run to a second line
when even that fails.

**`Attributes:` gets the same `(type)` treatment as `Args:`/`Returns:` —
every attribute typed, no exceptions.** There was no reason this was ever
different; complete it wherever it is missing, the same pass that completes
`Args:`/`Returns:`.

**The summary is one line.** If it does not fit one honest sentence, that is
a signal — weighed under single-responsibility, not a rule on its own — that
the function may be doing too much and splitting it is worth considering.

**No explanatory paragraphs.** No rationale, no mechanism narrative, no
project history, no incident references, in the docstring. That belongs in
`docs/` (an ADR, `AUDIT.md`, `CLOSED.md`, or `skills/uno-q-st3215/SKILL.md`
for hardware behaviour), in the fuller form it deserves there — not
compressed into source. **Decided 26 August 2026, replacing the previous
rule** ("push the explanation into a comment at the relevant line"), which is
exactly what produced a codebase where docstrings and comments outweighed
code.

Before / after:

```python
# Before
def set_torque(self, enabled: bool) -> bool:
    """Cut or restore drive torque without disturbing telemetry.

    Isolation exists to reduce wear at an unattended field site: the servo's
    electronics and sensors stay powered while the drive motor rests. This
    was decided under ADR-0010 after the operator asked whether isolation
    should survive a reboot...

    Args:
        enabled (bool): True to restore drive torque, false to cut it.

    Returns:
        bool: True when every step the servo answered to succeeded.
    """

# After
def set_torque(self, enabled: bool) -> bool:
    """Cut or restore drive torque without disturbing telemetry.

    Args:
        enabled (bool): True to restore drive torque, false to cut it.

    Returns:
        bool: True when every step the servo answered to succeeded.
    """
```

**Relocation is not a mechanical copy.** Check first whether `docs/` already
says it — the reboot-latch reasoning above, for instance, is already written
in `docs/adr/0010-motor-isolation-state-survives-a-reboot.md`, so the removed
paragraph here is simply deleted, not copied again. Only genuinely new
rationale gets added, in distilled form, to the matching doc. See T15.

```python
def get_position_by_name(self, name: str) -> Optional[SavedPosition]:
    """Retrieve a stored saved position by its operator-given name.

    Args:
        name (str): The position name to search for.

    Returns:
        Optional[SavedPosition]: The matching position, or None if not found.
    """
```

`Raises:` follows the same shape when the function raises deliberately:

```python
    Raises:
        NotFoundError: If no position has this id.
```

### Class docstrings carry `Attributes:`

Observed in `Eyal-FastAPI-Project`, absent from this repo. Every attribute is
listed with its type.

```python
class SavedPositionService:
    """Manages saved positions and moves the mechanism to one.

    Attributes:
        _positions (SavedPositionRepository): Saved-position persistence.
        _state (ServoStateStore): Shared servo and datum state.
        _motion (MotionService): Motion service used by go().
    """
```

### `__init__` gets its own docstring

With a full `Args:` block. This repo currently omits them.

### Instance attributes are annotated at assignment

```python
self._repository: CustomerRepository = repository   # reference standard
self._zeros = zeros                                 # this repo today
```

The annotation goes on, even though the constructor signature already types the
parameter.

### Inline comments

**None.** Zero `#` comments in `python/app/`, decided the same session as
the docstring rule above, for the same reason: a comment carrying real
rationale is exactly the kind of "insider information" that belongs in
`docs/`, not source, and a comment carrying no rationale is noise. The
narrow exceptions are tool directives (`# type: ignore`, `# noqa`,
`# pragma: no cover`), shebangs, encoding declarations, and licence headers.

## Imports

Grouped stdlib / third-party / local, and multi-name imports parenthesised one
per line with a trailing comma:

```python
from src.exceptions import (
    DuplicateException,
    NotFoundException,
    ReferentialIntegrityException,
)
```

## Project layout

The reference projects use a consistent `src/` tree:

```
src/{routes,services,repositories,schemas,models,enums,
     exceptions,factories,logging,settings,middleware,auth,database}
design_diagrams/{pumls,images}
```

This repo diverges: `python/app/` instead of `src/`, `routers/` instead of
`routes/`, and it folds settings, logging and exceptions into `core/`. It has no
`enums/`, `factories/`, `middleware/` or `design_diagrams/`.

`app.yaml` at the root is **required by Arduino App Lab** — it is a platform
requirement, not a project choice, and must not be tidied away.

**These divergences are not automatically defects** — this is an embedded app,
not a CRUD service, and `abstract/`+`concrete/` under `repositories/` expresses
the same intent as the reference `base_repository.py`+`mongodb/`. Renaming
`app/`→`src/` and `routers/`→`routes/` is churn with no payoff mid-project.
Worth adopting: **`design_diagrams/` with PlantUML** (see task T5).

## Trailing commas (ruff)

A trailing comma on the last element makes ruff split the collection one item per
line. Use it deliberately — it is the way to force the vertical layout:

```python
FAULT_NAMES = (
    "overload",
    "overcurrent",
    "overheat",
)
```

The authoritative ruff configuration lives on the isolated network and takes
precedence over this section.

## Exceptions

**`Exception` for abstract levels, `Error` for concrete ones.** Three tiers:

1. **Service base** — one per service. This project has a single service area, so
   one base: `ServoMvpException`.
2. **General category** — `NotFoundException`, `ConflictException`. Abstract.
3. **Concrete** — `ServoNotFoundError`, `DatumZeroError`. What actually gets
   raised.

Each class carries its **FastAPI status code** in its own definition, and an
**error code** built by accumulation down the hierarchy with `+=`, all-caps and
dot-separated:

```
SERVO_MVP.NOT_FOUND.SERVO_NOT_FOUND
```

Exceptions **carry metadata**, passed in the same shape throughout and logged at
the top level. They do not today — see task T6.

The payoff of the hierarchy is handler count: one handler registered against the
service base exception reads the status code, error code and metadata off
whatever was raised. **You do not write a handler per exception type.**

This repo currently has a flat set (`NotFoundError`, `ActiveZeroError`,
`DatumZeroError`, `OutOfTravelError`, `InvalidReadingError`) under a single
`DomainError` base, with no error codes and no metadata. Restructuring is T6.

## Database access

The abstract/concrete split that applies to repositories applies to the database
itself: an abstract `Database` contract with a concrete `SqliteDatabase`
implementation. This repo has only the concrete `Database`
(`python/app/db/database.py`) — see task T7.

## Control flow

- **Never** `break`.
- **Never** `continue` — use an early return instead.
- **Never** `while True`.
- **Never** list comprehensions — write the explicit `for` loop.

## Booleans and conditions

- Explicit checks only: `if value is True`, `if value is not None`,
  `if len(items) == 0`.
- **Never** implicit truthiness — not `if value:`, not `if not value:`.
- **Avoid `not`.** Prefer the positive form or an explicit comparison:
  `if value is False` over `if not value`.
- **Parenthesise every term of a multi-term condition**:

```python
if (reading.valid is True) and (zero.is_datum is False):
```

## Naming

- Never single-letter names. Never `a`, `b`, `x`, `i` alone.
- Name a variable for what it holds: `raw_counts`, not `rc`; `zero_id`, not `zid`.
- Domain terms come from `CONTEXT.md` — use the canonical term, not a synonym
  listed under `_Avoid_`.

## Architecture

- **Routers are thin.** Validate input, call a service, return a response. Zero
  business logic.
- **Services hold all business logic.** Dependencies arrive by constructor
  injection.
- **Services depend on abstract repositories only** (`repositories/abstract/`).
  A concrete repository is never imported into a service or a router.
- **`deps.py` is the only module that names concrete classes.** It is the
  composition root.

This repo already follows the pattern: SQLite sits behind `SavedPositionRepository`
and `TelemetryRepository`, and the simulated/hardware servo swap happens solely
in `get_servo_repository()`.

## Git

- Branch from `dev`: `feature/<name>`, one branch per **feature**, not per
  session or per date. A session commonly produces several feature branches;
  a feature that spans several sessions (a defect reopened and later closed,
  for instance) still gets one branch. This was written down 8 August 2026
  and not followed for 16 days (24 Aug audit, `BACKLOG.md` T15) because
  nothing enforced it — **the `deliver` skill now creates the branch as its
  first step**, so this rule should not need restating again. `<name>`
  describes what the branch does, e.g. `feature/fix-sqlite-concurrent-read-corruption`,
  not a session label or a date.
- Commit messages in plain English, grounded in the actual diff (not a
  rehash of a planning conversation):
  `add <thing> to <place>` / `fix <issue> in <place>` / `refactor <thing> in <place>`.
- **Never** Conventional-Commits style — no `feat(backend):`, no `chore:`.
- **No backlog codes (`D10`, `R5`, `T14`, "Batch 2") in commit messages.**
  Those mean nothing outside this project's own docs; `git log` should read
  as a standalone record. Cross-reference the backlog entry in the doc that
  closes the item, not in the commit that ships the fix.
- Concise by word choice, not by meaning — trim filler (articles, "in order
  to", restating context already obvious from the diff), don't compress the
  actual content.
- No hyphens in commit-message prose. Write compound modifiers as separate
  words (`busy state`, not `busy-state`) even where hyphenation would be
  normal English style elsewhere.

## C++ (sketch side)

You've said you steer Python confidently and C++ less so, so this section is my
proposal rather than your existing standard — review it as such.

**Carried over from the Python rules** (they transfer cleanly):

- Full types on every signature. No single-letter names.
- No `break`, no `continue`, no `while (true)` — with one exception below.
- Explicit comparisons: `if (count == 0)`, not `if (!count)`.
- Parenthesise every term of a multi-term condition, as in Python.

**Exception to the loop rules.** `RELAY_NOTES.md` records that the relay must
drain with `while`, never `if`, because the 64-byte UART ring overflows at one
byte per `loop()`. Drain loops stay. The rule is "no *unbounded* `while (true)`",
not "no `while`".

**C++-specific:**

- Doxygen-style `///` (or `/** */`) comments on every public method — one
  line of summary, then `@param` and `@return`, each with a short
  description of the value, not a restated type. This is the C++ analogue of
  the Google docstring, and `sketch/src/` already uses `///`.
- **Doc comments live in the header (`.h`), not the `.cpp`.** The header is
  the public interface; the implementation file states what a line does only
  where it is genuinely not obvious, never why in prose.
- **Same explanatory-paragraph rule as Python, decided the same session, 26
  August 2026**: the summary plus `@param`/`@return` is all that stays. No
  mechanism narrative, no incident history, no rationale paragraph. That
  content is relocated **only if it is not already written down** — check
  `docs/adr/`, `AUDIT.md`, `CLOSED.md`, and (for hardware/servo behaviour)
  `skills/uno-q-st3215/SKILL.md` first; add it, distilled, only where it is
  genuinely missing, never as a reflex copy. Comments explain *why* a line
  exists when it is not obvious from the code; they never restate *what* the
  line does.
- **No inline comments beyond that**, same exception list as Python
  (tool/compiler directives, licence headers) — with one addition specific
  to this codebase: a comment that exists purely to flag a `RELAY_NOTES.md`
  rule at the call site stays, but as a one-line pointer naming the rule,
  not a restatement of it.
- `constexpr` over `#define` for constants — `Config.h` already does this.
- Pass by `const&` for anything larger than a machine word; mark methods `const`
  when they do not mutate.
- Keep the pure-logic classes (`AngleMath`, `SignMagnitude`, `ServoStatus`)
  **header-only and Arduino-free**. That property is what makes the 164 native
  tests possible, and breaking it silently costs the whole host-test tier.
- Every file declares its own includes — `.h` files in a sketch are not
  auto-included.
- **Logging is mandatory** in any file touching hardware or the network, at a
  level that can be turned down. Today only `App.cpp` logs, and only a one-time
  setup banner — see backlog D3.

---

## Current gap against this standard

Measured over `python/app/`:

| Rule | Violations |
|---|---|
| `Args:` missing `(type)` | 67 |
| Implicit truthiness (`if not X`) | 4 |
| `while True` | 3 |
| List comprehensions | 3 |
| `break` | 2 |
| `continue` | 0 |
| `X \| None` unions | 0 |

The codebase is close to the standard already. The docstring types are the bulk
of the work and are mechanical. Run alongside T15's prose strip (same
Antigravity pass, `docs/handoff/antigravity-python-prose-strip.md`) rather
than as a separate session, since both touch the same docstrings.
