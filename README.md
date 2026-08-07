# Servo Control — UNO Q + Waveshare ST3215

FastAPI backend + LCARS web UI, served from the board. Any machine on the
network opens `http://<board-ip>:8000` — several at once, nothing installed
on the viewing machines.

**Status:** backend, GUI and tests are complete and green (142 tests, 100%
line coverage). The sketch (C side) is the remaining work.

---

## 1. RUN IT ON THE DEV PC — no board needed

```bash
cd python
pip install -r requirements-dev.txt
python run_dev.py
```

Open `http://127.0.0.1:8000` in Chrome.

`run_dev.py` exists because two imports only live on the board
(`arduino.app_utils` and possibly `Logger461`). It points DB_PATH and
LOG_FILE at local files first, then boots the app the way `main.py` does,
minus the Bridge relay. Console commands: `overload`, `state`, `quit`.

Run the tests:

```bash
cd python
pytest                                   # 142 tests
pytest --cov=app --cov-report=term       # 100% of app/
```

---

## 2. LAYOUT

```
servo_mvp/
├── app.yaml
├── python/
│   ├── app/            backend (services, routers, repositories)
│   ├── static/         index.html, style.css, app.js  (the GUI)
│   ├── tests/          unit / integration / e2e
│   ├── main.py         BOARD entrypoint
│   ├── run_dev.py      DEV-PC entrypoint
│   ├── .env.example    every setting, annotated with measured values
│   └── wheelhouse/     offline wheels for the air-gapped board
├── libraries/          patched Ethernet + SCServo, vendored
└── sketch/             the C side (to be written)
```

---

## 3. WHAT THE BENCH MEASUREMENTS CHANGED

Every value below came from the diagnostic app on real hardware, not a
datasheet.

| Setting | Value | Why |
|---|---|---|
| `OUTPUT_MIN_DEG` / `MAX` | −90 / +90 | The window operators asked for. 180° output = 264 servo° = 3004 counts — inside ONE servo turn (4096), so no multi-turn needed |
| `OUTPUT_STEP_DEG` | 0.06 | One encoder count at the output = (360/4096)×(30/44) = 0.0599° |
| `SERVO_DEADBAND_COUNTS` | 0 | Measured landing error: 0 → 0.06°, 1 → 0.10°, 8 → 0.52°, 32 → 1.98° |
| `MAX_SPEED_DPS` | 60 | The servo saturates near 1100 counts/s (~66°/s output) whatever is commanded |
| `DEFAULT_ACCELERATION` | 50 | Nothing measurably changes above ~50 |
| `SERVO_DIRECTION` | +1 | Confirmed: commanding +400 raised the reported position |
| `MULTI_TURN_ENABLED` | false | Not needed at ±90°. Kept because it is bench-proven to work |

**Multi-turn is not thrown away.** `configure_range()` exists on the
repository contract and is called at startup. Setting `MULTI_TURN_ENABLED=true`
applies the absolute sequence (angle limits 0, angle-resolution
amplification, phase BIT4). It was verified working at amplification 1 —
position read back past 4095 without wrapping, at the finest resolution.
Widening the travel window later is two numbers in `.env`, not a code change.

Also new since the last version:
- `ts` renamed to `timestamp` everywhere — entities, schemas, DB columns,
  CSV first column, query params, tests.
- Sixth fault flag `angle_fault` (status register bit 4) added end-to-end:
  entity, schema, `/state`, DB + migration, CSV contract, GUI tile.
- Negative angles are first-class. **No modulus-360 wrapping**: in a
  multi-turn system −25° and 335° are different absolute targets a whole
  output revolution apart, and wrapping would hide turn-count errors.

---

## 4. THE AIR-GAPPED BUNDLE

Develop as if already air-gapped, so shipping is "zip the folder":

1. **Wheels** — build `python/wheelhouse/` on this connected laptop
   (`--platform manylinux2014_aarch64`; the board is ARM64). See the README
   in that folder.
2. **Libraries** — drop the patched `Ethernet/` and `SCServo/` into
   `libraries/`. See the README there for the exact IPAddress patch.
3. **Pin the core version.** Board Manager does not exist on the air-gapped
   machine, so the target must already have `arduino:zephyr` at the same
   version you built against (0.56.0 or newer — it adds `Serial3` and the
   UNO Q main-thread-priority fix). This is the most likely cause of
   "it worked on my laptop".

---

## 5. DEPLOY TO THE BOARD

**Wipe first, then push.** `adb push` overwrites files it copies but does
**not** delete anything already on the board that is missing from the source.
Renamed or deleted files linger and can be picked up instead of the new ones:

```bash
adb shell rm -rf /home/arduino/ArduinoApps/servo_mvp
adb push ./servo_mvp /home/arduino/ArduinoApps/servo_mvp
```

Then, on the board, once:

```bash
cd /home/arduino/ArduinoApps/servo_mvp/python
cp .env.board .env
```

**That `cp` is the only manual step, and forgetting it is silent.** Without
`.env`, `use_hardware_servo` defaults to false, the backend runs the
simulator, and the UI moves convincingly while the real servo never twitches.
It is not shipped as `.env` because a dev machine that had it would try to
drive hardware during `pytest`.

Two ways to confirm which backend is live:

```bash
curl -s http://<board-ip>:8000/api/v1/system/health   # "servo_backend"
```

and the Python tab logs it at startup - a warning if it is simulated.

Open the app in App Lab and press **Run**. The entrypoint on the board is
`main.py`; `run_dev.py` is for the laptop.

Wiping the folder also removes `.cache/.venv`, so App Lab re-provisions the
Python environment on the next Run - a minute or two with the board online.
To keep the venv, delete everything except it instead.

Browse to `http://<board-ip>:8000`.

### After the first build, confirm the Ethernet patch survived

`~/.arduino15/internal/` is a user-global library cache shared by every app,
so the patched Ethernet should be reused:

```bash
grep -c 'IPAddress((uint32_t)' \
  ~/.arduino15/internal/Ethernet_2.0.2_*/Ethernet/src/EthernetClient.cpp
```

Three or more means the patch is intact. Zero means App Lab re-fetched the
library and you re-apply it - the patched copy is in `libraries/`.

---

## 6. CHECK THE BRIDGE CONTRACT AFTER TOUCHING EITHER SIDE

```bash
python3 tools/check_bridge_contract.py
```

Every function crossing the MCU/Linux boundary is declared twice - once in
C++, once in Python - and nothing makes the compiler or the interpreter
compare them. A wrong argument count compiles and imports cleanly on both
sides and fails at runtime as *silence*, not an error. That is exactly how
the relay broke: the sketch never sent `net_open`, so the Linux side had no
socket to put bytes into. Non-zero exit, so it can go in a pre-commit hook.

## 7. WHEN THE SKETCH IS READY

Switch `deps.py` from `SimulatedServoRepository` to
`BridgeServoRepository`. Nothing above that line changes — services, API,
GUI and all 142 tests stay exactly as they are. That swap is the whole
point of the repository abstraction.
