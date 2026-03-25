"""RPG Maker MV to Ren'Py Transpiler.

Orchestrates the full transpilation pipeline: loads RPG Maker MV JSON map files,
runs a data collection pass, then generates Ren'Py .rpy script files for
characters, switches/variables, map events, and game flow navigation.

Public API:
    transpile_to_renpy: Main entry point that processes input files and writes output.
    DataCollector: First-pass scanner that collects all referenced game state.
    RenPyGenerator: Converts a single map's events to Ren'Py script.
    generate_characters_rpy: Produces characters.rpy with Character definitions.
    generate_switches_rpy: Produces switches.rpy with default state values.
    generate_game_flow_rpy: Produces game_flow.rpy with map navigation labels.
"""

# ═══════════════════════════════════════════════════════════════════
# RPG Maker MV → Ren'Py Transpiler
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .collector import DataCollector
from .renpy_generator import RenPyGenerator
from .output_files import (
    generate_characters_rpy,
    generate_switches_rpy,
    generate_game_flow_rpy,
)


__all__ = [
    "transpile_to_renpy",
    "DataCollector",
    "RenPyGenerator",
    "generate_characters_rpy",
    "generate_switches_rpy",
    "generate_game_flow_rpy",
]


def transpile_to_renpy(input_paths: list[str], output_dir: str = "outputs",
                       multiline: bool = False) -> None:
    """Transpile one or more RPG Maker MV JSON maps to Ren'Py .rpy scripts.

    Runs the full pipeline:
    1. Load and parse each JSON map file.
    2. Extract map ID from the filename (e.g., "Map001.json" → 1).
    3. Run the data collector to discover all characters, switches, etc.
    4. Generate characters.rpy (Character definitions).
    5. Generate switches.rpy (default game state values).
    6. Generate a .rpy file for each map's events.
    7. Generate game_flow.rpy (map navigation labels).

    Args:
        input_paths: List of filesystem paths to RPG Maker MV .json map files.
        output_dir: Directory to write generated .rpy files (created if missing).
        multiline: If True, emit multi-line dialogue as Ren'Py triple-quoted strings.
    """
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # Storage for parsed map data and the shared collector
    all_map_data: dict[int, dict] = {}
    collector = DataCollector()

    # ── Phase 1: Load JSON files and run data collection ──
    for file_path in input_paths:
        with open(file_path, "r", encoding="utf-8") as json_file:
            parsed_map_data = json.load(json_file)

        # Extract numeric map ID from filename (e.g., "Map001" → 1)
        filename_stem = Path(file_path).stem
        map_id_match = re.search(r"(\d+)", filename_stem)
        map_id = int(map_id_match.group(1)) if map_id_match else len(all_map_data) + 1

        # Store parsed data and scan for referenced game state
        all_map_data[map_id] = parsed_map_data
        collector.collect_from_map(parsed_map_data, map_id)

    # Log collection summary
    print(f"[INFO] Collected from {len(all_map_data)} maps:")
    print(f"       {len(collector.characters)} characters")
    print(f"       {len(collector.switch_ids)} switches")
    print(f"       {len(collector.variable_ids)} variables")
    print(f"       {len(collector.self_switches)} self-switches")
    print()

    # ── Phase 2: Generate characters.rpy ──
    character_definitions = generate_characters_rpy(collector)
    characters_path = os.path.join(output_dir, "characters.rpy")
    with open(characters_path, "w", encoding="utf-8") as output_file:
        output_file.write(character_definitions)
    print(f"[OK] {characters_path}")

    # ── Phase 3: Generate switches.rpy (default game state) ──
    switch_definitions = generate_switches_rpy(collector)
    switches_path = os.path.join(output_dir, "switches.rpy")
    with open(switches_path, "w", encoding="utf-8") as output_file:
        output_file.write(switch_definitions)
    print(f"[OK] {switches_path}")

    # ── Phase 4: Generate a .rpy file for each map's events ──
    for map_id, map_data in sorted(all_map_data.items()):
        # Create a generator instance with access to all maps (for transfers)
        generator = RenPyGenerator(
            map_data, collector, map_id, all_map_data, multiline=multiline
        )
        map_script_source = generator.generate()

        # Build a safe filename from the map's display name
        map_display_name = map_data.get("display_name", f"map_{map_id}")
        safe_filename = re.sub(r"[^a-z0-9_]", "_", map_display_name.lower())
        output_filename = f"map_{map_id}_{safe_filename}.rpy"
        output_path = os.path.join(output_dir, output_filename)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(map_script_source)
        print(f"[OK] {output_path}")

    # ── Phase 5: Generate game_flow.rpy (navigation labels) ──
    game_flow_source = generate_game_flow_rpy(all_map_data, collector)
    game_flow_path = os.path.join(output_dir, "game_flow.rpy")
    with open(game_flow_path, "w", encoding="utf-8") as output_file:
        output_file.write(game_flow_source)
    print(f"[OK] {game_flow_path}")

    print(f"\n[DONE] Transpiled {len(all_map_data)} maps to {output_dir}/")
