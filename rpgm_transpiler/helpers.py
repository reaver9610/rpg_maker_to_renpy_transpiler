"""Pure utility functions for RPG Maker → Ren'Py conversion.

This module contains standalone helper functions with no dependencies on sibling
modules. Each function is pure (no side effects) and handles a specific
transformation needed during transpilation.

Functions are organized by purpose:
- Name sanitization: safe_var(), safe_label(), safe_audio_var(), safe_picture_var()
- Text processing: clean_text(), clean_text_preserve_lines()
- Asset conversion: side_image_tag()
- Formatting: join_with_interlines()

Design Philosophy:
- All functions are pure: same input → same output, no external state
- No dependencies on other transpiler modules (constants, collector, generator)
- Used throughout the codebase by collector, generator, and output modules
"""

import re


def safe_var(name: str) -> str:
    """Convert a character name to a safe Python/Ren'Py variable name.

    Ren'Py variable names must follow Python identifier rules:
    - Start with a letter or underscore
    - Contain only alphanumeric characters and underscores
    - Case-sensitive

    This function sanitizes RPG Maker character names (which may contain
    spaces, hyphens, or other special characters) into valid identifiers.

    Transformation Rules:
    1. Replace spaces with underscores: "Sailor Skipper" → "Sailor_Skipper"
    2. Replace hyphens with underscores: "Jean-Pierre" → "Jean_Pierre"
    3. Strip all remaining non-alphanumeric characters (except underscore)
    4. Preserve the original casing

    Args:
        name: Raw character display name from RPG Maker face asset.
            Examples: "Sailor Skipper", "Jean-Pierre", "Claire"

    Returns:
        Safe Python/Ren'Py variable name suitable for use in `define` statements.
        Examples: "Sailor_Skipper", "Jean_Pierre", "Claire"

    Example:
        >>> safe_var("Sailor Skipper")
        'Sailor_Skipper'
        >>> safe_var("Jean-Pierre")
        'Jean_Pierre'
        >>> safe_var("$Claire")
        'Claire'  # Note: $ is stripped, not replaced

    Note:
        This function does NOT guarantee uniqueness. If two characters have
        names that sanitize to the same variable (e.g., "Jean Pierre" and
        "Jean-Pierre"), they will collide. The caller is responsible for
        ensuring uniqueness if needed.
    """
    # Step 1: Replace spaces with underscores
    # This handles the most common case: multi-word names like "Sailor Skipper"
    clean = name.replace(" ", "_")
    
    # Step 2: Replace hyphens with underscores
    # Hyphens appear in names like "Jean-Pierre" and are invalid in Python identifiers
    clean = clean.replace("-", "_")
    
    # Step 3: Filter to only alphanumeric and underscore characters
    # This removes any remaining special characters: $, !, @, #, etc.
    # The generator expression iterates character-by-character, keeping valid ones
    clean = "".join(char for char in clean if char.isalnum() or char == "_")
    
    # Step 4: Return the sanitized name
    # The result is guaranteed to be a valid Python identifier (assuming input was non-empty)
    return clean


def safe_audio_var(name: str) -> str:
    """Convert an audio file name to a valid Python identifier for Ren'Py audio namespace.

    Ren'Py's audio namespace requires valid Python identifiers for variable names.
    Audio file names from RPG Maker may contain spaces, hyphens, and other characters
    that are invalid in Python identifiers.

    This function sanitizes the name while preserving readability:
    - Spaces become underscores: "Paths of Peril" → "Paths_of_Peril"
    - Hyphens become underscores: "slow-jam" → "slow_jam"
    - Only alphanumeric and underscore characters kept

    Args:
        name: Raw audio file name from RPG Maker.
        Examples: "Paths of Peril", "Kingdom of Peril Alt 1", "Contemplation"

    Returns:
        Sanitized name suitable for use in audio namespace.
        Examples: "Paths_of_Peril", "Kingdom_of_Peril_Alt_1", "Contemplation"

    Example:
        >>> safe_audio_var("Paths of Peril")
        'Paths_of_Peril'
        >>> safe_audio_var("Kingdom of Peril Alt 1")
        'Kingdom_of_Peril_Alt_1'
        >>> safe_audio_var("slow-jam")
        'slow_jam'

    Note:
        The result can be used in Ren'Py define statements:
        define audio.bgm_Paths_of_Peril = "audio/bgm/Paths of Peril.ogg"
        
        And play statements will find it in the audio namespace:
        play music bgm_Paths_of_Peril
    """
    # Step 1: Strip leading/trailing whitespace
    clean = name.strip()

    # Step 2: Replace spaces with underscores
    clean = clean.replace(" ", "_")

    # Step 3: Replace hyphens with underscores
    clean = clean.replace("-", "_")

    # Step 4: Filter to only alphanumeric and underscore characters
    clean = "".join(char for char in clean if char.isalnum() or char == "_")

    # Step 5: Ensure it doesn't start with a digit
    # Python identifiers can't start with a digit
    if clean and clean[0].isdigit():
        clean = f"_{clean}"

    return clean


def safe_picture_var(name: str) -> str:
    """Convert an RPG Maker picture filename to a valid Ren'Py image tag and variable name.

    RPG Maker MV picture filenames may contain spaces, hyphens, and other characters
    that are invalid in Ren'Py image tags and Python identifiers. This function
    sanitizes the name while preserving readability.

    Transforms:
    - Spaces become underscores: "instruction 6" → "instruction_6"
    - Hyphens become underscores: "my-picture" → "my_picture"
    - Only alphanumeric and underscore characters kept
    - Consecutive underscores collapsed to single: "a___b" → "a_b"
    - Leading/trailing underscores stripped

    Args:
        name: Raw picture filename from RPG Maker.
        Examples: "Poster_Recruitment", "instruction 6", "Claire_vs_MeanRefugee_Strip_1B"

    Returns:
        Sanitized name suitable for use in Ren'Py image tags and variable names.
        Examples: "Poster_Recruitment", "instruction_6", "Claire_vs_MeanRefugee_Strip_1B"

    Example:
        >>> safe_picture_var("Poster_Recruitment")
        'Poster_Recruitment'
        >>> safe_picture_var("instruction 6")
        'instruction_6'
        >>> safe_picture_var("Claire vs MeanRefugee Strip 1B")
        'Claire_vs_MeanRefugee_Strip_1B'

    Note:
        The result is used in Ren'Py image definitions and show/hide statements:
        image bg picture_Poster_Recruitment = "img/pictures/Poster_Recruitment.png"
        show bg picture_Poster_Recruitment as picture_3
        hide picture_3 onlayer pictures
    """
    # Step 1: Strip leading/trailing whitespace
    clean = name.strip()

    # Step 2: Replace spaces with underscores
    clean = clean.replace(" ", "_")

    # Step 3: Replace hyphens with underscores
    clean = clean.replace("-", "_")

    # Step 4: Filter to only alphanumeric and underscore characters
    clean = "".join(char for char in clean if char.isalnum() or char == "_")

    # Step 5: Collapse consecutive underscores into single underscore
    while "__" in clean:
        clean = clean.replace("__", "_")

    # Step 6: Strip leading/trailing underscores
    clean = clean.strip("_")

    return clean


def safe_label(name: str, event_id: int) -> str:
    """Convert an event name to a valid Ren'Py label.

    Ren'Py labels have stricter requirements than Python variables:
    - Must start with a letter or underscore (not a digit)
    - Must contain only alphanumeric characters and underscores
    - Must be unique within the game

    This function sanitizes the event name and prefixes it with the event ID
    to guarantee uniqueness. The format is: "event_{id}_{sanitized_name}".

    Transformation Rules:
    1. Strip leading/trailing whitespace
    2. Replace spaces with underscores
    3. Replace hyphens with underscores
    4. Strip all remaining non-alphanumeric characters (except underscore)
    5. If empty or starts with a digit, prepend "ev" to satisfy Ren'Py rules
    6. Convert to lowercase (Ren'Py convention)
    7. Format as "event_{event_id}_{clean_name}"

    Args:
        name: Raw event name from RPG Maker (e.g., "Town Elder", "EV001").
            May contain spaces, special characters, or be empty.
        event_id: Numeric event ID from RPG Maker, unique per map.
            Used as a prefix to guarantee label uniqueness.

    Returns:
        Valid Ren'Py label in the format "event_{id}_{name}".
        Examples: "event_5_town_elder", "event_12_ev001"

    Example:
        >>> safe_label("Town Elder", 5)
        'event_5_town_elder'
        >>> safe_label("EV001", 12)
        'event_12_ev001'
        >>> safe_label("", 3)  # Empty name
        'event_3_'  # Still valid with just ID prefix

    Note:
        The event_id prefix ensures uniqueness even if two events have
        the same name on the same map. This mirrors RPG Maker's behavior
        where event IDs are unique per map.
    """
    # Step 1: Strip leading/trailing whitespace
    # RPG Maker may include accidental whitespace in event names
    clean = name.strip()
    
    # Step 2: Replace spaces with underscores
    clean = clean.replace(" ", "_")
    
    # Step 3: Replace hyphens with underscores
    clean = clean.replace("-", "_")
    
    # Step 4: Filter to only alphanumeric and underscore characters
    # Removes any special characters that would be invalid in Ren'Py labels
    clean = "".join(char for char in clean if char.isalnum() or char == "_")
    
    # Step 5: Check if the label needs a prefix
    # Ren'Py labels must start with a letter or underscore, not a digit
    # If clean is empty (e.g., name was all special chars) or starts with a digit,
    # we prepend "ev" to make it valid
    if not clean or (not clean[0].isalpha() and clean[0] != "_"):
        clean = f"ev{clean}"
    
    # Step 6: Format the final label with event ID prefix and lowercase
    # Lowercase is a Ren'Py convention for readability
    # The event_id ensures uniqueness even if names collide
    return f"event_{event_id}_{clean}".lower()


def clean_text(text: str) -> str:
    """Remove RPG Maker escape codes and prepare text for Ren'Py strings.

    RPG Maker MV uses escape codes within dialogue text:
    - \\c[N]: Color code (N is color index 0-31)
    - \\n: Line break (separate TEXT_LINE commands in JSON)
    - \\\\: Literal backslash (double backslash)
    - \\I[N]: Icon placeholder
    - \\V[N]: Variable interpolation
    - \\N[N]: Actor name placeholder

    This function handles the most common codes (color codes, line breaks)
    and prepares the text for embedding in Ren'Py dialogue strings.

    Transformation Rules:
    1. Remove all color codes: \\c[N] -> (removed)
    2. Convert line breaks to spaces: \\n -> (space)
    3. Strip leading/trailing whitespace
    4. Escape double quotes for Ren'Py string literals

    Args:
        text: Raw RPG Maker text with escape codes.
        Example: \"\\\\c[3]Hello\\\\nWorld\" (note: JSON escapes backslashes)

    Returns:
        Cleaned text safe for Ren'Py dialogue strings.
        Example: \"Hello World\"

    Example:
        >>> clean_text(\"\\\\c[3]Hello World\")  # Color code removed
        'Hello World'
        >>> clean_text(\"Line 1\\\\nLine 2\")  # Line break -> space
        'Line 1 Line 2'
        >>> clean_text('He said \"Hello\"')  # Quotes escaped
        'He said \\\\\"Hello\\\\\"'

    Note:
        Variable interpolation (\\V[N]) and actor names (\\N[N]) are NOT
        handled by this function. They would need manual translation
        to Ren'Py's text interpolation syntax: [var_N] or [actor_N].

    Note:
        This function is used in the default (non-multiline) mode where
        all TEXT_LINE commands from a SHOW_TEXT block are concatenated
        into a single Ren'Py dialogue line.
    """
    # Step 1: Remove RPG Maker color escape codes
    # Pattern: \c[ followed by one or more digits, followed by ]
    # Example: \c[3] sets text color to color index 3
    # In JSON, backslashes are escaped, so we match \\c which represents \c in the text
    # The regex \c\((\d+)\) matches the escaped form: backslash, 'c', open paren, digits, close paren
    # We use re.sub to replace all matches with empty string (remove them)
    text = re.sub(r"\\c\[\d+\]", "", text)
    
    # Step 2: Convert RPG Maker line breaks to spaces
    # RPG Maker uses \n for manual line breaks within text
    # Ren'Py wraps text automatically, so we collapse line breaks to spaces
    # This ensures multi-line RPG Maker text becomes single-line Ren'Py dialogue
    # In JSON, the backslash is escaped, so \\n represents \n in the text
    text = text.replace("\\n", " ")
    
    # Step 3: Trim leading/trailing whitespace
    # RPG Maker text may have accidental leading/trailing spaces or line breaks
    # Stripping ensures clean output for Ren'Py
    text = text.strip()
    
    # Step 4: Escape double quotes for embedding in Ren'Py string literals
    # Ren'Py dialogue uses double quotes: e "Hello"
    # If the text contains quotes, they must be escaped: e "He said \\"Hi\\""
    # We replace " with \" to escape it for the Ren'Py string
    text = text.replace('"', '\\"')
    
    # Return the fully cleaned text
    return text


def clean_text_preserve_lines(text: str) -> str:
    r"""Remove RPG Maker escape codes while preserving internal line breaks.

    This is a variant of clean_text() used in multiline dialogue mode.
    Instead of collapsing line breaks to spaces, this function preserves
    them so each TEXT_LINE can be emitted on its own line in Ren'Py
    triple-quoted strings.

    Transformation Rules:
    1. Remove all color codes: \c[N] → (removed)
    2. Strip leading/trailing whitespace (per line, not whole text)
    3. Escape double quotes for Ren'Py string literals

    Args:
        text: Raw RPG Maker text with escape codes.
        Example: "\\c[3]Hello" (color code will be removed)

    Returns:
        Cleaned text with line breaks preserved.
        Example: "Hello" (color code removed, quotes preserved)

    Example:
        >>> clean_text_preserve_lines("\\c[3]Hello")
        'Hello'
        >>> clean_text_preserve_lines('He said "Hello"')
        'He said \\"Hello\\"'

    Note:
        This function is called for each TEXT_LINE command individually
        when the generator is in multiline mode. The generator then
        buffers these cleaned lines and emits them as a triple-quoted
        Ren'Py string when the buffer is flushed.

    Note:
        Unlike clean_text(), this function does NOT convert \n to spaces.
        The line breaks are preserved for triple-quoted string formatting.

    See Also:
        clean_text: The single-line variant that collapses line breaks.
        RenPyGenerator._flush_multiline_text: Emits the buffered lines.
    """
    # Step 1: Remove RPG Maker color escape codes
    # Same pattern as clean_text(): \c[N] where N is a digit sequence
    text = re.sub(r"\\c\[\d+\]", "", text)
    
    # Step 2: Strip leading/trailing whitespace
    # This removes any surrounding whitespace but preserves internal line breaks
    # (i.e., \n characters in the middle of the text are kept)
    text = text.strip()
    
    # Step 3: Escape double quotes for Ren'Py string literals
    # Same as clean_text(): replace " with \"
    text = text.replace('"', '\\"')
    
    # Return the cleaned text with line breaks preserved
    return text


def side_image_tag(face_name: str) -> str:
    """Convert an RPG Maker face asset name to a Ren'Py image tag.

    Ren'Py side images use a tag system for displaying character portraits.
    The tag identifies which image variant to show (e.g., different expressions).
    This function converts RPG Maker's face asset naming conventions to
    Ren'Py-compatible image tags.

    RPG Maker Face Asset Naming:
    - "$" prefix: Large sprite (used for important characters)
    - "!" prefix: No shadow (used for floating characters)
    - CamelCase: Standard naming (e.g., "SailorSkipper")
    - Numbers: Often used for generic NPCs (e.g., "People3")

    Ren'Py Image Tag Requirements:
    - Lowercase alphanumeric and underscores only
    - Used in "image side {tag}" declarations
    - Referenced in Character(image="{tag}") definitions

    Transformation Rules:
    1. Remove "$" and "!" prefixes (RPG Maker sprite markers)
    2. Insert underscores at camelCase boundaries: "SailorSkipper" → "Sailor_Skipper"
    3. Replace remaining spaces with underscores
    4. Convert to lowercase
    5. Filter to alphanumeric and underscore characters only

    Args:
        face_name: Raw face asset name from RPG Maker.
            Examples: "$Claire", "!SailorSkipper", "People3"

    Returns:
        Safe Ren'Py image tag.
        Examples: "claire", "sailor_skipper", "people3"

    Example:
        >>> side_image_tag("$Claire")
        'claire'
        >>> side_image_tag("!SailorSkipper")
        'sailor_skipper'
        >>> side_image_tag("People3")
        'people3'

    Note:
        The tag is used in two places:
        1. In side_images.rpy: "image side {tag} {face_id} = ..."
        2. In characters.rpy: "Character(..., image=\"{tag}\")"

    Note:
        Multiple face IDs from the same asset share the same tag.
        For example, faces 0-7 from "$Claire" all use tag "claire" with
        different face_id numbers: "image side claire 0", "image side claire 1", etc.

    See Also:
        generate_side_images_rpy: Uses this to create image declarations.
        generate_characters_rpy: Uses this in Character definitions.
    """
    # Step 1: Remove RPG Maker asset prefixes
    # "$" prefix indicates a large sprite (usually important characters)
    # "!" prefix indicates no shadow (for floating or special sprites)
    # Neither has meaning in Ren'Py, so we strip them
    name = face_name.replace("$", "").replace("!", "")
    
    # Step 2: Insert underscores at camelCase boundaries
    # Pattern: lowercase letter followed by uppercase letter
    # Example: "SailorSkipper" → "Sailor_Skipper"
    # The regex ([a-z])([A-Z]) captures two groups and inserts "_" between them
    # This makes multi-word names readable as separate words
    name = re.sub(r"([a-z])([A-Z])", r"\1_\2", name)
    
    # Step 3: Replace any remaining spaces with underscores
    # Handles cases where the name already has spaces (uncommon but possible)
    # The regex \s+ matches one or more whitespace characters
    name = re.sub(r"\s+", "_", name)
    
    # Step 4: Convert to lowercase
    # Ren'Py tags are conventionally lowercase for readability
    # Also ensures case-insensitive matching (Ren'Py treats tags as lowercase)
    name = name.lower()
    
    # Step 5: Filter to only alphanumeric and underscore characters
    # Removes any remaining special characters that would be invalid in tags
    # This is a defensive step to ensure the result is always valid
    return "".join(char for char in name if char.isalnum() or char == "_")


def to_title_case(name: str) -> str:
    """Convert a map name to title case for folder/file names.
    
    Converts map names to title case where the first letter of each word is capitalized.
    This provides more readable folder names than all uppercase or all lowercase.
    
    Transformation Rules:
    1. Replace underscores with spaces (for names that already have underscores)
    2. Convert to title case (capitalize first letter of each word)
    3. Replace spaces with underscores
    4. Filter to only alphanumeric and underscore characters
    5. Replace consecutive underscores with a single underscore
    6. Ensure the result is valid for filesystem (starts with letter/underscore)
    
    Args:
        name: Raw map name from MapInfos.json.
            Examples: "VALOS", "Outer Valos", "The_Brugginwood"
    
    Returns:
        Title case name safe for filesystem.
        Examples: "Valos", "Outer_Valos", "The_Brugginwood"
    
    Example:
        >>> to_title_case("VALOS")
        'Valos'
        >>> to_title_case("Outer Valos")
        'Outer_Valos'
        >>> to_title_case("The_Brugginwood")
        'The_Brugginwood'
    
    Note:
        This function preserves existing underscores and title casing.
        If the name is already in title case, it will be unchanged.
    """
    # Step 1: Replace underscores with spaces for consistent processing
    # This handles names like "The_Brugginwood" that already have underscores
    name_with_spaces = name.replace("_", " ")
    
    # Step 2: Convert to title case
    # This capitalizes the first letter of each word
    title_cased = name_with_spaces.title()
    
    # Step 3: Replace spaces with underscores for filesystem compatibility
    # Folders cannot have spaces in most filesystems
    with_underscores = title_cased.replace(" ", "_")
    
    # Step 4: Filter to only alphanumeric and underscore characters
    # Removes any special characters that would be invalid in folder names
    # This matches the same pattern used in safe_var() for consistency
    sanitized = "".join(char for char in with_underscores if char.isalnum() or char == "_")
    
    # Step 5: Replace consecutive underscores with a single underscore
    # This handles cases where special characters were removed, leaving double underscores
    # Example: "HOME & REFUGEE CAMP" -> "Home__Refugee_Camp" -> "Home_Refugee_Camp"
    while "__" in sanitized:
        sanitized = sanitized.replace("__", "_")
    
    # Step 6: Ensure the result is valid for filesystem
    # Folder names should start with a letter or underscore, not a digit
    # If it starts with a digit, prepend an underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = f"_{sanitized}"
    
    return sanitized


def safe_map_label(map_id: int, map_name: str) -> str:
    """Build a safe Ren'Py global label name for a map.

    Constructs a label in the form ``map_{id}_{Title_Case_Name}``, matching the
    naming convention used for map placeholder files and map entry labels.

    The title-cased name portion uses :func:`to_title_case` to produce a
    readable, filesystem-safe segment.

    Args:
        map_id: Numeric map ID (from filename or MapInfos.json).
        map_name: Raw map name (e.g., "Refugee Camp", "CHECKPOINT").

    Returns:
        Safe Ren'Py label string.
        Examples: ``"map_3_Refugee_Camp"``, ``"map_1_Checkpoint"``

    Example:
        >>> safe_map_label(3, "Refugee Camp")
        'map_3_Refugee_Camp'
        >>> safe_map_label(1, "CHECKPOINT")
        'map_1_Checkpoint'
    """
    return f"map_{map_id}_{to_title_case(map_name)}"


def join_with_interlines(lines: list[str], interlines: int) -> str:
    """Join output lines with configurable blank-line spacing, skipping comments.

    When interlines is 0, behaves like a standard ``"\\n".join(lines)``.
    When interlines > 0, inserts that many blank lines between each pair of
    **code** lines (non-comment, non-empty).  Comment lines (starting with
    ``#``) and intentionally empty lines are kept compact — no extra spacing
    is added around them.

    This prevents the interlines option from inflating comment header blocks
    or creating unnecessary gaps around structural blank lines.

    Args:
        lines: The output lines to join (code, comments, blanks).
        interlines: Number of blank lines to insert between code lines.
            ``0`` means standard single-newline join.
            ``1`` means one blank line between code lines, etc.

    Returns:
        The final file content as a single string.

    Example:
        >>> join_with_interlines(["# Header", "label start:", '    e "Hi"'], 1)
        '# Header\\nlabel start:\\n\\n    e "Hi"'
        # Note: no extra blank line between "# Header" and "label start:"
    """
    # Step 1: If interlines is 0 or negative, use standard join behavior
    # This preserves the default single-newline separation between all lines
    if interlines <= 0:
        return "\n".join(lines)

    # Step 2: Build the multi-newline separator for code-to-code spacing
    # interlines=1 produces "\\n\\n" (one blank line between content)
    # interlines=2 produces "\\n\\n\\n" (two blank lines between content)
    separator = "\n" * (interlines + 1)

    # Step 3: Iterate through lines and join with smart spacing
    # We only insert the interlines separator when BOTH the current line
    # and the next line are "code" (not comments, not empty).
    # Otherwise we insert a single newline to keep things compact.
    result: list[str] = []

    for i, line in enumerate(lines):
        # Append the current line to the result
        result.append(line)

        # Check if there is a next line to consider spacing for
        if i < len(lines) - 1:
            next_line = lines[i + 1]

            # Determine if the current line is a comment or empty
            # Comments start with "#" (possibly indented)
            # Empty lines are intentional structural separators already in the buffer
            current_is_comment_or_empty = line.lstrip().startswith("#") or line.strip() == ""

            # Determine if the next line is a comment or empty
            next_is_comment_or_empty = next_line.lstrip().startswith("#") or next_line.strip() == ""

            # Only add interlines spacing when both lines are regular code
            if not current_is_comment_or_empty and not next_is_comment_or_empty:
                # Both are code lines — insert the full interlines separator
                result.append(separator)
            else:
                # At least one line is a comment or empty — use a single newline
                # This keeps comment blocks and empty lines compact
                result.append("\n")

    # Step 4: Join all pieces into the final output string
    return "".join(result)


def make_indent(indent_width: int, level: int = 1) -> str:
    """Generate indentation string with configurable width.

    Args:
        indent_width: Number of spaces per indentation level.
        level: Indentation level (number of levels to indent).

    Returns:
        String of spaces representing the indentation.

    Example:
        >>> make_indent(4, 1)
        '    '
        >>> make_indent(4, 2)
        '        '
        >>> make_indent(2, 1)
        '  '
        >>> make_indent(2, 3)
        '      '
    """
    return " " * (indent_width * level)


def apply_case(text: str, mode: str) -> str:
    """Apply case transformation to text based on the specified mode.

    Args:
        text: The text to transform.
        mode: The case mode - "lower", "title", or "upper".

    Returns:
        The transformed text.

    Example:
        >>> apply_case("Claire", "lower")
        'claire'
        >>> apply_case("claire", "title")
        'Claire'
        >>> apply_case("claire", "upper")
        'CLAIRE'
    """
    if mode == "lower":
        return text.lower()
    elif mode == "title":
        return text.title()
    elif mode == "upper":
        return text.upper()
    else:
        return text
