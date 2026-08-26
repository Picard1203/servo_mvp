# Tasks — detail

Full entries for every open `T`-numbered item. Indexed one line each in
`../BACKLOG.md`; read this file only for the item you're picking up.

---

### T13 — Distil the remaining documents
**Status:** open · **Severity:** medium · **Raised by:** the operator, 8 August 2026

Docs are re-ingested at the start of every session, so their length is a
recurring tax on the work. Started 8 August 2026: closed items moved to
`docs/CLOSED.md` and Batch 1's own entries cut, taking `BACKLOG.md` from 15,223
words to ~10,600.

**Not yet done.** The remaining bloat is in entries written before this rule
(`D4` and `D22`, both previously listed here, were moved to `docs/CLOSED.md`
whole on 23 August 2026 rather than distilled in place — relocation, not this
item's kind of work; `D13` was already closed and moved before this table was
last checked, and was never actually bloat in *this* file at all. Both classes
of drift removed from this table accordingly):

| | words |
|---|---|
| `R2` | 520 |
| `R5`'s "use case" section | 459 |
| `T11` | 425 |
| `D10`, `D8`, `T10`, `D5`, `T9` | ~300 each |

Also worth a pass: `docs/WORKFLOWS.md` (1,754) and `CONVENTIONS.md` (1,350).

**Do it opportunistically** — distil an entry when you are already working on
that item, not as a sweep of its own. A sweep costs the tokens it is meant to
save, and rewriting reasoning you have not just re-derived is how facts get
dropped.

**Acceptance:** no open entry states the same thing twice, and every one keeps
its numbers, paths, decisions and honest statements of what was not tested. The
rule itself is in `CLAUDE.md` §4.

---

### T15 — Code-level documentation reads as unprofessional and costs tokens
**Status:** T15a run 26 August 2026, corrected the same session (see below) ·
T15b still open · **Raised by:** the operator, 24 August 2026 · **Decided:**
`OPEN_QUESTIONS.md` Q10, 26 August 2026

**T15a ran 26 August 2026 and needed real correction, not just review.**
Antigravity's own report claimed every file's relocations were complete; a
full manual diff read afterward found genuine load-bearing content silently
deleted with no relocation at all in several files — most seriously
`isolation_service.py` (this session's own torque-inversion fix comment) and
`servo_state.py`'s `_baseline_counts()` (the flagship D9 example T15's own
entry already cited by name). Restored to `docs/DESIGN_NOTES.md` and, in the
two cases judged genuinely safety-critical, as one-line inline pointers (the
operator's call, not a blanket exception). **Lesson, now the standing rule
for any future Antigravity run: verify against the actual diff, never take a
self-reported "complete" at face value** — see the hardened prompts and the
Part D addendum in `docs/handoff/antigravity-firmware-prose-strip.md`.

**`python/static/app.js` was reverted whole, not distilled.** Its entire
diff turned out to be comment/whitespace removal with zero functional,
docstring, or type contribution — confirmed by the report's own counts (all
zero except comments removed) and by re-checking the diff programmatically.
`CONVENTIONS.md` has no JavaScript section, so there was no decided
convention to strip *to* in the first place — including it in T15a's scope
was a scoping mistake, not a judgment failure on Antigravity's part. It
waits for **T18** to establish real JS conventions first.

**Decision (Q10):** docstring summary lines and the typed `Args:`/
`Returns:`/`Raises:`/`Attributes:` blocks stay and get completed — types were
never the problem. The explanatory paragraph between them, and every inline
comment, goes. Relocation is judgment work, not a mechanical copy: check
`docs/` first, and only add genuinely missing rationale there, distilled —
content already covered is deleted, not duplicated. Full rule in
`CONVENTIONS.md`'s Docstrings and C++ sections.

**T1 folds into this pass** — its non-docstring gaps (implicit-truthiness,
`while True`, list comprehensions, `break`) and its `(type)` completions are
the same Antigravity run as the prose strip, not a separate one.

**Split into two sessions, each with its own exact prompt** (not left to the
session to interpret):

- **T15a — `python/app/` only.** Done, corrected. `python/static/*.js` was
  removed from this prompt's scope after the run (see above) — a separate,
  future decision under T18, not a re-run of this one.
  `docs/handoff/antigravity-python-prose-strip.md`.
- **T15b — `sketch/src/`.** Deliberately separate: firmware comments encode
  hardware rules with no type system underneath, and `RELAY_NOTES.md`
  non-negotiable content must not be weakened.
  `docs/handoff/antigravity-firmware-prose-strip.md`.

Both prompts: name their exact file scope, state expected counts with a
stop-and-report tripwire on mismatch, name relocation destinations, require
`tools/verify.py` green with unchanged test counts after every file, forbid
`git` commands and test/baseline edits.

`python/static/style.css` and `index.html` are **out of scope for T15** —
see **T18**, which covers the front end's own conventions separately.

**Related:** CLAUDE.md §4's "write every document distilled" rule (same
cost, different location); **T18** (front-end conventions, a separate axis).

---

### T16 — Enhance `twin-review`: a fifth lens, and lenses made selectable
**Status:** open · **Raised by:** the operator, 25 August 2026, during R2

Two changes to `skills/twin-review/SKILL.md` (and its installed copy at
`~/.claude/skills/twin-review/`), decided but not yet made:

1. **A fifth lens, general correctness, composed by reference to
   `/code-review`** at a chosen effort level (medium by default) — the same
   composition pattern lens #2 already uses for `operator-lens` ("Load the
   operator-lens skill for the five questions"). The current four lenses
   (twin path, operator impact, relay/hardware safety, doc truth) are each
   specialised; none of them is a general bug hunt, so a plain logic error
   with no "twin" shape (wrong comparison, off-by-one, a leak with no mirror)
   can pass all four uncaught.
2. **Lens selection, not a fixed four (or five).** A small change that
   touches none of `sketch/`, no error path, no mirror gets no value from
   the relay-safety or twin-path lenses; forcing every run through all of
   them regardless of the diff wastes tokens on lenses with nothing to say.
   Should default to "everything relevant to what changed," not an
   unconditional fixed set.

**Deliberately deferred, together with actually running the enhanced skill**
— on the whole app, in one sitting, rather than piecemeal per feature. Includes
retroactively covering R2's `feature/motor-isolation` diff, which shipped
without a `twin-review` pass by explicit operator decision (see R2's entry).

**Also raised, not yet scoped:** folding this into `deliver`'s own pipeline
(`skills/deliver/SKILL.md`) rather than leaving it a manual on-demand step.

---

### T17 — Get a mechanical rig on the bench so R2's hand-turn scenario can actually be tested
**Status:** open · **Raised by:** the operator, 26 August 2026, closing out R2

R2 (motor isolation, closed — see `CLOSED.md`) confirmed torque actually cuts
and restores correctly, verified at the register level. One scenario from its
board-verification list stayed genuinely untested: whether the servo can be
freely hand-turned while isolated, and whether multi-turn position tracking
survives a shaft that moved without the drive doing it.

**Why it's a planning item, not something to just go do:** the current bench
is a bare servo with no belt, arm, or lever attached — there is nothing to
get a real grip on. A full free-spin attempt this session produced no
detectable difference between isolated and un-isolated; a much smaller nudge
(roughly a tenth of a degree, about the most the setup allows) did show the
expected qualitative difference repeatably - resists and corrects back when
un-isolated, stays put when isolated - but that was felt, not measured, and
is not the multi-turn-under-load scenario this item is actually about.
Outside research on this exact servo (STS3215, high-ratio metal gearbox)
suggests hand-backdriving is not a reliable test for this part even with a
lever — so this needs the actual mechanical rig (the belt-driven output the
rest of the project assumes, per the gear-ratio audit in
`PROJECT_STATE.md`) mounted, not just more attempts on the bare servo.

**Plan, not execute:** figure out what rig state is needed (belt mounted?
output arm attached? enough of R4's mechanical assembly to have a real lever?)
and when it's realistically available, before spending more bench time on a
test the current setup cannot support.

---

### T9 — Put a measured storage budget in writing
**Status:** open · **Raised by:** the operator, planning a one-to-two month test

The question is simple and nobody could answer it: *run this for two months —
does it fit?* Measured on the board on 7 August 2026, at the original 1 row/s:

| | rate | one month | two months |
|---|---|---|---|
| Telemetry database | ~80 bytes/row at 1 row/s → ~6.9 MB/day | ~208 MB | ~416 MB |
| Log at DEBUG | ~180 bytes/line, ~24 lines/min/operator → ~6.3 MB/day | ~188 MB | ~376 MB |

Free space on the board: **2.6 GB**. So a two-month run at DEBUG lands near
800 MB — it fits, but nothing enforces it and nobody had written it down.

**Recomputed, 23 August 2026 — `sampler_interval_seconds` is now 0.5, not
1.0.** The telemetry-database row doubles with it (log row is operator-poll
driven, not sampler-driven, unaffected): ~160 bytes/s → **~13.8 MB/day**.
`telemetry_retention_days` also dropped 60 → 30 the same session, so the
database no longer grows past that window — it plateaus at roughly
**13.8 MB/day × 30 days ≈ 414 MB**, not the ~416 MB two-month figure above,
which was for the old rate and window and no longer applies. Not
re-measured on the board at the new rate — this is arithmetic from the
7 August figures, flagged as such.

**Retention, corrected.** Telemetry purges at 60 days
(`telemetry_retention_days`), so the database plateaus rather than growing
without limit. The **real Logger461 rotates**, so production logging is bounded
too. What is *not* bounded is the **stand-in** in `main.py`, which is what runs
on any board without the wheel installed — including this one. It opens the file
and appends forever.

**Provisional numbers from Session 2's soak, 8 August 2026 — treat with
caution, both runs were abnormal (D4 reopened):** 3-operator run (~22 min,
`LOG_LEVEL` was inert at the time (D29, since closed 25 August 2026 — the
stand-in now actually filters), so this measured the DEBUG rate regardless
of the configured setting; a board on INFO from here on should log less
than this, not re-measured): db 0.27 MB/hr → 196 MB/month, log 0.19 MB/hr →
137 MB/month, mcu log 0.10 MB/hr → 75 MB/month. Broadly in the range this
table already expected, but a run dominated by connection-rejection churn
is not a clean
baseline — re-measure once D4 is actually closed.

Still to do:

- Confirm the telemetry purge actually plateaus the file. SQLite reuses freed
  pages rather than shrinking, so the size should level off, not fall — verify
  rather than assume.
- Measure the message rate with several operators, not one.
- **Size any MCU-side logging against this budget before adding it** (D3). Debug
  chatter from the relay is the highest-rate traffic in the system, and if it
  crosses the Bridge into the same log file it spends from the same allowance.
  If the stand-in is what will be running, give it rotation first.

**Acceptance:** a table like the one above, verified over a multi-hour run, with
a stated maximum footprint the board cannot exceed.

---

### T10 — Write the recovery runbook, in two halves
**Status:** open · **Severity:** high · **Raised by:** the operator answering
`OPEN_QUESTIONS.md` Q3, 8 August 2026

The site is roughly three hours away and **there is no written procedure for
what to do when the system misbehaves.** ADR-0007's entire argument rests on not
turning a signal loss into a site visit — and then nothing says what the person
who did travel should actually do.

The operator's answer defines the shape: **on site is the same UI as remote,
plus `adb`, because they are USB-C connected rather than coming through the
relay.** So there are two audiences and two documents:

**Remote half** — what an operator with only the browser can do. The UI says
OFFLINE: what does that mean, how long to wait before it is real (three failed
polls, about three seconds), what a refusal looks like versus a fault, and when
to stop pressing and call someone.

**On-site half** — the `adb` sequence, in order, with what is safe to run while
a mechanism is attached:

```bash
adb shell arduino-app-cli app logs  user:servo_mvp
adb shell arduino-app-cli app start user:servo_mvp   # ~16 s warm, ~7 min cold
```

Plus: reading the database directly, confirming `servo.backend backend=hardware`
rather than the simulator (D8), and **what is never safe** — the mechanism can
be moved by hand with power off, so a restart with somebody's hands in it is not
a neutral act.

**On-site is also the diagnostic seat.** Whoever holds the USB-C cable is the
only person who can catch D10's unexplained sampler exception, or anything the
soak surfaces. Give them the commands before the trip, not during it.

**Acceptance:** both halves written, and the on-site half rehearsed once by
somebody who did not write it.

**Related:** Q3, Q9, D3 (the MCU counters they will want and cannot read), D8.

---

### T11 — Write the operations manual
**Status:** open · **Severity:** high · **Raised by:** the operator, 8 August 2026

**The everyday document. Nothing in this repository tells someone how to operate
the system.** Every document here is written for whoever is *building* it —
`CLAUDE.md`, the ADRs, the conventions, this backlog. The person who sits down
in front of the UI to do a day's work has nothing.

That gap ships with the MVP unless it is closed: the receiving team runs this
unattended for days, and the benchmark is only as good as their ability to
operate it correctly for those days.

**Distinct from T10, and the split is deliberate:**

| | T11 — operations manual | T10 — recovery runbook |
|---|---|---|
| When it is read | every day | when something is wrong |
| Audience | the operator | the operator, then whoever is on site |
| Content | how to do the work | how to get back to working |

One fact in one file: **the manual does not repeat the runbook.** It points at
it.

**Contents, at minimum:**

- **The startup ritual.** Drive the mechanism to mid-travel, press Calibrate —
  and *why*, because the mechanism can be moved by hand while power is off, and
  because a datum that is not mid-travel strands half the travel window
  (ADR-0003, and the original cause behind D1).
- **What every control does**, including the ones whose meaning is not obvious:
  Lock versus motor isolation versus emergency stop, and why they are separate
  controls (R2, R8).
- **Saved positions**: what a zero is, what activating one changes, and how to
  get back to the datum (D12).
- **Reading the screen honestly**: what MOVING, SETTLING and HOLDING mean; what
  the unverified-reference warning means; what a blank position means and what
  it does not.
- **The travel window**: ±90 output degrees, 0.06° per step, and what a refusal
  as out-of-travel is telling them.
- **Pulling the data**: the export, the time range, and the graphs — the thing
  the receiving team will be doing at the end of their run.
- **What not to do**, with reasons rather than prohibitions.

**Write it after the batch-1 and batch-4 work, not before** — several of the
things it must describe are the things being changed. A manual describing the
current error messages would be wrong within a week.

**Acceptance:** somebody who has never seen the system can run a normal working
session from this document alone, without asking a developer.

**Related:** T10 (the emergency half), D12, D17, R2, R5.

---

### T5 — Add `design_diagrams/` with PlantUML
**Status:** open

Both reference projects (`Krusty-Crab`, `Eyal-FastAPI-Project`) carry
`design_diagrams/pumls/` — architecture diagram, ERD, project UML — plus rendered
images. This repo has none, and it is the more complex of the three: it spans two
processors, a serial bus, a relay and a browser.

**Acceptance:** at minimum an architecture diagram showing the MCU/Linux split
and the byte path from browser to servo, plus an ERD for the SQLite schema.

---

### T6 — Restructure the exception hierarchy
**Status:** open · **Priority:** later, but agreed

Adopt the three-tier hierarchy from `CONVENTIONS.md`: service base
(`ServoMvpException`) → general category (`NotFoundException`) → concrete
(`ServoNotFoundError`). Each class carries its FastAPI status code; error codes
accumulate with `+=` into `SERVO_MVP.NOT_FOUND.SERVO_NOT_FOUND`.

Exceptions must **carry metadata**, passed uniformly and logged at the top level.
They do not today.

The payoff is one handler on the service base exception instead of a handler per
type.

Current state: a flat set under `DomainError`, no error codes, no metadata.

**Acceptance:** one exception handler covers the service; every raised exception
carries a dotted error code and metadata.

---

### T7 — Add the database abstraction
**Status:** open

The abstract/concrete split used for repositories is missing for the database
itself. `python/app/db/database.py` is a concrete `Database` with no contract
above it; it should be an abstract `Database` with a concrete `SqliteDatabase`.

This is the gap meant by "database separation" — not the repository layer, which
already has it.

**Acceptance:** nothing outside the concrete implementation names SQLite.

---

### T2 — Package the air-gapped bundle
**Status:** open

Production runs on a secure isolated network. The wheelhouse
(`--platform manylinux2014_aarch64`) and the vendored patched `Ethernet`/`SCServo`
libraries must be present and verified before delivery.

Current development runs on a WiFi-mounted board instead, because there is only
one servo bus adapter and it sits on a "coloured" network that cannot be
introduced to the secure one. **The air-gapped path is therefore untested.**

**Acceptance:** a clean board with no network provisions and runs from the bundle
alone.

---

### T3 — Run the on-target test suite
**Status:** open · **Flow:** `WORKFLOWS.md` W6

`sketch/tests/OnTarget/` has never been uploaded. It covers ping, configuration
writes, landing accuracy and stop-hold — the things a host cannot check.

**Acceptance:** uploaded once with the servo free-shafted, tally recorded here.

---


### T18 — Front-end conventions, and split `app.js` by feature
**Status:** open · **Raised by:** the operator, 26 August 2026, during the
T15/Q10 discussion · **Scheduled:** after the client demo, unless brought
forward

**The front end was never given conventions.** `CONVENTIONS.md` covers
Python and C++ only. `python/static/app.js` is 2,140 lines in one file with
no JSDoc, no module boundaries; `style.css` (342 lines) and `index.html`
(164 lines) have no comment or structure rules either. This is why T15's
prose strip explicitly excludes all three files — stripping comments from
code with no standard to strip *to* would just be deletion, not a style
pass.

**Two halves:**

1. **Write the missing `CONVENTIONS.md` section** — JSDoc in the same shape
   already used elsewhere (one-line summary, typed `@param`/`@returns`, no
   explanatory paragraphs, matching the Python/C++ rule decided under Q10),
   plus comment rules for CSS and HTML.
2. **Split `app.js` by feature into native ES modules** (`<script type="module">`,
   no bundler — the air-gapped delivery path rules one out anyway, same
   reasoning as ADR's no-framework decision). Beyond consistency, this is
   expected to help cache granularity and maintainability; **on a
   LAN-served board, raw load time is unlikely to move much** — stated
   plainly so this isn't oversold as a performance fix it probably isn't.

**Why this is Claude-led, not Antigravity:** splitting a 2,140-line file by
feature changes load order and module boundaries in code the client will be
looking at during the demo. That is judgment work with a live board check
behind it, not a pattern-matched style pass — the opposite of T15a/T15b.

**Acceptance:** `CONVENTIONS.md` covers JS/CSS/HTML; `app.js` is split into
feature modules with no behaviour change, confirmed live on the board
(`/operator-lens` pass); `tools/check_client_behaviour.js` still passes
unmodified.

**Related:** T15 (same "strip the prose" motivation, different axis — code
organisation, not comment volume).
