# Servo Control — Arduino UNO Q + Waveshare ST3215

FastAPI backend and an LCARS web UI, served from the board. Any machine on the
network opens `http://<board-ip>:8000` — several at once, nothing installed on
the viewing machines.

**Status:** backend, UI, sketch and tests all exist and pass (207 Python tests,
194 native checks, bridge contract agrees). The system is **not yet stable** —
see `docs/BACKLOG.md` for the open defects.

**Working on this repo?** Start at `CLAUDE.md`, not here. This file is
installation and deployment only.

---

## 1. Run on a dev PC — no board needed

```bash
cd python
pip install -r requirements-dev.txt
python run_dev.py
```

Open `http://127.0.0.1:8000`.

`run_dev.py` exists because two imports only live on the board
(`arduino.app_utils`, `Logger461`). It points `DB_PATH` and `LOG_FILE` at local
files, then boots the app the way `main.py` does, minus the Bridge relay.
Console commands: `overload`, `state`, `quit`.

## 2. Verify

```bash
cd python && pytest                      # 207 tests
cd python && pytest --cov=app            # 99% of app/ (backlog D24)
cd sketch/tests/native && make           # 194 checks
python3 tools/check_bridge_contract.py   # "both sides agree"
```

**Run the bridge contract checker after touching either side of the MCU
boundary.** Every function crossing it is declared twice — once in C++, once in
Python — and nothing makes the compiler or interpreter compare them. A wrong
argument count compiles and imports cleanly on both sides, then fails at runtime
as *silence*. That is exactly how the relay broke once. Non-zero exit, so it
suits a pre-commit hook.

## 3. Layout

```
servo_mvp/
├── app.yaml                 required by Arduino App Lab
├── CLAUDE.md                how to work here — start here
├── CONTEXT.md               glossary
├── CONVENTIONS.md           code style
├── docs/
│   ├── PROJECT_STATE.md     where the project is
│   ├── BACKLOG.md           open defects and tasks
│   ├── adr/                 why it is built this way
│   ├── AUDIT.md             historical: the bug chain of the first round
│   └── FILE_REGISTRY.md     catalogue of superseded deliverables
├── python/
│   ├── app/                 backend
│   ├── static/              index.html, style.css, app.js
│   ├── tests/               unit / integration / e2e
│   ├── main.py              BOARD entrypoint
│   ├── run_dev.py           DEV-PC entrypoint
│   └── .env.board           copy to .env ON THE BOARD ONLY
├── sketch/                  the MCU side
├── libraries/               patched Ethernet + SCServo, vendored
└── tools/check_bridge_contract.py
```

## 4. The air-gapped bundle

Production runs on a secure isolated network (ADR-0005). Develop as if already
air-gapped, so shipping is "zip the folder".

1. **Wheels** — build `python/wheelhouse/` on a connected laptop
   (`--platform manylinux2014_aarch64`; the board is ARM64).
2. **Libraries** — patched `Ethernet/` and `SCServo/` in `libraries/`.
3. **Pin the core version.** Board Manager does not exist on an air-gapped
   machine, so the target must already have `arduino:zephyr` at the version you
   built against (0.56.0+ — it adds `Serial3` and the UNO Q main-thread-priority
   fix). This is the most likely cause of "it worked on my laptop".

**This path has never been exercised end to end** — development currently runs on
a WiFi-mounted board. See backlog T2.

## 5. Deploy to the board

**Wipe first, then push.** `adb push` overwrites what it copies but does **not**
delete anything already on the board that is missing from the source. Renamed or
deleted files linger and can be picked up instead of the new ones:

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
`.env`, `use_hardware_servo` defaults to false, the backend runs the simulator,
and the UI moves convincingly while the real servo never twitches. It is not
shipped as `.env` because a dev machine that had it would try to drive hardware
during `pytest`.

Confirm which backend is live:

```bash
curl -s http://<board-ip>:8000/api/v1/system/health   # "servo_backend"
```

The Python tab also logs it at startup — a warning if simulated.

Wiping the folder also removes `.cache/.venv`, so App Lab re-provisions the
Python environment on the next Run — a minute or two with the board online. To
keep the venv, delete everything except it.

Open the app in App Lab and press **Run**. The board entrypoint is `main.py`.

### After the first build, confirm the Ethernet patch survived

`~/.arduino15/internal/` is a user-global library cache shared by every app, so
the patched Ethernet should be reused:

```bash
grep -c 'IPAddress((uint32_t)' \
  ~/.arduino15/internal/Ethernet_2.0.2_*/Ethernet/src/EthernetClient.cpp
```

Three or more means the patch is intact. Zero means App Lab re-fetched the
library — re-apply it from `libraries/`.

## 6. Development shortcut

The working copy is often an **sshfs mount of the board**
(`arduino@192.168.1.192:/home/arduino/ArduinoApps/`), so edits land on the board
with no push step. Convenient for development; **not** the deployment path above.
