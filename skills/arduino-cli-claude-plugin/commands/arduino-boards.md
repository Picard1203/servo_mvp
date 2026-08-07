---
description: List connected Arduino boards and search for board support
argument-hint: [search-term]
allowed-tools: [Bash, Read]
---

## Context

Board detection: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/list-boards.sh`

## Task

Show the user information about Arduino boards. The user provided: $ARGUMENTS

If $ARGUMENTS is empty:
- Present the board detection results above in a clear, formatted way.
- Highlight the FQBN and port for each detected board.
- Show which platform cores are installed.

If $ARGUMENTS contains a search term:
- Run `arduino-cli board listall $ARGUMENTS` to search for matching board definitions.
- Show matching board names and their FQBNs.
- Indicate which platform cores would need to be installed to use those boards.
- If the core is not yet installed, suggest running `/arduino-build` which auto-installs cores, or manual install with `arduino-cli core install <core-id>`.

Present all information clearly. Highlight recommended next steps:
- If boards are detected: suggest `/arduino-new` or `/arduino-build`
- If no boards detected: suggest checking USB connections and searching by board name
- If searching: show how to install the needed core
