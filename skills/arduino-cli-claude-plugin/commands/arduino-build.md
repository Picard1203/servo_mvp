---
description: Compile an Arduino sketch for a target board
argument-hint: [sketch-path] [--fqbn <FQBN>]
allowed-tools: [Read, Write, Edit, Bash, Glob, Grep]
---

## Context

Connected boards: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/detect-board.sh`
Installed cores: !`arduino-cli core list`

## Task

Compile an Arduino sketch. The user provided: $ARGUMENTS

Steps:

1. **Determine the sketch path.**
   - If $ARGUMENTS includes a path, use it.
   - Otherwise, search the current directory and subdirectories for `.ino` files.
   - An Arduino sketch is a `.ino` file inside a directory with the same base name (e.g., `MySketch/MySketch.ino`).
   - If multiple sketches are found, ask the user which one to compile.

2. **Determine the target board (FQBN).** In priority order:
   a. If the user specified `--fqbn` in $ARGUMENTS, use that value.
   b. If a board was detected above, use its FQBN.
   c. Ask the user which board to target. Suggest running `/arduino-boards` to search.

3. **Ensure the platform core is installed.** Run:
   `bash ${CLAUDE_PLUGIN_ROOT}/scripts/ensure-core.sh <FQBN>`

4. **Compile the sketch.** Run:
   `arduino-cli compile --fqbn <FQBN> <sketch-path>`

5. **Report results:**
   - On success: report flash and RAM usage from output, suggest `/arduino-upload` as next step.
   - On failure: analyze error messages, identify the issue in the source code, suggest or apply fixes. If errors mention missing libraries, suggest using `/arduino-libs` to find and install them, or install directly with `arduino-cli lib install "<name>"`.
