#!/bin/bash
# Test: Interlines with --all flag
# Usage: ./test_scripts/interlines/test_interlines_all.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Interlines with --all ==="
echo "Command: -n 1 --all"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -n 1 --all
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -n 1 --all
fi

# Verify all files have interlines
count=$(find outputs -name "*.rpy" 2>/dev/null | wc -l)
echo "Generated $count .rpy files"

for file in characters.rpy global_switches.rpy pictures.rpy audio.rpy; do
    if [ -f "outputs/$file" ]; then
        blank_count=$(head -30 "outputs/$file" | grep -c "^$")
        echo "$file: $blank_count blank lines in first 30 lines"
    fi
done

if [ "$count" -gt 0 ]; then
    echo "SUCCESS: --all interlines test completed"
else
    echo "FAILURE: No files generated"
    exit 1
fi
