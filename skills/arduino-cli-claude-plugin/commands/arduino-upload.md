---
description: Upload a compiled sketch to a connected Arduino board
argument-hint: [sketch-path] [--port <port>] [--fqbn <FQBN>]
allowed-tools: [Read, Bash, Glob, Grep]
---

## Context

Connected boards: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/detect-board.sh`

## Task

Upload an Arduino sketch to a connected board. The user provided: $ARGUMENTS

Steps:

1. **Determine the sketch path.**
   - If $ARGUMENTS includes a path, use it.
   - Otherwise, search the current directory and subdirectories for `.ino` files.
   - If multiple sketches are found, ask the user which one.

2. **Determine port and FQBN.** In priority order:
   a. Use values from $ARGUMENTS if `--port` or `--fqbn` were specified.
   b. Use detected board info from context above.
   c. If multiple boards are connected, ask the user which one to target.
   d. If no boards are detected, report the error and suggest:
      - Check USB cable connection
      - Try a different USB port
      - Run `/arduino-boards` to diagnose

3. **Compile before uploading** to ensure the binary is up to date. Run:
   `arduino-cli compile --fqbn <FQBN> <sketch-path>`

4. **Upload the sketch.** Run:
   `arduino-cli upload -p <port> --fqbn <FQBN> <sketch-path>`

5. **Report results.**
   - On success: confirm upload completed, mention the user can open a serial monitor with `arduino-cli monitor -p <port>` (default 9600 baud).
   - On failure: analyze the error and suggest fixes for common issues:
     - Port permission denied: user may need to add themselves to the `dialout` group or grant terminal serial access in macOS Privacy settings
     - Wrong port: suggest re-running `/arduino-boards` to verify
     - Board not in bootloader mode: some boards (e.g., ESP32) require holding BOOT button during upload
     - avrdude sync error: try pressing reset button on the board
