# transpiler_rpy.py
"""
RPG Maker MV → Ren'Py Transpiler

Converts RPG Maker MV JSON map files to Ren'Py .rpy scripts.
Focus: dialogue, choices, conditional branches, switches, variables.

Usage:
    python transpiler_rpy.py map1.json [map2.json ...]
    python transpiler_rpy.py ./maps_directory/
    python transpiler_rpy.py -f map1.json
    python transpiler_rpy.py -m map1.json map2.json
    python transpiler_rpy.py -d ./maps_directory/
    python transpiler_rpy.py -r "Map*.json"
    [-o OUTPUT_DIR | --output OUTPUT_DIR]

Options:
    -o OUTPUT_DIR, --output OUTPUT_DIR  Output directory for generated .rpy files (default: outputs)
"""

import argparse
import glob
import os
import sys

from rpgm_transpiler import transpile_to_renpy


def parse_args():
    parser = argparse.ArgumentParser(
        description="RPG Maker MV → Ren'Py Transpiler",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "-f", "--file", metavar="FILE",
        help="Transpile a single file"
    )
    group.add_argument(
        "-m", "--multiple", metavar="FILES", nargs="+",
        help="Transpile multiple files"
    )
    group.add_argument(
        "-d", "--dir", metavar="DIRECTORY",
        help="Transpile all .json files in a directory"
    )
    group.add_argument(
        "-r", "--regex", metavar="PATTERN",
        help="Transpile files matching a glob pattern (e.g., 'Map*.json')"
    )
    
    parser.add_argument(
        "-o", "--output", metavar="OUTPUT_DIR",
        default="outputs",
        help="Output directory for generated .rpy files (default: outputs)"
    )

    return parser.parse_args()


def collect_paths(args) -> list[str]:
    paths = []

    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        paths.append(args.file)

    elif args.multiple:
        for f in args.multiple:
            if not os.path.isfile(f):
                print(f"Error: File not found: {f}")
                sys.exit(1)
            paths.append(f)

    elif args.dir:
        if not os.path.isdir(args.dir):
            print(f"Error: Directory not found: {args.dir}")
            sys.exit(1)
        for fname in sorted(os.listdir(args.dir)):
            if fname.endswith(".json"):
                paths.append(os.path.join(args.dir, fname))

    elif args.regex:
        pattern_matches = glob.glob(args.regex)
        if not pattern_matches:
            print(f"Error: No files match pattern: {args.regex}")
            sys.exit(1)
        paths.extend(sorted(pattern_matches))

    if not paths:
        print("No .json files found.")
        sys.exit(1)

    return paths


def main():
    args = parse_args()
    paths = collect_paths(args)
    transpile_to_renpy(paths, args.output)


if __name__ == "__main__":
    main()
