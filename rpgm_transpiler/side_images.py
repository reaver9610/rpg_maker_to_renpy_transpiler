"""Generates side_images.rpy with Ren'Py side image declarations.

This module creates the side_images.rpy file containing `image side` statements
for every character + face image ID combination discovered during collection.
Side images are displayed next to the dialogue box when a character speaks.

Side Images in Ren'Py:
Ren'Py supports side images that appear next to dialogue:
    image side claire 0 = "side_images/claire_0.png"

When a Character with image="claire" speaks:
    claire 0 "Hello!"
    
Ren'Py looks for "side claire 0" and displays it next to the dialogue.

RPG Maker Face Sheets:
RPG Maker MV uses face sheets: 4x2 grids of 144x144 pixel images.
Each face sheet can contain up to 8 faces (indices 0-7):
    Index layout:
    0 | 1 | 2 | 3
    4 | 5 | 6 | 7

The user must crop individual faces from these sheets and place them
in the side_images/ directory with appropriate filenames.

Output File Structure:
    # ═══════════════════════════════════════════════════
    # SIDE IMAGES
    # Auto-generated from RPG Maker MV
    # ═══════════════════════════════════════════════════

    # Place cropped face images in a side_images/ directory.
    # RPG Maker MV face sheets: 4x2 grid, 144x144 per face.
    # Face index 0=top-left, 1=top-center-left, ..., 7=bottom-right.

    image side claire 0 = "side_images/claire_0.png"
    image side claire 2 = "side_images/claire_2.png"
    image side sailor_skipper 1 = "side_images/sailorskipper_1.png"
    ...
"""

from .collector import DataCollector
from .helpers import side_image_tag


def generate_side_images_rpy(collector: DataCollector) -> str:
    """Generate side_images.rpy with Ren'Py side image declarations.

    Creates a .rpy file containing `image side` statements for every
    character + face image ID combination discovered during collection.
    Each declaration references a placeholder path in the side_images/
    directory where the user should place cropped face images.

    Face Sheet Processing:
    RPG Maker MV face sheets are 4x2 grids of 144x144 face images.
    The user must:
    1. Open the original face sheet (e.g., "Claire.png" from img/faces/)
    2. Crop individual faces at 144x144 pixels
    3. Save each face as side_images/{name}_{index}.png

    Face Index Layout:
        0 | 1 | 2 | 3
        4 | 5 | 6 | 7

    - Index 0: Top-left face
    - Index 1: Top-center-left face
    - Index 7: Bottom-right face

    Image Declaration Format:
        image side {tag} {face_id} = "side_images/{asset_name}_{face_id}.png"

    Example:
        For face asset "$Claire" with face IDs {0, 2, 5}:
        - side_image_tag("$Claire") → "claire"
        - Generates:
            image side claire 0 = "side_images/claire_0.png"
            image side claire 2 = "side_images/claire_2.png"
            image side claire 5 = "side_images/claire_5.png"

    Args:
        collector: DataCollector instance populated with character and face ID data.
            Required attributes:
            - character_face_ids: dict mapping face_name → set of face IDs

    Returns:
        Complete .rpy source string for side_images.rpy.
        Ready to be written to a file.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector ...
        >>> source = generate_side_images_rpy(collector)
        >>> with open("side_images.rpy", "w") as f:
        ...     f.write(source)

    Note:
        The generated file assumes image files exist at the specified paths.
        The user must create these files by cropping from RPG Maker face sheets.

    Note:
        Ren'Py uses .png format for images. Ensure cropped faces are saved
        in PNG format with transparency for best results.

    See Also:
        helpers.side_image_tag: Converts face names to image tags.
        characters.generate_characters_rpy: Uses the same tags for Character definitions.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# SIDE IMAGES")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    
    # ── Usage Instructions ──
    # Provide helpful comments for game designers
    output_lines.append("# Place cropped face images in a side_images/ directory.")
    output_lines.append("# RPG Maker MV face sheets: 4x2 grid, 144x144 per face.")
    output_lines.append("# Face index 0=top-left, 1=top-center-left, ..., 7=bottom-right.")
    output_lines.append("")

    # ── Image Declarations ──
    # Iterate over each face asset that has recorded face IDs
    for face_name in sorted(collector.character_face_ids.keys()):
        # Get the set of face IDs used for this character
        face_ids = sorted(collector.character_face_ids[face_name])
        
        # Skip if no face IDs (shouldn't happen, but defensive)
        if not face_ids:
            continue
        
        # Convert the face name to a Ren'Py image tag
        # Example: "$Claire" → "claire"
        tag = side_image_tag(face_name)
        
        # Create a safe filename from the face name
        # Strip $ and ! prefixes, convert to lowercase
        safe_name = face_name.replace("$", "").replace("!", "").lower()
        
        # Emit an image declaration for each face ID
        for face_id in face_ids:
            # Create the image declaration
            # Format: image side {tag} {face_id} = "side_images/{safe_name}_{face_id}.png"
            output_lines.append(
                f'image side {tag} {face_id} = "side_images/{safe_name}_{face_id}.png"'
            )
        
        # Add a blank line between characters for readability
        output_lines.append("")

    # Join all lines with newlines and return
    return "\n".join(output_lines)
