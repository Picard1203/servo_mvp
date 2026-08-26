# Review findings — Session 14 whole-app twin-review

**Transient triage input, not a backlog.** Written 26 August 2026 by the
inventory-mode `/twin-review` pass (`docs/BACKLOG.md` Session 14). Session 15
triages this: each entry becomes a `D`/`T`/`R` item or is dropped, then this
file is done being useful. Ranked most-severe first within each chunk.

**Baseline this pass ran against** (confirmed via `tools/verify.py` before
dispatch, unchanged after — no drift introduced by this pass, which was
read-only): 293 Python tests, 99.46% coverage (gate 99%), 194 native checks,
bridge contract agrees, 96 client-behaviour assertions, ruff advisory 50
findings (matches recorded baseline).

**Not reviewed by graphify, read manually where relevant:** `sketch/sketch.ino`,
`sketch/tests/OnTarget/OnTarget.ino`, `python/static/style.css` (no AST
extraction for `.ino`/`.css`).

**Every entry below is READ FROM CODE unless marked VERIFIED (something was
run to confirm it — a script, a repro, a grep, a test).**

---

## Backend — `python/app/`

1. **[HIGH] Three operator-facing controls report success without hardware
   acknowledgement.** `POST /servo/move`, `/servo/stop`, `/servo/isolate` all
   return their success shape (`202`/`200`) even when the Bridge/firmware
   never acked the command — `_command()` in
   `bridge_servo_repository.py:207-220` only logs a warning on a non-`"ok"`
   reply, never raises. **VERIFIED**: with a stubbed `"err"` bridge reply,
   `/move` returned `202 {"accepted": true}`, `/stop` returned
   `200 {"stopped": true}`, and `/isolate {"isolated": true}` returned `200`
   while the *next* `/state` call reported `isolated: false` in the same
   request cycle. `servo.py:56-84,103-116`; `motion_service.py`;
   `isolation_service.py:41-101`. Fix: make `_command`/callers surface a
   non-ack reply as a distinguishable error instead of a false success.

2. **[HIGH] Fine-approach move thread has no cancellation and can override a
   newer move.** `move_to()` spawns a daemon thread (`motion_service.py:98-102`)
   that sleeps up to 30s then unconditionally issues the *original* target
   (`:200`) with no generation check — a second `move_to()` call arriving
   during that sleep gets silently overridden afterward. The same thread's
   body is unguarded, so any exception inside it (e.g. finding 3 below) is
   swallowed by `threading` with zero trace and no follow-up event, even
   though `"servo.move.accepted"` already fired. Found independently by two
   lenses. Fix: a generation token checked before the final command, and a
   try/except around the thread body that logs and records a failure event.

3. **[HIGH] `move_to()` crashes with unhandled `TypeError` on an invalid read
   plus fine approach.** `current_output_deg()` returns `None` on an invalid
   reading; `_needs_fine_approach()` does `target_deg < start_deg` with no
   None-guard, unlike every other invalid-read path in this service, which
   raises `InvalidReadingError`. **VERIFIED**: reproduced
   `TypeError: '<' not supported between instances of 'float' and 'NoneType'`
   at `motion_service.py:177`. Masked today (`FINE_APPROACH_ENABLED=false`
   everywhere) but live code waiting for the flag to flip. Fix: guard
   `start_deg is None` the same way `read_counts()` does.

4. **[HIGH] `BridgeServoRepository`'s hardware import has no `except
   ImportError`,** unlike the three other identical import sites
   (`bridge_relay.py:37`, `mcu_log.py:40`, `routers/system.py:40`), so
   `use_hardware_servo=True` on a machine without the `arduino` package
   crashes app startup instead of degrading gracefully (`:59-61`).
   **VERIFIED**: reproduced the uncaught `ImportError`. This is the mirror
   image of D8 (wrong misconfiguration direction — hardware flag on where
   hardware isn't importable — crashes instead of degrading). Fix: wrap in
   the same `try/except ImportError` pattern as the other three sites.

5. **[HIGH] SSE stream generator swallows every exception silently** —
   `except (asyncio.CancelledError, Exception): pass`, no logging
   (`routers/stream.py:93-94`) — found independently by three lenses
   (twin-path, operator-impact, general-correctness). `TelemetryService._run()`
   handles the identical situation with `logger.exception(...)`
   (`telemetry_service.py:131-133`); this is the operator's primary live view
   and it can go stale with zero server-side trace. Fix: split the except —
   let `CancelledError` end quietly, log everything else before breaking.

6. **[HIGH] `CONVENTIONS.md`'s own gap table is stale after the fix it
   tracked landed.** The "Current gap against this standard" table
   (`CONVENTIONS.md:378-386`) still lists 67 missing-type `Args:` gaps, 4
   implicit-truthiness, 3 `while True`, 3 comprehensions, 2 `break` — but T1
   (closed 26 Aug, `docs/BACKLOG.md`) fixed all of it. **VERIFIED**: grep for
   every category above across `python/app/` returns zero matches. The file
   actively contradicts the current codebase on a rule this project treats as
   load-bearing. Fix: zero the table (or delete it, since T1 is closed).

7. **[MEDIUM] Pydantic validation errors have a different response shape than
   every domain error.** A bad `speed_dps`/`acceleration` — the error an
   operator is most likely to actually trigger — returns FastAPI's default
   `422 {"detail": [...]}` (a list), while every domain error returns
   `{"detail": "...", "reason": "..."}` (a string + reason). **VERIFIED**:
   reproduced both shapes side by side. Fix: a `RequestValidationError`
   handler normalizing to the domain-error shape.

8. **[MEDIUM] `calibrate()`'s off-centre warning re-derives reachability
   independently of, and can disagree with, the canonical per-side check** —
   uses a symmetric `half_window` from `max(abs(min), abs(max))` instead of
   `ServoStateStore.is_reachable()` (`zero_service.py:139-152`). **VERIFIED**:
   with an asymmetric window (`-30`/`90`), the two checks disagree. The
   `servo.calibrated` event also never records the off-centre condition even
   when it does warn (`:158-160`) — an operator only discovers the reduced
   range later via an unrelated `OutOfTravelError`.

9. **[MEDIUM] `MoveRequest`'s Pydantic bounds are frozen at import time**
   (`schemas/servo.py:10`) while the service layer always reads live
   `get_settings()` — diverges after any cache-clear (happens on every test
   via `conftest.py`, and would happen with any future hot-reload).
   **VERIFIED**: cleared the cache, changed `OUTPUT_MIN_DEG`, and got a value
   accepted by the schema that the live service would have rejected.

10. **[MEDIUM] No sqlite exception handling anywhere in the concrete
    repositories.** CLAUDE.md documents "database is locked" as a real,
    reproduced condition on this mount; an occurrence today surfaces as a
    generic unmapped 500, unlike every other error in the API.

11. **[MEDIUM] `_migrate()` swallows every `sqlite3.OperationalError`, not
    just "duplicate column"** (`db/database.py:100-104`) — including
    "database is locked" — with no logging, so a genuinely failed migration
    is indistinguishable from an already-applied one.

12. **[MEDIUM] `set_lock()`'s move-guard fails open on an invalid read** —
    `read_snapshot().moving is True` is `False` whenever the read is
    invalid, because `_empty_snapshot()` hardcodes `moving=False`
    (`motion_service.py:139-141`, `bridge_servo_repository.py:230`) — the one
    hardware-safety guard on this path silently bypasses exactly when state
    is least certain.

13. **[MEDIUM] `servo_state.py`'s `snapshot()` blanks all telemetry/faults to
    `None` on a single invalid read**, no hysteresis between a one-tick miss
    and a sustained fault (`:256-290`) — same shape as the documented D11
    precedent ("shouted OFFLINE at one dropped packet").

14. **[LOW-MEDIUM] `move_to()` blocks synchronously up to `settling_seconds`
    (1.5s default) before responding** when a lock-state change happened
    recently (`:225-232`) — a button press produces nothing for over a
    second.

15. **[LOW] `_ISOLATED_INTENT_KEY = "isolated"` defined as two independent
    literals** (`servo_state.py:18`, `isolation_service.py:15`) instead of a
    shared constant — agree today, no test would catch future drift.

16. **[LOW] `diagnostics/torque_register` returns ambiguous `null` on any
    failure**, no distinct status for "bus didn't answer" vs. "unexpected
    value" (engineer-facing diagnostic route, not main operator surface).

### Backend — doc truth

17. **[MEDIUM] `docs/CLOSED.md`'s T12 entry quotes a stale assertion count**
    ("63 now") inside the very sentence warning against quoting counts in
    prose — current is 96. **VERIFIED**.
18. **[LOW-MEDIUM] `docs/adr/0004`:14 states "186 tests" as an unqualified
    current fact** — now 293, no date qualifier (unlike similarly-aged facts
    elsewhere that are dated). **VERIFIED**.
19. **[LOW] `docs/adr/0004`:17-19 references README.md §7**, which no longer
    exists (README has 6 sections; the staleness it flagged is already
    resolved). **VERIFIED**.
20. **[LOW] Same fact (`main.py`'s `timeout_keep_alive`/`log_level` line) is
    cited at three different wrong line numbers** across D5 and ADR-0009 —
    real line is `main.py:242`. **VERIFIED**.
21. **[LOW] `docs/backlog/R.md`:155-156 cites `telemetry_service.py:17` for
    `torque_kgcm` CSV columns** — that line is now unrelated code; real refs
    are lines 106/152. **VERIFIED**.

---

## Firmware — `sketch/src/` (+ `sketch/sketch.ino`, `OnTarget.ino`)

1. **[HIGH — build-breaking] `NetworkRelay.cpp:170` is a stray, unmatched
   closing brace.** **VERIFIED twice independently**: a brace-depth script
   (both raw and with strings/comments stripped, ruling out a string-literal
   artifact) reports depth -1 for this file only — every other file in
   `sketch/src/` balances. Manually traced every block from line 22 through
   `Poll()`'s close at line 168: each one balances internally. `Poll()`
   itself closes cleanly at line 168 (matching its open at line 101), which
   leaves the file back at `namespace net`'s depth. Line 172
   (`}  // namespace net`) is the real, correctly-labeled closer — line 170's
   bare `}` immediately before it has nothing left to close and drives depth
   to -1. This is an unconditional syntax error at namespace scope (no
   macros or templates involved that could change brace structure) — a real
   C++ compiler will reject the file. Neither existing check catches it: the
   native suite never compiles this file (needs `Arduino.h`/`Ethernet.h`/
   Zephyr headers, native tests only cover pure-logic headers), and the
   bridge contract checker reads source text, not a build. This file's mtime
   matches the "strip explanatory prose from sketch/src/" commit (5437552,
   reviewed and merged since) — worth confirming during the fix whether that
   commit is where the stray brace was introduced, or whether it predates it.
   Fix: delete line 170.

2. **[HIGH] `ReadRawCounts()` returns 0 on a failed position read with no
   failure signal, and three callers command a real move to it** —
   `Stop()`, `SetTorque(true)`, `ClearFault()` (`ServoController.cpp:68-71,
   95-102,140-145,151-165`) all use the result as "hold here" and dispatch it
   through `Move()`, which acks success regardless. This is the exact
   ADR-0008 anti-pattern (fixed on the Python side) reproduced in firmware —
   confirmed independently by three lenses. A bus glitch during a Stop or
   torque-enable silently commands the servo toward position 0 while
   reporting success.

3. **[HIGH] `ReadSnapshot()` doesn't validate 6 individual reads before
   marking the snapshot `valid=true`** (`:43-66`) — position/temp/voltage/
   current/load are packed in unchecked against their own failure sentinels,
   and a failed status-byte read defaults `faults` to all-`false` ("no
   faults") rather than unknown, while `valid` stays `true`. Confirmed by
   three lenses independently. Matches ADR-0008's stated extension ("`moving`
   and the six fault flags null on a failed read the same way") — the
   extension exists in the ADR but wasn't implemented here.

4. **[HIGH] Empty/malformed `servo_move` Bridge payload silently commands a
   move to counts 0 and acks `"ok"`** — `FieldAt`'s fallback for a missing
   field is `0` (`BridgeApi.cpp:25-40,53-63`), and 0 is a legal target, so a
   truncated/malformed RPC call becomes a real move with no error anywhere.
   Confirmed by two lenses independently.

5. **[MEDIUM] `NetworkRelay::Poll()`'s bulk-read loop `return`s (not
   `continue`s) on a lock timeout inside a `for` over slots 0..5** —
   contention deterministically starves the same higher-numbered slots every
   pass (`:155-167`). A plausible second mechanism (distinct from the known
   256-byte overflow) for SSE disturbance during a large export.

6. **[MEDIUM] `WriteToClient` holds `chip_lock_` across `client.write()`.**
   If the vendored Ethernet driver's `write()` blocks on a stalled remote
   peer, one bad connection could stall service to every other client —
   compounded by Python's `bridge_relay.py` serializing all replies through
   one global lock too. **Partially unverified**: the vendored library isn't
   in this checkout, so the write's actual max blocking duration wasn't
   confirmed — the lock-holds-across-write fact itself is verified by
   reading; the compounded multi-client scenario is a hypothesis to check
   against real hardware before treating as settled.

7. **[MEDIUM] `WriteByte`/`WriteWord` (raw register writes) have zero
   retries and zero diagnostic logging**, unlike every read path (4 retries +
   `DiagLog::Push`) — used by `servo_set_deadband`/`servo_configure_range`
   (`ServoBus.cpp:58-64`). A genuine bus write failure during EEPROM config
   leaves no trace.

8. **[MEDIUM] `Move()`'s `WritePosEx` failure path logs nothing, while the
   harmless out-of-range refusal path logs clearly** (`ServoController.cpp:
   73-93`) — inverted signal-to-noise: the case needing explanation most is
   silent.

9. **[MEDIUM] `DiagLog::Push` in `WriteToClient`'s timeout path isn't
   rate-limited** and can overrun the 32-entry ring / compete for the Bridge
   RPC buffer during exactly the high-load condition (a large export) it
   exists to diagnose (`Config.h:31-33`, `NetworkRelay.cpp:78-83`). Relevant
   to backlogged T9.

10. **[MEDIUM] A half-configured boot reports "ready" identically to a fully
    good one** — `Begin()`'s config-write failures (torque limit, angle
    range) log nothing and don't affect `get_status`'s ready/no-servo, which
    only checks `bus_.Refresh()` (`App.cpp:29,47,58-59`).

11. **[MEDIUM] `kCountsPerTurn` defined independently in `Config.h` and
    `ServoRegisters.h`** (agree today, no shared source). `AngleMath.h`/
    `AngleConverter` is dead code in production (never included by
    `App.cpp`/`BridgeApi.cpp`) while Python holds its own independent copy of
    the same constants — the on-target smoke test validates only the dead
    firmware copy, so it can't catch drift in the copy that actually matters.

12. **[LOW-MEDIUM] `NetworkRelay.h`'s `chunk_bytes_` field is stored but
    never read** — `Poll()` hardcodes `config::kRelayChunkBytes` instead
    (`:85`, `.cpp:156`). Currently harmless (both values coincide today).

13. **[LOW] `was_up_[8]` is a hardcoded array size decoupled from
    `config::kMaxRelaySockets`** — latent out-of-bounds if the ceiling is
    ever raised past 8 (impossible today — hardware max is 8).

14. **[LOW] `SignMagnitude::Decode`/`Encode` duplicated in C++ and Python,
    called by neither production path** (test-only in both languages).

### Firmware — doc truth

15. **[HIGH] `skills/uno-q-st3215/SKILL.md`:194 states "the working relay
    used 256"** — `RELAY_NOTES.md` documents 256 as a confirmed structural
    overflow; the actual shipped value is 224. This file explicitly bills
    itself as bench-verified; a developer trusting this line could revert to
    a value now confirmed broken. **VERIFIED**.
16. **[MEDIUM] `CONVENTIONS.md`:364 cites "164 native tests"** (stale, now
    194) and **`:368-370`** describes D3 (C++ logging) as still-open — D3 is
    closed, with 10 logging call sites added across 3 files. **VERIFIED**.
17. **[MEDIUM] `RELAY_NOTES.md`:63-67 misattributes
    `DEFAULT_RPC_BUFFER_SIZE`** to the wrong vendored header (value correct,
    citation wrong) — undermines the re-derivability of the "don't raise past
    230" claim it anchors. **VERIFIED**.
18. **[LOW] Doc citation drift, several instances (all VERIFIED by grep, none
    change behavior):** ADR-0009 cites `Config.h:45` for `kMaxRelaySockets`
    (actual 29); `docs/CLOSED.md`'s R2 entry cites `ServoRegisters.h:53` for
    `kTorqueSwitch` (actual 43); ADR-0006 says the CSV format is declared "at
    the top of `BridgeApi.h`" (it's `BridgeApi.cpp`'s `FormatSnapshot`);
    `SKILL.md`'s top-level Bridge-contract list omits `servo_read_torque`
    despite documenting it elsewhere in the same file; both `README.md`'s and
    `SKILL.md`'s contract tables list a non-existent `servo_centre_here`
    endpoint (deliberately not exposed, per `DESIGN_NOTES.md:47`) and omit
    the real `servo_set_torque`/`servo_read_torque`; `RELAY_NOTES.md`'s
    section "7" physically appears before section "6".
19. **[LOW] `README.md`'s "Known gap: nothing in src/ logs" (pointing at D3)
    is stale** — D3 is closed and current code logs from `ServoBus`,
    `ServoController`, `NetworkRelay`. **VERIFIED**.

---

## Frontend — `python/static/` (+ `style.css`)

1. **[HIGH] `renderZeros()` computes saved-position offsets without applying
   `servo_direction`**, unlike every other angle value in this file and
   unlike the backend's own conversion (`app.js:678` vs
   `servo_state.py:_to_output_deg`). On any `SERVO_DIRECTION=-1` install,
   every non-active saved position shows the wrong sign — this is a literal
   recurrence of D9's mechanism, which the codebase's own D9 record already
   warned about. Confirmed independently by two lenses.

2. **[MEDIUM] `faultIsStale` is gated on `!measured` instead of `!known`** —
   during the 1-2 poll "one blip isn't a fault" grace window, the alarm
   banner can show a real position number *and* "(last known — position
   unknown)" simultaneously (`app.js:523,610`) — a direct on-screen
   contradiction, the exact failure mode this file's own comments say it
   exists to prevent.

3. **[MEDIUM] `COUNTS_PER_OUTPUT_DEG` hardcodes `counts_per_turn` and
   `servo_deg_per_output_deg` client-side** (`app.js:14`) — either being
   retuned in `.env` silently desyncs `renderZeros()`'s math from the
   backend, independent of finding 1.

4. **[MEDIUM] `doMove()`'s angle range check uses hardcoded `ANGLE_MIN`/
   `ANGLE_MAX`** instead of the live `output_min_deg`/`output_max_deg` this
   same file already reads from SSE state for the position bar
   (`:749-753` vs `:434-435`) — diverges the moment config changes from the
   ADR-0003 default.

5. **[MEDIUM] `nudge()`'s angle stepper hardcodes `ANGLE_STEP=0.06`**
   (`:2076`) — if `output_step_deg` is retuned, every nudge press produces a
   value the backend now rejects every time. The file's own comment
   documents this constant family already caused D21.

6. **[MEDIUM] "Start time must be earlier than end time" is misrouted
   through `sayError()`,** which has no `.status`/`.reason` to key off and
   falls back to the generic "controller is busy" message instead of the
   real date-range problem (`:1959-1961`).

7. **[MEDIUM] Speed nudge has no bound (unlike Angle's), and `doMove()` has
   no client-side speed range check at all** — a rejected out-of-range speed
   reaches the operator as raw backend validation text with no field name
   (`:2070-2079,744-753`).

8. **[MEDIUM] 5 of 6 fault types have no recovery control and no remedy text
   in the alarm banner** — only overload gets a "Clear fault & resume"
   button and explanatory suffix; the rest show a sticky red alarm with
   nothing to do or read (`:565,605-624`) — a direct "no route back" finding
   (D12-shaped).

9. **[MEDIUM] Exporting a zero-sample time range downloads a structurally
   valid, silently empty `.xlsx`** with no on-screen signal the window was
   empty (`:2030-2068`).

10. **[LOW] Connecting-state LED shows the same green as a confirmed-healthy
    connection**, next to text reading "CONNECTING" (`index.html:15`,
    `style.css:44,47`).
11. **[LOW] Empty Recent Activity feed renders as a blank panel**, no
    placeholder text (`:726-740`).
12. **[LOW] `servoRatio === 0` treated same as "no ratio"** in export
    (`:935`) — defensive-only, near-zero real likelihood.

**Confirmed by this pass, not new:** D19 (baseline-of-0-when-no-zero-active,
`:670`) and D12 (datum excluded from saved-positions list, `:673`) are both
still present, unregressed. **D17 partially addressed, not confirmed closed**
— the bar now scales against the live `output_min_deg`/`output_max_deg`
range (`:434-446`), satisfying the first half of D17's acceptance criteria
(`docs/backlog/D.md:238-239`), but this pass did not check the second half —
"the datum visible as a marked centre." Verify that specifically before
closing D17.

### Frontend — doc truth

13. **[MEDIUM] `app.js:620,800` use "home" in operator-facing text** —
    `CONTEXT.md`'s own glossary says "avoid: home" for this exact concept
    ("datum never home") — literally the project's own worked example,
    violated in live UI copy. **VERIFIED**.
14. **[LOW] `app.js:31,355` comments describe SSE cadence as "1 s"/"per
    second"** — actual cadence is 0.5s. **VERIFIED**.
15. **[LOW] `app.js:712` comment shows a pre-D33-fix timestamp example**
    (no UTC offset). **VERIFIED**.
16. **[LOW] `docs/CLOSED.md`'s D15 entry's "known gap" (doExport unguarded)
    was never updated after D18 closed it.** **VERIFIED**.
17. **[LOW] `style.css:219-221` references a touch/pointer note in `bind()`**
    that no longer exists in `app.js`. **VERIFIED**.
18. **[LOW] D34/D32 `CLOSED.md` entries cite stale `app.js` line numbers**
    (file grew from later features) — behavior still correct, citations
    drifted. **VERIFIED**.

---

## Docs — `docs/`, `CLAUDE.md`, `CONTEXT.md`, `CONVENTIONS.md`, `docs/adr/`

1. **[HIGH] `docs/backlog/T.md` contradicts itself on `telemetry_retention_days`**
   — line 91 says it's 30, line 98 says "corrected... 60 days." Three other
   docs (`PROJECT_STATE.md`, `R.md`, `CLOSED.md`) agree it's 30, so `T.md`'s
   own "corrected" line at 98 appears to be the wrong one. **VERIFIED**. This
   item's whole point is a capacity calculation that depends on which value
   is real — matters directly, not just as hygiene.

2. **[HIGH] `README.md` quotes "211 Python tests" (twice)** — current count
   is 293. README is the file `docs/PROJECT_STATE.md` names as what the
   receiving/procurement team judges the MVP by — this is D24's exact failure
   shape, in a file the T16/T19 number-hygiene passes never touched.
   **VERIFIED**.

3. **[MEDIUM] `docs/WORKFLOWS.md:263` instructs bare `pytest # 207`** — bare
   `pytest` fails per CLAUDE.md's own documented PATH note; count is stale
   and the block omits the 4th check (client-behaviour). **VERIFIED**.

4. **[MEDIUM] `CONVENTIONS.md:213` contradicts its own opening precedence
   rule** — says the ruff config "on the isolated network... takes
   precedence over this section," directly against `:9-13`'s "where the two
   disagree, this file wins," and points to a source that's unreachable.

5. **[MEDIUM] `docs/agents/domain.md` references a removed file**
   (`docs/FILE_REGISTRY.md`) and says "seven ADRs" when 10 exist — this file
   exists specifically to orient sub-agents before they explore code.
   **VERIFIED**.

6. **[MEDIUM] Operator-facing gaps in `README.md`** (the only doc a
   non-developer/deployer actually follows today, per `CLAUDE.md`'s own
   routing table): health-check ordering has the reader curl `/health`
   *before* being told to press Run in App Lab (likely prompting an
   unnecessary destructive re-wipe when it fails); "press Run" never says
   what a failed start looks like, unlike the very next subsection; the
   health-check example shows only the success value, not the D8
   silent-simulator failure it exists to catch; the doc never says how to
   obtain `<board-ip>`, the first thing a reader needs. All read from docs.

7. **[LOW] `CLAUDE.md §6` promises `adb` "start and stop" but the command
   block only shows start/restart/logs**, no stop.

8. **[LOW] Several stale/duplicate number citations, all VERIFIED by
   grep, none change behavior:** ADR-0009/`OPEN_QUESTIONS.md`/`R.md` disagree
   on the line number for `kMaxRelaySockets` (44 vs 45); `PROJECT_STATE.md`'s
   own headline "Status" block is 2 sessions stale against its own later
   entries in the same file (mitigated by an explicit disclaimer); ADR-0004
   states "186 tests" as an unqualified current fact (now 293); `AUDIT.md`'s
   frozen snapshot (186 tests/100% coverage/164 checks) has no in-file note
   that it's superseded (mitigated by the file's own top-of-file FROZEN
   banner); D35's headline "roughly 1.5-2x" undersells its own measured
   "1.5x-2.3x" range in five copies, which could bias triage away from the
   correct hypothesis (2.15x).
9. **[LOW] README.md's Ethernet-patch check doesn't state what "one or two"
   (a partial patch) means**, only "zero" and "three or more."

