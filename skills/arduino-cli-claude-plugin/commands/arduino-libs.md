---
description: Search for and install Arduino libraries
argument-hint: <search-term | install library-name>
allowed-tools: [Bash]
---

## Context

Installed libraries: !`arduino-cli lib list 2>/dev/null || echo "No libraries installed"`

## Task

Help the user find or install Arduino libraries. The user provided: $ARGUMENTS

If $ARGUMENTS is empty:
- Show the currently installed libraries from the context above.
- Suggest searching for new libraries with `/arduino-libs <keyword>`.

If $ARGUMENTS starts with "install" (e.g., "install Servo" or "install FTDebouncer"):
- Extract the library name (everything after "install").
- Run `arduino-cli lib install "<library-name>"`.
- Report success or failure.
- On success, show how to include it: `#include <LibraryName.h>`.

Otherwise, treat $ARGUMENTS as a search query:
- Run `arduino-cli lib search $ARGUMENTS` to find matching libraries.
- Show the top results (limit display to the 10 most relevant).
- For each match, show: Name, Author, and one-line description (Sentence field).
- Suggest installing with `/arduino-libs install <name>`.
