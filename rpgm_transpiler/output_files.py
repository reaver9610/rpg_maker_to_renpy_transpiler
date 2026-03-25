"""Generates auxiliary Ren'Py .rpy files from collected metadata.

Produces three supporting files that the main map scripts depend on:
- characters.rpy: Ren'Py Character definitions with names and colors.
- switches.rpy: Default values for all switches, variables, self-switches, items, gold, and quest log.
- game_flow.rpy: Navigation labels that call each map's event handler.
"""

# ═══════════════════════════════════════════════════════════════════
# FILE GENERATORS — produce the .rpy files
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector
from .renpy_generator import safe_var, side_image_tag


def _get_character_color(face_name: str) -> str:
    """Assign a hex color to a character based on RPG Maker face asset naming.

    Characters in RPG Maker MV often use consistent naming prefixes for
    character groups (e.g., all guard sprites contain "guard"). This function
    maps those patterns to colors for Ren'Py dialogue styling.

    Args:
        face_name: Raw face asset name from RPG Maker (e.g., "$Claire", "!GuardPeople3").

    Returns:
        Hex color string for the character's dialogue text (e.g., "#e8c547").
    """
    lowercase_name = face_name.lower()

    # Claire: protagonist/golden color
    if "claire" in lowercase_name:
        return "#e8c547"

    # Guards and town NPCs: red
    elif "guard" in lowercase_name or "people3" in lowercase_name:
        return "#c44040"

    # Sailors and skippers: blue
    elif "sailor" in lowercase_name or "skipper" in lowercase_name:
        return "#4a90d9"

    # Smugglers: gray
    elif "smuggler" in lowercase_name:
        return "#7a7a7a"

    # All other characters: white (default)
    else:
        return "#ffffff"


def generate_characters_rpy(collector: DataCollector) -> str:
    """Generate characters.rpy with Ren'Py Character definitions.

    Creates a .rpy file containing `define` statements for every character
    discovered during the collection phase. Each Character gets a display
    name and a color based on the face asset naming conventions.

    Args:
        collector: DataCollector instance populated with character data.

    Returns:
        Complete .rpy source string for characters.rpy.
    """
    output_lines: list[str] = []

    # File header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# CHARACTERS")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    # Ren'Py requires an init python block; we use an empty one as a placeholder
    output_lines.append("init python:")
    output_lines.append("    pass")
    output_lines.append("")

    # Generate a define statement for each discovered character
    for face_name, display_name in sorted(collector.characters.items()):
        safe_variable_name = safe_var(display_name)
        character_color = _get_character_color(face_name)
        has_face_ids = face_name in collector.character_face_ids and collector.character_face_ids[face_name]
        if has_face_ids:
            image_tag = side_image_tag(face_name)
            output_lines.append(
                f'define {safe_variable_name} = Character("{display_name}", color="{character_color}", image="{image_tag}")'
            )
        else:
            output_lines.append(
                f'define {safe_variable_name} = Character("{display_name}", color="{character_color}")'
            )

    output_lines.append("")
    return "\n".join(output_lines)


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


def generate_side_images_rpy(collector: DataCollector) -> str:
    """Generate side_images.rpy with Ren'Py side image declarations.

    Creates a .rpy file containing `image side` statements for every
    character + face image ID combination discovered during collection.
    Each declaration references a placeholder path in the side_images/
    directory where the user should place cropped face images.

    RPG Maker MV face sheets are 4x2 grids of 144x144 face images.
    The user must crop individual faces from these sheets and place
    them at the referenced paths (e.g., side_images/people3_7.png).

    Args:
        collector: DataCollector instance populated with character and face ID data.

    Returns:
        Complete .rpy source string for side_images.rpy.
    """
    output_lines: list[str] = []

    # File header with instructions
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# SIDE IMAGES")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    output_lines.append("# Place cropped face images in a side_images/ directory.")
    output_lines.append("# RPG Maker MV face sheets: 4x2 grid, 144x144 per face.")
    output_lines.append("# Face index 0=top-left, 1=top-center-left, ..., 7=bottom-right.")
    output_lines.append("")

    for face_name in sorted(collector.character_face_ids.keys()):
        face_ids = sorted(collector.character_face_ids[face_name])
        if not face_ids:
            continue
        tag = side_image_tag(face_name)
        safe_name = face_name.replace("$", "").replace("!", "").lower()
        for face_id in face_ids:
            output_lines.append(
                f'image side {tag} {face_id} = "side_images/{safe_name}_{face_id}.png"'
            )
        output_lines.append("")

    return "\n".join(output_lines)
