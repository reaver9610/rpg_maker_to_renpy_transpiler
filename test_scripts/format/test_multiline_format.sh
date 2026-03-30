#!/bin/bash
# Test: Multiline format (-f --multiline)
# Usage: ./test_scripts/format/test_multiline_format.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Multiline Format ==="
echo "Command: -f --multiline"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -f --multiline
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -f --multiline
fi

# Check for triple-quoted strings in event files
event_file=$(find outputs -name "*event*.rpy" -type f | head -1)
if [ -n "$event_file" ]; then
    echo "--- Checking $event_file for triple-quoted strings ---"
    if grep -q '"""' "$event_file"; then
        echo "SUCCESS: Triple-quoted strings found (multiline format)"
    else
        echo "WARNING: No triple-quoted strings found"
    fi
    head -30 "$event_file"
else
    echo "FAILURE: No event files found"
    exit 1
fi
