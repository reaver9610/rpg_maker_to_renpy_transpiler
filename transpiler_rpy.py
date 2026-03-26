"""CLI entry point for the RPG Maker MV to Ren'Py transpiler.

Parses command-line arguments to determine input files (single file, multiple
files, directory, or glob pattern), resolves them to a list of .json paths,
and invokes the transpilation pipeline.

Usage:
    python transpiler_rpy.py -i --file map1.json              # Single file
    python transpiler_rpy.py -i --multiple map1.json map2.json # Multiple files
    python transpiler_rpy.py -i --directory ./maps_directory/  # Directory
    python transpiler_rpy.py -i --regex "Map*.json"            # Glob pattern
    python transpiler_rpy.py -i --file map1.json -o output/     # Custom output dir
    python transpiler_rpy.py -i --file map1.json -f --multiline # Multiline format

Options:
    -i --file FILE          Transpile a single file
    -i --multiple FILES...  Transpile multiple files (space-separated)
    -i --directory DIR      Transpile all .json files in a directory
    -i --regex PATTERN      Transpile files matching a glob pattern
    -o OUTPUT_DIR           Output directory for generated .rpy files (default: outputs)
    -f --single             Emit single-line dialogue (default)
    -f --multiline          Emit multi-line dialogue as Ren'Py triple-quoted strings
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from collections.abc import Sequence
from typing import Any

from rpgm_transpiler import transpile_to_renpy


class InputAction(argparse.Action):
    """Custom action to handle -i with sub-flags (--file, --multiple, --directory, --regex).

    This action intercepts -i/--input and the following argument to dispatch
    to the appropriate input mode subcommand.
    """

    INPUT_MODES = {
        "--file": "file",
        "-file": "file",
        "--multiple": "multiple",
        "-multiple": "multiple",
        "--directory": "directory",
        "-directory": "directory",
        "--regex": "regex",
        "-regex": "regex",
    }

    def __init__(self, option_strings: list[str], dest: str, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ):
        """Mark that input mode is required; actual parsing happens in custom logic."""
        setattr(namespace, self.dest, True)


class FormatAction(argparse.Action):
    """Custom action to handle -f with sub-flags (--single, --multiline)."""

    def __init__(self, option_strings: list[str], dest: str, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ):
        """Mark that format mode is specified; actual parsing happens in custom logic."""
        setattr(namespace, self.dest, True)


def parse_args() -> argparse.Namespace:
    """Parse and return CLI arguments for the transpiler.

    Uses custom parsing logic to handle nested sub-flags:
    - `-i --file`, `-i --multiple`, `-i --directory`, `-i --regex` for input sources
    - `-f --single`, `-f --multiline` for format options

    Returns:
        Parsed argument namespace with input_mode, input_value, output,
        and multiline attributes.
    """
    argument_parser = argparse.ArgumentParser(
        description="RPG Maker MV → Ren'Py Transpiler",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        usage=(
            "rpgm-transpile -i (--file FILE | --multiple FILES... | --directory DIR | --regex PATTERN)\n"
            " [-o OUTPUT_DIR] [-n N] [-f (--single | --multiline)]"
        ),
    )

    # Input flag - required marker, actual sub-flag parsed manually
    argument_parser.add_argument(
        "-i", "--input",
        action=InputAction,
        dest="input_required",
        help="Input source (required) - use with --file, --multiple, --directory, or --regex"
    )

    # Register input sub-flags as optional arguments (parsed manually)
    argument_parser.add_argument(
        "--file", "-file",
        metavar="FILE",
        dest="file",
        help="Transpile a single file (use with -i)"
    )
    argument_parser.add_argument(
        "--multiple", "-multiple",
        metavar="FILES",
        nargs="+",
        dest="multiple",
        help="Transpile multiple files (use with -i)"
    )
    argument_parser.add_argument(
        "--directory", "-directory",
        metavar="DIR",
        dest="directory",
        help="Transpile all .json files in a directory (use with -i)"
    )
    argument_parser.add_argument(
        "--regex", "-regex",
        metavar="PATTERN",
        dest="regex",
        help="Transpile files matching a glob pattern (use with -i)"
    )

    # Output directory option (defaults to "outputs")
    argument_parser.add_argument(
        "-o", "--output",
        metavar="OUTPUT_DIR",
        default="outputs",
        help="Output directory for generated .rpy files (default: outputs)"
    )

    # Interlines option (number of blank lines between each output line)
    argument_parser.add_argument(
        "-n", "--interlines",
        metavar="N",
        type=int,
        default=0,
        help="Number of blank lines between each line in output (default: 0)"
    )

    # Format flag - parsed manually for --single/--multiline sub-options
    argument_parser.add_argument(
        "-f", "--format",
        action=FormatAction,
        dest="format_specified",
        help="Format options (--single or --multiline)"
    )

    # Format sub-flags (parsed manually)
    argument_parser.add_argument(
        "--single",
        action="store_true",
        dest="single",
        default=False,
        help="Emit single-line dialogue (default)"
    )
    argument_parser.add_argument(
        "--multiline",
        action="store_true",
        dest="multiline",
        default=False,
        help="Emit multi-line dialogue as Ren'Py triple-quoted strings"
    )

    # Parse arguments
    args = argument_parser.parse_args()

    # Validate input mode requirements
    if not getattr(args, "input_required", False):
        argument_parser.error("Input source is required. Use -i with --file, --multiple, --directory, or --regex.")

    # Count how many input modes were specified
    input_modes = [
        args.file is not None,
        args.multiple is not None,
        args.directory is not None,
        args.regex is not None,
    ]
    input_mode_count = sum(input_modes)

    if input_mode_count == 0:
        argument_parser.error(
            "No input source specified after -i. Use --file, --multiple, --directory, or --regex."
        )
    elif input_mode_count > 1:
        argument_parser.error(
            "Only one input source can be specified: --file, --multiple, --directory, or --regex."
        )

    # Validate format sub-options
    format_specified = getattr(args, "format_specified", False)
    if args.single and args.multiline:
        argument_parser.error("Cannot specify both --single and --multiline together.")

    # Determine multiline setting (default: single-line)
    args.multiline = args.multiline if (format_specified and args.multiline) else False

    return args


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

    # Mode: single file (--file)
    if cli_args.file:
        if not os.path.isfile(cli_args.file):
            print(f"Error: File not found: {cli_args.file}")
            sys.exit(1)
        resolved_paths.append(cli_args.file)

    # Mode: multiple files (--multiple)
    elif cli_args.multiple:
        for file_path in cli_args.multiple:
            if not os.path.isfile(file_path):
                print(f"Error: File not found: {file_path}")
                sys.exit(1)
            resolved_paths.append(file_path)

    # Mode: directory (--directory) — scan for .json files
    elif cli_args.directory:
        if not os.path.isdir(cli_args.directory):
            print(f"Error: Directory not found: {cli_args.directory}")
            sys.exit(1)
        # Files to exclude from map processing (not map JSON files)
        excluded_files = {"MapInfos.json", "System.json"}
        for filename in sorted(os.listdir(cli_args.directory)):
            if filename.endswith(".json") and filename not in excluded_files:
                resolved_paths.append(os.path.join(cli_args.directory, filename))

    # Mode: glob pattern (--regex)
    elif cli_args.regex:
        pattern_matches = glob.glob(cli_args.regex)
        if not pattern_matches:
            print(f"Error: No files match pattern: {cli_args.regex}")
            sys.exit(1)
        # Files to exclude from map processing (not map JSON files)
        excluded_files = {"MapInfos.json", "System.json"}
        resolved_paths.extend(sorted([p for p in pattern_matches if os.path.basename(p) not in excluded_files]))

    # Ensure at least one file was found
    if not resolved_paths:
        print("No .json files found.")
        sys.exit(1)

    return resolved_paths


def main() -> None:
    """CLI entry point for the RPG Maker MV to Ren\'Py transpiler.

    Parses arguments, resolves input paths, and invokes the main
    transpile_to_renpy pipeline.
    """
    cli_args = parse_args()
    resolved_paths = collect_paths(cli_args)
    transpile_to_renpy(
        resolved_paths, cli_args.output, multiline=cli_args.multiline, interlines=cli_args.interlines
    )


if __name__ == "__main__":
    main()
