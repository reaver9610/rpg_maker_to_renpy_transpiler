"""Generates characters.rpy with Ren'Py Character definitions.

Creates a .rpy file containing `define` statements for every character
discovered during the collection phase. Each Character gets a display
name, a color, and optionally an `image=` parameter for side images.
"""

# ═══════════════════════════════════════════════════════════════════
# CHARACTERS — Character definition generator
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector
from .helpers import safe_var, side_image_tag


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
