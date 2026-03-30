#!/bin/bash
# Test: Default case (title case for variables, lowercase for images)
# Usage: ./test_scripts/case/test_case_default.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Default Case Mode ==="
echo "Command: (no -c flag)"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/
fi

# Check character case
if [ -f "outputs/characters.rpy" ]; then
    echo "--- Character definitions (expect title case names) ---"
    grep "^define " outputs/characters.rpy | head -5
fi

# Check side image case
if [ -f "outputs/side_images.rpy" ]; then
    echo "--- Side image tags (expect lowercase) ---"
    grep "^image side " outputs/side_images.rpy | head -5
fi

echo "SUCCESS: Default case test completed"
