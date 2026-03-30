#!/bin/bash
# Test: Interlines for pictures.rpy specifically
# Usage: ./test_scripts/interlines/test_interlines_pictures.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Interlines for Pictures ==="
echo "Command: -n 1 --pictures"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -n 1 --pictures
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -n 1 --pictures
fi

# Verify pictures.rpy has interlines
if [ -f "outputs/pictures.rpy" ]; then
    echo "--- pictures.rpy (first 25 lines) ---"
    head -25 outputs/pictures.rpy
    blank_count=$(head -30 outputs/pictures.rpy | grep -c "^$")
    echo ""
    echo "pictures.rpy: $blank_count blank lines in first 30 lines"
    if [ "$blank_count" -gt 5 ]; then
        echo "SUCCESS: Interlines applied to pictures.rpy"
    else
        echo "WARNING: Few blank lines found"
    fi
else
    echo "FAILURE: pictures.rpy not generated"
    exit 1
fi
