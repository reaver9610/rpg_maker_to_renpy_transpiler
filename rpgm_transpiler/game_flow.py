"""Generates game_flow.rpy that handles the game's starting entry point.

This module creates the game_flow.rpy file providing the ``label start:``
entry point for the Ren'Py game.

Navigation Architecture (new per-file structure):
Each map has its own placeholder file that defines the global label::

    # game_flow.rpy
    label start:
        jump map_1_Checkpoint

    # maps/map_3_Refugee_Camp/map_3_Refugee_Camp.rpy
    label map_3_Refugee_Camp:
        call map_3_Refugee_Camp.event_3_auto
        call map_3_Refugee_Camp.event_39_roadblock_setup
        return

    # maps/map_3_Refugee_Camp/map_3_Refugee_Camp_events/map_3_Refugee_Camp_event_3_auto.rpy
    label map_3_Refugee_Camp.event_3_auto:
        # autorun content
        return

    # maps/map_3_Refugee_Camp/map_3_Refugee_Camp_events/map_3_Refugee_Camp_event_11_torch.rpy
    label map_3_Refugee_Camp.event_11:
        # event content
        return

Transfers between maps use ``jump map_{id}_{Name}`` targeting the global
label defined in each map's placeholder file.

Output File Structure:
    # ═══════════════════════════════════════════════════
    # GAME FLOW — Map Navigation
    # Auto-generated from RPG Maker MV
    # ═══════════════════════════════════════════════════

    label start:
        # Change this to your starting map
        # jump map_1_Checkpoint
        # jump map_2_Hookton_Village
        # jump map_3_Refugee_Camp
        jump map_1_Checkpoint
"""

from .collector import DataCollector
from .helpers import safe_map_label, join_with_interlines, make_indent


def generate_game_flow_rpy(
    all_map_data: dict[int, dict],
    collector: DataCollector,
    interlines: int = 0,
    indent_width: int = 4,
) -> str:
    """Generate game_flow.rpy with the ``start`` entry point.

    Creates a minimal .rpy file containing only the ``label start:``
    label.  Map entry labels (``label map_{id}_{Name}:``) live in their
    respective map placeholder files, not here.

    The ``start`` label jumps to the first map's global label.
    Commented-out alternatives for every map are included for easy
    reconfiguration by the game designer.

    Args:
        all_map_data: Maps ``map_id`` → parsed JSON data for each map.
            Used to list available maps in comments and determine the default.
        collector: DataCollector instance with map name metadata.
            Used to retrieve display names for map IDs.
        interlines: Number of blank lines to insert between each output line.
            ``0`` means no extra spacing.

    Returns:
        Complete .rpy source string for game_flow.rpy.

    Example:
        >>> source = generate_game_flow_rpy(all_map_data, collector)
        >>> with open("game_flow.rpy", "w") as f:
        ...     f.write(source)
    """
    output_lines: list[str] = []

    # ── File Header ──
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GAME FLOW — Map Navigation")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # ── Start Label ──
    output_lines.append("label start:")

    # List all available maps as commented-out alternatives
    output_lines.append(f"{make_indent(indent_width)}# Change this to your starting map")
    for map_id in sorted(all_map_data.keys()):
        map_name = collector.map_names.get(map_id) or all_map_data[map_id].get("displayName", f"Map {map_id}")
        label = safe_map_label(map_id, map_name)
        output_lines.append(f"{make_indent(indent_width)}# jump {label}  # {map_name}")

    # Emit the default jump to the first map
    first_map_id = min(all_map_data.keys()) if all_map_data else 1
    first_map_name = (
        collector.map_names.get(first_map_id)
        or all_map_data.get(first_map_id, {}).get("displayName", f"Map{first_map_id}")
    )
    first_label = safe_map_label(first_map_id, first_map_name)
    output_lines.append(f"{make_indent(indent_width)}jump {first_label}")

    output_lines.append("")

    return join_with_interlines(output_lines, interlines)
