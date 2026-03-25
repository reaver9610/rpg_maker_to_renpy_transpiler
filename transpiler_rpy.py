"""CLI entry point for the RPG Maker MV to Ren'Py transpiler.

Parses command-line arguments to determine input files (single file, multiple
files, directory, or glob pattern), resolves them to a list of .json paths,
and invokes the transpilation pipeline.

Usage:
    python transpiler_rpy.py -f map1.json             # Single file
    python transpiler_rpy.py -m map1.json map2.json   # Multiple files
    python transpiler_rpy.py -d ./maps_directory/      # Directory
    python transpiler_rpy.py -r "Map*.json"             # Glob pattern
    python transpiler_rpy.py -f map1.json -o output/   # Custom output dir
    python transpiler_rpy.py -f map1.json -l            # Multiline dialog

Options:
    -f FILE          Transpile a single file
    -m FILES...      Transpile multiple files (space-separated)
    -d DIRECTORY     Transpile all .json files in a directory
    -r PATTERN       Transpile files matching a glob pattern
    -o OUTPUT_DIR    Output directory for generated .rpy files (default: outputs)
    -l, --multiline  Emit multi-line dialogue as Ren'Py triple-quoted strings
"""

from __future__ import annotations

import argparse
import glob
import os
import sys

from rpgm_transpiler import transpile_to_renpy


def parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments for the transpiler.

    Defines four mutually exclusive input modes:
    - `-f/--file`: Single JSON map file.
    - `-m/--multiple`: Multiple JSON map files (space-separated).
    - `-d/--dir`: All .json files in a directory.
    - `-r/--regex`: Files matching a glob pattern.

    Also accepts `-o/--output` for the output directory (default: "outputs").

    Returns:
        Parsed argument namespace with file/multiple/dir/regex and output attributes.
    """
    argument_parser = argparse.ArgumentParser(
        description="RPG Maker MV → Ren'Py Transpiler",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Mutually exclusive group: exactly one input mode must be specified
    input_mode_group = argument_parser.add_mutually_exclusive_group(required=True)
    input_mode_group.add_argument(
        "-f", "--file", metavar="FILE",
        help="Transpile a single file"
    )
    input_mode_group.add_argument(
        "-m", "--multiple", metavar="FILES", nargs="+",
        help="Transpile multiple files"
    )
    input_mode_group.add_argument(
        "-d", "--dir", metavar="DIRECTORY",
        help="Transpile all .json files in a directory"
    )
    input_mode_group.add_argument(
        "-r", "--regex", metavar="PATTERN",
        help="Transpile files matching a glob pattern (e.g., 'Map*.json')"
    )

    # Output directory option (defaults to "outputs")
    argument_parser.add_argument(
        "-o", "--output", metavar="OUTPUT_DIR",
        default="outputs",
        help="Output directory for generated .rpy files (default: outputs)"
    )

    # Multiline dialog format option
    argument_parser.add_argument(
        "-l", "--multiline",
        action="store_true",
        default=False,
        help="Emit multi-line dialogue as Ren'Py triple-quoted strings"
    )

    return argument_parser.parse_args()


def collect_paths(cli_args: argparse.Namespace) -> list[str]:
    """Resolve CLI arguments to a sorted list of .json file paths.

    Validates that all specified files/directories exist, then expands
    directory and glob inputs into individual file paths. Exits with
    an error message if any input is invalid or no files are found.

    Args:
        cli_args: Parsed argument namespace from parse_args().

    Returns:
        Sorted list of absolute/relative paths to .json map files.

    Raises:
        SystemExit: If any input path is invalid or no files are found.
    """
    resolved_paths: list[str] = []

    # Mode: single file (-f/--file)
    if cli_args.file:
        if not os.path.isfile(cli_args.file):
            print(f"Error: File not found: {cli_args.file}")
            sys.exit(1)
        resolved_paths.append(cli_args.file)

    # Mode: multiple files (-m/--multiple)
    elif cli_args.multiple:
        for file_path in cli_args.multiple:
            if not os.path.isfile(file_path):
                print(f"Error: File not found: {file_path}")
                sys.exit(1)
            resolved_paths.append(file_path)

    # Mode: directory (-d/--dir) — scan for .json files
    elif cli_args.dir:
        if not os.path.isdir(cli_args.dir):
            print(f"Error: Directory not found: {cli_args.dir}")
            sys.exit(1)
        for filename in sorted(os.listdir(cli_args.dir)):
            if filename.endswith(".json"):
                resolved_paths.append(os.path.join(cli_args.dir, filename))

    # Mode: glob pattern (-r/--regex)
    elif cli_args.regex:
        pattern_matches = glob.glob(cli_args.regex)
        if not pattern_matches:
            print(f"Error: No files match pattern: {cli_args.regex}")
            sys.exit(1)
        resolved_paths.extend(sorted(pattern_matches))

    # Ensure at least one file was found
    if not resolved_paths:
        print("No .json files found.")
        sys.exit(1)

    return resolved_paths


def main() -> None:
    """CLI entry point for the RPG Maker MV to Ren'Py transpiler.

    Parses arguments, resolves input paths, and invokes the main
    transpile_to_renpy pipeline.
    """
    cli_args = parse_args()
    resolved_paths = collect_paths(cli_args)
    transpile_to_renpy(resolved_paths, cli_args.output, multiline=cli_args.multiline)


if __name__ == "__main__":
    main()
