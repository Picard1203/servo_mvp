# Tasks — detail

Full entries for every open `T`-numbered item. Indexed one line each in
`../BACKLOG.md`; read this file only for the item you're picking up.

---

### T20 — Doc-truth sweep from the whole-app review
**Status:** open · **Severity:** low · **Raised by:** Session 14
`/twin-review`, triaged 1 September 2026 · **Antigravity-shaped**

~25 VERIFIED stale citations, counts and dead references, one mechanical
pass, no judgment calls: `README.md` quotes "211 Python tests" twice (current
293+); `docs/CONVENTIONS.md`'s gap table still lists 67 missing-type gaps etc.
though T1 (closed) fixed all of it — verified zero matches by grep;
`docs/backlog/T.md` self-contradicts on `telemetry_retention_days` (30 vs.
"corrected... 60"; three other docs agree it's 30); `skills/uno-q-st3215/
SKILL.md:194` tells a future developer the working relay chunk value is 256,
which is now confirmed a structural overflow — the shipped value is 224;
`docs/CONVENTIONS.md:364` cites "164 native tests" (now 194); `docs/agents/
domain.md` references a deleted `docs/FILE_REGISTRY.md` and says "seven
ADRs" (10 exist); `docs/WORKFLOWS.md:263` instructs bare `pytest # 207`,
which fails per `CLAUDE.md`'s own PATH note; ADR-0004 states "186 tests"
unqualified (now 293+); plus ~15 stale line-number/section citations across
`ADR-0009`, `R.md`, `docs/history/CLOSED.md`, `RELAY_NOTES.md`, `README.md` (full list:
`docs/REVIEW_FINDINGS.md`, retired — see git history at the commit that
removed it, or this item's own working notes).

**Acceptance:** every citation above corrected to the real current value or
path; no new prose added, only facts fixed.

---

### T21 — Constants and dead code with no shared source
**Status:** open · **Severity:** low · **Raised by:** Session 14
`/twin-review`, triaged 1 September 2026

Five findings, one family — a value or a converter exists twice with nothing
enforcing agreement: `kCountsPerTurn` defined independently in `Config.h` and
`ServoRegisters.h` (agree today, no shared source); `_ISOLATED_INTENT_KEY =
"isolated"` defined as two independent literals (`servo_state.py:18`,
`isolation_service.py:15`); `NetworkRelay.h`'s `chunk_bytes_` field is stored
but never read — `Poll()` hardcodes `config::kRelayChunkBytes` instead;
`was_up_[8]` is a hardcoded array size decoupled from
`config::kMaxRelaySockets` (latent out-of-bounds if the ceiling is ever
raised past 8); `SignMagnitude::Decode`/`Encode` duplicated in C++ and
Python, called by neither production path.

**The one with a decision attached: `AngleMath.h`'s `AngleConverter`.** Dead
in production — never included by `App.cpp`/`BridgeApi.cpp`, referenced only
by `test_pure_logic.cpp` — while Python holds its own independent copy of the
same geometry and direction constants (D39 found and fixed the live copy;
the on-target smoke test still only validates the dead firmware copy, so it
cannot catch drift in the copy that actually matters). **Decide:** wire it
in as the real conversion path, or delete it and its test — leaving it as an
untested, unreachable second implementation is the worse of the two options.

**Acceptance:** each of the five either gets a shared source or the entry
records why duplication is fine; the `AngleConverter` decision is made, not
left standing.

**Related:** D39.

---

### T13 — Distil the remaining documents
**Status:** open · **Severity:** medium · **Raised by:** the operator, 8 August 2026

Docs are re-ingested at the start of every session, so their length is a
recurring tax on the work. Started 8 August 2026: closed items moved to
`docs/history/CLOSED.md` and Batch 1's own entries cut, taking `BACKLOG.md` from 15,223
words to ~10,600.

**Not yet done.** The remaining bloat is in entries written before this rule
(`D4` and `D22`, both previously listed here, were moved to `docs/history/CLOSED.md`
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

Also worth a pass: `docs/WORKFLOWS.md` (1,754) and `docs/CONVENTIONS.md` (1,350).

**Do it opportunistically** — distil an entry when you are already working on
that item, not as a sweep of its own. A sweep costs the tokens it is meant to
save, and rewriting reasoning you have not just re-derived is how facts get
dropped.

**Acceptance:** no open entry states the same thing twice, and every one keeps
its numbers, paths, decisions and honest statements of what was not tested. The
rule itself is in `CLAUDE.md` §4.

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
**Status:** open · half-done · **Priority:** later, but agreed · structure
built 30 August 2026, Session 16 (opportunistic, alongside R10)

**Done:** the three-tier hierarchy — `ServoAppException` (not
`ServoMvpException`; renamed, the "MVP" phase label doesn't belong in a
permanent exception name) → category (`ConflictException`,
`NotFoundException`, `ValidationException`) → concrete
(`LockedError`, `DuplicateNameError`, ...). Each carries its `fastapi.status`
code. Error codes accumulate via `ServoAppException.__init_subclass__`
reading `code=` off the class-definition line (`class LockedError(
ConflictException, code="LOCKED")`), not hand-written string
concatenation at each level — `LockedError.error_code ==
"SERVO_MVP.CONFLICT.LOCKED"`. One handler in `app.py`
(`_register_error_handlers`) replaced eleven per-type handlers, logging
every domain refusal from the exception itself instead of the scattered
`logger.warning()` calls at raise sites, which were removed as
redundant.

**Not done:** the acceptance below still isn't met. `metadata` is
structurally supported by every exception (`ServoAppException.__init__`
accepts it, inherited unchanged by every subclass) and is populated at
the four sites `motion_service.py` raises from
(`LockedError`/`IsolatedError`/`LockedAndIsolatedError`/`StepError`/
`OutOfTravelError`), but not yet at the others (`InvalidReadingError` in
`calibration_service.py`/`servo_state.py`, `NotFoundError`/
`StalePositionError`/`PositionOutOfRangeError` in
`saved_position_service.py`, `DuplicateNameError` in
`sqlite_saved_position_repository.py`). Deferred deliberately, at the
user's instruction, mid-session — infra first, population later, not
this run.

**Acceptance:** one exception handler covers the service (met); every
raised exception carries a dotted error code (met) and populated
metadata (not met — sweep the remaining raise sites).

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

**The front end was never given conventions.** `docs/CONVENTIONS.md` covers
Python and C++ only. `python/static/app.js` is 2,140 lines in one file with
no JSDoc, no module boundaries; `style.css` (342 lines) and `index.html`
(164 lines) have no comment or structure rules either. This is why T15's
prose strip explicitly excludes all three files — stripping comments from
code with no standard to strip *to* would just be deletion, not a style
pass.

**Two halves:**

1. **Write the missing `docs/CONVENTIONS.md` section** — JSDoc in the same shape
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

**Acceptance:** `docs/CONVENTIONS.md` covers JS/CSS/HTML; `app.js` is split into
feature modules with no behaviour change, confirmed live on the board
(`/operator-lens` pass); `tools/check_client_behaviour.js` still passes
unmodified.

**Related:** T15 (same "strip the prose" motivation, different axis — code
organisation, not comment volume).

---

### T23 — Run graphify's semantic pass on the doc backlog it's never had
**Status:** open · **Severity:** low · **Raised by:** Session 23, 3 September
2026

**The bare `graphify update .` this project runs after every change is
AST-only — a Python script, no LLM, no way to dispatch a subagent.** The
richer semantic pass (extracting rationale and concepts from prose, the
"fusion" `CLAUDE.md` describes) only ran once, at the graph's original
build on 7 August. Every doc edited or created since — `docs/CONTEXT.md`,
most ADRs, `docs/BACKLOG.md`, `docs/WORKFLOWS.md`, `docs/PROJECT_STATE.md`,
`app.py`, and everything from Session 23 itself — has had its structure
kept current but never had its content re-extracted. Confirmed via
`detect_incremental()`: 41 real project doc files pending, not a bug.

**What went wrong trying to close it this session:** dispatched two
subagents (Agent tool) at ~20 files each, per the `graphify` skill's own
chunking guidance. Both ran for a long time, visibly read files, burned
real session usage, and produced no output — no chunk file ever written to
disk. Likely cause: several of these docs are long (`CLAUDE.md`,
`BACKLOG.md`, `CONTEXT.md`, every ADR), and 20-file chunks sized for
typical source files may simply be too much content for one subagent turn
to finish. Abandoned rather than retried blind, per the operator's own
call — cost already sunk once, not worth risking twice.

**Do it this way instead:** either (a) set `GEMINI_API_KEY`/`GOOGLE_API_KEY`
before running `/graphify --update` — the skill uses `extract_corpus_parallel`
directly against Gemini instead of dispatching subagents at all, sidestepping
this failure mode entirely, or (b) if staying subagent-based, chunk far
smaller — 5-6 files per subagent, not 20 — so a single failure loses a
little work, not all of it.

**Acceptance:** `graphify query` can answer a question grounded in one of
the docs above (e.g. Session 23's own W9 rationale) that today only exists
in AST-invisible prose.

---

### T24 — A screening filter judges only its first six trials, tainting the "futile" verdicts on the PID gains
**Status:** open · **Severity:** low · **Found:** 8 September 2026, Session 27,
while building B9 on top of the same function

`screening_arm_filter` in `tools/d48_s26_campaign.py` collects a second batch
of trials when an arm needs re-screening, then decides using `trials[:SCREEN_N]`
— always the same first six, never the six it just went and collected. The
extra trials cost real board time and then do not reach the decision.

**Why it matters and why it was not fixed on the spot:** blocks B3–B6 used this
filter to call the PID-gain arms FUTILE. Those verdicts are recorded and were
acted on — the whole investigation moved off gain tuning partly because of
them. Re-reading them needs a deliberate look at what each arm's full trial set
actually says, which is a different job from fixing the line. It was noticed
mid-session while building something else on the same function, and tucking a
reinterpretation of four already-recorded blocks into that session would have
been worse than filing it.

Not urgent: the D48 conclusion does not rest on those blocks. The floor
trade-off was established by dose-response and confirmatory blocks that do not
use this filter, and the fix that closed D48 was in software, not in a gain.

**Acceptance:** the re-screen branch decides on every trial it collected, with a
test that fails on the current behaviour; then B3–B6's recorded verdicts are
re-derived from their stored trials and either confirmed or corrected in place
in D48's closed entry.

**Related:** D48 (closed), the same file's `_record_dose_response` picker bug
fixed in Session 27.
