# Conventions

The coding standard for this repo. Written to be handed to an executing agent
verbatim — every rule is checkable without judgement calls.

Status: **draft**. Derived from the standard used in `Eyal-FastAPI-Project` and
`Krusty-Crab`, with two deliberate updates noted under *Types*.

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

Google format. **`Args:` and `Returns:` always carry the type in parentheses.**

Keep them short. No long paragraphs — if a docstring needs three sentences of
prose to explain the mechanism, the explanation belongs in a comment at the
relevant line, not in the docstring.

```python
def get_zero_by_name(self, name: str) -> Optional[ZeroReference]:
    """Retrieve a stored zero reference by its operator-given name.

    Args:
        name (str): The zero reference name to search for.

    Returns:
        Optional[ZeroReference]: The matching zero, or None if not found.
    """
```

`Raises:` follows the same shape when the function raises deliberately:

```python
    Raises:
        NotFoundError: If no zero has this id.
```

### Class docstrings carry `Attributes:`

Observed in `Eyal-FastAPI-Project`, absent from this repo. Every attribute is
listed with its type.

```python
class ZeroService:
    """Manages saved zeros, the active baseline, and calibration.

    Attributes:
        _zeros (ZeroRepository): Zero reference data access.
        _servo (ServoRepository): Servo access, simulated or hardware.
        _state (ServoStateStore): Shared servo and lock state.
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

This repo already follows the pattern: SQLite sits behind `ZeroRepository` and
`TelemetryRepository`, and the simulated/hardware servo swap happens solely in
`get_servo_repository()`.

## Git

- Branch from `dev`: `feature/<name>`.
- Commit messages in plain English:
  `add <thing> to <place>` / `fix <issue> in <place>` / `refactor <thing> in <place>`.
- **Never** Conventional-Commits style — no `feat(backend):`, no `chore:`.

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

- Doxygen-style `///` comments on every public method — one line of summary,
  then `@param` and `@return`. This is the C++ analogue of the Google docstring,
  and `sketch/src/` already uses `///`.
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
of the work and are mechanical.
