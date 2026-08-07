---
description: Create a new Arduino sketch project
argument-hint: <sketch-name>
allowed-tools: [Read, Write, Edit, Bash, Glob]
---

## Context

Connected boards: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/detect-board.sh`

## Task

Create a new Arduino sketch named "$ARGUMENTS".

Steps:

1. If no sketch name was provided ($ARGUMENTS is empty), ask the user for a name before proceeding.

2. Run `arduino-cli sketch new $ARGUMENTS` to create the sketch directory and boilerplate .ino file.

3. Read the generated .ino file to confirm creation.

4. If the user described what the sketch should do (in prior conversation context), replace the boilerplate `setup()` and `loop()` functions with appropriate code implementing that functionality. Include necessary `#include` directives and pin definitions.

5. If a board was detected above, note its FQBN so the user knows what target to use when building.

6. Report:
   - The created file path
   - Next steps: use `/arduino-build` to compile, `/arduino-upload` to upload
   - If a board is connected, mention its name and FQBN
