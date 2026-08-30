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

