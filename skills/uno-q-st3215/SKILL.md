---
name: uno-q-st3215
description: Hardware expertise for the Arduino UNO Q (Qualcomm MPU + STM32 MCU over Zephyr, Bridge RPC) driving Waveshare ST3215 serial-bus servos, including the Ethernet-shield relay. Use when working on firmware, the MCU/Linux boundary, servo positioning or calibration on this board.
---

# Arduino UNO Q + Waveshare ST3215

Bench-verified hardware knowledge. Every number here was measured on real
hardware, not read from a datasheet.

**Read this before writing code for this board.** Generic Arduino knowledge is
actively wrong on the UNO Q in ways that compile cleanly and fail at runtime.

---

## 1. This is not a normal Arduino

The UNO Q is a **dual-brain board**:

- **Qualcomm Dragonwing QRB2210** running Debian Linux — the "Linux side" or MPU.
  Python, FastAPI, anything Linux.
- **STMicroelectronics STM32U585** (Cortex-M33) running **Zephyr** — the "MCU
  side". This is where sketches run.

Consequences that break normal assumptions:

- **The Arduino core is precompiled Zephyr firmware. A sketch is loaded as a
  relocatable ELF via LLEXT.** "Uploading a sketch" is not flashing a chip.
  Advice built around `avrdude`, bootloaders or classic `arduino-cli upload`
  flows does not transfer.
- **The two sides talk over the Bridge**, an RPC channel. Not serial, not I2C.
- **Pin the core version.** `arduino:zephyr` **0.56.0 or newer** — it adds
  `Serial3` and the UNO Q main-thread-priority fix. Board Manager does not exist
  on an air-gapped machine, so the target must already have the version you built
  against. This is the most likely cause of "it worked on my laptop".
- **App Lab** is the IDE. `app.yaml` at the project root is required by it.

### Sketch layout

Arduino compiles `src/` **recursively** and does **no preprocessing** on
`.cpp`/`.h` files — only `.ino` files get concatenated and auto-prototyped. So:

- Put real logic in `src/` as ordinary C++. Keep the `.ino` to a few lines.
- **`.h` files in a sketch are not auto-included.** Every file declares its own
  includes.
- Anything under `tests/` is *not* compiled into the main sketch — only `src/` is.

---

## 2. The ST3215 servo

Use the **SMS_STS** protocol class. **Never SCSCL** — wrong protocol family for
this servo, and its register map genuinely differs (e.g. mode sits at offset
19 in the SC map, 33 in the STS map — the same register number means a
different thing in each).

### Register map (the ones that matter)

| Reg | Name | Notes |
|---|---|---|
| `0x10` | max torque | 2 bytes |
| `0x12` | phase | **BIT4 = 1 enables multi-turn** |
| `0x15`-`0x17` | position P/D/I | 1 byte each. Factory default `P=32 D=32 I=0`. **Bench-verified 2 September 2026: lowering `P` was the single most consistent fix found for load-induced settling oscillation, out of everything tried** — matches published community guidance for this exact servo family (LeRobot/Hugging Face: "lowering the P-gain is the most critical fix for stable, smooth motion" on Feetech STS3215). This project kept `P=24` (down from factory `32`). `D`/`I` were never touched. |
| `0x18` | min start force | 2 bytes, 0..1000 — same ceiling as torque limit (`0x30`). Guarantees a minimum push on every corrective move, even when the calculated correction is too small to break static friction on its own; at the factory default of `0` a small residual error can sit uncorrected forever (the servo "knows" it's off but never applies enough force to move). Bench-tuned to **150** on this project — held up well unloaded and under one steady hand-drag load test, but **do not treat it as a settled, monotonic tuning knob**: a fine sweep (85/90/95/98/100/150/200) under load found the response non-monotonic, with no clean threshold. See the oscillation note below. |
| `0x1A`/`0x1B` | CW/CCW dead zone | 1 byte each, 0..32 counts — unit is 1 raw servo-shaft encoder step (not degrees; convert via the system's own counts-per-degree). Factory default `1`, the register's own floor (cannot go smaller, it is an unsigned integer). **Interacts with `0x18` and with load**: a wider dead zone reduces (but on this project's bench testing did not reliably eliminate) load-induced settling oscillation, at a real, roughly linear accuracy cost (each step of dead zone ≈ one more encoder count of possible final-position slop, per side). Dead zone `2/2` cleaned up ~80% of trials at this project's worst-behaved point under a proxy load; `1/1` did not reliably help under load at all, despite fixing an *unloaded* extremes-only oscillation earlier in the same project (see below) — **do not assume an unloaded dead-zone fix transfers to a loaded one.** |
| `0x22` | protect torque | |
| `0x24` | overload torque | |
| `0x28` | torque switch | **0 disables drive torque, 1 restores it, 128 sets current position to 2048.** Confirmed against Waveshare's own register map, not inferred. Torque off keeps the electronics powered (sensors keep answering) — this is how you cut motor power without losing telemetry. **These three values share ONE register with a mode-select semantic**: write it through an SDK helper (`EnableTorque(id, 0/1)`), never a raw `WriteByte` with a variable, or a stray 128 silently re-centres the servo and destroys calibration. |
| `0x2E` | goal speed | 2 bytes, counts/s. Bench-confirmed 1 September 2026 (see Bench-verified behaviour, below): the documented conversion (1 unit ≈ 1 encoder count/s, scaled by the belt ratio) is accurate once measured off `0x3A` directly — an earlier wall-clock-based measurement (elapsed time over distance) read as "1.5-2.3x faster than commanded" purely from acceleration ramp-up and fine-approach's two-leg travel, not a register discrepancy. |
| `0x30` | torque limit | 2 bytes, 0..1000 |
| `0x37` | **lock** | **EEPROM write lock** (0 unlocked, 1 locked). This is *not* an operator safety lock — never conflate them. EEPROM writes need the unlock ritual. |
| `0x3A` | present speed | 2 bytes, sign-magnitude — same wire format as present position, decode explicitly (below). The only reliable way to measure real servo speed: elapsed-time/distance is diluted by acceleration ramp-up and, if fine approach is active, its own two-leg structure. |
| `0x3C` | present load | **PWM duty, NOT torque.** Do not report it as torque. |
| `0x41` | status | fault bits, below |

### A settling oscillation, unloaded, at travel extremes — real, not a tuning artifact

At some positions — bench-confirmed at the far ends of this project's travel
window, one servo turn's worth of extension from centre, **unloaded** — a
nonzero minimum start force (`0x18`) combined with zero dead zone
(`0x1A`/`0x1B`) can produce a **sustained limit-cycle oscillation** that
never damps on its own: the shaft trembles between two positions about one
encoder count apart, indefinitely, stopping only when a new command
interrupts it. This is a textbook stiction-driven limit cycle (a correction
too weak to break static friction, force builds, it slips and overshoots,
repeat) and matches this exact servo's own documented behaviour
independently: Robo9's STS3215 bench testing reports "the servo exhibits
jitter or oscillation when the arm is extended." **Watch the shaft directly
(not just a single position poll) when tuning `0x18` upward** — a single
reading can land mid-oscillation and look like a real, stable result. Two
independent fixes work *for this unloaded, extremes-only case*: restore the
factory dead zone (`1`, coarser accuracy) or raise `0x18` further.

### The same symptom, under load, is a different and harder problem

**Do not assume the fix above transfers to a loaded servo.** Bench-tested 2
September 2026 with a hand-applied and improvised-weight proxy load (not a
rigid mount): the same low-amplitude settling oscillation reappeared, but
**worst at a mid-travel position, not the extremes** — the opposite of
where the unloaded case predicts trouble. Neither raising `0x18` (swept
85-200, non-monotonic response) nor a wider dead zone (`2/2` helped most of
the time but not reliably) fully resolved it; reducing the anti-backlash
overshoot magnitude did not help either. What did help most, consistently:
**lowering `P`** (see the register table above).

**Working hypothesis, evidence-based but not confirmed: this looks like
load-coupled mechanical resonance, not simple stiction.** Signs pointing
that way: non-monotonic response to every register tried; no consistent
effect from overshoot magnitude (stiction limit cycles care about the
final correction's force, not how far the initial swing was); severity
tied to a specific joint angle unrelated to travel-limit proximity (a
belt-driven arm's effective inertia and leverage shift with position, which
would shift a resonant frequency but wouldn't obviously affect Coulomb
friction this way); roughly half of identical repeats at fixed settings
failing and half not (consistent with sensitivity to starting phase, not a
deterministic threshold); and direct hand contact reliably damping it — the
textbook resonance remedy. If this holds, **resonant frequency is a
property of the attached mass and mounting stiffness**, so a fix tuned on
one mechanical configuration (a bench proxy, a different arm) has no
particular reason to transfer to another. Verify under the real load,
mounted as it will actually be used, not a hand-held stand-in.

### The firmware's own settle-completion event can miss this entirely

`servo.move.fine_approach`'s `wait_elapsed_s` field (this project's Python
layer, not a servo register) reports how long its own settle *check*
took to clear — it does **not** mean the shaft was actually still. Measured
directly: one move reported `wait_elapsed_s=3.5s` while continuous raw
position polling (not the "moving" flag, which also stayed `false`
throughout) showed 19 direction reversals still ongoing 14+ seconds later.
**Never judge settle quality from an elapsed-time or "moving" flag alone —
poll raw position continuously through the whole window and look for
reversals, or watch the shaft directly.**

**Position polling alone can still miss it — check current too.** The servo
can correct an error smaller than its own encoder resolution (one count,
0.06° at 4096 counts/turn on this project's belt ratio) without the
reported position ever crossing a count boundary, so a reversal counter
built on position alone can score zero reversals while the servo is
genuinely still working. Measured directly: one configuration held
`reversals=0` across three repeats at a target angle while mean current sat
at 0.08A against 0.00A for the same angle and target under a different
configuration — current was the only signal that showed anything was
happening. **A quiet position trace is not sufficient evidence of a quiet
servo — check current in the same window before calling a settle clean.**

### Status register 0x41 — six faults

Confirmed from the official memory table:

```
bit0 voltage   bit1 sensor   bit2 temperature
bit3 current   bit4 angle    bit5 overload
```

**bit4 (angle) is the one that gets missed.** If a status decoder handles five
faults, it is wrong.

### Sign-magnitude wire format

STS position fields are **sign-magnitude, not two's complement**. Decoding them
as two's complement produces the classic symptom: **a small negative position
reads as ~32700**. Decode explicitly.

### Bench-verified behaviour

- **4096 counts per servo turn.**
- **Direction +1** — commanding +400 raises the reported position.
- **Deadband 0.** Measured landing error: 0→0.06°, 1→0.10°, 8→0.52°, 32→1.98°.
  Larger deadbands cost accuracy for nothing.
- **Speed saturates near 1100 counts/s** (~66°/s output) whatever you command.
- **Below that ceiling, `0x2E` means what it says — measured off `0x3A`
  directly.** Commanding 9-15 output °/s (~150-250 counts/s after the belt
  ratio) landed within a few percent of the documented conversion. At
  higher commanded speeds over a *short* travel distance, measured speed
  can fall well short of the commanded value — plain acceleration ramp-up
  (not enough distance to reach cruise speed before decelerating), not a
  register problem. Judge "is it going the right speed" from `0x3A` over a
  long enough move, never from elapsed-time-over-distance on a short one.
- **Acceleration has no measurable effect above ~50.**
- **Serial1 @ 1 Mbps is reliable** — 200/200 reads, 220 µs each.
- **Restoring torque after cutting it: re-command the present position
  BEFORE re-enabling, not after.** Torque can be written to while the
  goal register is written too, so writing the current position as the
  goal while still off leaves nothing for the servo to correct the
  instant it re-engages — otherwise it may snap toward a stale goal set
  before torque was cut, or toward wherever the shaft was hand-turned to
  while free. **Designed, not yet bench-verified** — the dev rig this
  was built against doesn't have the belt mounted; confirm on real
  hardware, with the arm deliberately displaced while torque is off,
  before trusting it. Also unconfirmed for this configuration: whether
  multi-turn absolute position tracking survives the shaft being turned
  by hand while torque is off.

---

## 3. Geometry — and the one law that matters

This project drives the servo through a **44:30 belt reduction**. Angles at the
mechanism ("output degrees") are not servo degrees.

```
1 count       = (360/4096) × (30/44) = 0.0599  ≈ 0.06 output degrees
180° output   = 264° servo           = 3004 counts   → fits in ONE servo turn
```

Because ±90° fits inside one turn, **multi-turn is off** but implemented and
bench-proven (angle limits 0, angle-resolution amplification, phase BIT4).
Widening the window is two config numbers, not a code change.

### The law

> **The datum must sit mid-travel (~2048). A datum at count 0 strands the entire
> negative half of the window.**

The servo is configured min angle limit 0, max 4095. **It clamps below 0
silently and still acknowledges the command.** So a bad datum produces: commanded
−45°, servo stops at 0, API reports success. Nothing detects it unless you check
the count range yourself.

Corollaries:

- **A failed read must never become a position.** If a read returns invalid, it
  must not be stored as a datum, a zero reference, or anything else. A failed
  read that reports 0 becomes a datum of 0 becomes half the travel unreachable.
- **Refuse unreachable targets; never clamp them.** Clamping hides the error.
- **No modulus-360 wrapping.** In a multi-turn system −25° and 335° are
  different absolute targets a full output revolution apart, and wrapping hides
  turn-count errors.
- **Default the baseline to the centre of travel**, not 0, when no datum exists.

---

## 4. The Ethernet-shield relay

On this board the Linux side may have **no network of its own** (production
boards can have the WiFi/BT chip desoldered). The Ethernet shield sits on the
**MCU**, and a relay pumps bytes across the Bridge to Linux.

### SpiRemap — apply it twice

SPI2 sits on D11–D13, but the Ethernet Shield takes SPI from the **ICSP header**
(PD1/PC2/PC3). So the SPI pins must be remapped —

> **after `SPI.begin()` AND AGAIN after `Ethernet.init()`.**

`Ethernet.init()` re-initialises the SPI pins and undoes the first remap. Miss
the second call and the W5500 reports "no hardware".

Ethernet 2.0.2 also needs an `IPAddress((uint32_t)0)` cast patch on this core.

### Seven relay rules — every one of these was a real bug

1. **Adopt connections with `accept()`, never `available()`.** `accept()` hands
   over a connection exactly once, transferring ownership. `available()` returns
   whichever client has unread data — *the same client again on every call*. An
   accept loop built on `available()` adopts one connection into several slots,
   splitting one HTTP request across several sockets. Symptom: first exchange or
   two work, then everything is corrupt.
2. **Detect disconnects BEFORE accepting, on the edge.** Order inside the poll:
   disconnect detection → accept → pump. Accept-first lets a just-dropped slot be
   handed to a new connection before `net_close` was sent, and Linux then feeds
   the new connection's bytes into the old socket. Symptom: uvicorn logging
   "Invalid HTTP request received" during connection churn. Track `was_up[slot]`
   and act on the transition — testing `!connected()` every pass emits `net_close`
   continuously for merely-idle slots.
3. **`loop()` must yield.** The poll returns immediately when idle, so `loop()`
   spins at full speed and starves the Bridge RPC thread. A `servo_read` then
   misses its 10 s deadline and the late reply arrives as **"Response for unknown
   msgid"**. A `delay(1)` at the end of the tick prevents it and costs nothing.
4. **One bulk read per slot per pass.** `client.read(buffer, sizeof(buffer))`,
   never byte-at-a-time. Never block or `delay()` inside the pump — the same
   `loop()` also drives the servo bus. (The UART RX ring is 64 bytes; drain with
   `while`, not `if`.)
5. **Chunk size is one number in two places.** `kRelayChunkBytes` on the MCU and
   `relay_chunk_bytes` in the backend settings must match. It is bytes per Bridge
   message — halving it doubles the Bridge round trips for identical payload.
   **The working relay used 256.**
6. **Serialise Bridge calls.** A sampler thread and HTTP threads calling the
   Bridge concurrently interleave message ids and produce "Response for unknown
   msgid" plus 10 s timeouts. Use a lock.
7. **Serialise the W5500 itself, across threads.** Rules 1–6 govern ordering
   *within* the poll; this is the one they miss. `Poll()` runs on the loop
   thread while `net_tx` / `net_shutdown` run on the **Bridge** thread, and
   there are six sockets but **one chip on one SPI bus**. Two threads
   mid-transaction splice their messages: the chip answers nonsense or waits
   for a message that never finishes, the Bridge thread blocks behind it, and
   `servo_read` dies at 10 s. Use a **mutex** (one resource, not a count —
   and on Zephyr `k_mutex` gives priority inheritance). Three traps: never
   hold it across a callback that notifies Linux (the Bridge thread may be
   waiting for it inside `net_tx` — instant deadlock); bound the Bridge-side
   wait with `K_MSEC` so a busy chip fails a write instead of hanging the RPC
   thread; and cover whole operations, or you only narrow the window.
   **`provide_safe` does not do this for you** — it means "called from the
   Bridge thread while `loop()` may be in the relay", i.e. *you* are now
   responsible. The name reads like a guarantee and is not one.

Console: `Serial` works and is proven over USB. `Monitor` (the Bridge's console
facade) is an option, not a requirement — its only advantage is reaching App Lab
over WiFi.

---

## 5. The Bridge contract

Every function crossing the MCU/Linux boundary is declared **twice** — once in
C++, once in Python — and **nothing makes the compiler or interpreter compare
them**. A wrong argument count compiles and imports cleanly on both sides, then
fails at runtime as **silence**, not an error.

```
Linux -> MCU   servo_read, servo_move, servo_stop, servo_set_deadband,
               servo_configure_range, servo_set_torque, servo_read_torque,
               servo_read_tuning, servo_write_tuning, servo_read_speed,
               get_status, net_tx(slot,data), net_shutdown(slot)
               (CentreHere() is deliberately NOT exposed here - see
               BridgeApi.h's own comment: calibration is a software
               relabel recorded in SQLite, and a servo-held position
               offset would be a second, competing source of truth)
MCU -> Linux   net_open(slot, client_ip), net_rx(slot, data), net_close(slot)
```

- Payloads are **plain CSV strings** — readable verbatim in a log, which is the
  whole point on a boundary that fails silently.
- Servo command payload shapes:
  ```
  servo_read              ""                        -> snapshot CSV
  servo_move              "counts,speed,accel"      -> "ok" | "err"
  servo_stop               ""                        -> "ok" | "err"
  servo_set_deadband       "counts"                  -> "ok" | "err"
  servo_configure_range    "multiturn,amplification" -> "ok" | "err"
  servo_set_torque         "enabled"                 -> "ok" | "err"
  servo_read_torque        (no payload)              -> "0" | "1" | "err"
  servo_read_tuning        (no payload)              -> "valid,p,d,i,msf,cw,ccw"
  servo_write_tuning       "p,d,i,msf,cw,ccw"        -> "ok" | "err"
                           (-1 per field means leave that register alone)
  servo_read_speed         (no payload)              -> signed counts/s | "err"
  get_status               (no payload)              -> "ready" | "no-servo"
  ```
  `get_status` takes no parameter because Python calls it with no payload at
  all (the health check) — a `String` parameter on that handler fails to bind.
- Snapshot fields:
  `valid,counts,moving,temp_c,volt_v,curr_a,torque_kgcm,load,status_bits`
- **Field 0 is `valid`.** Never discard it. Discarding it is how a failed read
  became a calibration datum of 0.
- **`valid` governs the WHOLE snapshot, not just `counts`.** A failed read
  yields a zeroed struct, so `temp_c`, `volt_v`, `curr_a` and `torque_kgcm` all
  arrive as `0.0` and `moving` and every status bit arrive as `false`. Each one
  is a plausible measurement: 0.0 V reads as *lost power*, and "not moving, no
  faults" reads as *sitting still and healthy*. Guarding `counts` alone leaves
  eleven fields lying. **Decide what an invalid snapshot means once, at the
  boundary, and apply it to every field at the same time** — doing `counts`
  first and the rest later is how you get two defects out of one bug.
- Relay payloads are `MsgPack::bin_t<uint8_t>` — binary, must **not** be packed
  into a `String`.
- `net_tx` / `net_shutdown` are registered with `provide_safe`: they are called
  from the Bridge thread while `loop()` may be inside the relay.
- **Run the contract checker after touching either side.** It exits non-zero, so
  it suits a pre-commit hook.

---

## 6. Symptom → cause

| Symptom | Cause |
|---|---|
| Move to a negative angle stops at 0, reports success | Datum at/near count 0; servo clamps silently below 0 |
| Position reads ~32700 | Sign-magnitude decoded as two's complement |
| "Response for unknown msgid" / `servo_read` 10 s timeout | `loop()` not yielding, or concurrent unserialised Bridge calls |
| W5500 "no hardware" | SpiRemap not applied the second time, after `Ethernet.init()` |
| First exchange works, then corruption | Relay using `available()` instead of `accept()` |
| Stalls of ~11 s, dropped sockets, first button press ignored | W5500 touched from the loop and Bridge threads with no mutex (rule 7) |
| A stored position of 0 or -1 that the servo never reported | A failed read used without checking the snapshot's `valid` flag |
| Commanded 90 deg, mechanism moved 212 deg | Two baselines: display and motion disagree on the no-datum default |
| `Invalid Library Reference: Xxx ()` at build | A library in `sketch.yaml` with no version |
| uvicorn "Invalid HTTP request received" during churn | Accepting before detecting disconnects |
| Bridge call silently does nothing | Argument-count mismatch across the boundary — run the contract checker |
| UI moves convincingly, servo never twitches | Running the simulated backend; `.env` missing on the board |
| Calibration captured a datum of 0 | A failed read was stored as a position — `valid` flag discarded |
| One fault never trips | Status decoder missing bit4 (angle) |
| A torque/move write always "succeeds" even when the servo never answers | Checked the SCServo library's write-return value (`EnableTorque`, `WritePosEx`) against `-1` — that sentinel is for this library's *read* calls only; writes return `Ack()`'s own convention, 0 fail / 1 success, never -1 |
| Shaft trembles between two positions near the far end of travel, never stops on its own | `0x18` (min start force) nonzero with `0x1A`/`0x1B` (dead zone) at 0 — a stiction-driven limit cycle, see §2's register-map note |
| A move looks 1.5-2x faster than commanded, measured by elapsed time | Measuring speed from wall-clock/distance instead of `0x3A` — acceleration ramp-up on a short move (or fine approach's own two-leg travel) inflates the apparent speed, `0x2E`'s own conversion is accurate |

---

## 7. Deployment traps

- **`adb push` never deletes.** It overwrites what it copies but leaves anything
  already on the board that is missing from the source. Renamed or deleted files
  linger and get picked up instead of the new ones. **Wipe the target directory
  first.**
- **Wiping also removes `.cache/.venv`**, so App Lab re-provisions Python on the
  next Run. To keep the venv, delete everything except it.
- **A missing `.env` is silent.** Without it the backend falls back to the
  simulator and the UI looks perfect while nothing moves. Verify which backend is
  live rather than assuming.
- **Check the Ethernet patch survived a rebuild.** `~/.arduino15/internal/` is a
  user-global library cache shared by every app; App Lab can re-fetch and drop
  the patch.

---

## 8. Working rules

- **Say what was tested versus assumed.** On this board, near-total coverage of
  the Linux side has repeatedly meant nothing — every serious defect lived in the
  relay and the controller, which the simulator does not exercise.
- **Port, don't re-derive.** The relay was once rewritten from scratch instead of
  ported, and the rewrite reintroduced problems the original had already solved.
  Read the working reference before rewriting.
- **Keep pure-logic classes header-only and Arduino-free** (angle maths,
  sign-magnitude, status decoding). That property is what makes host-native
  testing possible; breaking it silently costs the whole fast test tier.
- **A green host test suite says nothing about the hardware path.** Host tests
  cover maths. Only on-target tests cover whether the servo answers, whether
  configuration writes stick, whether a move lands, and whether stop holds.
