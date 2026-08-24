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
192 Python tests, 100% line coverage of app/
164 native sketch checks, -Wall -Wextra -Wpedantic -Werror
Bridge contract checker: both sides agree
```

**It has now been run on real hardware, driving the real servo** (7 August 2026,
backlog T8). That run changed the picture more than any amount of reading could
have.

**Closed by it:** D1, D2, D9, and the cause of D4. **Opened by it:** D10, D11,
D12 — none of which anyone had thought to look for.

**The system is materially calmer but not yet stable.** What the run proved, in
numbers, before and after the W5500 fix:

| | before | after |
|---|---|---|
| Sampler stalls in the 10–12 s band | 3 | 0 |
| Longest sampler gap | 11.00 s | 2.00 s |
| Fabricated positions written to the database | 7 | 0 |
| Bridge timeouts logged (`servo.bridge.error`) | 3 | 0 |
| Fabricated positions logged as such | not recorded at all | 0 to record |

Coverage at 100% still means every line ran, not that every assumption was
questioned. It did not prevent the six defects in `AUDIT.md`, and it did not
prevent D9 — where the correct rule and its violation sat twelve lines apart in
one file, both covered, both green.

### The single most important open item

**D10 — the sampler threw once in seven minutes and the log cannot say why.**
`logger.exception` recorded the message without the exception or traceback.

It ranks first not because it is the biggest defect but because everything
remaining is measurement — the D4 soak, first paint, the chunk-size experiment,
the benchmarks that define "stable" — and an unexplained exception that destroys
its own evidence corrupts every measurement taken near it.

**Amended 8 August 2026.** That reasoning held while everything remaining *was*
measurement. It no longer is. Two things now outrank it:

- **D13, and the decision it needs.** "Press it twice" is the behaviour that
  will be remembered by the people deciding whether to procure this. It is
  measured, its cause is understood, and what is missing is a choice — which is
  why it is going to an ADR rather than to a fix.
- **R2 and R5** — the only two things scoped *in MVP* that do not exist yet.
  Defects have bounded effort because their causes are known; unbuilt features
  do not. They were absent from the ordering entirely until this date.

D10 keeps its place among the measurements, watched for on every board run. It
is no longer the first thing.

### The lesson worth carrying

Three of this project's defect families are now the same defect: **a rule applied
to one path and not to its twin.** `AUDIT.md`'s originals, D2's
`calibrate()`-but-not-`capture()`, and D9's two baselines. When fixing anything
here, the second question is always: *where is this rule's twin, and does it
know?*

## The cut line

**What ships, what slips, what does not go.** Set 8 August 2026. This is the
scope statement the project did not have — `BACKLOG.md` said what the work *is*,
in what order, and nothing said what happens when there is not time for all of
it. Scaling down is a decision to be taken deliberately, in this table, not by
running out of week.

Batch numbers refer to the ordering in `BACKLOG.md`.

### Must ship — no handover without these

| | Why it is non-negotiable |
|---|---|
| **D13 decided** (+ D14, D15) | "Press it twice" is what a procurement audience remembers. The decision needs an ADR |
| **D4 closed by a real soak** | A race that stopped reproducing has not been proved absent |
| **R1 answered** | The one capacity number anyone will ask for |
| **R2** motor isolation | Scoped in MVP explicitly *so MVP testing exercises it* |
| **R5** metrics export, **torque included** | Without it there is nothing to judge, and R6 cannot be written |
| **D22** export over any range | The benchmark is a multi-day unattended run at the receiving team's site; a 24-hour button cannot retrieve it |
| **R6** "stable" as numbers | The delivery is judged against it |
| **D8** made impossible to get wrong | A silent fallback to the simulator at handover is the worst failure available |
| **D16** | The operator must not be shown 0.00 V as a measurement |
| **T10** the recovery runbook | The receiving team runs it unattended for days. They must know what to do when it misbehaves, and the site is three hours away |
| **T11** the operations manual | Nothing in the repo tells anyone how to *operate* this. Every document is written for whoever is building it |
| **Docs true** | Cheap, and the project's own standard |

### Should ship — cut only under real pressure, and say so out loud

**D3** (MCU logging — strong case: two diagnostics exist and cannot be read),
**D6** (first paint measured), **T3** (on-target run), **T5** (diagrams),
**D7** (operator screen — *blocked on Q1*), **D12**, **D17**, **D18**, **T9**
(storage confirmed over hours), **D5**.

Cutting any of these means handing over something that works but cannot be
explained, measured or diagnosed by the people receiving it. That is a real cost
— it is simply not a reason to miss a date.

### Will not ship — decided, not forgotten

**T1, T6, T7** — the mechanical conventions pass. The MVP was written "dirty" on
purpose. It is the right work and it is invisible to the people judging this;
if it collides with the date, it loses. **R3, R4, R8, D19, D20** — post-MVP or
pending an answer, by decision.

### The branch that is not ours to choose

**T2** (air-gapped bundle) depends on adapter delivery — see R7 and Q7.

- **Adapters arrive in time** → T2 moves to *must ship*, and the system is boxed
  into the secure network for handover.
- **They do not** → ship on the single coloured adapter, and **state plainly in
  the handover that the air-gapped path has never been exercised.** It must not
  be discovered by the receiving team.

**Assume the second until told otherwise** (Q7).

### What this line assumes

That there is a date. Nothing in this repository states one — see Q8. Until it
is answered, this table is a priority ordering rather than a schedule.

---

## Environment right now

- Development runs on a **WiFi-mounted board**, not an air-gapped one. There is
  one servo bus adapter and it sits on a "coloured" internet-facing network that
  cannot be introduced to the secure network.
- **The air-gapped path has therefore never been exercised** (backlog T2, R7).
- More adapters are expected within the month. If they arrive before the MVP is
  finished, the system gets boxed into the secure network for handover; if not,
  it ships with the single coloured adapter.
- **This version now runs on the board.** `python/.env` exists, the backend logs
  `backend=hardware` at boot, and the database is populated. The app is started
  headlessly with `arduino-app-cli app start user:servo_mvp`, which is also how
  App Lab starts it — App Lab opens its Python and serial monitors when it does.
- **The database is `ArduinoApps/servo_mvp/servo_mvp.db`, inside the sshfs
  mount.** `.env.board` sets a relative `DB_PATH` on purpose, because the Python
  side runs in a container where `HOME` is `/home/app`. Earlier docs claimed it
  sat outside the mount and needed `adb`; that is true only of the default.
- The active datum is count 2049, captured mid-travel by the operator, and ±90
  is reachable in both directions from it.

## Hardware facts, all bench-verified

- 4096 counts per servo turn, 44:30 belt → **0.06° per count** at the output
  (true value **0.059925**; 0.06 is a deliberate rounding, see the audit below)
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
- **The W5500 is one chip on one SPI bus, reached from two threads.** `Poll()`
  runs on the loop thread, `net_tx` / `net_shutdown` on the Bridge thread. They
  must be serialised — `RELAY_NOTES.md` rule 7. Six sockets are not six
  resources.
- Sketch libraries need explicit versions in `sketch.yaml`; an unversioned
  reference fails with `Invalid Library Reference`. The **platform** is still
  unpinned and needs `arduino:zephyr` ≥ 0.56.0 (backlog T2)

## Gear-ratio audit — 8 August 2026

**All three sides agree on the ratio.** Checked because angle maths crossing two
processors and a browser is exactly where a twin-path defect would hide, and
because D9 was a baseline disagreement of this shape.

| | counts/turn | belt | counts per output degree |
|---|---|---|---|
| Python | `config.py:94` = 4096 | `config.py:95` = 44.0/30.0 | `servo_state.py:33,120,151` → **16.6874** |
| C++ | `AngleMath.h:27` | `AngleMath.h:23` = 44/30 | `AngleMath.h:53` → **16.6874** |
| Browser | `app.js:17` `4096 * (44/30) / 360` | — | **16.6874** |

Both derived checks hold: ±90° = **3004 counts** total span, and one count =
**0.059925** output degrees. No side hardcodes a pre-computed constant — each
derives from `counts_per_turn` and the belt ratio, so retuning either propagates.

**Two things the audit found, both recorded:**

- **`output_step_deg = 0.06` is a rounding of 0.059925**, used consistently by
  both sides (`config.py:106`, `app.js:27`) and documented at `config.py:103`.
  It means a commanded step is 1.0012 counts, so roughly one nudge in 800 moves
  two counts instead of one — under 0.12° across the full ±90 range.
  **The operator is aware of the rounding and has not decided whether to change
  it (8 August 2026).** Recommendation: leave it. 0.06 is a number an operator
  can read and type; 0.059925 is not, and the error it buys is a tenth of a
  degree across the whole travel window on a mechanism whose datum was captured
  by hand. Revisit only if a requirement appears that needs count-exact
  addressing from the UI — and if it does, the fix is to command *counts* rather
  than to print more decimals.
- **The UI tells the operator the step is 0.1°** while config and backend both
  enforce 0.06 — filed as **D21**. The ratio is right everywhere; the sentence
  describing it to the operator is not.

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
  project has lived there. The native tests cover pure maths only. The W5500
  mutex (backlog D4) was verified by compiling, running and measuring on the
  board — **not by a single test**, because no test in this repository can
  reach it.
- **`sketch/tests/OnTarget/` has never been uploaded** (backlog T3).
- **The C++ side does not log** anything during operation (backlog D3), so when
  the MCU misbehaves there is no way to see what it did.
- **"Stable" is not yet defined by numbers.** It gets defined by measurement —
  backlog R5 and R6.
