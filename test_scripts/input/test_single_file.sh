#!/bin/bash
# Test: Single file input (-i --file)
# Usage: ./test_scripts/input/test_single_file.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Single File Input ==="
echo "Command: -i --file inputs/Map001.json"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --file inputs/Map001.json
else
    PYTHONPATH=. python transpiler_rpy.py -i --file inputs/Map001.json
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
