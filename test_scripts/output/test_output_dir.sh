#!/bin/bash
# Test: Custom output directory (-o)
# Usage: ./test_scripts/output/test_output_dir.sh [--global]

set -e

USE_GLOBAL=${1:-""}

CUSTOM_DIR="outputs/custom_output_test"

echo "=== Test: Custom Output Directory ==="
echo "Command: -o $CUSTOM_DIR"

# Clean previous output
rm -rf "$CUSTOM_DIR" 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -o "$CUSTOM_DIR"
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -o "$CUSTOM_DIR"
fi

# Verify output in custom directory
count=$(find "$CUSTOM_DIR" -name "*.rpy" 2>/dev/null | wc -l)
if [ "$count" -gt 0 ]; then
    echo "SUCCESS: Generated $count .rpy file(s) in $CUSTOM_DIR"
    ls -la "$CUSTOM_DIR"/*.rpy 2>/dev/null | head -5
    # Cleanup
    rm -rf "$CUSTOM_DIR"
else
    echo "FAILURE: No files generated in custom directory"
    exit 1
fi
