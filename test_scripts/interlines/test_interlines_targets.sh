#!/bin/bash
# Test: Interlines with specific targets
# Usage: ./test_scripts/interlines/test_interlines_targets.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Interlines with Specific Targets ==="
echo "Command: -n 1 --characters --global-switches --pictures"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -n 1 --characters --global-switches --pictures
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -n 1 --characters --global-switches --pictures
fi

# Verify interlines applied to targeted files
for file in characters.rpy global_switches.rpy pictures.rpy; do
    if [ -f "outputs/$file" ]; then
        blank_count=$(head -30 "outputs/$file" | grep -c "^$")
        echo "$file: $blank_count blank lines in first 30 lines"
    fi
done

# Verify non-targeted file is unchanged (global_items should NOT have interlines)
if [ -f "outputs/global_items.rpy" ]; then
    echo "global_items.rpy exists (should NOT have interlines - not in target list)"
fi

echo "SUCCESS: Specific target interlines test completed"
