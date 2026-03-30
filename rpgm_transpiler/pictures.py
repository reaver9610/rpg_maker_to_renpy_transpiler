"""Generates pictures.rpy with Ren'Py picture layer, transforms, and image definitions.

This module creates the pictures.rpy file containing:

1. Custom picture layer registration via renpy.add_layer()
   - The "pictures" layer sits above "master" (backgrounds/sprites) and below
     "screens" (UI elements), so overlay images appear on top of the scene
     but behind dialogue and menus.

2. A parameterized picture_position transform
   - Maps RPG Maker's Show Picture parameters (x, y, zoom, opacity) to
     Ren'Py transform properties (xpos, ypos, zoom, alpha).
   - Used as: show bg picture_X as picture_N at picture_position(x, y, zx, zy, a)

3. Image definitions for each unique picture filename
   - Each RPG Maker picture file becomes a Ren'Py image definition.
   - Naming convention: image bg picture_<SafeName> = "img/pictures/<OriginalName>.png"
   - The "bg" prefix follows Ren'Py background image conventions.

RPG Maker MV Picture System:
- Pictures are numbered slots (1-100) that display images overlaying the game screen
- They support arbitrary positioning, scaling, opacity, and blend modes
- Commonly used for CG scenes, tutorial screens, posters, and UI overlays
- Image files live in the RPG Maker project's img/pictures/ folder

Ren'Py Mapping:
- RPG Maker picture slot N → show/hide tag "picture_N" on "pictures" layer
- RPG Maker img/pictures/<name>.png → Ren'Py "img/pictures/<name>.png"
- RPG Maker origin/top-left → xpos/ypos relative to screen top-left
- RPG Maker zoom (0-200%) → Ren'Py zoom (0.0-2.0)
- RPG Maker opacity (0-255) → Ren'Py alpha (0.0-1.0)

Output Format:
    # ═══════════════════════════════════════════════════
    # PICTURE DEFINITIONS
    # Auto-generated from RPG Maker MV
    # ═══════════════════════════════════════════════════

    # ── Custom Picture Layer ──
    init python:
        renpy.add_layer("pictures", above="master", below="screens")

    # ── Picture Position Transform ──
    transform picture_position(x=0, y=0, zoom_x=1.0, zoom_y=1.0, alpha=1.0):
        xpos x
        ypos y
        zoom zoom_x
        yzoom zoom_y
        alpha alpha

    # ── Picture Images ──
    image bg picture_Poster_Recruitment = "img/pictures/Poster_Recruitment.png"
    image bg picture_Instruction_6 = "img/pictures/instruction 6.png"
    ...

Usage in Generated Event Scripts:
    show bg picture_Poster_Recruitment as picture_3 at picture_position(0, 0, 1.0, 1.0, 1.0)
    ...
    hide picture_3 onlayer pictures
"""

from .collector import DataCollector
from .helpers import join_with_interlines, safe_picture_var


def generate_pictures_rpy(
    collector: DataCollector,
    interlines: int = 0,
    indent_width: int = 4,
) -> str:
    """Generate pictures.rpy with layer registration, transforms, and image definitions.

    Creates a .rpy file containing:
    1. Custom "pictures" layer registration (above master, below screens)
    2. A parameterized picture_position transform for RPG Maker compatibility
    3. Image definitions for every unique picture filename found during collection

    The image definitions are sorted alphabetically for consistent output.
    Each definition maps a sanitized variable name to the image file path
    within the img/pictures/ directory tree.

    Args:
        collector: DataCollector instance populated with picture data.
            Required attribute:
            - picture_filenames: set of picture file names
              e.g., {"Poster_Recruitment", "instruction 6", "Arrival_2"}
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.
        indent_width: Number of spaces per indentation level (default: 4).
            Used for the init python block indentation.

    Returns:
        Complete .rpy source string for pictures.rpy.
        Returns empty string if no picture references were found (no file needed).

    Example:
        >>> collector = DataCollector()
        >>> collector.picture_filenames = {"Poster_Recruitment", "instruction 6"}
        >>> source = generate_pictures_rpy(collector)
        >>> # source contains renpy.add_layer("pictures", ...)
        >>> #         and transform picture_position(...)
        >>> #         and image bg picture_Poster_Recruitment = ...
        >>> #         and image bg picture_Instruction_6 = ...

    Note:
        The "bg" prefix follows Ren'Py convention for background images.
        The actual image files (.png, etc.) are NOT copied by the transpiler.
        The user must manually copy them to the output img/pictures/ directory.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# PICTURE DEFINITIONS")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # If no pictures at all, return empty string (no file needed)
    if not collector.picture_filenames:
        return ""

    # ── Custom Picture Layer Registration ──
    # Register a dedicated "pictures" layer for overlay images.
    # This layer sits above "master" (backgrounds and sprites) and below
    # "screens" (UI elements like dialogue boxes and menus).
    output_lines.append("# ── Custom Picture Layer ──")
    output_lines.append("# Pictures are displayed on a dedicated layer above backgrounds")
    output_lines.append("# and sprites, but below the dialogue window and UI elements.")
    output_lines.append("init python:")
    indent = " " * indent_width
    output_lines.append(f'{indent}renpy.add_layer("pictures", above="master", below="screens")')
    output_lines.append("")

    # ── Picture Position Transform ──
    # A parameterized transform that maps RPG Maker's Show Picture parameters
    # to Ren'Py transform properties. Used as: show ... at picture_position(x,y,zx,zy,a)
    output_lines.append("# ── Picture Position Transform ──")
    output_lines.append("# Parameterized transform matching RPG Maker's Show Picture parameters.")
    output_lines.append("# x, y: Pixel position from top-left corner")
    output_lines.append("# zoom_x, zoom_y: Scale factor (1.0 = 100%, original size)")
    output_lines.append("# alpha: Opacity (1.0 = fully opaque, 0.0 = fully transparent)")
    output_lines.append("transform picture_position(x=0, y=0, zoom_x=1.0, zoom_y=1.0, alpha=1.0):")
    output_lines.append(f"{indent}xpos x")
    output_lines.append(f"{indent}ypos y")
    output_lines.append(f"{indent}zoom zoom_x")
    output_lines.append(f"{indent}yzoom zoom_y")
    output_lines.append(f"{indent}alpha alpha")
    output_lines.append("")

    # ── Image Definitions ──
    # Each unique RPG Maker picture filename becomes a Ren'Py image definition.
    # Naming convention: image bg picture_<SafeName> = "img/pictures/<OriginalName>.png"
    output_lines.append("# ── Picture Images ──")
    output_lines.append("# Each image definition maps a sanitized variable name to the")
    output_lines.append("# image file path in img/pictures/. Files must be copied manually.")
    for name in sorted(collector.picture_filenames):
        safe_name = safe_picture_var(name)
        output_lines.append(f'image bg picture_{safe_name} = "img/pictures/{name}.png"')
    output_lines.append("")

    # Join all lines with interlines spacing
    return join_with_interlines(output_lines, interlines)
