#!/bin/bash
# Test: Custom indent width (-s 2)
# Usage: ./test_scripts/indent/test_indent_width_custom.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Custom Indent Width (2 spaces) ==="
echo "Command: -s 2"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -s 2
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -s 2
fi

# Check indentation
event_file=$(find outputs -name "*event*.rpy" -type f | head -1)
if [ -n "$event_file" ]; then
    echo "--- First indented line in $event_file ---"
    grep -m1 "^  " "$event_file" | cat -A
    spaces=$(grep -m1 "^  " "$event_file" | sed 's/\(^\s*\).*/\1/' | wc -c)
    echo "Indentation: $((spaces - 1)) spaces (expect 2)"
else
    echo "FAILURE: No event files found"
    exit 1
fi

echo "SUCCESS: Custom indent width test completed"
