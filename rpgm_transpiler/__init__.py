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
- Self-switch keys (for event-local state, grouped by map)
- Item IDs (for inventory tracking)
- Map transfer targets (for navigation structure)

Pass 2 (Generation):
Multiple generators produce output files using Ren'Py named stores:
- characters.rpy: Character() definitions with colors and image tags
- global_switches.rpy: Global switches in the game_switch store
- global_variables.rpy: Global variables in the game_vars store
- global_items.rpy: Item inventory in the game_items store
- global_economy.rpy: Player currency in the game_economy store
- global_quests.rpy: Quest tracking in the game_quest store
- side_images.rpy: Side image declarations
- map_{id}_{Name}.rpy: Map placeholder (global label + autorun calls)
- map_{id}_{Name}_event_{id}_{name}.rpy: One per autorun/regular event (local labels)
    - game_flow.rpy: Start entry point

    Output Examples:
    - maps/.../map_1_Town.rpy: Map placeholder (global label + autorun calls)
    - maps/.../map_1_Town_events/map_1_Town_event_3_intro.rpy: One per autorun event (local labels)
    - maps/.../map_1_Town_events/map_1_Town_event_11_shopkeeper.rpy: One per regular event (local labels)

Public API:
    transpile_to_renpy: Main entry point that processes input files and writes output.

    DataCollector: First-pass scanner that collects all referenced game state.

    RenPyGenerator: Converts a single map's events to Ren'Py script.

    generate_characters_rpy: Produces characters.rpy with Character definitions.

    generate_global_switches_rpy: Produces global_switches.rpy with switch declarations.

    generate_global_variables_rpy: Produces global_variables.rpy with variable declarations.

    generate_global_items_rpy: Produces global_items.rpy with item declarations.

    generate_global_economy_rpy: Produces global_economy.rpy with gold declaration.

    generate_global_quests_rpy: Produces global_quests.rpy with quest log declaration.

    generate_map_switches_rpy: Produces per-map self-switch declaration files.

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
from .generator import RenPyGenerator, MapGenerationResult
from .characters import generate_characters_rpy
from .switches import (
    generate_global_switches_rpy,
    generate_global_variables_rpy,
    generate_global_items_rpy,
    generate_global_economy_rpy,
    generate_global_quests_rpy,
    generate_map_switches_rpy,
    generate_event_switches_rpy,
)
from .game_flow import generate_game_flow_rpy
from .side_images import generate_side_images_rpy
from .helpers import to_title_case, safe_map_label

__all__ = [
    "transpile_to_renpy",
    "DataCollector",
    "RenPyGenerator",
    "MapGenerationResult",
    "generate_characters_rpy",
    "generate_side_images_rpy",
    "generate_global_switches_rpy",
    "generate_global_variables_rpy",
    "generate_global_items_rpy",
    "generate_global_economy_rpy",
    "generate_global_quests_rpy",
    "generate_map_switches_rpy",
    "generate_event_switches_rpy",
    "generate_game_flow_rpy",
]


def transpile_to_renpy(
    input_paths: list[str],
    output_dir: str = "outputs",
    multiline: bool = False,
    interlines: int = 0,
    interlines_targets: set[str] | None = None,
    indent_width: int = 4,
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
    5. Generate global_switches.rpy (game_switch store declarations)
    6. Generate global_variables.rpy (game_vars store declarations)
    7. Generate global_items.rpy (game_items store declarations)
    8. Generate global_economy.rpy (game_economy store: gold)
    9. Generate global_quests.rpy (game_quest store: quest_log)
    10. Generate side_images.rpy (side image declarations per face ID)
    11. Generate per-map files (placeholder, autorun, events, switches)
    12. Generate game_flow.rpy (start entry point)

    Output Files:
    For input maps Map001.json and Map002.json with display names "Town" and "Forest":
    - outputs/characters.rpy: Character definitions
    - outputs/global_switches.rpy: game_switch store declarations
    - outputs/global_variables.rpy: game_vars store declarations
    - outputs/global_items.rpy: game_items store declarations
    - outputs/global_economy.rpy: game_economy store (gold)
    - outputs/global_quests.rpy: game_quest store (quest_log)
    - outputs/side_images.rpy: Side image declarations
    - outputs/maps/.../map_1_Town.rpy: Map placeholder (label map_1_Town:)
    - outputs/maps/.../map_1_Town_event_3_intro.rpy: Autorun event (local label)
    - outputs/maps/.../map_1_Town_event_11_shopkeeper.rpy: Regular event (local label)
    - outputs/maps/.../map_1_Town_switches.rpy: Town self-switches
    - outputs/game_flow.rpy: Start entry point

    Args:
        input_paths: List of filesystem paths to RPG Maker MV .json map files.
        Each file should be a valid RPG Maker MV map export (Map*.json).
        output_dir: Directory to write generated .rpy files.
        Created if it doesn't exist. Defaults to "outputs".
        multiline: If True, emit multi-line dialogue as Ren'Py triple-quoted strings.
        If False (default), concatenate TEXT_LINE commands into single lines.
        interlines: Number of blank lines to insert between each line in the output.
        Default 0 means no extra spacing. Use 1 for single blank line between lines, etc.
        interlines_targets: Set of file types to apply interlines to.
        Valid values: "maps", "characters", "global_switches", "global_variables",
        "global_items", "global_economy", "global_quests", "side_images", "game_flow".
        If None and interlines > 0, defaults to {"maps"}.
        If interlines == 0, this parameter is ignored.
        indent_width: Number of spaces per indentation level. Default is 4.

    Example:
        >>> transpile_to_renpy(["inputs/Map001.json"], "renpy_output/")
        [INFO] Collected from 1 maps:
         3 characters
         5 switches
         2 variables
         1 maps with self-switches

        [OK] renpy_output/characters.rpy
        [OK] renpy_output/global_switches.rpy
        [OK] renpy_output/global_variables.rpy
        [OK] renpy_output/global_items.rpy
        [OK] renpy_output/global_economy.rpy
        [OK] renpy_output/global_quests.rpy
        [OK] renpy_output/side_images.rpy
        [OK] renpy_output/maps/map_1_Town/map_1_Town.rpy
        [OK] renpy_output/maps/map_1_Town/map_1_Town_event_3_intro.rpy
        [OK] renpy_output/maps/map_1_Town/map_1_Town_event_11.rpy
        [OK] renpy_output/maps/map_1_Town/map_1_Town_switches.rpy
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

    # Set default interlines_targets if not specified
    # Default: apply interlines to maps only
    if interlines_targets is None:
        interlines_targets = {"maps"} if interlines > 0 else set()
    
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
    # PHASE 0c: Load MapInfos.json if available
    # ═══════════════════════════════════════════════════════════════════
    
    # MapInfos.json contains map hierarchy information (parent-child relationships)
    # This is used to create a hierarchical folder structure for map files
    map_infos: dict[int, dict] = {}  # map_id -> {name, parentId, order}
    map_folder_paths: dict[int, str] = {}  # map_id -> folder path
    
    # Check for MapInfos.json in the same directory as the first input file
    if input_paths:
        input_dir = os.path.dirname(input_paths[0]) or "."
        map_infos_path = os.path.join(input_dir, "MapInfos.json")
        
        # Check if MapInfos.json exists
        if os.path.exists(map_infos_path):
            try:
                with open(map_infos_path, "r", encoding="utf-8") as map_infos_file:
                    map_infos_list = json.load(map_infos_file)
                    # Convert list to dictionary with map_id as key
                    # MapInfos.json is a sparse array where index = map_id
                    # Some entries may be null (index 0 is usually null)
                    for map_info in map_infos_list:
                        if map_info is not None:
                            map_id = map_info.get("id")
                            if map_id is not None:
                                map_infos[map_id] = {
                                    "name": map_info.get("name", f"map_{map_id}"),
                                    "parentId": map_info.get("parentId", 0),
                                    "order": map_info.get("order", 0)
                                }
                    print(f"[INFO] Loaded MapInfos.json with {len(map_infos)} maps for hierarchical folder structure")
                    
                    # Build folder paths for each map
                    from .helpers import to_title_case, safe_var
                    def get_folder_path(map_id: int) -> str:
                        """Recursively build folder path from map hierarchy."""
                        if map_id in map_folder_paths:
                            return map_folder_paths[map_id]
                        
                        if map_id not in map_infos:
                            # Map not found in MapInfos, use default
                            map_folder_paths[map_id] = f"map_{map_id}"
                            return map_folder_paths[map_id]
                        
                        map_info = map_infos[map_id]
                        parent_id = map_info["parentId"]
                        
                        if parent_id == 0 or parent_id not in map_infos:
                            # Root map or parent not in MapInfos
                            folder_name = f"map_{map_id}_{to_title_case(map_info['name'])}"
                            map_folder_paths[map_id] = folder_name
                        else:
                            # Child map - get parent path and append
                            parent_path = get_folder_path(parent_id)
                            folder_name = f"map_{map_id}_{to_title_case(map_info['name'])}"
                            map_folder_paths[map_id] = os.path.join(parent_path, folder_name)
                        
                        return map_folder_paths[map_id]
                    
                    # Build paths for all maps
                    for map_id in map_infos:
                        get_folder_path(map_id)
                    
            except (json.JSONDecodeError, OSError) as e:
                print(f"[WARN] Could not load MapInfos.json: {e}")
        else:
            # Also check in the workspace root if input_dir is different
            root_map_infos_path = os.path.join(".", "MapInfos.json")
            if root_map_infos_path != map_infos_path and os.path.exists(root_map_infos_path):
                try:
                    with open(root_map_infos_path, "r", encoding="utf-8") as map_infos_file:
                        map_infos_list = json.load(map_infos_file)
                        for map_info in map_infos_list:
                            if map_info is not None:
                                map_id = map_info.get("id")
                                if map_id is not None:
                                    map_infos[map_id] = {
                                        "name": map_info.get("name", f"map_{map_id}"),
                                        "parentId": map_info.get("parentId", 0),
                                        "order": map_info.get("order", 0)
                                    }
                        print(f"[INFO] Loaded MapInfos.json with {len(map_infos)} maps for hierarchical folder structure")
                        
                        # Build folder paths for each map
                        from .helpers import to_title_case, safe_var
                        def get_folder_path(map_id: int) -> str:
                            """Recursively build folder path from map hierarchy."""
                            if map_id in map_folder_paths:
                                return map_folder_paths[map_id]
                            
                            if map_id not in map_infos:
                                map_folder_paths[map_id] = f"map_{map_id}"
                                return map_folder_paths[map_id]
                            
                            map_info = map_infos[map_id]
                            parent_id = map_info["parentId"]
                            
                            if parent_id == 0 or parent_id not in map_infos:
                                folder_name = f"map_{map_id}_{to_title_case(map_info['name'])}"
                                map_folder_paths[map_id] = folder_name
                            else:
                                parent_path = get_folder_path(parent_id)
                                folder_name = f"map_{map_id}_{to_title_case(map_info['name'])}"
                                map_folder_paths[map_id] = os.path.join(parent_path, folder_name)
                            
                            return map_folder_paths[map_id]
                        
                        for map_id in map_infos:
                            get_folder_path(map_id)
                        
                except (json.JSONDecodeError, OSError) as e:
                    print(f"[WARN] Could not load MapInfos.json: {e}")

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
    total_self_switches = sum(len(channels) for ev_switches in collector.self_switches.values() for channels in ev_switches.values())
    print(f"[INFO] Collected from {len(all_map_data)} maps:")
    print(f"    {len(collector.characters)} characters")
    print(f"    {len(collector.switch_ids)} switches")
    print(f"    {len(collector.variable_ids)} variables")
    print(f"    {total_self_switches} self-switches across {len(collector.self_switches)} maps")
    print()

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 2: Generate characters.rpy
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the character definitions
    character_interlines = interlines if "characters" in interlines_targets else 0
    character_definitions = generate_characters_rpy(collector, interlines=character_interlines, indent_width=indent_width)
    
    # Build the output file path
    characters_path = os.path.join(output_dir, "characters.rpy")
    
    # Write the file
    with open(characters_path, "w", encoding="utf-8") as output_file:
        output_file.write(character_definitions)
    
    # Log success
    print(f"[OK] {characters_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3a: Generate global_switches.rpy (game_switch store)
    # ═══════════════════════════════════════════════════════════════════
    
    global_switches_interlines = interlines if "global_switches" in interlines_targets else 0
    global_switches_src = generate_global_switches_rpy(collector, interlines=global_switches_interlines, indent_width=indent_width)
    global_switches_path = os.path.join(output_dir, "global_switches.rpy")
    with open(global_switches_path, "w", encoding="utf-8") as output_file:
        output_file.write(global_switches_src)
    print(f"[OK] {global_switches_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3b: Generate global_variables.rpy (game_vars store)
    # ═══════════════════════════════════════════════════════════════════
    
    global_variables_interlines = interlines if "global_variables" in interlines_targets else 0
    global_variables_src = generate_global_variables_rpy(collector, interlines=global_variables_interlines, indent_width=indent_width)
    global_variables_path = os.path.join(output_dir, "global_variables.rpy")
    with open(global_variables_path, "w", encoding="utf-8") as output_file:
        output_file.write(global_variables_src)
    print(f"[OK] {global_variables_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3c: Generate global_items.rpy (game_items store)
    # ═══════════════════════════════════════════════════════════════════
    
    global_items_interlines = interlines if "global_items" in interlines_targets else 0
    global_items_src = generate_global_items_rpy(collector, interlines=global_items_interlines, indent_width=indent_width)
    if global_items_src:
        global_items_path = os.path.join(output_dir, "global_items.rpy")
        with open(global_items_path, "w", encoding="utf-8") as output_file:
            output_file.write(global_items_src)
        print(f"[OK] {global_items_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3d: Generate global_economy.rpy (game_economy store)
    # ═══════════════════════════════════════════════════════════════════
    
    global_economy_interlines = interlines if "global_economy" in interlines_targets else 0
    global_economy_src = generate_global_economy_rpy(interlines=global_economy_interlines, indent_width=indent_width)
    global_economy_path = os.path.join(output_dir, "global_economy.rpy")
    with open(global_economy_path, "w", encoding="utf-8") as output_file:
        output_file.write(global_economy_src)
    print(f"[OK] {global_economy_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 3e: Generate global_quests.rpy (game_quest store)
    # ═══════════════════════════════════════════════════════════════════
    
    global_quests_interlines = interlines if "global_quests" in interlines_targets else 0
    global_quests_src = generate_global_quests_rpy(interlines=global_quests_interlines, indent_width=indent_width)
    global_quests_path = os.path.join(output_dir, "global_quests.rpy")
    with open(global_quests_path, "w", encoding="utf-8") as output_file:
        output_file.write(global_quests_src)
    print(f"[OK] {global_quests_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 4: Generate side_images.rpy (side image declarations)
    # ═══════════════════════════════════════════════════════════════════
    
    # Generate the side image declarations
    side_images_interlines = interlines if "side_images" in interlines_targets else 0
    side_images_definitions = generate_side_images_rpy(collector, interlines=side_images_interlines, indent_width=indent_width)
    
    # Build the output file path
    side_images_path = os.path.join(output_dir, "side_images.rpy")
    
    # Write the file
    with open(side_images_path, "w", encoding="utf-8") as output_file:
        output_file.write(side_images_definitions)
    
    # Log success
    print(f"[OK] {side_images_path}")

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 5: Generate per-map files (placeholder, autorun, events)
    # ═══════════════════════════════════════════════════════════════════

    # Each map now produces multiple files:
    #   map_{id}_{Name}.rpy                        — global label placeholder
    #   map_{id}_{Name}_switches.rpy               — per-map self-switches
    #   map_{id}_{Name}_events/                     — events subfolder
    #       map_{id}_{Name}_event_{id}_{name}.rpy  — one per autorun/regular event

    # Helper to write a file and log it
    def _write_file(path: str, content: str) -> None:
        """Write content to a file and print a success message."""
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] {path}")

    for map_id, map_data in sorted(all_map_data.items()):
        # Resolve the human-readable map name for this map
        map_name_for_header = map_infos[map_id]["name"] if map_id in map_infos else None
        map_interlines = interlines if "maps" in interlines_targets else 0

        # Create a generator instance for this map
        generator = RenPyGenerator(
            map_data, collector, map_id, all_map_data,
            multiline=multiline, interlines=map_interlines,
            map_name=map_name_for_header,
            indent_width=indent_width,
        )

        # Generate split output: map placeholder, autorun files, event files
        result = generator.generate()

        # ── Determine output directory for this map ──
        if map_id in map_folder_paths:
            # Use hierarchical folder structure from MapInfos.json
            maps_base_dir = os.path.join(output_dir, "maps")
            os.makedirs(maps_base_dir, exist_ok=True)
            full_folder_path = os.path.join(maps_base_dir, map_folder_paths[map_id])
            os.makedirs(full_folder_path, exist_ok=True)
        else:
            # Fallback to flat structure (no MapInfos.json loaded)
            full_folder_path = output_dir

        # ── Base path for all files of this map ──
        # Uses the map_label_name from the generator for consistency
        # Example: "map_3_Refugee_Camp" → "maps/.../map_3_Refugee_Camp"
        base_path = os.path.join(full_folder_path, result.map_label_name)

        # ── Write map placeholder: map_{id}_{Name}.rpy ──
        # Contains: label map_{id}_{Name}: call .autorun; return
        _write_file(f"{base_path}.rpy", result.map_label)

        # ── Write event files into events subfolder ──
        # Each event gets its own subfolder with the event script and switch declarations
        if result.autorun or result.events:
            events_dir = os.path.join(full_folder_path, f"{result.map_label_name}_events")
            os.makedirs(events_dir, exist_ok=True)

            map_name_raw = map_name_for_header or map_data.get("displayName", f"Map{map_id}")

            # Write autorun event files
            # Each autorun gets: subfolder/event_script.rpy + subfolder/event_switches.rpy
            for event_id, (source, filename_suffix) in result.autorun.items():
                event_subdir = os.path.join(events_dir, f"{result.map_label_name}_{filename_suffix}")
                os.makedirs(event_subdir, exist_ok=True)

                # Write event script: map_{id}_{Name}_{event_label}.rpy
                event_file = os.path.join(event_subdir, f"{result.map_label_name}_{filename_suffix}.rpy")
                _write_file(event_file, source)

                # Write per-event self-switch declarations (skipped if no switches)
                event_switches_src = generate_event_switches_rpy(
                    collector, map_id, event_id, map_name_raw, filename_suffix,
                    interlines=map_interlines, indent_width=indent_width,
                )
                if event_switches_src:
                    switches_file = os.path.join(event_subdir, f"{result.map_label_name}_{filename_suffix}_switches.rpy")
                    _write_file(switches_file, event_switches_src)

            # Write regular event files
            # Each event gets: subfolder/event_script.rpy + subfolder/event_switches.rpy
            for event_id, (source, filename_suffix) in result.events.items():
                event_subdir = os.path.join(events_dir, f"{result.map_label_name}_{filename_suffix}")
                os.makedirs(event_subdir, exist_ok=True)

                # Write event script: map_{id}_{Name}_{event_label}.rpy
                event_file = os.path.join(event_subdir, f"{result.map_label_name}_{filename_suffix}.rpy")
                _write_file(event_file, source)

                # Write per-event self-switch declarations (skipped if no switches)
                event_switches_src = generate_event_switches_rpy(
                    collector, map_id, event_id, map_name_raw, filename_suffix,
                    interlines=map_interlines, indent_width=indent_width,
                )
                if event_switches_src:
                    switches_file = os.path.join(event_subdir, f"{result.map_label_name}_{filename_suffix}_switches.rpy")
                    _write_file(switches_file, event_switches_src)

    # ═══════════════════════════════════════════════════════════════════
    # PHASE 6: Generate game_flow.rpy (navigation labels)
    # ═══════════════════════════════════════════════════════════════════

    # Generate the game flow navigation
    # Apply interlines only if "game_flow" is in targets
    game_flow_interlines = interlines if "game_flow" in interlines_targets else 0
    game_flow_source = generate_game_flow_rpy(all_map_data, collector, interlines=game_flow_interlines, indent_width=indent_width)
    
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
