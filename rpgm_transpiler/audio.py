"""Generates audio.rpy with Ren'Py audio variable definitions.

This module creates the audio.rpy file containing `define audio.` statements for every
audio asset (BGM, BGS, SE, ME) discovered during the collection phase. Each definition
maps a sanitized variable name to the audio file path within the `audio/` directory tree.

Audio Types in RPG Maker MV vs Ren'Py:
RPG Maker MV has four audio categories:
- BGM (Background Music): Looping music tracks for maps/events
- BGS (Background Sound): Looping ambient audio (rain, wind, crowd)
- SE (Sound Effect): One-shot sounds triggered by events
- ME (Music Effect): Short musical stings (fanfares, jingles)

Ren'Py has default channels:
- music: For background music (maps to BGM and ME)
- sound: For sound effects (maps to SE)
- No default BGS channel — requires custom channel registration

Output Format:
    # ── BGM (Background Music) ──
    define audio.bgm_Paths_of_Peril = "audio/bgm/Paths of Peril.ogg"
    define audio.bgm_Dungeon2 = "audio/bgm/Dungeon2.ogg"

    # ── BGS (Background Sound) ──
    define audio.bgs_Night = "audio/bgs/Night.ogg"
    define audio.bgs_Whispers = "audio/bgs/Whispers.ogg"

    # ── SE (Sound Effects) ──
    define audio.se_Move1 = "audio/se/Move1.ogg"

    # ── ME (Music Effects) ──
    define audio.me_Inn = "audio/me/Inn.ogg"

Naming Convention:
- Variable names use dot notation: audio.bgm_Paths_of_Peril
- Spaces and hyphens in original names become underscores
- File paths preserve original RPG Maker names (including spaces)
- audio/{type}/{OriginalName}.{ext}

Channel Registration:
The file includes a comment noting that a 'bgs' channel must be registered
if any BGS audio is present:
    init python:
        renpy.music.register_channel("bgs", mixer="sfx", loop=True)
"""

from .collector import DataCollector
from .helpers import join_with_interlines, safe_audio_var


def generate_audio_rpy(
    collector: DataCollector,
    audio_ext: str = "ogg",
    interlines: int = 0,
    indent_width: int = 4,
) -> str:
    """Generate audio.rpy with define statements for all discovered audio assets.

    Creates a .rpy file containing `define audio.{var} = "path"` declarations for
    every unique BGM, BGS, SE, and ME audio file found during collection. Also
    includes a comment about registering the custom 'bgs' channel if BGS audio
    is present.

    The definitions are organized by audio type (BGM, BGS, SE, ME) with section
    headers. Each type's entries are sorted alphabetically for consistent output.

    Args:
        collector: DataCollector instance populated with audio data.
            Required attributes:
            - audio_bgm: set of BGM file names (e.g., {"Paths of Peril", "Dungeon2"})
            - audio_bgs: set of BGS file names (e.g., {"Night", "Whispers"})
            - audio_se: set of SE file names (e.g., {"Move1", "Bell3"})
            - audio_me: set of ME file names (e.g., {"Inn"})
        audio_ext: File extension for audio files (default: "ogg").
            Supported: ogg, opus, mp3, mp2, flac, wav.
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.
        indent_width: Number of spaces per indentation level (default: 4).
            Used for the channel registration code block.

    Returns:
        Complete .rpy source string for audio.rpy.
        Returns header with "no audio found" message if no audio references were found.

    Example:
        >>> collector = DataCollector()
        >>> collector.audio_bgm = {"Paths of Peril", "Dungeon2"}
        >>> collector.audio_se = {"Move1"}
        >>> source = generate_audio_rpy(collector, audio_ext="ogg")
        >>> # source contains define audio.bgm_Paths_of_Peril = "audio/bgm/Paths of Peril.ogg"
        >>> #         and define audio.bgm_Dungeon2 = "audio/bgm/Dungeon2.ogg"
        >>> #         and define audio.se_Move1 = "audio/se/Move1.ogg"

    Note:
        The dot notation `define audio.bgm_X` is used so that Ren'Py's `play`
        statement can find the audio variable in the audio namespace automatically:
        play music bgm_Paths_of_Peril

    Note:
        Actual audio files (.ogg, etc.) are NOT copied by the transpiler.
        The user must manually copy them to the output `audio/` directory
        maintaining the same folder structure.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# AUDIO DEFINITIONS")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # Track whether any definitions were generated
    has_any_audio = bool(
        collector.audio_bgm or collector.audio_bgs
        or collector.audio_se or collector.audio_me
    )

    # If no audio at all, return just the header (still useful as a placeholder)
    if not has_any_audio:
        output_lines.append("# No audio references found in the input data.")
        output_lines.append("")
        return join_with_interlines(output_lines, interlines)

    # ── Audio Channel Registration ──
    # Register custom channels for all audio types used in the game.
    # This replaces Ren'Py's default 'music' and 'sound' channels with
    # RPG Maker-style channels: bgm, bgs, se, me.
    output_lines.append("# ── Audio Channel Registration ──")
    output_lines.append("# Register custom channels for all audio types.")
    output_lines.append("# Ren'Py's default channels (music, sound) are replaced with RPG Maker-style channels.")
    output_lines.append("init python:")
    indent = " " * indent_width
    if collector.audio_bgm:
        # BGM: Background music, loops by default, uses music mixer
        output_lines.append(f'{indent}renpy.music.register_channel("bgm", mixer="music", loop=True)')
    if collector.audio_bgs:
        # BGS: Background sound (ambient), loops by default, uses sfx mixer
        output_lines.append(f'{indent}renpy.music.register_channel("bgs", mixer="sfx", loop=True)')
    if collector.audio_se:
        # SE: Sound effects, one-shot (no loop), uses sfx mixer
        output_lines.append(f'{indent}renpy.music.register_channel("se", mixer="sfx", loop=False)')
    if collector.audio_me:
        # ME: Music effects (stings/fanfares), one-shot, uses music mixer
        output_lines.append(f'{indent}renpy.music.register_channel("me", mixer="music", loop=False)')
    output_lines.append("")

    # ── BGM (Background Music) ──
    if collector.audio_bgm:
        output_lines.append("# ── BGM (Background Music) ──")
        for name in sorted(collector.audio_bgm):
            # Sanitize name for valid Python identifier
            # e.g., "Paths of Peril" → "Paths_of_Peril"
            safe_name = safe_audio_var(name)
            # Path preserves original name (with spaces)
            output_lines.append(f'define audio.bgm_{safe_name} = "audio/bgm/{name}.{audio_ext}"')
        output_lines.append("")

    # ── BGS (Background Sound) ──
    if collector.audio_bgs:
        output_lines.append("# ── BGS (Background Sound) ──")
        for name in sorted(collector.audio_bgs):
            safe_name = safe_audio_var(name)
            output_lines.append(f'define audio.bgs_{safe_name} = "audio/bgs/{name}.{audio_ext}"')
        output_lines.append("")

    # ── SE (Sound Effects) ──
    if collector.audio_se:
        output_lines.append("# ── SE (Sound Effects) ──")
        for name in sorted(collector.audio_se):
            safe_name = safe_audio_var(name)
            output_lines.append(f'define audio.se_{safe_name} = "audio/se/{name}.{audio_ext}"')
        output_lines.append("")

    # ── ME (Music Effects) ──
    if collector.audio_me:
        output_lines.append("# ── ME (Music Effects) ──")
        for name in sorted(collector.audio_me):
            safe_name = safe_audio_var(name)
            output_lines.append(f'define audio.me_{safe_name} = "audio/me/{name}.{audio_ext}"')
        output_lines.append("")

    # Join all lines with interlines spacing
    return join_with_interlines(output_lines, interlines)

    # ── BGS Channel Registration Note ──
    # Ren'Py has no default 'bgs' channel. If BGS audio is present, the user
    # needs to register a custom channel. We emit a Python block for this.
    if collector.audio_bgs:
        output_lines.append("# ── BGS Channel Registration ──")
        output_lines.append("# Ren'Py does not have a default 'bgs' channel.")
        output_lines.append("# The following registers a custom channel for background sounds.")
        output_lines.append("# Place this in a file that loads early (e.g., init.rpy) or keep it here.")
        output_lines.append("init python:")
        indent = " " * indent_width
        output_lines.append(f"{indent}renpy.music.register_channel(\"bgs\", mixer=\"sfx\", loop=True)")
        output_lines.append("")

    # ── BGM (Background Music) ──
    if collector.audio_bgm:
        output_lines.append("# ── BGM (Background Music) ──")
        for name in sorted(collector.audio_bgm):
            # Bracket notation preserves original name with spaces
            # e.g., define audio["bgm_Paths of Peril"] = "audio/bgm/Paths of Peril.ogg"
            output_lines.append(f'define audio["bgm_{name}"] = "audio/bgm/{name}.{audio_ext}"')
        output_lines.append("")

    # ── BGS (Background Sound) ──
    if collector.audio_bgs:
        output_lines.append("# ── BGS (Background Sound) ──")
        for name in sorted(collector.audio_bgs):
            output_lines.append(f'define audio["bgs_{name}"] = "audio/bgs/{name}.{audio_ext}"')
        output_lines.append("")

    # ── SE (Sound Effects) ──
    if collector.audio_se:
        output_lines.append("# ── SE (Sound Effects) ──")
        for name in sorted(collector.audio_se):
            output_lines.append(f'define audio["se_{name}"] = "audio/se/{name}.{audio_ext}"')
        output_lines.append("")

    # ── ME (Music Effects) ──
    if collector.audio_me:
        output_lines.append("# ── ME (Music Effects) ──")
        for name in sorted(collector.audio_me):
            output_lines.append(f'define audio["me_{name}"] = "audio/me/{name}.{audio_ext}"')
        output_lines.append("")

    # Join all lines with interlines spacing
    return join_with_interlines(output_lines, interlines)
