# R-items — detail

Full entries for every open `R`-numbered item (requirements/build items).
Indexed one line each in `../BACKLOG.md`; read this file only for the item
you're picking up.

---

### R1 — Determine the real concurrent-operator ceiling
Target: roughly three remote operators plus one local USB-C session, all
connected at once without failure. This requirement appears in no other document.
The only enforced limit anywhere is `kMaxRelaySockets = 6`.

**Open question:** can the Bridge sustain that load at all? Unknown.

**Sharpened by the operator, 8 August 2026** (`OPEN_QUESTIONS.md` Q2, Q3, Q9):

- **The sessions are screens left open, not people driving.** That is the cheap
  case — a polling browser reuses one connection. Driving is occasional.
- **The on-site session is the same UI plus `adb`**, connected over USB-C.
- **7 is a hard ceiling, not a setting.** `Config.h:44` already recorded why:
  the W5500 has 8 hardware sockets and the listener takes one. Raising
  `kMaxRelaySockets` from 6 buys **exactly one more slot**, then stops.
- **So the lever is `timeout_keep_alive=5`, not the socket count.** Five seconds
  of slot retention per connection is what produces the measured ceiling of
  about one new connection per second. That is the number to tune.
- **And the arithmetic may not be what it looks like** — if the USB-C session
  reaches uvicorn without crossing the W5500 (Q9), it costs no relay socket at
  all and the budget is the remote screens alone. **Unverified. Do not report
  R1 as met on the strength of it.**

**Measured, 8 August 2026 — target not met at 3 operators, against an
architecture since replaced.** `synthetic_operator.py` modelled each operator
as 3 independent poll streams (state, zeros, events), matching what `app.js`
did per-tab at the time. 3 operators = up to 9 concurrent streams against 6
slots: **1462 rejections in ~22 minutes**, ending in a stall that needed a
restart to clear. **1 operator = 3 streams, comfortably under the ceiling:
only 49 rejections and no oversubscription signature** — but the same D4
stall still occurred twice and self-recovered.

**Stale as of 11 August 2026 — do not read this measurement as current.**
Two things changed since: D4 closed (cause and fix in `docs/CLOSED.md`), and
the SSE migration collapsed those 3 poll streams/operator to 1 stream/operator,
so "9 concurrent streams for 3 operators" no longer describes what `app.js`
opens. **R1 is not blocked on D4 any more; it is simply unmeasured against
the current architecture.** Re-measurement is scheduled as a real (not
synthetic) software stress test, varying operator counts, no rig involved
— session 17 in `../BACKLOG.md`'s current plan. Still unverified
regardless: the USB-C/Q9 question above.

---

### R3 — Confirm whether the Bridge could carry a frontend framework
The no-framework decision was justified partly on the assumption that the Bridge
relay could not carry a framework's payloads. **That assumption is unverified**
and may be wrong.

It does not change the current decision — the air gap independently rules out a
build pipeline — but the reasoning must not be written into an ADR as fact until
it is tested. See `docs/adr/` when written.

---

### R4 — Post-MVP: mechanical restraint servos, unified under one Lock
After the MVP is accepted, additional servos will be added to physically restrain
the primary servo. At that point the digital Lock, motor isolation and the
mechanical restraint are meant to become a **single** Lock concept rather than
three separate controls.

Out of scope for delivery; recorded so today's decisions do not foreclose it —
in particular, the Lock's API and UI should not be shaped as if "digital only"
were permanent.

**The mechanism already exists today, manually.** Two butterfly screws clamp a
3D-printed arch onto the shaft, operated by hand — R4 is the mechanical team
adding servos to drive those screws so it's software-controllable and
sensed. Motivation (operator, 25 Aug 2026, during R2's design): once the
physical lock holds position by friction, the primary servo's motor can rest
(isolated) instead of being held energised for months at a field site — the
point of **R2**'s isolation feature in the first place. R8 (emergency stop)
is expected to engage isolation and the physical lock together for an
instant stop.

---

### R8 — Emergency stop
**Scope:** post-MVP · **Can wait**

A single operator action that engages the Lock **and** removes motor power at
once, rather than requiring the two to be composed by hand. Requested by the same
discussion that produced R2.

This is the reason Lock and motor isolation are kept as separate controls — see
R2. Fusing them now would leave no distinct meaning for emergency stop later.

---

### R5 — Metrics export and benchmarking output
**Scope:** in MVP · **Status:** mechanism, UX gaps and operator-requested richness all shipped, 23 August 2026 (Session 5) · one gap genuinely still open, see table below

Pull telemetry for an arbitrary time range and chart it for delivery. The
point is that the MVP must be **benchmarkable**: the receiving teams need to
see whether the servo actually handles what it is asked to handle.

**Shipped, 23 August 2026 — architecture note.** The 10 August decision
below (XLSX not CSV, native charts, one data product) still holds exactly
as reasoned. What changed is **who builds the file**: not the export
endpoint (`openpyxl` was the original example) but the **browser**,
client-side, in `app.js` — decided deliberately, not a fallback. The server
stays a dumb byte pump per ADR-0001: it streams the existing compact binary
format (`GET /api/v1/telemetry/binary`, gzip'd) and never has to hold or
transmit a built `.xlsx`, which would be a far larger payload crossing the
same ~11.5 KB/s Bridge link that already dominates every other timing
number in this project. See D31 for the board measurements this rests on.

An 11 August session wrote most of this once already (`app.js`'s
`generateExcelXlsxZip`) and it never actually worked — two functions it
called, `makeChartXml`/`makeDrawingXml`, were never written at all,
guaranteed `ReferenceError` on every attempt. Rebuilt 23 August against a
real generated reference workbook (verified with `XlsxWriter`, unzipped, the
actual chart XML schema copied from there, not guessed a second time from
documentation) — see D31.

**Format decided 10 August 2026 (operator + team lead), revised same day.**
Export format is **XLSX (Excel), not CSV** — team lead's correction: a CSV
cannot carry a chart, and the point of this item is that it must. Charts are
native Excel chart objects, not rendered images — this still avoids the
original matplotlib/sampler-contention risk (D22's stated concern), because
writing chart-definition objects into the workbook is not rasterising a
plot. The data sheet is the raw form; the chart objects read from it
directly inside the same file, so there is still one data product, not two.

The standalone CSV export button was retired (operator decision, predates
this session) once XLSX existed as the one export artifact.

**Elevated to a build item, 8 August 2026.** The second of the two unbuilt
in-MVP items. Its absence is not a missing feature — it is the reason R6 cannot
be written, the reason the soak run has no output format, and the reason the
receiving teams have nothing to judge. **Everything measured so far has been
read out of an ad-hoc query or a log.**

### The use case this actually serves — stated 8 August 2026 by the operator

**The receiving team runs the system for several days on their own, unattended.
Afterwards we load what it recorded and see what happened.** That is the
benchmark. It reframes R5 from "graphs for a handover slide" into **a forensic
record of a run nobody watched**, and three consequences follow:

- **Every field gets the same chart treatment — position, torque, temperature,
  voltage, current.** No field is singled out over another. **Revised 10
  August 2026** (operator): the original text elevated torque above the
  others; corrected — the standard is "give the full picture," applied
  uniformly, and any field gets extra numeric detail (e.g. peaks/sustained
  figures) if it genuinely needs it to be read correctly, not because of
  which field it is. `torque_kgcm` is already sampled, stored
  (`sqlite_telemetry_repository.py:28`) and in the CSV columns
  (`telemetry_service.py:17`), same as the rest — the data layer needs
  nothing regardless of chart treatment.
- **Nobody is watching while it runs.** Anything not recorded is lost for good.
  Before that run, confirm the sampler survives days rather than minutes (D10's
  unexplained exception, T9's growth rates, and the stand-in logger in `main.py`
  that appends forever without rotation).
- **The window is days, not a session.** See D22 — the only export control in the
  UI is fixed at 24 hours, so after a five-day run an operator can retrieve the
  last day of it and no more.

**30-day telemetry retention (`telemetry_retention_days`, lowered from 60
this session) is the real upper bound on a single export now** — a full
30-day/0.5s-interval pull is 5.18M rows, board-tested at that exact scale
(see below), not just assumed to fit.

**Acceptance, made concrete — what actually shipped:**

- Given a start and end timestamp, the workbook carries every field with
  the same treatment: position, torque, temperature, voltage, current,
  sampler interval. Peak/sustained figures are computed once, from the
  full-resolution dataset, on the **Overview** sheet — never from a
  downsampled series.
- **Every field gets a native Excel line chart**, built from a hidden
  `ChartData` sheet whose cells are **live formulas** pointing back at the
  exact day-sheet cell each downsampled point came from (min-max binning,
  ≤2000 points/chart — keeps spikes/faults visible, not smoothed away).
  Editing a day sheet updates the chart. Every formula cell also carries a
  cached value (matching real Excel output, confirmed against a generated
  reference file) so a renderer that doesn't recalculate on open —
  OnlyOffice, some LibreOffice paths — still shows something correct.
- **One worksheet per calendar day** for the raw data, full resolution, no
  downsampling, no row cap — bounds every sheet far under Excel's
  1,048,576-row ceiling regardless of range length. This is also what
  closed the old silent-truncation defect: `export_max_rows` no longer
  needs to be a practical limit (raised 50,000 → 10,000,000, a defensive
  ceiling only — see `config.py`).
- **Must work over a multi-day window.** Board-tested at the real worst
  case: 30 days / 5.18M rows completes in ~73s and produces a 193MB file
  (client-side, in-browser) — down from an unoptimized first pass that
  either exhausted a 4GB heap (15 days) or produced a 349–475MB file,
  fixed by two changes: the zip writer now actually deflates its contents
  (it shipped uncompressed at first — a real gap, caught by testing at
  real scale, not assumed fixed because it "worked" at 2 days), and each
  day's XML is built, compressed and discarded one at a time instead of
  holding the whole range in memory at once. Further shrunk 45% (349MB →
  193MB) by dropping a redundant duplicate timestamp column (kept only a
  native Excel date, not a spelled-out text copy too), packing the 8
  boolean/fault columns into one bitmask byte (same encoding
  `export_binary_stream` already uses — one fact, one place), and rounding
  values to the 2 decimals the sensor data actually supports.
- Runs on the board *or* off it against a pulled database — generation is
  entirely client-side JavaScript, needs only the binary stream, never the
  servo attached.
- The standalone CSV export was retired (see above) — XLSX is the one
  export artifact now, its data sheets serving the role CSV used to.
- Chart XML verified against a real `XlsxWriter`-generated reference file,
  not written from documentation alone — the previous attempt's
  `makeChartXml`/`makeDrawingXml` were never implemented, see D31.

**A real corruption bug shipped with the first "done" claim, found by the
operator opening a real export in OnlyOffice, fixed the same session.**
The central directory's general-purpose-flag and compression-method
fields were at swapped byte offsets — `unzip -t` doesn't catch this,
`zipfile`/`openpyxl`/OnlyOffice do, and did. Fixed and re-verified against
the exact real board data with `zipfile.testzip()` and
`openpyxl.load_workbook()`, not just `unzip -t` again. **The lesson, not
just the fix: a file "opening" in one lenient tool is not proof it's
correct — validate with the strictest available reader, and test cross-app
compatibility for real, not by inspection.**

**Shipped, 23 August 2026 (Session 5) — the operator redirected this session
live, mid-plan, to two new fields plus the whole UX gap table at once.**
Decisions below are scoped to this one item, so recorded here rather than
as a standalone ADR.

- **Target angle and servo (pre-ratio) angle, end to end** — captured
  (`ServoStateStore.set_target`/`_to_servo_deg`, `servo_state.py`), persisted
  (`telemetry.target_deg`, nullable, idempotent migration), carried over the
  binary contract (header gains the gear ratio as a float so the client
  derives servo angle rather than re-declaring the constant — the exact
  duplication that caused D9), shown live (`.subline` under the big
  readout: target, signed Δ, servo angle, plus a target marker on the
  travel bar — the deviation is spatial, not arithmetic) and in the export
  (own columns, own line chart, an overlay chart plotting measured against
  target on one axis). Stop marks the target **stale, not cleared** — kept
  on screen dimmed, because "asked for 45, stopped at 27" is the reading
  the feature exists for.
- **Angle-correlated charts** — torque/voltage/current/temperature each
  plotted against **output angle** (mechanical team's request), line style,
  angle-sorted downsample. Real OOXML type is `c:scatterChart` with
  `scatterStyle="lineMarker"` (a category axis cannot carry a genuinely
  numeric, unevenly-spaced axis) — verified against an XlsxWriter reference
  before writing it by hand, same rule as everything else here.
- **Typed chart-range selector** — two date cells on Overview
  (`RANGE_FROM_CELL`/`RANGE_TO_CELL`); every `ChartData` formula gates on
  them (`IF(AND(...),value,NA())`, `dispBlanksAs="gap"`) rather than a
  per-day picker. Confirmed live against real board data: editing the
  dates narrows every chart.
- **Richer Overview**: a per-day table (samples, moving %, angle travelled,
  peak torque/current, temp/voltage range, stalls) below the chart grid,
  derived from data already grouped by day — no schema change.
- **Decoded flags** — the bitmask column is gone; `Moving`/`Locked` are
  their own columns, `Faults` is a decoded name list. Closes the old
  "flags too compact" complaint by construction rather than tuning the
  packing.
- **All day-sheet columns sized explicitly** (were unset entirely —
  `makeDaySheetXml` had no `<cols>` at all, not just a narrow date column).
- **LCARS styling** — real palette hex values from `style.css`, not
  re-guessed: tangerine header/title band, panel2 row banding (row-level
  `s=`+`customFormat="1"`, confirmed to render with no per-cell stamps —
  matters at 5.18M rows), alarm-bg fault rows, Bahnschrift SemiCondensed/
  Consolas fonts matching the app's own choices.

**Desired angle's earlier "defer to a later session" reasoning (retroactive
NULLs on existing rows) turned out not to be the operator's actual ask** —
they wanted it captured going forward and shown live too, not just charted
retroactively. Overridden on request; the retroactive-NULL fact is still
true and just doesn't matter for what was actually wanted.

**Five more defects found live on the real board, same session, fixed
before calling it done — the export's own standing lesson (found by
opening a real file, not assumed) held again:**

1. Travel bar scaled position as `deg/360` on a mechanism that travels
   −90..+90 — every negative angle rendered as 0%, indistinguishable from
   the datum. Found designing the target marker; fixed by sending the
   reachable range in the state response instead of a second hardcoded
   copy of it in `app.js`.
2. Binary format's documented types disagreed with the actual struct
   (`voltage_v`/`current_a` declared `H` in the comment and read as
   `getUint16` client-side, packed as signed `h` server-side). Harmless at
   real values; fixed since those exact lines were already being touched.
3. **A genuine regression, caught and reverted the same session**: `c:dateAx`
   with automatic tick spacing rendered cleanly against an isolated
   reference (500 evenly-spaced points) but produced an illegible
   per-second label smear against real, denser board data — worse than
   the original crowding it was meant to fix. Reverted to `c:catAx` with
   an explicitly computed `tickLblSkip` (we already know the point count;
   no reason to trust a renderer's heuristic on data it hadn't been tried
   against) plus restored diagonal label rotation, both re-verified
   against real board exports before shipping.
4. Overview's title band and its own value column (the range-selector
   dates) were both too narrow for their own content — same class of gap
   this whole item exists to close, just not caught until a real render.
5. The target/Δ/servo sub-line had uneven spacing (6px between a label
   and its own value, 18px between items) — visually lopsided around Δ
   specifically. Flattened to one uniform gap.

**Known gap, still genuinely open:**

| Gap | What was seen | What's needed |
|---|---|---|
| No narrative of *what happened* (moves, refusals, fault transitions over time) | R5's stated use case is reconstructing an unattended run; a table of instantaneous values requires the reader to re-derive events by eye. Root cause: the only place holding that narrative, `EventService` (`core/events.py`), is an **in-memory ring buffer** that does not survive past the SSE session it feeds live — there is nothing left to export by the time an operator requests a range | Needs a persisted move/event history — a real schema item, own session, not a same-session `app.js` patch |

**Related:** this is also how "stable" gets defined — see R6. D18 — the export
is the seed of this and currently fails silently. T9 — the storage numbers this
must not contradict.

**Blocks:** MVP handover, and R6 entirely.

---

### R6 — Define "stable" by benchmark, not by adjective
"Stable enough to hand over" cannot currently be written down as a checklist.
The plan is to measure first, then set the bar from what the measurements show.

Agreed elements of the bar so far: all defects closed; `CONVENTIONS.md` applied
(T1); air-gapped bundle built and booted on a clean board (T2); on-target tests
run (T3); concurrent-operator ceiling measured and meeting roughly 3 remote plus
1 local (R1); UI verified at the operator screen size (D7); the C++ side
diagnosable (D3); docs true. Numbers for the rest come from R5.

The existing tests run and pass, but are judged not to cover enough — coverage of
the relay and controller is the known hole (see `AUDIT.md`).

---

### R7 — Handover logistics depend on adapter delivery
More servo bus adapters are expected to arrive this month. The current adapter is
on a "coloured" (internet-facing) network and cannot be introduced to the secure
isolated network, which is why development runs on a WiFi-mounted board and the
air-gapped path stays untested (T2).

- **If the adapters arrive before the MVP is finished:** box the system into the
  secure network and hand it over there.
- **If they do not:** hand over with the single existing coloured adapter.

This is a delivery-shaping constraint, not a task.

---

### R10 — Zero service overhaul: calibration stays, "zeros" become saved points
**Status:** open · **Raised by:** client demo feedback, 27 August 2026,
decided with the team lead, 30 August 2026 · **Design worked out in full
this session**

The client doesn't want "zeros" — a saved position that, when selected,
reassigns the baseline (what 0° means). They want to keep working in one
fixed perspective and just save labelled points within it. **Calibration
(the one datum, ADR-0003's mid-travel reference) is unaffected and stays
exactly as it works today.**

**Two separate, smaller pieces replace today's `ZeroService`:**

1. **Calibration collapses into `app_state`, no dedicated table.**
   `calibrate()` is the only method of today's `ZeroService` anything else
   depends on (`servo_state.py:187,248` only ever call `get_active()`,
   which is always the datum once nothing else can activate a baseline).
   `capture()`, `activate()`, `delete()`, `list_all()` and their guard
   exceptions (`ActiveZeroError`, `DatumZeroError`) are all dead once
   nothing calls them — delete them, don't keep them as compatibility
   shims. Store the datum as two keys (`datum_raw_counts`,
   `datum_captured_at`) on the existing `app_state` key-value table
   (`isolation_service.py`'s `_ISOLATED_INTENT_KEY` is the pattern to
   copy) instead of a `zeros` table that only ever holds one row. Deletes
   the `zeros` table, `ZeroReference`, `ZeroRepository`/
   `SqliteZeroRepository` entirely. Rename `ZeroService` →
   `CalibrationService`, `routers/zeros.py` → a one-endpoint calibration
   router. `CONTEXT.md`'s *Zero reference*/*Baseline* glossary entries
   retire or fold into *Datum* — there's no longer a distinguishable
   genus.

2. **New saved-points feature, genuinely separate storage.** Angle
   (within ±90°) + operator description, many rows, grows over time — a
   real table (not `app_state`, which is for small flags, not a growing
   list of named records). **Must store `raw_counts`, never a degree
   value** — output degrees are computed relative to the datum
   (`servo_state.py:347`), so a point stored as degrees silently points
   to a different physical position after any future recalibration; a
   point stored as `raw_counts` is the servo's absolute hardware reading
   and stays correct regardless of the datum. Display still shows a live
   angle computed from `raw_counts` + the current datum. No activation,
   no baseline concept at all — moving to a saved point is just a normal
   move-to-angle call.

**Why not use the servo's own re-centre (`0x28 = 128`) instead of a
software datum:** considered and rejected. It's a live, irreversible
mutation of the servo's own encoder reference (no undo, no history, wrong
if the shaft isn't exactly at the physical reference when it's sent), and
it entangles calibration with one servo's register quirk, breaking the
hardware abstraction (ADR-0004) that lets calibration logic run against
the simulated backend. The project has direct scar tissue here already —
R2's board verification found `ServoController.cpp` checking the wrong ack
sentinel on writes to this same register family.

**Closes D12 and D19 by construction** — both are artifacts of the
activate/baseline model being removed (D12: "no way back to the datum
after activating a zero" — nothing to activate any more; D19: "saved
positions listed against baseline 0 when no zero active" — points are
always shown against the one datum, never a possibly-absent baseline).
Close both explicitly once R10 ships, don't leave them open.

**Stale once this ships, needs a pass:** T11 (operations manual, not yet
written) currently describes the old model ("what activating [a zero]
changes... get back to the datum (D12)") — write T11 against R10's model,
not today's.

**An ADR should formalize this on build** — not written yet since the
design isn't built; write it as part of implementing R10, not before.

**Related:** ADR-0003 (datum, mid-travel), ADR-0004 (repository
abstraction), D12, D19, T11.
