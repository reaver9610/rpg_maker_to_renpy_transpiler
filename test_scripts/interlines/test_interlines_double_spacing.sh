#!/bin/bash
# Test: Double spacing interlines (-n 2)
# Usage: ./test_scripts/interlines/test_interlines_double_spacing.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Double Spacing Interlines ==="
echo "Command: -n 2 --pictures"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -n 2 --pictures
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -n 2 --pictures
fi

# Compare spacing with baseline
if [ -f "outputs/pictures.rpy" ]; then
    echo "--- pictures.rpy (lines 24-35) with -n 2 ---"
    sed -n '24,35p' outputs/pictures.rpy
    echo ""
    blank_count=$(sed -n '24,35p' outputs/pictures.rpy | grep -c "^$")
    echo "Blank lines in lines 24-35: $blank_count (expect ~4 for double spacing)"
    echo "SUCCESS: Double spacing test completed"
else
    echo "FAILURE: pictures.rpy not generated"
    exit 1
fi
