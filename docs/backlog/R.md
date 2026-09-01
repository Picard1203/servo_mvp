# R-items — detail

Full entries for every open `R`-numbered item (requirements/build items).
Indexed one line each in `../BACKLOG.md`; read this file only for the item
you're picking up.

---

### R11 — Accept any typed angle; snap to the nearest step and show the delta
**Status:** open · **Raised by:** the client, via the operator, rig hand-testing
1 September 2026

Typing `85` is refused today because it is not an exact multiple of
`output_step_deg` (0.06°) — the operator is asked to do arithmetic the
machine should do. New design: accept any typed angle, snap to the nearest
reachable step under the hood, and show both the requested angle and the
snapped target with the delta between them in the UI.

**Not a revert of D32 — stated here so it isn't re-litigated.** D32 (closed
24 August 2026) killed *silent* rewriting: typing `0.08` became `0.06` with
nothing on screen, and its fix was explicit refusal instead. This is
*transparent* snapping — the delta is always shown. Same code path, a
different decision, made with the client in the room this time.

**Design:** snapping happens in one place, the backend
(`MotionService._validate_step`, `motion_service.py:259-273`, becomes a snap
instead of a raise), and the response carries the requested angle, the
snapped angle and the delta. The frontend stops holding its own copy of the
step constant and displays what it is told — removing, not synchronizing,
the twin: `nudge()`'s hardcoded `ANGLE_STEP=0.06` (`app.js:21,2151`, the same
constant family that caused D21 once already — confirmed still live by
grep, 1 Sept). Session 14's `/twin-review` also flagged `COUNTS_PER_OUTPUT_DEG`
(`app.js:14`) as a second hardcoded-geometry copy — **checked 1 Sept, no
longer exists**; R10's saved-positions rebuild removed all client-side
counts/degree math, so that half of the finding is stale and only
`ANGLE_STEP` is real work here.

**Ordering constraint: must land before R12.** Snapping changes what a valid
target *is* — a snapped value can cross R12's soft-limit confirmation
threshold, so R12 has to be built knowing this behavior exists, not the other
way round.

**Acceptance:** any typed angle is accepted (within the travel window); the
UI shows the requested angle, the snapped target, and the delta; the client
holds no copy of the step size.

**Related:** D21, D32 (the decision this refines, not reverts).

---

### R12 — Extended travel: soft limit ±90°, hard limit ±95°, confirmed in between
**Status:** open · **Raised by:** the operator, rig hand-testing 1 September
2026 · decided with the operator: hard limit is **95°**, not 93°

For a special occasion the operator has no way past the current ±90° window,
and no way to be deliberate about going past it. New three-state model:

- **Soft limit ±90.0°** — normal operating window. Behaves exactly as today,
  no prompt.
- **Between soft and hard** — accepted only after an explicit on-screen
  confirmation, reusing the existing `confirmDlg` modal (`index.html`,
  already used for calibrate and remove; `app.js:219-243`).
- **Hard limit ±95.0°** — absolute. Never confirmable, refused the way
  out-of-travel is refused today.

"Soft limit" and "hard limit" go into `CONTEXT.md`'s glossary and both values
into config, so the terms mean one thing each across code, UI copy and docs.

**Contradicts ADR-0003 — surfaced, not silently overridden.** ADR-0003 says
widening the window is "two numbers in `.env`, not a code change" — that
covers *one* window. This is a layered limit, and ADR-0003's "targets
outside the window are refused, never clamped" needs a third state.
**ADR-0012** records the soft/hard model and amends ADR-0003 by reference,
rather than editing it in place.

**R11 must land first** — see its ordering constraint above.

**Twin-path.** The travel limit is asserted in four places: `MoveRequest`'s
Pydantic bounds, frozen at import time rather than reading live settings
(`schemas/servo.py:10` vs. `get_settings()` — Session 14 `/twin-review`,
verified by clearing the cache and getting a value the schema would accept
but the service would reject); `MotionService._validate_reachable`; the
client's hardcoded `ANGLE_MIN`/`ANGLE_MAX` (`app.js:749-753`, same review,
diverges from the live `output_min_deg`/`output_max_deg` this file already
reads elsewhere for the position bar); and firmware's
`IsCountReachable`/`configure_range`. Three of the four do not yet know about
a middle state. **The firmware limit stays a hard backstop and is not
widened** — the soft/hard band is a policy layer above it, not a change to
what the hardware will accept.

**Acceptance:** 89.9° moves silently; 92° prompts for confirmation; 96° is
refused; declining the prompt issues no move; a value snapped by R11 into the
confirmation band still prompts.

**Assumed until the real loaded rig:** that ±95° is mechanically safe under
load — this work proves the software gate, not the mechanism's tolerance.

**Related:** ADR-0003, ADR-0012 (new), R11 (ordering).

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

**Update, 30 August 2026 (Session 17 Software Soak):** Fully measured across 5 structured runs on bare bench:
- **1 operator (Run 1, 10 min)**: 129 requests, 1,258 SSE frames, 0 D4 stalls, 0 failed reads.
- **3 operators (Run 2, 10 min, nominal remote target)**: 120 requests, **0 failures (100% success)**, 3,744 SSE frames, 0 stalls.
- **4 operators (Run 4, 10 min, boundary probe)**: 121 requests, **0 failures (100% success)**, 4,974 SSE frames. Proved the 4-operator boundary: 4 persistent SSE sockets leave 2 slots for actions, causing stream jitter during 45s binary exports, but queuing cleanly with 0 dropped actions.
- **3 remote + 1 local USB-C (Run 3, 38.4 min sustained)**: 754 requests, **0 transport failures (100% delivery)**, 15,005 SSE frames delivered, 0 D4 stalls, 0 MCU errors.
- **Q9 Formally Proven**: Local ADB forward (`127.0.0.1:8001`) communicates directly with Linux Uvicorn, bypassing the W5500 completely and consuming 0 relay sockets.
- **Capacity Law Established**: Nominal sweet spot is 3 remote operators (leaving 3 slots for REST). Boundary is 4 operators (2 slots left). Theoretical edge is 5 operators (1 slot left). Hard lockout at 6 operators (0 slots left).
- **Status**: Software capacity target (3 remote + 1 local) is **MET and verified on the bench**. Final sign-off under mechanical load scheduled for Rig Day (`../RIG_TESTING_PROTOCOL.md`).

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

