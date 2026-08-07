#!/bin/bash
# Ensure the platform core for a given FQBN is installed
# Usage: ensure-core.sh <fqbn>
# Example: ensure-core.sh arduino:avr:uno
# Extracts the core ID (first two colon-separated segments) and checks/installs

ARDUINO_CLI="arduino-cli"
FQBN="$1"

if [ -z "$FQBN" ]; then
    echo "ERROR: No FQBN provided"
    echo "Usage: ensure-core.sh <fqbn>"
    exit 1
fi

# Extract core ID from FQBN (e.g., "arduino:avr:uno" -> "arduino:avr")
CORE_ID=$(echo "$FQBN" | cut -d: -f1,2)

echo "Checking if core $CORE_ID is installed..."

installed=$("$ARDUINO_CLI" core list --json 2>/dev/null | python3 -c "
import json, sys
data = json.load(sys.stdin)
for p in data.get('platforms', []):
    pid = p.get('id', '')
    if pid == '$CORE_ID':
        print('INSTALLED:' + p.get('installed_version', 'unknown'))
        sys.exit(0)
print('NOT_INSTALLED')
")

if [[ "$installed" == INSTALLED:* ]]; then
    version="${installed#INSTALLED:}"
    echo "Core $CORE_ID is already installed (version $version)."
else
    echo "Core $CORE_ID is not installed. Installing..."
    "$ARDUINO_CLI" core update-index
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to update core index. Attempting install anyway..."
    fi
    "$ARDUINO_CLI" core install "$CORE_ID"
    if [ $? -eq 0 ]; then
        echo "Core $CORE_ID installed successfully."
    else
        echo "ERROR: Failed to install core $CORE_ID"
        echo "You may need to add additional board manager URLs for this core."
        echo "Use: arduino-cli config set board_manager.additional_urls <URL>"
        exit 1
    fi
fi
