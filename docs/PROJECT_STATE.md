# Project state

Where the project is right now. Updated as reality changes.

**This file does not list open work** — that is `BACKLOG.md`. It does not explain
decisions — that is `docs/adr/`. It does not define terms — that is `CONTEXT.md`.

---

## What this is

Arduino UNO Q + Waveshare ST3215 serial-bus servo. A FastAPI backend and an
LCARS-themed web UI served from the board: operators open
`http://<board-ip>:8000`, several at once, nothing installed on their machines.

The network path runs through the MCU, not the Linux side — production boards
have the WiFi/Bluetooth chip desoldered (ADR-0001).

## Where it is heading

A **delivered MVP**. Other teams will judge it and decide whether to procure a
full project. So the bar is not "feature complete" — it is **stable, benchmarkable
and conventionally built**.

Post-MVP, additional servos will be added as mechanical restraint (backlog R4).

## Status

Everything exists — backend, UI, sketch, tests — and all three verification
commands pass:

```
186 Python tests, 100% line coverage of app/
164 native sketch checks, -Wall -Wextra -Wpedantic -Werror
Bridge contract checker: both sides agree
```

**But the system is not stable.** Eight open defects are recorded in
`BACKLOG.md`, several observed on real hardware. Coverage at 100% means every
line ran, not that every assumption was questioned — it did not prevent any of
the six defects in `AUDIT.md`, and it is not preventing the current eight.

### The single most important open item

**D2 — `capture()` can store a failed read as position 0.** It is the linchpin,
not just one bug among eight.

Moves are deliberately permitted while the position reference is unverified
(ADR-0007), because the site is roughly three hours away and refusing movement
would turn a recoverable signal loss into a site visit. That makes the travel
window the only guard against driving into a silent clamp — and **the travel
window is computed from the datum.** A bad datum displaces the guard by exactly
the error it exists to catch.

Fix D2 first. D1 is its symptom.

## Environment right now

- Development runs on a **WiFi-mounted board**, not an air-gapped one. There is
  one servo bus adapter and it sits on a "coloured" internet-facing network that
  cannot be introduced to the secure network.
- **The air-gapped path has therefore never been exercised** (backlog T2, R7).
- More adapters are expected within the month. If they arrive before the MVP is
  finished, the system gets boxed into the secure network for handover; if not,
  it ships with the single coloured adapter.
- This version has not yet been run on the board: there is no `.env` and no
  database (backlog D8).

## Hardware facts, all bench-verified

- 4096 counts per servo turn, 44:30 belt → **0.06° per count** at the output
- ±90° = **3004 counts**; the datum must sit **mid-travel (~2048)**
- **A datum at count 0 makes the negative half unreachable** — the servo clamps
  below 0 silently and still reports success
- direction **+1**; deadband **0**; speed saturates ~**1100 counts/s**;
  acceleration has no effect above ~**50**
- Serial1 @ 1 Mbps is reliable (200/200 reads, 220 µs)
- Ethernet shield needs **SpiRemap** — SPI2 sits on D11–D13 but the shield takes
  SPI from ICSP (PD1/PC2/PC3). Apply it after `SPI.begin()` **and again** after
  `Ethernet.init()`
- Ethernet 2.0.2 needs an `IPAddress((uint32_t)0)` cast patch on this core
- `kMaxRelaySockets = 6` is the **only** connection limit in the system

## Decisions on record

Seven ADRs in `docs/adr/`. Do not re-litigate these without reopening the ADR:

| ADR | Decision |
|---|---|
| 0001 | Network path runs through the MCU |
| 0002 | Plain HTML/CSS/JS — no framework, no build step |
| 0003 | Travel window ±90 output degrees; multi-turn off but configurable |
| 0004 | Repository abstraction with a simulated backend |
| 0005 | Develop as if already air-gapped |
| 0006 | Bridge payloads are CSV strings |
| 0007 | Moves are permitted while position is unverified |

## Known gaps, stated honestly

- **The relay and controller have no automated coverage.** Every bug in this
  project has lived there. The native tests cover pure maths only.
- **`sketch/tests/OnTarget/` has never been uploaded** (backlog T3).
- **The C++ side does not log** anything during operation (backlog D3), so when
  the MCU misbehaves there is no way to see what it did.
- **"Stable" is not yet defined by numbers.** It gets defined by measurement —
  backlog R5 and R6.
