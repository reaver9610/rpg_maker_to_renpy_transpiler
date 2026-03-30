#!/bin/bash
# Test: Combined options (multiline + custom output + interlines)
# Usage: ./test_scripts/combined/test_multiline_output.sh [--global]

set -e

USE_GLOBAL=${1:-""}

CUSTOM_DIR="outputs/combined_test"

echo "=== Test: Combined Options ==="
echo "Command: -f --multiline -o $CUSTOM_DIR -n 1 --all"

# Clean previous output
rm -rf "$CUSTOM_DIR" 2>/dev/null || true

if [ "$USE_GLOBAL" = "--global" ]; then
    rpgm-transpile -i --directory inputs/ -f --multiline -o "$CUSTOM_DIR" -n 1 --all
else
    PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/ -f --multiline -o "$CUSTOM_DIR" -n 1 --all
fi

# Verify output
count=$(find "$CUSTOM_DIR" -name "*.rpy" 2>/dev/null | wc -l)
echo "Generated $count .rpy files in $CUSTOM_DIR"

# Check multiline format
event_file=$(find "$CUSTOM_DIR" -name "*event*.rpy" -type f | head -1)
if [ -n "$event_file" ] && grep -q '"""' "$event_file"; then
    echo "SUCCESS: Multiline format applied"
else
    echo "WARNING: No triple-quoted strings found"
fi

# Cleanup
rm -rf "$CUSTOM_DIR"
echo "SUCCESS: Combined options test completed"
