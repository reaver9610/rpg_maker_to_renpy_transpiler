#!/bin/bash
# Test: Multiple files input (-i --multiple)
# Usage: ./test_scripts/input/test_multiple_files.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Multiple Files Input ==="
echo "Command: -i --multiple inputs/Map001.json inputs/Map002.json"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --multiple inputs/Map001.json inputs/Map002.json
else
    PYTHONPATH=. python transpiler_rpy.py -i --multiple inputs/Map001.json inputs/Map002.json
fi

# Count generated files
count=$(find outputs -name "*.rpy" 2>/dev/null | wc -l)
if [ "$count" -gt 0 ]; then
    echo "SUCCESS: Generated $count .rpy file(s)"
    find outputs -name "*.rpy" | head -10
else
    echo "FAILURE: No .rpy files generated"
    exit 1
fi
