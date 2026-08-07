#!/bin/bash
# Detect connected Arduino boards using arduino-cli
# Outputs tab-separated: PORT  FQBN  BOARD_NAME
# Only shows boards with matching_boards (filters Bluetooth, debug ports, etc.)
# Prints NO_BOARDS_DETECTED if no recognized Arduino boards found

ARDUINO_CLI="arduino-cli"

json_output=$("$ARDUINO_CLI" board list --json 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$json_output" ]; then
    echo "ERROR: Failed to run arduino-cli board list"
    exit 1
fi

echo "$json_output" | python3 -c "
import json, sys

data = json.load(sys.stdin)
boards_found = False

for port_entry in data.get('detected_ports', []):
    matching = port_entry.get('matching_boards', [])
    if matching:
        port = port_entry['port']['address']
        for board in matching:
            boards_found = True
            fqbn = board.get('fqbn', 'unknown')
            name = board.get('name', 'Unknown Board')
            print(f'{port}\t{fqbn}\t{name}')

if not boards_found:
    print('NO_BOARDS_DETECTED')
"
