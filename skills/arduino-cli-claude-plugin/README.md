# Arduino CLI Plugin for Claude Code

A Claude Code plugin that enables Claude to **create, compile, and upload Arduino projects** using the [`arduino-cli`](https://arduino.github.io/arduino-cli/) command-line tool.

## Features

- **5 slash commands** for the complete Arduino workflow: create sketches, compile, upload, manage boards, and install libraries
- **Auto-activating skill** that gives Claude Arduino domain knowledge whenever you discuss embedded development
- **Automatic board detection** that identifies connected Arduino hardware and resolves the correct FQBN (Fully Qualified Board Name)
- **Smart core management** that auto-installs platform cores when needed
- **Comprehensive reference library** covering 30+ boards, troubleshooting guides, and reusable code patterns

---

## Prerequisites

| Requirement | Details |
|---|---|
| **arduino-cli** | Install from [arduino.github.io/arduino-cli](https://arduino.github.io/arduino-cli/latest/installation/) |
| **Python 3** | Used by helper scripts for JSON parsing (pre-installed on macOS) |
| **Claude Code** | The Claude Code CLI tool |
| **Arduino board** | Any supported board: Arduino AVR (Uno, Nano, Mega), SAMD (MKR, Zero), Renesas (UNO R4), ESP32, ESP8266, Adafruit, Raspberry Pi Pico, STM32, and more |

Verify `arduino-cli` is installed:

```bash
arduino-cli version
```

---

## Installation

Load the plugin when launching Claude Code:

```bash
claude --plugin-dir /path/to/this/plugin
```

For example:

```bash
claude --plugin-dir ~/Desktop/claude-arduino-skill
```

### Permissions

The plugin includes a `.claude/settings.local.json` that pre-approves the following operations so you don't get prompted for each command:

- All `arduino-cli` subcommands (compile, upload, sketch new, core install, lib install, etc.)
- Execution of the plugin's helper scripts
- Basic file operations (ls, mkdir, cat, chmod)

You can review and modify these permissions in `.claude/settings.local.json`.

---

## Quick Start

Get from zero to a blinking LED in 6 steps:

### 1. Connect Your Board

Plug your Arduino board into a USB port.

### 2. Verify Detection

```
/arduino-boards
```

This lists all connected boards with their port, FQBN, and installed platform cores.

### 3. Create a Sketch

```
/arduino-new Blink
```

This creates a `Blink/Blink.ino` file with Arduino boilerplate. You can also describe what you want:

> "Create an Arduino sketch that blinks the built-in LED every 500ms and prints the uptime to serial"

Claude will generate the appropriate code automatically.

### 4. Compile

```
/arduino-build Blink
```

The command auto-detects your connected board's FQBN and installs the platform core if needed. On success, it reports flash and RAM usage.

### 5. Upload

```
/arduino-upload Blink
```

Compiles the sketch (ensuring it's up to date) and uploads it to the detected board. On success, it suggests opening a serial monitor.

### 6. Monitor (Optional)

After upload, you can monitor serial output:

```bash
arduino-cli monitor -p /dev/cu.usbmodem* -c baudrate=9600
```

---

## Commands Reference

### `/arduino-new`

Create a new Arduino sketch project.

**Syntax:**

```
/arduino-new <sketch-name>
```

**Behavior:**

- Creates a sketch directory with a `.ino` file using `arduino-cli sketch new`
- If you described functionality in the conversation, Claude replaces the boilerplate with working code
- Detects connected boards and reports the FQBN for building
- Suggests next steps (`/arduino-build`, `/arduino-upload`)

**Examples:**

```
/arduino-new TemperatureLogger
/arduino-new MotorController
```

---

### `/arduino-build`

Compile an Arduino sketch for a target board.

**Syntax:**

```
/arduino-build [sketch-path] [--fqbn <FQBN>]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `sketch-path` | No | Path to sketch directory or `.ino` file. If omitted, searches the current directory. |
| `--fqbn <FQBN>` | No | Target board FQBN (e.g., `arduino:avr:uno`). If omitted, uses the detected board. |

**Behavior:**

1. **Finds the sketch** -- searches current directory for `.ino` files if no path given
2. **Resolves the board** -- uses the `--fqbn` argument, detected board, or asks you
3. **Installs the platform core** if not already installed (e.g., `arduino:avr`, `esp32:esp32`)
4. **Compiles** and reports flash/RAM usage
5. **On errors** -- analyzes compilation errors, identifies issues in source code, and suggests or applies fixes. If libraries are missing, suggests `/arduino-libs`.

**Examples:**

```
/arduino-build
/arduino-build MySketch
/arduino-build MySketch --fqbn arduino:avr:nano
```

---

### `/arduino-upload`

Upload a compiled sketch to a connected Arduino board.

**Syntax:**

```
/arduino-upload [sketch-path] [--port <port>] [--fqbn <FQBN>]
```

**Arguments:**

| Argument | Required | Description |
|---|---|---|
| `sketch-path` | No | Path to sketch. If omitted, searches current directory. |
| `--port <port>` | No | Serial port (e.g., `/dev/cu.usbmodem1234`). If omitted, uses detected port. |
| `--fqbn <FQBN>` | No | Target board FQBN. If omitted, uses detected board. |

**Behavior:**

1. **Finds the sketch** and determines port + FQBN (from arguments or auto-detection)
2. **Compiles first** to ensure the binary is up to date
3. **Uploads** to the board
4. **On success** -- confirms upload and suggests opening a serial monitor
5. **On failure** -- diagnoses common issues:
   - Permission denied on serial port
   - Wrong port or FQBN
   - Board not in bootloader mode (ESP32 BOOT button, SAMD double-tap reset)
   - avrdude sync errors

**Examples:**

```
/arduino-upload
/arduino-upload MySketch
/arduino-upload MySketch --port /dev/cu.usbmodem1234 --fqbn arduino:avr:uno
```

---

### `/arduino-boards`

List connected Arduino boards or search for board support.

**Syntax:**

```
/arduino-boards [search-term]
```

**Two modes:**

**List mode** (no arguments): Shows all connected boards with:
- Board name, FQBN, port, protocol
- Installed platform cores and versions
- If no boards detected: shows all serial ports and troubleshooting tips

**Search mode** (with argument): Searches the board database:
- Runs `arduino-cli board listall <search-term>`
- Shows matching board names and FQBNs
- Indicates which platform cores are needed

**Examples:**

```
/arduino-boards
/arduino-boards uno
/arduino-boards esp32
/arduino-boards nano
```

---

### `/arduino-libs`

Search for and install Arduino libraries.

**Syntax:**

```
/arduino-libs <search-term | install library-name>
```

**Three modes:**

| Mode | Syntax | Behavior |
|---|---|---|
| **List** | `/arduino-libs` | Shows currently installed libraries |
| **Search** | `/arduino-libs <keyword>` | Searches the library registry, shows top 10 results |
| **Install** | `/arduino-libs install <name>` | Installs the library and shows how to include it |

**Examples:**

```
/arduino-libs
/arduino-libs servo
/arduino-libs debouncer
/arduino-libs install FTDebouncer
/arduino-libs install "Adafruit NeoPixel"
```

---

## Auto-Activating Skill

The plugin includes an **arduino-development** skill that activates automatically when you discuss Arduino-related topics. Unlike slash commands which you invoke explicitly, the skill provides background knowledge that informs Claude's responses.

### Trigger Topics

The skill activates when you mention:

- Arduino project creation, programming, or code writing
- Specific boards: Arduino Uno, Nano, Mega, ESP32, ESP8266, Adafruit boards
- Topics: microcontroller programming, embedded development, IoT prototyping, sensor projects, servo control
- Actions: compiling sketches, uploading code, blinking LEDs, reading sensors

### What It Provides

When active, Claude gains knowledge of:

- The complete Arduino CLI workflow (detect, install core, create, compile, upload, monitor)
- Sketch structure conventions (`setup()`, `loop()`, pin constants, timing functions)
- Multi-file project organization
- Library management
- Available slash commands

### Reference Files

The skill can consult these reference documents as needed:

| File | Contents |
|---|---|
| `references/board-platforms.md` | 30+ boards with FQBNs, core IDs, and board manager URLs |
| `references/troubleshooting.md` | Compilation, upload, and serial monitor error diagnosis |
| `references/project-patterns.md` | 9 reusable code patterns (state machines, debouncing, EEPROM, etc.) |

---

## Project Structure

```
arduino-cli-plugin/
├── .claude-plugin/
│   └── plugin.json                  # Plugin manifest (name, version, description)
├── .claude/
│   └── settings.local.json         # Pre-approved permissions for arduino-cli commands
│
├── commands/                        # Slash commands (user-invoked)
│   ├── arduino-new.md              # /arduino-new   - Create a new sketch
│   ├── arduino-build.md            # /arduino-build - Compile a sketch
│   ├── arduino-upload.md           # /arduino-upload - Upload to board
│   ├── arduino-boards.md           # /arduino-boards - List/search boards
│   └── arduino-libs.md             # /arduino-libs  - Search/install libraries
│
├── scripts/                         # Helper scripts (called by commands)
│   ├── detect-board.sh             # Detect connected boards, output PORT/FQBN/NAME
│   ├── ensure-core.sh              # Check/install platform core for a given FQBN
│   └── list-boards.sh             # Human-readable board listing with core info
│
├── skills/                          # Auto-activating knowledge
│   └── arduino-development/
│       ├── SKILL.md                # Core Arduino development guidance
│       └── references/
│           ├── board-platforms.md  # Board/FQBN/core mapping table
│           ├── troubleshooting.md  # Common errors and fixes
│           └── project-patterns.md # Reusable Arduino code patterns
│
└── README.md                       # This file
```

### Directory Roles

| Directory | Purpose |
|---|---|
| `commands/` | Slash commands -- markdown files that define user-invokable actions. Each command gathers context (board detection, installed cores) and provides Claude with step-by-step instructions. |
| `scripts/` | Bash scripts that parse `arduino-cli --json` output using Python3. Shared by multiple commands to avoid duplication. |
| `skills/` | Auto-activating domain knowledge. The `SKILL.md` is loaded when Arduino topics are discussed. Reference files are loaded on-demand for detailed information. |

---

## Supported Boards

### Official Arduino Boards (No Extra Configuration)

| Board | FQBN | Core ID |
|---|---|---|
| Arduino Uno | `arduino:avr:uno` | `arduino:avr` |
| Arduino Nano | `arduino:avr:nano` | `arduino:avr` |
| Arduino Mega 2560 | `arduino:avr:mega:cpu=atmega2560` | `arduino:avr` |
| Arduino Leonardo | `arduino:avr:leonardo` | `arduino:avr` |
| Arduino MKR1000 | `arduino:samd:mkr1000` | `arduino:samd` |
| Arduino MKR WiFi 1010 | `arduino:samd:mkrwifi1010` | `arduino:samd` |
| Arduino Zero | `arduino:samd:arduino_zero_edbg` | `arduino:samd` |
| Arduino UNO R4 Minima | `arduino:renesas_uno:minima` | `arduino:renesas_uno` |
| Arduino UNO R4 WiFi | `arduino:renesas_uno:unor4wifi` | `arduino:renesas_uno` |
| Arduino Nano 33 BLE | `arduino:mbed_nano:nano33ble` | `arduino:mbed_nano` |
| Arduino Nano RP2040 | `arduino:mbed_nano:nanorp2040connect` | `arduino:mbed_nano` |

Install a core: `arduino-cli core install <core-id>`

### 3rd-Party Boards (Require Board Manager URLs)

These boards need an additional board manager URL configured before installing the core.

#### ESP32

```bash
arduino-cli config set board_manager.additional_urls \
  https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32
```

Boards: ESP32 Dev Module (`esp32:esp32:esp32`), ESP32-S3 (`esp32:esp32:esp32s3`), ESP32-C3 (`esp32:esp32:esp32c3`), NodeMCU-32S (`esp32:esp32:nodemcu-32s`)

#### ESP8266

```bash
arduino-cli config set board_manager.additional_urls \
  https://arduino.esp8266.com/stable/package_esp8266com_index.json
arduino-cli core update-index
arduino-cli core install esp8266:esp8266
```

Boards: NodeMCU (`esp8266:esp8266:nodemcuv2`), Wemos D1 Mini (`esp8266:esp8266:d1_mini`)

#### Adafruit

```bash
arduino-cli config set board_manager.additional_urls \
  https://adafruit.github.io/arduino-board-index/package_adafruit_index.json
arduino-cli core update-index
arduino-cli core install adafruit:samd
```

Boards: Feather M0/M4, Circuit Playground Express, ItsyBitsy M4, QT Py

#### Raspberry Pi Pico (RP2040)

```bash
arduino-cli config set board_manager.additional_urls \
  https://github.com/earlephilhower/arduino-pico/releases/download/global/package_rp2040_index.json
arduino-cli core update-index
arduino-cli core install rp2040:rp2040
```

Boards: Raspberry Pi Pico (`rp2040:rp2040:rpipico`), Pico W (`rp2040:rp2040:rpipicow`)

#### Multiple URLs

To support multiple 3rd-party board families, combine URLs with commas:

```bash
arduino-cli config set board_manager.additional_urls \
  https://espressif.github.io/arduino-esp32/package_esp32_index.json,\
  https://arduino.esp8266.com/stable/package_esp8266com_index.json,\
  https://adafruit.github.io/arduino-board-index/package_adafruit_index.json
```

For the complete board reference table, see [`skills/arduino-development/references/board-platforms.md`](skills/arduino-development/references/board-platforms.md).

---

## Troubleshooting

### Board Not Detected

| Symptom | Solution |
|---|---|
| No boards listed in `/arduino-boards` | Check USB cable (some are charge-only), try a different USB port |
| Board shows as "Unknown" | Install the correct platform core; use `/arduino-boards <board-name>` to search |
| Port listed but no board name | The platform core for this board is not installed |

### Compilation Errors

| Error | Solution |
|---|---|
| `No such file or directory` (includes) | Install the missing library: `/arduino-libs install <name>` |
| `was not declared in this scope` | Add the correct `#include` directive or check the board supports the function |
| `Sketch too big` | Remove unused libraries, use `F()` macro for strings, use smaller data types |
| `Low memory available` | Use `PROGMEM` for constants, avoid `String` class, reduce buffer sizes |

### Upload Errors

| Error | Solution |
|---|---|
| `Permission denied` on serial port | **macOS**: Grant terminal serial access in System Settings > Privacy & Security. **Linux**: `sudo usermod -a -G dialout $USER` |
| `stk500_getsync() not in sync` | Try the old bootloader variant (`arduino:avr:nano:cpu=atmega328old`), or press reset before upload |
| `No device found on port` | Close other serial monitors, verify port with `/arduino-boards`, try different USB port |
| ESP32 `Failed to connect: Timed out` | Hold the BOOT button while upload starts |
| `dfu-util: No DFU capable USB device` | Double-tap the reset button to enter bootloader mode (SAMD boards) |

### Serial Monitor Issues

| Symptom | Solution |
|---|---|
| Garbled output | Baud rate mismatch -- ensure `Serial.begin()` rate matches monitor setting |
| No output at all | Missing `Serial.begin()` in `setup()`, or wrong baud rate |
| `Port is busy` | Another application is using the serial port -- close it first |

For the comprehensive troubleshooting guide, see [`skills/arduino-development/references/troubleshooting.md`](skills/arduino-development/references/troubleshooting.md).

---

## How It Works

### Architecture

The plugin uses three interconnected component types:

```
User invokes /arduino-build
        │
        ▼
┌─────────────────────────────────────────────┐
│  Command (commands/arduino-build.md)        │
│                                             │
│  1. Injects context via inline bash:        │
│     !`bash scripts/detect-board.sh`         │
│     !`arduino-cli core list`                │
│                                             │
│  2. Provides Claude with step-by-step       │
│     instructions for the task               │
└──────────┬──────────────────────────────────┘
           │ calls
           ▼
┌─────────────────────────────────────────────┐
│  Scripts (scripts/*.sh)                     │
│                                             │
│  - detect-board.sh: Parse --json output     │
│    with Python3, filter real Arduino boards │
│  - ensure-core.sh: Check/install platform   │
│  - list-boards.sh: Format board info        │
└─────────────────────────────────────────────┘
```

Meanwhile, the **skill** operates independently:

```
User says "I want to read a temperature sensor with Arduino"
        │
        ▼
┌─────────────────────────────────────────────┐
│  Skill (skills/arduino-development/)        │
│                                             │
│  SKILL.md loaded into context               │
│  (workflow, conventions, available commands) │
│                                             │
│  References loaded on-demand:               │
│  - board-platforms.md (board lookup)        │
│  - troubleshooting.md (error diagnosis)     │
│  - project-patterns.md (code templates)     │
└─────────────────────────────────────────────┘
```

### Key Design Principles

1. **Commands are self-contained** -- Each command gathers its own context via inline bash execution. Commands work correctly even without the skill being active.

2. **Progressive disclosure** -- The skill's SKILL.md is lean (~700 words). Detailed board tables, troubleshooting guides, and code patterns live in `references/` and are loaded only when Claude determines they're needed.

3. **Smart board detection** -- The `detect-board.sh` script filters `arduino-cli board list --json` output to exclude Bluetooth, debug console, and other non-Arduino serial ports. Only entries with `matching_boards` in the JSON are reported.

4. **JSON over text** -- Scripts parse `arduino-cli --json` output (machine-readable) rather than the human-readable text output, ensuring reliable data extraction regardless of formatting changes.

5. **Python3 for portability** -- Scripts use Python3 for JSON parsing instead of `jq`, since Python3 is pre-installed on macOS and most Linux distributions.

---

## Customization

### Modifying Permissions

Edit `.claude/settings.local.json` to adjust what the plugin is allowed to do:

```json
{
  "permissions": {
    "allow": [
      "Bash(arduino-cli:*)",
      "Bash(bash:*)"
    ]
  }
}
```

Remove entries to restrict operations, or add new patterns as needed.

### Adding Board Manager URLs

For 3rd-party boards not covered by the default configuration:

```bash
arduino-cli config set board_manager.additional_urls <URL1>,<URL2>
arduino-cli core update-index
```

The board-platforms reference file (`skills/arduino-development/references/board-platforms.md`) documents URLs for ESP32, ESP8266, Adafruit, Raspberry Pi Pico, and STM32 boards.

### Adding New Commands

Create a new `.md` file in the `commands/` directory:

```markdown
---
description: Short description for /help listing
argument-hint: <required-arg> [optional-arg]
allowed-tools: [Bash, Read, Write]
---

## Context

Connected boards: !`bash ${CLAUDE_PLUGIN_ROOT}/scripts/detect-board.sh`

## Task

Instructions for Claude on how to execute this command...
```

The `!` backtick syntax runs a bash command inline and injects the output as context before Claude processes the instructions.

### Adding Code Patterns

Add new patterns to `skills/arduino-development/references/project-patterns.md`. The skill references this file, and Claude will consult it when the user's project matches a documented pattern.

Current patterns include: non-blocking timing (millis), state machines, sensor averaging, button debouncing, serial command parsing, multi-file projects, interrupt-driven input, PWM fading, and EEPROM storage.
