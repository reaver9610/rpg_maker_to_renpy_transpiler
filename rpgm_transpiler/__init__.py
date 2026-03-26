"""RPG Maker MV to Ren'Py Transpiler.

This module orchestrates the full transpilation pipeline: loads RPG Maker MV JSON map
files, runs a data collection pass, then generates Ren'Py .rpy script files for
characters, switches/variables, map events, and game flow navigation.

Architecture Overview:
The transpiler uses a two-pass approach:

Pass 1 (Collection):
The DataCollector scans all map JSON to discover:
- Character names and face IDs (for Character definitions and side images)
- Switch IDs (for game state initialization)
- Variable IDs (for game state initialization)
- Self-switch keys (for event-local state)
- Item IDs (for inventory tracking)
- Map transfer targets (for navigation structure)

Pass 2 (Generation):
Multiple generators produce output files:
- characters.rpy: Character() definitions with colors and image tags
- switches.rpy: Default game state values
- side_images.rpy: Side image declarations
- map_{id}_*.rpy: Event handlers for each map
- game_flow.rpy: Navigation labels and entry points

Public API:
    transpile_to_renpy: Main entry point that processes input files and writes output.

    DataCollector: First-pass scanner that collects all referenced game state.

    RenPyGenerator: Converts a single map's events to Ren'Py script.

    generate_characters_rpy: Produces characters.rpy with Character definitions.

    generate_switches_rpy: Produces switches.rpy with default state values.

    generate_game_flow_rpy: Produces game_flow.rpy with map navigation labels.

    generate_side_images_rpy: Produces side_images.rpy with side image declarations.

Usage Example:
    >>> from rpgm_transpiler import transpile_to_renpy
    >>> transpile_to_renpy(["inputs/Map001.json", "inputs/Map002.json"], "outputs/")

Command Line Usage:
    $ rpgm-transpile -d inputs/ -o outputs/
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .collector import DataCollector
from .generator import RenPyGenerator
from .characters import generate_characters_rpy
from .switches import generate_switches_rpy
from .game_flow import generate_game_flow_rpy
from .side_images import generate_side_images_rpy


__all__ = [
    "transpile_to_renpy",
    "DataCollector",
    "RenPyGenerator",
    "generate_characters_rpy",
    "generate_side_images_rpy",
    "generate_switches_rpy",
    "generate_game_flow_rpy",
]


def transpile_to_renpy(
    input_paths: list[str],
    output_dir: str = "outputs",
    multiline: bool = False,
    interlines: int = 0,
) -> None:
    """Transpile one or more RPG Maker MV JSON maps to Ren'Py .rpy scripts.

    This is the main entry point for the transpiler. It runs the full pipeline:
    loading JSON files, collecting game state references, and generating all
    output files.

    Pipeline Phases:
    1. Load and parse each JSON map file
    2. Extract map ID from the filename (e.g., "Map001.json" → 1)
    3. Run the data collector to discover all characters, switches, etc.
    4. Generate characters.rpy (Character definitions)
    5. Generate switches.rpy (default game state values)
    6. Generate side_images.rpy (side image declarations per face ID)
    7. Generate a .rpy file for each map's events
    8. Generate game_flow.rpy (map navigation labels)

    Output Files:
    For input maps Map001.json and Map002.json with display names "Town" and "Forest":
    - outputs/characters.rpy: Character definitions
    - outputs/switches.rpy: Game state initialization
    - outputs/side_images.rpy: Side image declarations
    - outputs/map_1_town.rpy: Town events
    - outputs/map_2_forest.rpy: Forest events
    - outputs/game_flow.rpy: Navigation structure

    Args:
        input_paths: List of filesystem paths to RPG Maker MV .json map files.
        Each file should be a valid RPG Maker MV map export (Map*.json).
        output_dir: Directory to write generated .rpy files.
        Created if it doesn't exist. Defaults to "outputs".
        multiline: If True, emit multi-line dialogue as Ren'Py triple-quoted strings.
        If False (default), concatenate TEXT_LINE commands into single lines.
        interlines: Number of blank lines to insert between each line in the output.
        Default 0 means no extra spacing. Use 1 for single blank line between lines, etc.

    Example:
        >>> transpile_to_renpy(["inputs/Map001.json"], "renpy_output/")
        [INFO] Collected from 1 maps:
         3 characters
         5 switches
         2 variables
         1 self-switches

        [OK] renpy_output/characters.rpy
        [OK] renpy_output/switches.rpy
        [OK] renpy_output/side_images.rpy
        [OK] renpy_output/map_1_town.rpy
        [OK] renpy_output/game_flow.rpy

        [DONE] Transpiled 1 maps to renpy_output/

    Note:
        Map IDs are extracted from filenames. The pattern matches digits
        in the filename (e.g., "Map001.json" → 1, "Map123.json" → 123).
        If no digits are found, maps are numbered sequentially.

    Note:
        All output files are written with UTF-8 encoding to support
        international characters in dialogue text.

    Raises:
        FileNotFoundError: If any input file doesn't exist.
        json.JSONDecodeError: If any input file isn't valid JSON.
        OSError: If output directory can't be created or files can't be written.
    """
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 0: Setup
    # ═══════════════════════════════════════════════════════════════════
    
    # Ensure the output directory exists
    # exist_ok=True means no error if the directory already exists
    os.makedirs(output_dir, exist_ok=True)

    # Initialize storage for parsed map data
    # Key: map_id (int), Value: parsed JSON dict
    all_map_data: dict[int, dict] = {}
    
    # Create the shared data collector
    # This will accumulate references from all maps
    collector = DataCollector()
    
    # ═══════════════════════════════════════════════════════════════════
    # PHASE 0b: Load System.json if available
    # ═══════════════════════════════════════════════════════════════════
    
    # Check for System.json in the same directory as the first input file
    # System.json contains switch/variable names for human-readable output
    if input_paths:
        # Get the directory of the first input file
        input_dir = os.path.dirname(input_paths[0]) or "."
        system_json_path = os.path.join(input_dir, "System.json")
        
        # Check if System.json exists
        if os.path.exists(system_json_path):
            try:
                with open(system_json_path, "r", encoding="utf-8") as system_file:
                    collector.system_data = json.load(system_file)
                print(f"[INFO] Loaded System.json for switch/variable name resolution")
            except (json.JSONDecodeError, OSError) as e:
                print(f"[WARN] Could not load System.json: {e}")
        else:
            # Also check in the workspace root if input_dir is different
            root_system_path = os.path.join(".", "System.json")
            if root_system_path != system_json_path and os.path.exists(root_system_path):
                try:
                    with open(root_system_path, "r", encoding="utf-8") as system_file:
                        collector.system_data = json.load(system_file)
                    print(f"[INFO] Loaded System.json for switch/variable name resolution")
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[WARN] Could not load System.json: {e}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 1: Load JSON files and run data collection
    # ═══════════════════════════════════════════════════════════════════
    
    for file_path in input_paths:
        # Open and parse the JSON file
        # UTF-8 encoding ensures international characters are handled correctly
        with open(file_path, "r", encoding="utf-8") as json_file:
            parsed_map_data = json.load(json_file)

        # Extract the numeric map ID from the filename
        # RPG Maker uses the pattern "Map{ID}.json" (e.g., "Map001.json")
        # We use a regex to extract the digits
        filename_stem = Path(file_path).stem  # "Map001" from "Map001.json"
        map_id_match = re.search(r"(\d+)", filename_stem)  # Match digits
        
        # Determine the map ID
        if map_id_match:
            # Extract digits from filename: "Map001" → 1
            map_id = int(map_id_match.group(1))
        else:
            # Fallback: use sequential numbering if no digits found
            # This handles edge cases like custom filename formats
            map_id = len(all_map_data) + 1

        # Store the parsed map data for later use
        all_map_data[map_id] = parsed_map_data
        
        # Run the collection pass on this map
        # This discovers all characters, switches, variables, etc.
        collector.collect_from_map(parsed_map_data, map_id)

    # ── Log collection summary ──
    # Provide feedback about what was discovered
    print(f"[INFO] Collected from {len(all_map_data)} maps:")
    print(f"    {len(collector.characters)} characters")
    print(f"    {len(collector.switch_ids)} switches")
    print(f"    {len(collector.variable_ids)} variables")
    print(f"    {len(collector.self_switches)} self-switches")
    print()

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Generate characters.rpy
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the character definitions
    character_definitions = generate_characters_rpy(collector, interlines=interlines)
    
    # Build the output file path
    characters_path = os.path.join(output_dir, "characters.rpy")
    
    # Write the file
    with open(characters_path, "w", encoding="utf-8") as output_file:
        output_file.write(character_definitions)
    
    # Log success
    print(f"[OK] {characters_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3: Generate switches.rpy (default game state)
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the switch/variable definitions
    switch_definitions = generate_switches_rpy(collector, interlines=interlines)
    
    # Build the output file path
    switches_path = os.path.join(output_dir, "switches.rpy")
    
    # Write the file
    with open(switches_path, "w", encoding="utf-8") as output_file:
        output_file.write(switch_definitions)
    
    # Log success
    print(f"[OK] {switches_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Generate side_images.rpy (side image declarations)
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the side image declarations
    side_images_definitions = generate_side_images_rpy(collector, interlines=interlines)
    
    # Build the output file path
    side_images_path = os.path.join(output_dir, "side_images.rpy")
    
    # Write the file
    with open(side_images_path, "w", encoding="utf-8") as output_file:
        output_file.write(side_images_definitions)
    
    # Log success
    print(f"[OK] {side_images_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: Generate a .rpy file for each map's events
    # ═══════════════════════════════════════════════════════════════════
    
    # Process maps in sorted order for consistent output
    for map_id, map_data in sorted(all_map_data.items()):
        # Create a generator instance for this map
        # The generator needs:
        # - map_data: The parsed JSON for this map
        # - collector: The shared collector with all discovered data
        # - map_id: The numeric ID of this map
        # - all_map_data: All maps (for cross-map transfer references)
        # - multiline: Whether to emit triple-quoted strings
        # - interlines: Number of blank lines between output lines
        generator = RenPyGenerator(
            map_data, collector, map_id, all_map_data, multiline=multiline, interlines=interlines
        )
        
        # Generate the Ren'Py source
        map_script_source = generator.generate()

        # Build the output filename
        # Format: map_{id}_{sanitized_display_name}.rpy
        # The display name provides context for humans reading the file
        map_display_name = map_data.get("display_name", f"map_{map_id}")
        
        # Sanitize the display name for use in a filename
        # Replace non-alphanumeric characters with underscores
        safe_filename = re.sub(r"[^a-z0-9_]", "_", map_display_name.lower())
        
        # Build the full filename
        output_filename = f"map_{map_id}_{safe_filename}.rpy"
        
        # Build the full output path
        output_path = os.path.join(output_dir, output_filename)

        # Write the file
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(map_script_source)
        
        # Log success
        print(f"[OK] {output_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Generate game_flow.rpy (navigation labels)
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the game flow navigation
    game_flow_source = generate_game_flow_rpy(all_map_data, collector, interlines=interlines)
    
    # Build the output file path
    game_flow_path = os.path.join(output_dir, "game_flow.rpy")
    
    # Write the file
    with open(game_flow_path, "w", encoding="utf-8") as output_file:
        output_file.write(game_flow_source)
    
    # Log success
    print(f"[OK] {game_flow_path}")

    # ═══════════════════════════════════════════════════════════════════
    # COMPLETION
    # ═══════════════════════════════════════════════════════════════════
    
    # Log completion summary
    print(f"\n[DONE] Transpiled {len(all_map_data)} maps to {output_dir}/")
