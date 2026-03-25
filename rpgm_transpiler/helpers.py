"""Pure utility functions for RPG Maker → Ren'Py conversion.

Standalone helpers with no dependencies on sibling modules:
- safe_var(): Converts names to safe Python variable names.
- safe_label(): Converts event names to valid Ren'Py labels.
- clean_text(): Strips RPG Maker escape codes from dialogue text.
- clean_text_preserve_lines(): Like clean_text but preserves line breaks.
- side_image_tag(): Converts face asset names to Ren'Py image tags.
"""

import re


def safe_var(name: str) -> str:
    """Convert a character name to a safe Python/Ren'Py variable name.

    Replaces spaces and hyphens with underscores, strips any remaining
    non-alphanumeric characters, and returns a valid identifier suitable
    for use in Ren'Py `define` statements.

    Args:
        name: Raw character display name (e.g., "Sailor Skipper").

    Returns:
        Safe variable name (e.g., "Sailor_Skipper").
    """
    clean = name.replace(" ", "_").replace("-", "_")
    clean = "".join(char for char in clean if char.isalnum() or char == "_")
    return clean


def safe_label(name: str, event_id: int) -> str:
    """Convert an event name to a valid Ren'Py label.

    Sanitizes the event name, prefixes it with the event ID for uniqueness,
    and ensures it starts with a letter or underscore (required by Ren'Py).

    Args:
        name: Raw event name from RPG Maker (e.g., "Town Elder").
        event_id: Numeric event ID for uniqueness (e.g., 5).

    Returns:
        Valid Ren'Py label (e.g., "event_5_town_elder").
    """
    clean = name.strip().replace(" ", "_").replace("-", "_")
    clean = "".join(char for char in clean if char.isalnum() or char == "_")
    # Ren'Py labels must start with a letter or underscore
    if not clean or (not clean[0].isalpha() and clean[0] != "_"):
        clean = f"ev{clean}"
    return f"event_{event_id}_{clean}".lower()


def clean_text(text: str) -> str:
    """Remove RPG Maker escape codes and prepare text for Ren'Py strings.

    Strips color codes (\\c[N]), converts line breaks to spaces, trims
    whitespace, and escapes double quotes for safe embedding in Ren'Py
    dialogue strings.

    Args:
        text: Raw RPG Maker text with escape codes (e.g., "\\c[3]Hello\\nWorld").

    Returns:
        Cleaned text safe for Ren'Py dialogue (e.g., "Hello World").
    """
    # Remove RPG Maker color escape codes: \c[3], \c[14], etc.
    text = re.sub(r"\\c$$\d+$$", "", text)
    # Convert RPG Maker line breaks to spaces (Ren'Py wraps automatically)
    text = text.replace("\\n", " ")
    # Trim leading/trailing whitespace
    text = text.strip()
    # Escape double quotes for embedding in Ren'Py string literals
    text = text.replace('"', '\\"')
    return text


def clean_text_preserve_lines(text: str) -> str:
    """Like clean_text but preserves internal line breaks.

    Used in multiline dialog mode where each TEXT_LINE command is its own
    buffer entry. Strips color codes, trims whitespace, and escapes quotes,
    but does not collapse line breaks.

    Args:
        text: Raw RPG Maker text with escape codes.

    Returns:
        Cleaned text with line breaks preserved.
    """
    text = re.sub(r"\\c$$\d+$$", "", text)
    text = text.strip()
    text = text.replace('"', '\\"')
    return text


def side_image_tag(face_name: str) -> str:
    """Convert an RPG Maker face asset name to a Ren'Py image tag.

    Strips special prefixes ($, !), lowercases, inserts underscores at
    camelCase boundaries, and replaces spaces. Produces a tag suitable
    for use in Ren'Py `image side` declarations and Character `image=`.

    Args:
        face_name: Raw face asset name (e.g., "$People3", "!SailorSkipper").

    Returns:
        Safe image tag (e.g., "people3", "sailor_skipper").
    """
    name = face_name.replace("$", "").replace("!", "")
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    name = re.sub(r"\s+", "_", name)
    name = name.lower()
    return "".join(char for char in name if char.isalnum() or char == "_")
