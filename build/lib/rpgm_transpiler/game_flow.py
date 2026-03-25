"""Generates game_flow.rpy that handles map navigation and entry points.

Creates a .rpy file with:
- A `start` label that jumps to the first map.
- A `map_{id}_enter` label for each map that calls its event handler.
"""

# ═══════════════════════════════════════════════════════════════════
# GAME FLOW — Navigation label generator
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector


def generate_game_flow_rpy(all_map_data: dict[int, dict],
                           collector: DataCollector) -> str:
    """Generate game_flow.rpy that handles map navigation and entry points.

    Creates a .rpy file with:
    - A `start` label that jumps to the first map.
    - A `map_{id}_enter` label for each map that calls its event handler.
    This provides the top-level navigation structure for the Ren'Py game.

    Args:
        all_map_data: Maps map_id → parsed JSON data for each transpiled map.
        collector: DataCollector instance with map name metadata.

    Returns:
        Complete .rpy source string for game_flow.rpy.
    """
    output_lines: list[str] = []

    # File header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GAME FLOW — Map Navigation")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # Start label: entry point for the Ren'Py game
    output_lines.append("label start:")
    output_lines.append("    # Change this to your starting map")
    # List all available maps as commented-out jump alternatives
    for map_id in sorted(all_map_data.keys()):
        map_name = all_map_data[map_id].get("display_name", f"Map {map_id}")
        output_lines.append(f"    # jump map_{map_id}_enter  # {map_name}")
    # Default: jump to map 1
    output_lines.append("    jump map_1_enter")
    output_lines.append("")
    output_lines.append("")

    # Generate an entry label for each map that calls its event handler
    for map_id, map_data in sorted(all_map_data.items()):
        map_name = map_data.get("display_name", f"Map {map_id}")
        output_lines.append(f"label map_{map_id}_enter:")
        output_lines.append(f"    # {map_name}")
        output_lines.append(f"    call map_{map_id}_events")
        output_lines.append(f"    return")
        output_lines.append("")

    return "\n".join(output_lines)
