#!/bin/bash
# Test: Default indent width (4 spaces)
# Usage: ./test_scripts/indent/test_indent_width_default.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Default Indent Width (4 spaces) ==="
echo "Command: (no -s flag, default 4)"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/
fi

# Check indentation
event_file=$(find outputs -name "*event*.rpy" -type f | head -1)
if [ -n "$event_file" ]; then
    echo "--- First indented line in $event_file ---"
    grep -m1 "^    " "$event_file" | cat -A
    spaces=$(grep -m1 "^    " "$event_file" | sed 's/\(^\s*\).*/\1/' | wc -c)
    echo "Indentation: $((spaces - 1)) spaces (expect 4)"
else
    echo "FAILURE: No event files found"
    exit 1
fi

echo "SUCCESS: Default indent width test completed"
