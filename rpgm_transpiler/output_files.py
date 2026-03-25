# ═══════════════════════════════════════════════════════════════════
# FILE GENERATORS — produce the .rpy files
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector
from .renpy_generator import safe_var


def _get_character_color(face_name: str) -> str:
    """Assign a color to a character based on naming conventions."""
    name = face_name.lower()
    if "claire" in name:
        return "#e8c547"
    elif "guard" in name or "people3" in name:
        return "#c44040"
    elif "sailor" in name or "skipper" in name:
        return "#4a90d9"
    elif "smuggler" in name:
        return "#7a7a7a"
    else:
        return "#ffffff"


def generate_characters_rpy(collector: DataCollector) -> str:
    """Generate characters.rpy with all Character definitions."""
    lines = []
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("# CHARACTERS")
    lines.append("# Auto-generated from RPG Maker MV")
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("")
    lines.append("init python:")
    lines.append("    pass")
    lines.append("")

    for face_name, display_name in sorted(collector.characters.items()):
        safe = safe_var(display_name)
        color = _get_character_color(face_name)
        lines.append(f'define {safe} = Character("{display_name}", color="{color}")')

    lines.append("")
    return "\n".join(lines)


def generate_switches_rpy(collector: DataCollector) -> str:
    """Generate switches.rpy with all default switch/variable values."""
    lines = []
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("# GAME STATE — Switches, Variables, Self-Switches")
    lines.append("# Auto-generated from RPG Maker MV")
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("")
    lines.append("init python:")
    lines.append("")

    if collector.switch_ids:
        lines.append("    # ── Global Switches ──")
        for sid in sorted(collector.switch_ids):
            lines.append(f"    switch_{sid} = False")
        lines.append("")

    if collector.variable_ids:
        lines.append("    # ── Variables ──")
        for vid in sorted(collector.variable_ids):
            lines.append(f"    var_{vid} = 0")
        lines.append("")

    if collector.self_switches:
        lines.append("    # ── Self-Switches ──")
        for eid, ch in sorted(collector.self_switches):
            lines.append(f"    selfswitch_{eid}_{ch} = False")
        lines.append("")

    if collector.item_ids:
        lines.append("    # ── Items ──")
        for iid in sorted(collector.item_ids):
            lines.append(f"    item_{iid} = 0")
        lines.append("")

    lines.append("    # ── Gold ──")
    lines.append("    gold = 0")
    lines.append("")

    lines.append("    # ── Quest Log ──")
    lines.append("    quest_log = []")
    lines.append("")

    return "\n".join(lines)


def generate_game_flow_rpy(all_map_data: dict[int, dict],
                           collector: DataCollector) -> str:
    """Generate game_flow.rpy that handles map navigation."""
    lines = []
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("# GAME FLOW — Map Navigation")
    lines.append("# Auto-generated from RPG Maker MV")
    lines.append("# ═══════════════════════════════════════════════════")
    lines.append("")

    lines.append("label start:")
    lines.append("    # Change this to your starting map")
    for mid in sorted(all_map_data.keys()):
        name = all_map_data[mid].get("display_name", f"Map {mid}")
        lines.append(f"    # jump map_{mid}_enter  # {name}")
    lines.append("    jump map_1_enter")
    lines.append("")
    lines.append("")

    for mid, mdata in sorted(all_map_data.items()):
        name = mdata.get("display_name", f"Map {mid}")
        lines.append(f"label map_{mid}_enter:")
        lines.append(f"    # {name}")
        lines.append(f"    call map_{mid}_events")
        lines.append(f"    return")
        lines.append("")

    return "\n".join(lines)