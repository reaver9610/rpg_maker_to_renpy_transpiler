"""Generates side_images.rpy with Ren'Py side image declarations.

Creates a .rpy file containing `image side` statements for every
character + face image ID combination discovered during collection.
Each declaration references a placeholder path in the side_images/
directory where the user should place cropped face images.
"""

# ═══════════════════════════════════════════════════════════════════
# SIDE IMAGES — Side image declaration generator
# ═══════════════════════════════════════════════════════════════════

from .collector import DataCollector
from .helpers import side_image_tag


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
