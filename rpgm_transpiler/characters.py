"""Generates characters.rpy with Ren'Py Character definitions.

This module creates the characters.rpy file containing `define` statements for every
character discovered during the collection phase. Each Character definition includes
a display name, a color for dialogue text, and optionally an `image=` parameter for
side image display.

Character Definition Format:
Ren'Py Character objects are defined in .rpy files and used throughout the game:
    define claire = Character("Claire", color="#e8c547", image="claire")

The 'image' parameter enables side image display. When dialogue is shown, Ren'Py
automatically looks for "image side {tag} {face_id}" and displays it next to
the dialogue box.

Color Assignment Strategy:
This module uses a simple pattern-matching approach to assign colors:
- Named characters get specific colors (e.g., "Claire" → golden)
- Character type patterns get shared colors (e.g., "guard" → red)
- Unknown characters default to white

This is a game-specific implementation. Projects with different character naming
conventions should modify _get_character_color() accordingly.

Output File Structure:
    # ═══════════════════════════════════════════════════
    # CHARACTERS
    # Auto-generated from RPG Maker MV
    # ═══════════════════════════════════════════════════

    init python:
        pass

    define claire = Character("Claire", color="#e8c547", image="claire")
    define sailor_skipper = Character("Sailor Skipper", color="#4a90d9", image="sailor_skipper")
    ...
"""

from .collector import DataCollector
from .helpers import safe_var, side_image_tag


def _get_character_color(face_name: str) -> str:
    """Assign a hex color to a character based on RPG Maker face asset naming.

    Characters in RPG Maker MV often use consistent naming prefixes for character
    groups (e.g., all guard sprites contain "guard"). This function maps those
    patterns to colors for Ren'Py dialogue styling.

    Color Assignment Rules:
    1. "claire" in name → Golden (#e8c547) - Protagonist color
    2. "guard" or "people3" in name → Red (#c44040) - Guards and town NPCs
    3. "sailor" or "skipper" in name → Blue (#4a90d9) - Sailor characters
    4. "smuggler" in name → Gray (#7a7a7a) - Antagonist NPCs
    5. Default → White (#ffffff) - Unknown characters

    Case Insensitivity:
    All name matching is case-insensitive to handle variations in asset naming.

    Args:
        face_name: Raw face asset name from RPG Maker.
            Examples: "$Claire", "!GuardPeople3", "SailorSkipper"

    Returns:
        Hex color string for the character's dialogue text.
        Format: "#RRGGBB" (e.g., "#e8c547")

    Example:
        >>> _get_character_color("$Claire")
        '#e8c547'
        >>> _get_character_color("!GuardPeople3")
        '#c44040'
        >>> _get_character_color("UnknownNPC")
        '#ffffff'

    Note:
        This is a game-specific implementation. The color assignments reflect
        the original game's character naming conventions. Projects with
        different naming schemes should modify the pattern matching logic.

    See Also:
        Ren'Py Character documentation: https://www.renpy.org/doc/html/dialogue.html#defining-characters
    """
    # Convert to lowercase for case-insensitive matching
    lowercase_name = face_name.lower()

    # ── Claire: Protagonist with golden color ──
    # The protagonist uses a warm golden color for their dialogue
    if "claire" in lowercase_name:
        return "#e8c547"

    # ── Guards and Town NPCs: Red color ──
    # Guards and generic town NPCs use red for authority figures
    # "people3" is a common RPG Maker naming convention for generic NPCs
    elif "guard" in lowercase_name or "people3" in lowercase_name:
        return "#c44040"

    # ── Sailors and Skippers: Blue color ──
    # Maritime characters use blue to reflect the sea theme
    elif "sailor" in lowercase_name or "skipper" in lowercase_name:
        return "#4a90d9"

    # ── Smugglers: Gray color ──
    # Antagonist NPCs use gray to appear neutral/suspicious
    elif "smuggler" in lowercase_name:
        return "#7a7a7a"

    # ── Default: White color ──
    # All unknown characters default to white (no color tint)
    else:
        return "#ffffff"


def generate_characters_rpy(collector: DataCollector) -> str:
    """Generate characters.rpy with Ren'Py Character definitions.

    Creates a .rpy file containing `define` statements for every character
    discovered during the collection phase. Each Character definition includes:
    - Display name: Human-readable name shown in dialogue
    - Color: Hex color for dialogue text (from _get_character_color)
    - Image tag: Optional, enables side image display

    Side Image Integration:
    When a character has face IDs recorded (used in dialogue), the Character
    definition includes an `image=` parameter. This tells Ren'Py to look for
    side images with the matching tag:
        define claire = Character("Claire", color="#e8c547", image="claire")

    At runtime, Ren'Py will look for "side claire {face_id}" images.

    Args:
        collector: DataCollector instance populated with character data.
            Required attributes:
            - characters: dict mapping face_name → display_name
            - character_face_ids: dict mapping face_name → set of face IDs

    Returns:
        Complete .rpy source string for characters.rpy.
        Ready to be written to a file.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector ...
        >>> source = generate_characters_rpy(collector)
        >>> with open("characters.rpy", "w") as f:
        ...     f.write(source)

    Output Format:
        # ═══════════════════════════════════════════════════
        # CHARACTERS
        # Auto-generated from RPG Maker MV
        # ═══════════════════════════════════════════════════

        init python:
            pass

        define claire = Character("Claire", color="#e8c547", image="claire")
        define sailor_skipper = Character("Sailor Skipper", color="#4a90d9", image="sailor_skipper")

    Note:
        The init python block with 'pass' is included as a placeholder for
        future Python code. Ren'Py requires at least one statement in a block.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# CHARACTERS")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    
    # ── Init Python Block ──
    # Include an empty init python block as a placeholder
    # This allows for future Python code additions without restructuring
    output_lines.append("init python:")
    output_lines.append("    pass")
    output_lines.append("")

    # ── Character Definitions ──
    # Iterate over characters in sorted order for consistent output
    for face_name, display_name in sorted(collector.characters.items()):
        # Convert the display name to a safe Python variable name
        # Example: "Sailor Skipper" → "Sailor_Skipper"
        safe_variable_name = safe_var(display_name)
        
        # Get the color for this character
        # Color is determined by face asset naming patterns
        character_color = _get_character_color(face_name)
        
        # Check if this character has face IDs (used for side images)
        has_face_ids = face_name in collector.character_face_ids and collector.character_face_ids[face_name]
        
        # Emit the Character definition
        if has_face_ids:
            # Character has face images: include image tag for side display
            image_tag = side_image_tag(face_name)
            output_lines.append(
                f'define {safe_variable_name} = Character("{display_name}", color="{character_color}", image="{image_tag}")'
            )
        else:
            # Character has no face images: omit image parameter
            output_lines.append(
                f'define {safe_variable_name} = Character("{display_name}", color="{character_color}")'
            )

    # Add trailing newline
    output_lines.append("")
    
    # Join all lines with newlines and return
    return "\n".join(output_lines)
