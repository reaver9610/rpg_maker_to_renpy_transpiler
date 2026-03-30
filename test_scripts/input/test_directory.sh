#!/bin/bash
# Test: Directory input (-i --directory)
# Usage: ./test_scripts/input/test_directory.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Directory Input ==="
echo "Command: -i --directory inputs/"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/
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
