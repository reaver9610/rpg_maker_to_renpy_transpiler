#!/bin/bash
# Test: Combined options (indent width + case)
# Usage: ./test_scripts/combined/test_indent_and_case.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Combined Indent + Case ==="
echo "Command: -s 2 -c --lower"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -s 2 -c --lower
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -s 2 -c --lower
fi

# Check indentation and case
event_file=$(find outputs -name "*event*.rpy" -type f | head -1)
if [ -n "$event_file" ]; then
    echo "--- Indentation check (expect 2 spaces) ---"
    grep -m1 "^  " "$event_file" | cat -A
fi

if [ -f "outputs/characters.rpy" ]; then
    echo "--- Case check (expect lowercase) ---"
    grep "^define " outputs/characters.rpy | head -3
fi

echo "SUCCESS: Combined indent + case test completed"
