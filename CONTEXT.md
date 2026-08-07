# Servo MVP — context

Arduino UNO Q + Waveshare ST3215 serial-bus servo. FastAPI backend and an
LCARS-themed web UI served from the board: operators open `http://<board-ip>:8000`,
several at once, nothing installed on their machines. Final deployment is
air-gapped; the dev board has WiFi, the production ones will not.

## Layout

```
servo_mvp/
├── app.yaml
├── docs/
│   ├── AUDIT.md                  full-system audit, read this for context
│   ├── PROJECT_STATE.md          "attach at start of a new chat" snapshot
│   ├── FILE_REGISTRY.md          catalogue of every file ever delivered
│   └── adr/                      architecture decision records
├── python/
│   ├── app/                      backend
│   ├── static/                   index.html, style.css, app.js
│   ├── tests/                    186 tests, 100% line coverage
│   ├── main.py                   BOARD entrypoint
│   ├── run_dev.py                DEV-PC entrypoint (no board needed)
│   └── .env.board                copy to .env ON THE BOARD ONLY
├── sketch/
│   ├── sketch.ino                thin; real code in src/
│   ├── src/                      C++ classes + RELAY_NOTES.md
│   └── tests/native/             164 host checks, `make`
├── libraries/                    patched Ethernet + SCServo go here
└── tools/check_bridge_contract.py
```

## Run it

```bash
cd python && python run_dev.py     # laptop, simulator, no board
cd python && pytest                # 186 tests
cd sketch/tests/native && make     # 164 checks, no board
python3 tools/check_bridge_contract.py
```

Board deploy: wipe first (`adb push` never deletes), then
`cp .env.board .env` — that single step turns on the real servo. Without it
the simulator runs and the UI looks perfect while nothing moves.

## Locked decisions — do not re-litigate

| Decision | Why |
|---|---|
| Travel ±90° (180° total) | Fits one servo turn (3004 counts); multi-turn off but configurable |
| Plain HTML/CSS/JS, no framework | Air-gap: no build pipeline to vendor |
| LCARS light theme, ISA-101 safety colours | Chosen after many iterations |
| Typed inputs, not sliders | Operators need exact angles |
| `timestamp`, never `ts` | Descriptive naming |
| Bridge payloads: CSV strings, typed args | Debuggable in a log |

These are also candidates for `docs/adr/` write-ups if the reasoning behind
any of them needs to be revisited later.

## Hardware facts, all bench-verified

- 4096 counts per servo turn, 44:30 belt → **0.06° per count** at the output
- ±90° = **3004 counts**; the datum must sit **mid-travel (~2048)**
- **A datum at count 0 makes the negative half unreachable** — the servo
  clamps below 0 silently and still reports success
- direction **+1**; deadband **0**; speed saturates ~**1100 counts/s**;
  acceleration has no effect above ~**50**
- Serial1 @ 1 Mbps is reliable (200/200 reads, 220 µs)
- Ethernet shield needs **SpiRemap** — SPI2 sits on D11–D13 but the shield
  takes SPI from ICSP (PD1/PC2/PC3). Apply it after `SPI.begin()` **and
  again** after `Ethernet.init()`
- Ethernet 2.0.2 needs an `IPAddress((uint32_t)0)` cast patch on this core

## Bugs already found and fixed — do not reintroduce

Full detail in `docs/AUDIT.md` and `sketch/src/RELAY_NOTES.md`.

1. **Relay must use `accept()`, never `available()`** — `available()`
   re-adopts the same client into several slots and splits one HTTP request
   across several sockets
2. **Detect disconnects BEFORE accepting** — otherwise a reused slot
   corrupts the next request
3. **`loop()` must yield** (`delay(1)`) or the Bridge thread starves and
   `servo_read` hits its 10 s timeout
4. **Bridge calls must be serialised** with a lock — the sampler thread and
   HTTP threads collide, producing "Response for unknown msgid"
5. **Failed reads must be distinguishable from data** (`snapshot.valid`) —
   otherwise a failed read becomes a calibration datum of 0
6. Unreachable targets are refused (`out_of_travel`), not silently clamped

## Known gaps, stated honestly

- **The relay and controller have no automated coverage.** Every bug in this
  project lived there. The native tests cover pure maths only.
- **`sketch/tests/OnTarget/` has never been uploaded.** It checks ping,
  config writes, landing accuracy and stop-holds — things a host cannot.
- 100% coverage did not prevent any of the six defects above.

## Older files

`docs/FILE_REGISTRY.md` catalogues every file ever delivered — what each one
is, whether it is superseded, and when you would want it. The two worth
knowing about: `4_relay_sketch_ino.txt` and `5_relay_main_py.txt` are the
*working* relay implementation, and comparing against them is how the worst
bug was found.

## How to work on this repo

- Read the working reference before rewriting anything — several bugs came
  from re-deriving solved behaviour instead of porting it
- Never bundle unrelated changes into a fix
- Deliver patches as idempotent `preview` / `--apply` scripts, not full
  re-pushes
- Say plainly what was actually tested versus assumed
- Run the three verification commands above before and after any change; if
  the numbers (186 / 164 / "both sides agree") do not match, stop and say so
