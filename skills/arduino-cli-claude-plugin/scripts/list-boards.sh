#!/bin/bash
# List all connected Arduino boards in a readable format
# Shows recognized boards with details, and falls back to showing
# all serial ports if no boards are recognized

ARDUINO_CLI="arduino-cli"

echo "=== Connected Arduino Boards ==="
echo ""

json_output=$("$ARDUINO_CLI" board list --json 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$json_output" ]; then
    echo "ERROR: Failed to run arduino-cli board list"
    echo "Make sure arduino-cli is installed and accessible."
    exit 1
fi

echo "$json_output" | python3 -c "
import json, sys

data = json.load(sys.stdin)
found = 0

for port_entry in data.get('detected_ports', []):
    matching = port_entry.get('matching_boards', [])
    port_info = port_entry['port']
    if matching:
        for board in matching:
            found += 1
            print(f'Board {found}:')
            print(f'  Name:     {board.get(\"name\", \"Unknown\")}')
            print(f'  FQBN:     {board.get(\"fqbn\", \"Unknown\")}')
            print(f'  Port:     {port_info[\"address\"]}')
            print(f'  Protocol: {port_info.get(\"protocol_label\", \"Unknown\")}')
            props = port_info.get('properties', {})
            if 'serialNumber' in props:
                print(f'  Serial:   {props[\"serialNumber\"]}')
            print()

if found == 0:
    print('No recognized Arduino boards detected.')
    print()
    print('All serial ports found:')
    for port_entry in data.get('detected_ports', []):
        port_info = port_entry['port']
        label = port_info.get('protocol_label', '')
        addr = port_info['address']
        print(f'  {addr} ({label})')
    print()
    print('If your board is connected but not listed:')
    print('  1. Check USB cable connection')
    print('  2. Install the correct platform core (use /arduino-boards <board-name> to search)')
    print('  3. Some boards need drivers installed first')
"

echo ""
echo "=== Installed Platform Cores ==="
echo ""
"$ARDUINO_CLI" core list
