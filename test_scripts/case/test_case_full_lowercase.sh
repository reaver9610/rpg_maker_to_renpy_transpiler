#!/bin/bash
# Test: Full lowercase (-c --lower --lower-display --lower-image)
# Usage: ./test_scripts/case/test_case_full_lowercase.sh [--global]

set -e

USE_GLOBAL=${1:-""}

echo "=== Test: Full Lowercase Mode ==="
echo "Command: -c --lower --lower-display --lower-image"

# Clean previous output
rm -rf outputs/*.rpy outputs/*/ 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -c --lower --lower-display --lower-image
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -c --lower --lower-display --lower-image
fi

# Check all cases
if [ -f "outputs/characters.rpy" ]; then
    echo "--- Character definitions (expect all lowercase) ---"
    grep "^define " outputs/characters.rpy | head -5
fi

if [ -f "outputs/side_images.rpy" ]; then
    echo "--- Side image tags (expect all lowercase) ---"
    grep "^image side " outputs/side_images.rpy | head -5
fi

echo "SUCCESS: Full lowercase case test completed"
