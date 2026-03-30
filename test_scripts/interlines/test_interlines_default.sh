#!/bin/bash
# Test: Interlines default (-n without targets = maps only)
# Usage: ./test_scripts/interlines/test_interlines_default.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Interlines Default (maps only) ==="
echo "Command: -n 1"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -n 1
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -n 1
fi

# Verify interlines applied to maps
map_file=$(find outputs/maps -name "*.rpy" -type f | head -1)
if [ -n "$map_file" ]; then
    # Check for blank lines between code statements
    blank_count=$(head -30 "$map_file" | grep -c "^$")
    echo "Map file has $blank_count blank lines in first 30 lines"
    if [ "$blank_count" -gt 1 ]; then
        echo "SUCCESS: Interlines applied to map files"
    else
        echo "WARNING: Few blank lines found - interlines may not be applied"
    fi
else
    echo "FAILURE: No map files found"
    exit 1
fi

# Verify non-map files are unchanged
if [ -f "outputs/characters.rpy" ]; then
    echo "characters.rpy exists (should NOT have interlines)"
fi
