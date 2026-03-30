#!/bin/bash
# Test: Uppercase variable names (-c --upper)
# Usage: ./test_scripts/case/test_case_upper.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Uppercase Variable Names ==="
echo "Command: -c --upper"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -c --upper
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -c --upper
fi

# Check character case
if [ -f "outputs/characters.rpy" ]; then
    echo "--- Character definitions (expect UPPERCASE names) ---"
    grep "^define " outputs/characters.rpy | head -5
fi

echo "SUCCESS: Uppercase case test completed"
