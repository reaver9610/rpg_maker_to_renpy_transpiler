"""Generates switches.rpy with default game state variable declarations.

Creates a .rpy file containing `init python:` assignments for every
switch, variable, self-switch, item, and utility variable (gold, quest log)
discovered during the collection phase.
"""

# ═══════════════════════════════════════════════════════════════════
# SWITCHES — Game state generator
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector


def generate_switches_rpy(collector: DataCollector) -> str:
    """Generate switches.rpy with default game state variable declarations.

    Creates a .rpy file containing `init python:` assignments for every
    switch, variable, self-switch, item, and utility variable (gold, quest log)
    discovered during the collection phase. All switches default to False,
    all variables default to 0.

    Args:
        collector: DataCollector instance populated with switch/variable/item data.

    Returns:
        Complete .rpy source string for switches.rpy.
    """
    output_lines: list[str] = []

    # File header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GAME STATE — Switches, Variables, Self-Switches")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    output_lines.append("init python:")
    output_lines.append("")

    # Global switches: boolean flags (False = OFF, True = ON)
    if collector.switch_ids:
        output_lines.append("    # ── Global Switches ──")
        for switch_id in sorted(collector.switch_ids):
            output_lines.append(f"    switch_{switch_id} = False")
        output_lines.append("")

    # Variables: integer values with default of 0
    if collector.variable_ids:
        output_lines.append("    # ── Variables ──")
        for variable_id in sorted(collector.variable_ids):
            output_lines.append(f"    var_{variable_id} = 0")
        output_lines.append("")

    # Self-switches: event-local boolean flags (keyed by event_id + channel letter)
    if collector.self_switches:
        output_lines.append("    # ── Self-Switches ──")
        for event_id, channel in sorted(collector.self_switches):
            output_lines.append(f"    selfswitch_{event_id}_{channel} = False")
        output_lines.append("")

    # Items: integer counters (0 = not in inventory)
    if collector.item_ids:
        output_lines.append("    # ── Items ──")
        for item_id in sorted(collector.item_ids):
            output_lines.append(f"    item_{item_id} = 0")
        output_lines.append("")

    # Gold: player currency, always initialized
    output_lines.append("    # ── Gold ──")
    output_lines.append("    gold = 0")
    output_lines.append("")

    # Quest log: list of quest strings from plugin commands
    output_lines.append("    # ── Quest Log ──")
    output_lines.append("    quest_log = []")
    output_lines.append("")

    return "\n".join(output_lines)
