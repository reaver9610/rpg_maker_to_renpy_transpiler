#!/bin/bash
# Test: Lowercase variable names (-c --lower)
# Usage: ./test_scripts/case/test_case_lower.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Lowercase Variable Names ==="
echo "Command: -c --lower"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -c --lower
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -c --lower
fi

# Check character case
if [ -f "outputs/characters.rpy" ]; then
    echo "--- Character definitions (expect lowercase names) ---"
    grep "^define " outputs/characters.rpy | head -5
fi

echo "SUCCESS: Lowercase case test completed"
