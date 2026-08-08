# Sketch — the MCU side

Thin `.ino`, real C++ underneath.

```
sketch/
├── sketch.ino          setup() / loop() only
├── sketch.yaml         board profile + library pins
├── src/                every line of real logic
└── tests/
    ├── native/         host tests, no board needed
    └── OnTarget/       on-board smoke test (its own sketch)
```

## Why the code lives in `src/`

Arduino compiles `src/` **recursively**, and — the part that matters — it does
**no preprocessing** on `.cpp`/`.h` files. Only `.ino` files get concatenated
and have prototypes generated for them. So putting the logic in `src/` gives
ordinary, reviewable C++: real headers, real namespaces, real classes, no
compiler magic. `sketch.ino` is four lines that hand off to `App`.

`.h` files in a sketch are **not** auto-included, which is why every file
declares its own includes.

## Design

| Class | Responsibility |
|---|---|
| `AngleConverter` | counts ⟷ output degrees, direction sign |
| `SignMagnitude` | STS wire-format decode (the "reads 32700" bug) |
| `ServoFaults` | status register 0x41 → six named flags |
| `ServoBus` | the only place that touches the serial bus: retries, EEPROM unlock ritual |
| `ServoController` | the operations the backend asks for |
| `SpiRemap` | routes SPI2 to the ICSP header so the shield is visible |
| `NetworkRelay` | shield ⟷ Linux byte pump, callback seam, no Bridge dependency |
| `BridgeApi` | the contract with Python; the only file that knows payload formats |
| `App` | composition root — builds the graph once, drives it |

The first three are **header-only and Arduino-free on purpose**: that is what
makes them testable on a development machine.

## Testing

Two tiers, because they catch different things.

**1. Host-native — run these constantly.** No board, no libraries, milliseconds.

```bash
cd tests/native
make
```

The pure-logic classes have no Arduino dependency, so they compile with plain
`g++`. The harness (`TinyTest.h`) is ~60 lines and deliberately *not* AUnit or
GoogleTest: every dependency is a liability on an air-gapped machine.

Covers: sign-magnitude decoding, angle round-trips within one count, the ±90°
window fitting in one servo turn, direction mirroring, speed conversion, and
every status bit.

**2. On-target — run when hardware changes.** Open `tests/OnTarget/` as a
sketch and upload it. It covers only what a host cannot: that the servo
answers, that configuration writes stick, that a commanded move lands, and
that stop holds. Serial Monitor at 115200 over USB; it runs once and prints a
tally.

That folder is not compiled into the main sketch — Arduino's recursive
compilation is limited to `src/`.

## Two things that were learned the hard way

**Apply `SpiRemap` twice.** The UNO Q routes SPI2 to D11–D13, but the Ethernet
Shield takes SPI from the ICSP header (PD1/PC2/PC3). `Ethernet.init()`
re-initialises the SPI pins and undoes the first remap, so it must be applied
again afterwards or the W5500 reports "no hardware".

**Drain with `while`, never `if`.** The UART RX ring is 64 bytes and the
socket buffers are small; one byte per `loop()` is not fast enough.

## The contract with Python

Plain comma-separated payloads over the Bridge — readable in a log, and
neither side can drift from a field order the other assumes. Documented at the
top of `src/BridgeApi.h` and mirrored in
`python/app/repositories/concrete/bridge_servo_repository.py`.

```
servo_read             ""                        -> snapshot CSV
servo_move             "counts,speed,accel"      -> "ok" | "err"
servo_stop             ""                        -> "ok" | "err"
servo_set_deadband     "counts"                  -> "ok" | "err"
servo_configure_range  "multiturn,amplification" -> "ok" | "err"
servo_centre_here      ""                        -> "ok" | "err"
get_status             ""                        -> "ready" | "no-servo"
```

Snapshot fields: `valid,counts,moving,temp_c,volt_v,curr_a,torque_kgcm,load,status_bits`

## Going live

Already wired. `deps.py` selects `BridgeServoRepository` over
`SimulatedServoRepository` on the `use_hardware_servo` setting, so going live is
a configuration flag on the board (`cp .env.board .env`), not a code change.
Nothing above that line changes — services, API, UI and all 192 tests stay
exactly as they are. See ADR-0004.

## Known gap

Nothing in `src/` logs during operation — `App.cpp` prints a one-time setup
banner and that is all. `ServoBus`, `ServoController`, `NetworkRelay` and
`BridgeApi` are silent, and every defect this project has had lived in those four
files. See backlog D3.
