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


class CaseAction(argparse.Action):
    """Custom action to handle -c with sub-flags (--lower, --title, --upper)."""

    def __init__(self, option_strings: list[str], dest: str, **kwargs):
        super().__init__(option_strings, dest, nargs=0, **kwargs)

    def __call__(
        self,
        parser: argparse.ArgumentParser,
        namespace: argparse.Namespace,
        values: str | Sequence[Any] | None,
        option_string: str | None = None,
    ):
        """Mark that case mode is specified; actual parsing happens in custom logic."""
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

    # Indent width option
    argument_parser.add_argument(
        "-s", "--indent-width",
        metavar="N",
        type=int,
        default=4,
        help="Number of spaces per indentation level (default: 4)"
    )

    # Case flag - parsed manually for --lower/--title/--upper and their variants
    argument_parser.add_argument(
        "-c", "--case",
        action=CaseAction,
        dest="case_specified",
        help="Character name casing options (--lower, --title, --upper)"
    )

    # Case sub-flags for variable name
    argument_parser.add_argument(
        "--lower",
        action="store_true",
        dest="case_lower",
        default=False,
        help="Use lowercase for variable names (e.g., claire)"
    )
    argument_parser.add_argument(
        "--title",
        action="store_true",
        dest="case_title",
        default=False,
        help="Use title case for variable names (e.g., Claire) [default]"
    )
    argument_parser.add_argument(
        "--upper",
        action="store_true",
        dest="case_upper",
        default=False,
        help="Use uppercase for variable names (e.g., CLAIRE)"
    )

    # Case sub-flags for display name
    argument_parser.add_argument(
        "--lower-display",
        action="store_true",
        dest="case_lower_display",
        default=False,
        help="Use lowercase for display names"
    )
    argument_parser.add_argument(
        "--title-display",
        action="store_true",
        dest="case_title_display",
        default=False,
        help="Use title case for display names [default]"
    )
    argument_parser.add_argument(
        "--upper-display",
        action="store_true",
        dest="case_upper_display",
        default=False,
        help="Use uppercase for display names"
    )

    # Case sub-flags for image tag
    argument_parser.add_argument(
        "--lower-image",
        action="store_true",
        dest="case_lower_image",
        default=False,
        help="Use lowercase for image tags [default]"
    )
    argument_parser.add_argument(
        "--title-image",
        action="store_true",
        dest="case_title_image",
        default=False,
        help="Use title case for image tags"
    )
    argument_parser.add_argument(
        "--upper-image",
        action="store_true",
        dest="case_upper_image",
        default=False,
        help="Use uppercase for image tags"
    )

    # Interlines option (number of blank lines between each output line)
    argument_parser.add_argument(
        "-n", "--interlines",
        metavar="N",
        type=int,
        default=0,
        help="Number of blank lines between each line in output (default: 0)"
    )

    # Interlines target flags (which files to apply interlines to)
    argument_parser.add_argument(
        "--maps",
        action="store_true",
        dest="interlines_maps",
        default=False,
        help="Apply interlines to map files (default when -n is used)"
    )
    argument_parser.add_argument(
        "--characters",
        action="store_true",
        dest="interlines_characters",
        default=False,
        help="Apply interlines to characters.rpy"
    )
    argument_parser.add_argument(
        "--global-switches",
        action="store_true",
        dest="interlines_global_switches",
        default=False,
        help="Apply interlines to global_switches.rpy"
    )
    argument_parser.add_argument(
        "--global-variables",
        action="store_true",
        dest="interlines_global_variables",
        default=False,
        help="Apply interlines to global_variables.rpy"
    )
    argument_parser.add_argument(
        "--global-items",
        action="store_true",
        dest="interlines_global_items",
        default=False,
        help="Apply interlines to global_items.rpy"
    )
    argument_parser.add_argument(
        "--global-economy",
        action="store_true",
        dest="interlines_global_economy",
        default=False,
        help="Apply interlines to global_economy.rpy"
    )
    argument_parser.add_argument(
        "--global-quests",
        action="store_true",
        dest="interlines_global_quests",
        default=False,
        help="Apply interlines to global_quests.rpy"
    )
    argument_parser.add_argument(
        "--side-images",
        action="store_true",
        dest="interlines_side_images",
        default=False,
        help="Apply interlines to side_images.rpy"
    )
    argument_parser.add_argument(
        "--game-flow",
        action="store_true",
        dest="interlines_game_flow",
        default=False,
        help="Apply interlines to game_flow.rpy"
    )
    argument_parser.add_argument(
        "--all",
        action="store_true",
        dest="interlines_all",
        default=False,
        help="Apply interlines to all output files"
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

    # Build interlines_targets set based on flags
    # If --all is specified, apply to all files
    # If no specific flags but -n is used, default to maps only
    # If specific flags are used, apply only to those targets
    interlines_targets: set[str] = set()
        
    if getattr(args, "interlines_all", False):
        # --all: apply to all file types
        interlines_targets = {
            "maps", "characters", "global_switches", "global_variables",
            "global_items", "global_economy", "global_quests",
            "side_images", "game_flow",
        }
    elif args.interlines > 0:
        # -n was used, check for specific targets
        if (getattr(args, "interlines_maps", False) or
            getattr(args, "interlines_characters", False) or
            getattr(args, "interlines_global_switches", False) or
            getattr(args, "interlines_global_variables", False) or
            getattr(args, "interlines_global_items", False) or
            getattr(args, "interlines_global_economy", False) or
            getattr(args, "interlines_global_quests", False) or
            getattr(args, "interlines_side_images", False) or
            getattr(args, "interlines_game_flow", False)):
            # Specific targets specified, use those
            if getattr(args, "interlines_maps", False):
                interlines_targets.add("maps")
            if getattr(args, "interlines_characters", False):
                interlines_targets.add("characters")
            if getattr(args, "interlines_global_switches", False):
                interlines_targets.add("global_switches")
            if getattr(args, "interlines_global_variables", False):
                interlines_targets.add("global_variables")
            if getattr(args, "interlines_global_items", False):
                interlines_targets.add("global_items")
            if getattr(args, "interlines_global_economy", False):
                interlines_targets.add("global_economy")
            if getattr(args, "interlines_global_quests", False):
                interlines_targets.add("global_quests")
            if getattr(args, "interlines_side_images", False):
                interlines_targets.add("side_images")
            if getattr(args, "interlines_game_flow", False):
                interlines_targets.add("game_flow")
        else:
            # No specific targets, default to maps only
            interlines_targets = {"maps"}
    
    args.interlines_targets = interlines_targets

    # Build case_mode dictionary based on flags
    # Determine variable name case
    var_case = "title"  # default
    if args.case_lower:
        var_case = "lower"
    elif args.case_upper:
        var_case = "upper"
    # args.case_title is default, no need to check

    # Determine display name case
    display_case = "title"  # default
    if args.case_lower_display:
        display_case = "lower"
    elif args.case_upper_display:
        display_case = "upper"
    # args.case_title_display is default, no need to check

    # Determine image tag case
    image_case = "lower"  # default
    if args.case_title_image:
        image_case = "title"
    elif args.case_upper_image:
        image_case = "upper"
    # args.case_lower_image is default, no need to check

    # Build the case_mode dict
    args.case_mode = {
        "var": var_case,
        "display": display_case,
        "image": image_case,
    }

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

    # Validate indent_width
    if cli_args.indent_width < 1:
        print("Error: indent width must be at least 1")
        sys.exit(1)

    resolved_paths = collect_paths(cli_args)
    transpile_to_renpy(
        resolved_paths,
        cli_args.output,
        multiline=cli_args.multiline,
        interlines=cli_args.interlines,
        interlines_targets=cli_args.interlines_targets,
        indent_width=cli_args.indent_width,
        case_mode=cli_args.case_mode,
    )


if __name__ == "__main__":
    main()
