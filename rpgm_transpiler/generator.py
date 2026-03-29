"""Core Ren'Py code generator for RPG Maker MV map events.

This module implements the second-pass generator that converts RPG Maker MV map event
data into Ren'Py .rpy script source. It handles dialogue text, player choices,
conditional branches, switch/variable modifications, map transfers, sound effects,
plugin commands, and more.

Architecture Overview:
The generator uses a stateful approach with three main components:
1. Output buffer (self.lines): Accumulates generated Ren'Py lines
2. Indentation tracking (self.indent_level, _push, _pop): Manages Ren'Py block structure
3. Text buffer (self._text_buffer): Accumulates multi-line dialogue before emitting

Text Buffering Strategy:
RPG Maker splits dialogue into SHOW_TEXT + TEXT_LINE commands. The generator buffers
TEXT_LINE content and only emits when:
- A non-text command appears (flush before processing)
- The event/page ends (final flush)
- The speaker changes (new SHOW_TEXT flushes the old buffer)

This allows proper handling of multi-line dialogue and Ren'Py's triple-quoted strings.

Command Dispatch:
The _emit_command_list method is the main dispatch loop. It iterates over RPG Maker
commands and routes each to the appropriate handler based on the command code.
Complex commands (choices, conditionals) are handled by dedicated methods that
scan forward through the command list to collect branch contents.

Ren'Py Output Format:
Generated .rpy files follow this structure:
1. Header comment with map name and ID
2. Autorun events under a single map_{id}_enter label
3. Regular events as individual callable labels
4. Each label ends with 'return'

Each event has a comment header showing its ID, name, and position for debugging.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .constants import CMD
from .collector import DataCollector
from .helpers import (
    safe_var, safe_label, safe_map_label, clean_text,
    clean_text_preserve_lines, join_with_interlines,
)


@dataclass
class MapGenerationResult:
    """Holds generated Ren'Py source for a single map's components.

    Each field contains a complete .rpy file content string ready to be
    written to disk. The map placeholder calls each autorun event in
    sequence, while every event file uses a fully qualified local label
    under the map's global label.

    Attributes:
        map_label: Content for the map placeholder file
            (e.g., ``map_3_Refugee_Camp.rpy``).
            Contains the global label and calls to autorun events.
        autorun: Mapping of event ID → (source, filename_suffix) for each autorun event.
            ``source`` is the complete .rpy file content.
            ``filename_suffix`` is the descriptive label string
            (e.g., ``"event_57_auto"``) used to build the filename:
            ``{map_label_name}_{filename_suffix}.rpy``.
        events: Mapping of event ID → (source, filename_suffix) for each regular event.
            ``source`` is the complete .rpy file content.
            ``filename_suffix`` is the descriptive label string
            (e.g., ``"event_40_under"``) used to build the filename:
            ``{map_label_name}_{filename_suffix}.rpy``.
        map_label_name: The global label name used across all files
            (e.g., ``"map_3_Refugee_Camp"``).
    """
    map_label: str
    autorun: dict[int, tuple[str, str]] = field(default_factory=dict)
    events: dict[int, tuple[str, str]] = field(default_factory=dict)
    map_label_name: str = ""


class RenPyGenerator:
    """Generates Ren'Py .rpy source files from RPG Maker MV map data.

    The RenPyGenerator processes a single map's events and produces a complete
    .rpy file with labels for each event, dialogue lines, menu choices,
    conditional branches, and state-modifying commands.

    Instance Lifecycle:
    1. __init__: Store map data, collector reference, and configuration
    2. generate(): Main entry point that orchestrates emission
    3. _emit_header(): Write file header
    4. _emit_events(): Process all events (autorun + regular)
    5. Return the accumulated output as a string

    State Management:
    - lines: Output buffer, accumulates Ren'Py script lines
    - indent_level: Current indentation depth (4 spaces per level)
    - _text_buffer: Accumulated dialogue lines waiting to be emitted
    - _current_speaker: Active character name (or None for narration)
    - _current_face: Active face asset name for side image lookup
    - _current_face_id: Active face ID for expression variant

    Multiline Mode:
    When multiline=True, the generator emits multi-line dialogue as Ren'Py
    triple-quoted strings instead of single-line concatenations. This preserves
    the original line structure from RPG Maker.

    Example Output Structure:
        # ═══════════════════════════════════════════════════
        # Town Square (Map ID: 1)
        # Auto-generated from RPG Maker MV
        # ═══════════════════════════════════════════════════

        # ── Autorun sequence ──
        label map_1_enter:
            # Event 5: "Intro"
            claire "Welcome to the town!"
            return

        # ── Event 3: "Shopkeeper" (pos 5,7) ──
        label event_3_shopkeeper:
            shopkeeper "What would you like to buy?"
            menu:
                "Potion":
                    $ game_economy.gold -= 50
                "Nothing":
                    pass
            return
    """

    def __init__(
        self,
        map_data: dict[str, Any],
        collector: DataCollector,
        map_id: int = 0,
        all_map_data: dict[int, dict[str, Any]] | None = None,
        multiline: bool = False,
        interlines: int = 0,
        map_name: str | None = None,
        indent_width: int = 4,
    ) -> None:
        """Initialize the generator with map data and shared metadata.

        Sets up the output buffer, indentation tracking, and text buffering
        state. Stores references to the map data and collector for use during
        generation.

        Args:
            map_data: Parsed JSON for this specific map.
                Expected structure:
                {
                    "displayName": str,
                    "events": [event_dict | null, ...]
                }
            collector: Shared DataCollector with character/switch/variable metadata.
                Used to look up character display names and validate references.
            map_id: Numeric ID of this map (from filename).
                Used in label names: map_{id}_enter, map_{id}_events
            all_map_data: All parsed maps, keyed by map ID.
                Used for cross-map references (transfer targets).
                If None, the generator cannot resolve transfer target names.
            multiline: If True, emit multi-line dialogue as Ren'Py triple-quoted strings.
                Otherwise, concatenate TEXT_LINE commands into single dialogue lines.
        interlines: Number of blank lines to insert between each output line.
        Default 0 means no extra spacing.
        map_name: Human-readable name for this map (from MapInfos.json).
        If None, falls back to displayName from map_data or "Unknown".
        Used in file header comments.
        indent_width: Number of spaces per indentation level.
        Defaults to 4.

        Example:
            >>> collector = DataCollector()
            >>> collector.collect_from_map(map_data, 1)
            >>> generator = RenPyGenerator(map_data, collector, 1, {1: map_data})
            >>> rpy_source = generator.generate()
        """
        # Store the map's parsed JSON data
        # This is the source data for all event processing
        self.map_data = map_data
        
        # Store the collector reference
        # Used to look up character names from face asset names
        self.collector = collector
        
        # Store the map ID
        # Used in label names to ensure uniqueness across maps
        self.map_id = map_id
        
        # Store all map data for cross-map references
        # Used when emitting TRANSFER_PLAYER commands to show target map names
        self.all_map_data = all_map_data or {}
        
        # Store the multiline mode flag
        # True: emit dialogue as triple-quoted strings
        # False: emit dialogue as single lines (TEXT_LINE concatenation)
        self.multiline = multiline

        # Store the interlines count
        # Number of blank lines to insert between each output line
        # 0 = default (no extra spacing), 1 = single blank line between lines, etc.
        self.interlines = interlines

        # Store the map name for use in header comments
        # Priority: provided map_name > displayName from map_data > "Unknown"
        self.map_name = map_name or map_data.get("displayName", "Unknown")

        # Store the indent width for use in _indent method
        # Number of spaces per indentation level
        self.indent_width = indent_width

        # Store the global label name for this map
        # Used for local label qualification: map_{id}_{Title_Case_Name}
        # Example: "map_3_Refugee_Camp"
        self.map_label_name = safe_map_label(map_id, self.map_name)

        # Store the Ren'Py named store name for this map's self-switches
        # Used in self-switch references: $ map_{id}_{name}_self_switches.switch_{eid}_{ch} = True
        self.map_store_name = collector.get_self_switch_store_name(map_id)

        # Build a lookup dict of event_id → safe_label for descriptive self-switch names
        # Example: {40 → "event_40_under", 57 → "event_57_auto"}
        # Used to generate switch_40_under_A instead of switch_40_A
        self._event_names: dict[int, str] = {}
        for event in map_data.get("events", []):
            if event is not None:
                eid = event["id"]
                ename = event.get("name", f"EV{eid:03d}")
                self._event_names[eid] = safe_label(ename, eid)

        # Initialize the output buffer
        # All generated Ren'Py lines are appended here
        self.lines: list[str] = []
        
        # Initialize indentation tracking
        # 0 = no indentation, each level adds 4 spaces
        self.indent_level = 0
        
        # Initialize the text buffer for dialogue accumulation
        # TEXT_LINE commands append here, flush emits as dialogue
        self._text_buffer: list[str] = []
        
        # Track the current speaker for dialogue emission
        # Set by SHOW_TEXT, used when flushing text buffer
        # None means narration (no speaker prefix)
        self._current_speaker: str | None = None
        
        # Track the current face asset name
        # Used for side image lookup in characters.rpy
        self._current_face: str | None = None
        
        # Track the current face ID
        # Used to select expression variant in side_images.rpy
        # None means no face (narration)
        self._current_face_id: int | None = None

    def _indent(self) -> str:
        """Return the current indentation prefix.

        Ren'Py uses 4-space indentation for blocks (labels, if/else, menu).
        This method returns the appropriate number of spaces based on the indent_width setting.

        Returns:
            String of spaces matching the current indentation depth.
            Example: level 2 with indent_width 4 → "        " (8 spaces)
            Example: level 2 with indent_width 2 → "    " (4 spaces)

        Example:
            >>> self.indent_level = 2
            >>> self.indent_width = 4
            >>> self._indent()
            '        '  # 8 spaces
            >>> self.indent_width = 2
            >>> self._indent()
            '    '  # 4 spaces
        """
        # Calculate indentation: indent_width spaces per indent level
        return " " * (self.indent_level * self.indent_width)

    def _emit(self, line: str = "") -> None:
        """Append a line to the output buffer with current indentation.

        Non-empty lines are prefixed with the current indentation.
        Empty lines are emitted without indentation (for readability).

        This is the primary method for adding content to the output.
        All other emission methods call _emit internally.

        Args:
            line: The Ren'Py script line to append.
                Empty string (default) emits a blank line.

        Example:
            >>> self.indent_level = 1
            >>> self._emit('label start:')
            # Appends: "    label start:" (4 spaces + content)
            >>> self._emit()
            # Appends: "" (blank line, no indentation)
        """
        # Check if the line has content
        if line:
            # Non-empty line: prepend with current indentation
            # This ensures proper Ren'Py block structure
            self.lines.append(self._indent() + line)
        else:
            # Empty line: emit as-is for readability
            # Empty lines separate sections without indentation
            self.lines.append("")

    def _push(self) -> None:
        """Increase indentation by one level (4 spaces).

        Called when entering a new Ren'Py block:
        - After a label: label foo: → _push()
        - After an if/elif/else: if condition: → _push()
        - After a menu option: "Choice": → _push()

        Must be paired with _pop() to maintain correct indentation.

        Example:
            >>> self.indent_level = 0
            >>> self._push()  # Enter label block
            >>> self.indent_level
            1
            >>> self._push()  # Enter nested if block
            >>> self.indent_level
            2
        """
        # Increment the indent level by 1
        self.indent_level += 1

    def _pop(self) -> None:
        """Decrease indentation by one level (4 spaces), clamped to 0.

        Called when exiting a Ren'Py block:
        - After the last statement in a label block: _pop()
        - After an if/elif/else block ends: _pop()
        - After a menu option's statements: _pop()

        Safe to call even if indent_level is 0 (clamps to 0).

        Example:
            >>> self.indent_level = 2
            >>> self._pop()  # Exit nested if block
            >>> self.indent_level
            1
            >>> self._pop()  # Exit label block
            >>> self.indent_level
            0
            >>> self._pop()  # Safe, stays at 0
            >>> self.indent_level
            0
        """
        # Decrement indent level, but never go below 0
        # max(0, ...) prevents negative indentation
        self.indent_level = max(0, self.indent_level - 1)

    def _self_switch_name(self, event_id: int, channel: str) -> str:
        """Build a descriptive self-switch variable name.

        Uses the event's safe label to produce readable names like
        ``switch_40_under_A`` instead of the generic ``switch_40_A``.

        Args:
            event_id: The numeric event ID.
            channel: The self-switch channel letter (``"A"``, ``"B"``, ``"C"``, ``"D"``).

        Returns:
            Descriptive self-switch variable name.
            Example: ``"switch_40_under_A"``
        """
        label = self._event_names.get(event_id, "")
        if label:
            # Strip "event_" prefix: "event_40_under" → "40_under"
            name_part = label.replace("event_", "", 1)
            return f"switch_{name_part}_{channel}"
        return f"switch_{event_id}_{channel}"

    def generate(self) -> MapGenerationResult:
        """Generate Ren'Py source split into map placeholder, autorun, and event files.

        Main entry point for the generator.  Produces a :class:`MapGenerationResult`
        whose fields contain the complete .rpy content for:

        - The map placeholder (global label that calls autorun events)
        - One file per autorun event (fully qualified local labels)
        - One file per regular event (fully qualified local labels)

        Returns:
            MapGenerationResult with all generated file contents.

        Example:
            >>> result = generator.generate()
            >>> result.map_label_name
            'map_3_Refugee_Camp'
            >>> result.map_label
            'label map_3_Refugee_Camp:\\n    call .event_3_auto\\n    return'
        """
        # Classify events into autorun and regular
        autorun_events, regular_events = self._classify_events()

        # Generate the map placeholder file
        map_label = self._generate_map_label(autorun_events)

        # Generate one autorun file per autorun event
        # Skip empty events (those with no meaningful commands)
        autorun_files: dict[int, tuple[str, str]] = {}
        for event in autorun_events:
            event_id, result_tuple = self._generate_event_file(event, is_autorun=True)
            if result_tuple is not None:
                autorun_files[event_id] = result_tuple

        # Generate one event file per regular event
        # Skip empty events (those with no meaningful commands)
        event_files: dict[int, tuple[str, str]] = {}
        for event in regular_events:
            event_id, result_tuple = self._generate_event_file(event, is_autorun=False)
            if result_tuple is not None:
                event_files[event_id] = result_tuple

        return MapGenerationResult(
            map_label=map_label,
            autorun=autorun_files,
            events=event_files,
            map_label_name=self.map_label_name,
        )

    # ── Event Classification ──

    def _classify_events(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """Separate map events into autorun and regular categories.

        RPG Maker events have a 'trigger' type on their first page:
        - Trigger 3 = autorun (fires automatically when map loads)
        - Any other trigger = regular (action button, touch, parallel, etc.)

        Returns:
            Two-tuple of (autorun_events, regular_events).
        """
        events = self.map_data.get("events", [])
        autorun_events: list[dict[str, Any]] = []
        regular_events: list[dict[str, Any]] = []

        for event in events:
            if event is None:
                continue
            pages = event.get("pages", [])
            if pages and pages[0].get("trigger") == 3:
                autorun_events.append(event)
            else:
                regular_events.append(event)

        return autorun_events, regular_events

    # ── File Generators ──

    def _emit_header_to(self, target_lines: list[str]) -> None:
        """Write the decorative header comment block into a target line list.

        This is a variant of ``_emit_header`` that writes to an arbitrary
        ``list[str]`` buffer instead of ``self.lines``, enabling generation
        of multiple independent files from the same generator instance.

        Args:
            target_lines: Mutable list to receive the header lines.
        """
        header = [
            "# ═══════════════════════════════════════════════════",
            f"# {self.map_name} (Map ID: {self.map_id})",
            "# Auto-generated from RPG Maker MV",
            "# ═══════════════════════════════════════════════════",
            "",
        ]
        target_lines.extend(header)

    def _emit_header(self) -> None:
        """Write the file header comment block into ``self.lines``.

        Header Format:
            # ═══════════════════════════════════════════════════
            # {map_name} (Map ID: {map_id})
            # Auto-generated from RPG Maker MV
            # ═══════════════════════════════════════════════════
        """
        self._emit_header_to(self.lines)

    def _generate_map_label(self, autorun_events: list[dict[str, Any]]) -> str:
        """Generate the map placeholder .rpy content.

        Produces the global label that serves as the map's entry point.
        If autorun events exist, each one is called in sequence using
        short-form local label references (``.event_X_name``).

        Output Example:
            # ═══════════════════════════════════════════════════
            # Refugee Camp (Map ID: 3)
            # Auto-generated from RPG Maker MV
            # ═══════════════════════════════════════════════════

            label map_3_Refugee_Camp:
                call .event_3_auto
                call .event_39_roadblock_setup
                return

        Args:
            autorun_events: List of classified autorun event dicts.

        Returns:
            Complete .rpy file content as a string.
        """
        buf: list[str] = []
        self._emit_header_to(buf)

        buf.append(f"label {self.map_label_name}:")

        if autorun_events:
            for event in autorun_events:
                event_name = event.get("name", f"EV{event['id']:03d}")
                label = safe_label(event_name, event["id"])
                buf.append(f"    call .{label}")

        buf.append("    return")
        buf.append("")

        return join_with_interlines(buf, self.interlines)

    def _generate_event_file(
        self,
        event: dict[str, Any],
        is_autorun: bool,
    ) -> tuple[int, tuple[str, str] | None]:
        """Generate a single .rpy file for one event.

        Creates a fully qualified local label under the map's global label
        and emits the event's page content.  Also computes the filename
        suffix (the label portion like ``"event_40_under"``) used to build
        the output filename.

        Events that contain no meaningful commands (only a label and return)
        are detected and skipped by returning ``None``.

        Args:
            event: Parsed RPG Maker event dict.
            is_autorun: Whether this is an autorun event (affects header comment).

        Returns:
            Two-tuple of ``(event_id, (source, label) | None)``.
            ``source`` is the complete .rpy file content.
            ``label`` is the safe label string for filename construction
            (e.g., ``"event_40_under"``).
            Returns ``None`` as the second element when the event is empty.
        """
        # Compute the safe label for this event
        # This is used both in the file content and for the output filename
        event_id = event["id"]
        event_name = event.get("name", f"EV{event_id:03d}")
        label = safe_label(event_name, event_id)

        # Save current output buffer and indentation state
        saved_lines = self.lines
        saved_indent = self.indent_level
        saved_text_buffer = self._text_buffer
        saved_speaker = self._current_speaker
        saved_face = self._current_face
        saved_face_id = self._current_face_id

        # Create a fresh buffer for this file
        self.lines = []
        self.indent_level = 0
        self._text_buffer = []
        self._current_speaker = None
        self._current_face = None
        self._current_face_id = None

        # Emit header and event content, passing pre-computed label
        self._emit_header()
        self._emit_event(event, use_local_label=True, label=label)

        # Join lines into final source
        source = join_with_interlines(self.lines, self.interlines)

        # Restore previous state
        self.lines = saved_lines
        self.indent_level = saved_indent
        self._text_buffer = saved_text_buffer
        self._current_speaker = saved_speaker
        self._current_face = saved_face
        self._current_face_id = saved_face_id

        # ── Detect empty events ──
        # An event is empty if its source contains no meaningful code lines
        # beyond the header, comment, label declaration, and return statement.
        # These represent decorative RPG Maker elements (torches, glows, etc.)
        # with no dialogue or gameplay logic.
        if self._is_empty_event_source(source):
            return event["id"], None

        return event["id"], (source, label)

    @staticmethod
    def _is_empty_event_source(source: str) -> bool:
        """Check whether a generated event source is empty.

        An event source is considered empty when it contains no meaningful
        code lines after stripping the file header, comment lines, the
        ``label`` declaration, and the final ``return``.

        Args:
            source: Complete .rpy file content for a single event.

        Returns:
            ``True`` if the event has no meaningful content.
        """
        for line in source.splitlines():
            stripped = line.strip()
            # Skip empty lines
            if not stripped:
                continue
            # Skip comment lines (header and inline comments)
            if stripped.startswith("#"):
                continue
            # Skip the label declaration line
            if stripped.startswith("label "):
                continue
            # Skip bare return statement
            if stripped == "return":
                continue
            # Found a meaningful line (dialogue, menu, if, $, etc.)
            return False
        # No meaningful lines found
        return True

    def _emit_event(
        self,
        event: dict[str, Any],
        use_local_label: bool = False,
        label: str | None = None,
    ) -> None:
        """Generate Ren'Py code for a single RPG Maker event.

        Creates a label for the event and processes its pages. The label
        name is derived from the event's name and ID using safe_label().

        When ``use_local_label`` is True the fully qualified local-label form
        ``label {map_label_name}.{event_label}:`` is emitted instead of a
        plain global label.  This is required when the label lives in a
        separate file from the map's global label.

        Single-Page Events:
        Events with one page emit their commands directly without conditionals.

        Multi-Page Events:
        Events with multiple pages generate an if/elif chain that checks
        each page's conditions (RPG Maker evaluates pages in reverse order).

        Args:
            event: Parsed RPG Maker event JSON object.
            use_local_label: If True, emit a fully qualified local label
                (``label {map_label_name}.{event_label}:``).
                If False, emit a plain global label (``label {event_label}:``).
            label: Pre-computed safe label string (e.g., ``"event_40_under"``).
                If None, computed from the event name and ID via ``safe_label()``.
                Passing a pre-computed label avoids duplicate computation when
                the caller already has it.

        Event Label Format:
            # ── Event {id}: "{name}" (pos {x},{y}) ──
            label map_3_Refugee_Camp.event_{id}_{sanitized_name}:
                # [page content]
                return
        """
        # Get the event's numeric ID
        event_id = event["id"]
        
        # Get the event's name, falling back to "EV{id:03d}" if missing
        # The :03d format pads with zeros: EV001, EV002, etc.
        event_name = event.get("name", f"EV{event_id:03d}")
        
        # Generate a safe Ren'Py label from the event name and ID
        # Example: "Town Elder", 5 → "event_5_town_elder"
        # Use pre-computed label if provided, otherwise compute it now
        if label is None:
            label = safe_label(event_name, event_id)
        
        # Build the fully qualified label if local mode is requested
        # Example: "map_3_Refugee_Camp.event_3_auto"
        if use_local_label:
            full_label = f"{self.map_label_name}.{label}"
        else:
            full_label = label
        
        # Get the event's pages
        pages = event.get("pages", [])

        # Emit comment header showing event ID, name, and position
        # This helps with debugging and understanding the generated code
        self._emit(f'# ── Event {event_id}: "{event_name}" (pos {event["x"]},{event["y"]}) ──')
        self._emit()

        # Check the number of pages
        if len(pages) == 1:
            # Single page: emit commands directly without conditionals
            # This is the common case for simple events
            self._emit(f"label {full_label}:")
            self._push()
            self._emit_page(pages[0], event_id)
            self._emit("return")
            self._pop()
        else:
            # Multiple pages: emit if/elif chain checking page conditions
            # RPG Maker evaluates pages in reverse order (highest first)
            self._emit(f"label {full_label}:")
            self._push()
            self._emit_multi_page(pages, event_id)
            self._emit("return")
            self._pop()

        # Emit a blank line for spacing
        self._emit()

    def _emit_multi_page(self, pages: list[dict[str, Any]], event_id: int) -> None:
        """Generate conditional block for multi-page events.

        RPG Maker events with multiple pages use a priority system:
        pages are evaluated in reverse order (highest page number first),
        and the first page whose conditions are all met is the one that runs.

        We mirror this with an if/elif chain:
        - The last page (highest index) becomes "if"
        - Earlier pages become "elif" branches in reverse order
        - Pages with no conditions use "True" (always matches)

        Emission Order:
        For pages [0, 1, 2], we emit:
            if <page 2 conditions>:
                # Page 2
                ...
            elif <page 1 conditions>:
                # Page 1
                ...
            elif True:  # Page 0 fallback
                # Page 0
                ...

        Args:
            pages: List of event page objects in RPG Maker order (index 0 = first page).
            event_id: The owning event's ID (for self-switch references in conditions).

        Note:
            We iterate in reverse order using enumerate(reversed(pages)) to
            match RPG Maker's evaluation order while tracking the actual page index.
        """
        # Iterate in reverse to match RPG Maker's priority (highest page number first)
        # reverse_index tracks our position in the reversed list
        # actual_page_index is the original index (for comments)
        for reverse_index, page in enumerate(reversed(pages)):
            # Calculate the actual page index in the original list
            # If we have 3 pages [0, 1, 2], reversed is [2, 1, 0]
            # reverse_index 0 → actual_page_index 2
            # reverse_index 1 → actual_page_index 1
            # reverse_index 2 → actual_page_index 0
            actual_page_index = len(pages) - 1 - reverse_index

            # Build the Ren'Py condition expression from the page's conditions
            page_conditions = page.get("conditions", {})
            condition_expression = self._build_renpy_condition(page_conditions, event_id)

            # Determine the condition keyword (if vs elif)
            # First iteration (reverse_index 0) uses "if", rest use "elif"
            condition_keyword = "if" if reverse_index == 0 else "elif"
            
            # Emit the condition line
            if condition_expression:
                # Has conditions: emit the condition expression
                self._emit(f"{condition_keyword} {condition_expression}:")
            else:
                # No conditions: emit True (always matches)
                # This is the fallback page in RPG Maker
                if reverse_index == 0:
                    # First (highest priority) page with no conditions
                    self._emit(f"{condition_keyword} True:")
                else:
                    # Later pages with no conditions (shouldn't happen often)
                    self._emit(f"elif True: # page {actual_page_index} fallback")

            # Enter the conditional block
            self._push()
            
            # Emit a comment identifying the page
            self._emit_comment(f"Page {actual_page_index}")
            
            # Emit the page's commands
            self._emit_page(page, event_id)
            
            # Exit the conditional block
            self._pop()

    def _emit_page(self, page: dict[str, Any], event_id: int) -> None:
        """Generate Ren'Py code for a single event page.

        Processes the page's command list, emitting all commands.
        Handles text buffering by flushing before and after command processing.

        Process:
        1. Flush any pending text from previous pages
        2. Emit all commands in the page's list
        3. Flush any remaining text

        Args:
            page: Parsed event page JSON with 'list' of commands.
                Expected structure:
                {
                    "conditions": dict,
                    "trigger": int,
                    "list": [command_dict, ...]
                }
            event_id: The owning event's ID (for self-switch references).

        Note:
            Double flushing (before and after) ensures all text is emitted
            even if the command list ends with dialogue.
        """
        # Get the command list from the page
        command_list = page.get("list", [])
        
        # Flush any pending text from previous processing
        # This ensures we start with a clean buffer
        self._flush_text()
        
        # Emit all commands in the list
        self._emit_command_list(command_list, event_id)
        
        # Flush any remaining text after all commands
        # This emits any dialogue at the end of the command list
        self._flush_text()

    def _emit_command_list(self, commands: list[dict[str, Any]], event_id: int) -> None:
        """Process a list of RPG Maker commands and emit Ren'Py equivalents.

        This is the main command dispatch loop. It walks through the command
        array, handling each command type by emitting the appropriate Ren'Py
        script lines. Text lines are buffered; other commands flush the buffer first.

        Command Processing Flow:
        1. Iterate through commands with a while loop (allows index manipulation)
        2. Check the command code against CMD dictionary
        3. Route to appropriate handler
        4. Update command_index (some handlers return new index)

        Text Buffering:
        TEXT_LINE commands don't emit immediately—they append to _text_buffer.
        The buffer is flushed when:
        - A non-text command appears (call _flush_text before processing)
        - The command list ends (call _flush_text after processing)

        Complex Commands:
        SHOW_CHOICES and CONDITIONAL require scanning forward through the command
        list to collect branch contents. These handlers return the updated index.

        Args:
            commands: Array of RPG Maker command objects.
                Each command has: code (int), indent (int), parameters (list)
            event_id: The owning event's ID (for self-switch references).

        Note:
            We use a while loop instead of for because some handlers
            need to advance the index past multiple commands (e.g., choice blocks).
        """
        # Initialize the command index
        # We use a while loop to allow index manipulation
        command_index = 0
        
        # Iterate through commands
        while command_index < len(commands):
            # Get the current command
            command = commands[command_index]
            
            # Extract the command code
            command_code = command["code"]
            
            # Extract the parameters array
            parameters = command.get("parameters", [])

            # ── END (code 0): End of command list ──
            # Stop processing when we hit the END command
            if command_code == CMD["END"]:
                break

            # ── SHOW_TEXT (code 101): Start of dialogue block ──
            # Sets the speaker and face for subsequent TEXT_LINE commands
            elif command_code == CMD["SHOW_TEXT"]:
                # Flush any pending text before changing speakers
                self._flush_text()
                
                # Extract face asset name (first parameter)
                face_asset_name = parameters[0] if len(parameters) > 0 else ""
                
                # Extract face ID (second parameter, default 0)
                face_id = parameters[1] if len(parameters) > 1 else 0
                
                # Check if a face asset is specified
                if face_asset_name:
                    # Look up the display name from collected character data
                    # This converts asset names like "$Claire" to "Claire"
                    self._current_speaker = self.collector.characters.get(face_asset_name, face_asset_name)
                    
                    # Store the face asset name for side image lookup
                    self._current_face = face_asset_name
                    
                    # Store the face ID for expression variant
                    self._current_face_id = face_id
                else:
                    # No face: this is narration (no speaker prefix)
                    self._current_speaker = None
                    self._current_face = None
                    self._current_face_id = None

            # ── TEXT_LINE (code 401): Dialogue text line ──
            # Appended to the text buffer for later emission
            elif command_code == CMD["TEXT_LINE"]:
                # Get the dialogue text from parameters
                dialogue_text = parameters[0] if parameters else ""
                
                # Clean the text based on multiline mode
                if self.multiline:
                    # Preserve line breaks for triple-quoted strings
                    dialogue_text = clean_text_preserve_lines(dialogue_text)
                else:
                    # Convert line breaks to spaces
                    dialogue_text = clean_text(dialogue_text)
                
                # Append to the text buffer
                # Multiple TEXT_LINEs accumulate until flushed
                self._text_buffer.append(dialogue_text)

            # ── SHOW_CHOICES (code 102): Player choice menu ──
            # Emits a Ren'Py menu block with choice options
            elif command_code == CMD["SHOW_CHOICES"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract choice labels (first parameter)
                choice_labels = parameters[0] if parameters else []
                
                # Extract cancel behavior (fourth parameter)
                # 0 = disallow cancel, 1 = cancel, 2 = cancel branch
                cancel_behavior = parameters[3] if len(parameters) > 3 else 0
                
                # Emit the choice block and get the updated command index
                # _emit_choice_block scans forward to collect branch commands
                command_index = self._emit_choice_block(
                    commands, command_index, choice_labels, cancel_behavior, event_id
                )
                # Skip the increment at the bottom (index already updated)
                continue

            # ── CONDITIONAL (code 111): If/else branch ──
            # Emits a Ren'Py if/elif/else block
            elif command_code == CMD["CONDITIONAL"]:
                # Flush any pending text
                self._flush_text()
                
                # Emit the conditional block and get the updated command index
                # _emit_conditional_block scans forward to collect branch commands
                command_index = self._emit_conditional_block(commands, command_index, event_id)
                # Skip the increment at the bottom (index already updated)
                continue

            # ── CONTROL_SWITCHES (code 121): Set global switches ──
            # Emits: $ game_switch.switch_{id}_{name} = True/False
            elif command_code == CMD["CONTROL_SWITCHES"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract range bounds and value
                start_id, end_id, value = parameters[0], parameters[1], parameters[2]
                
                # Convert RPG Maker value to Ren'Py boolean
                # RPG Maker: 0 = ON (True), 1 = OFF (False)
                renpy_value = "True" if value == 0 else "False"
                
                # Emit assignment for each switch in the range
                for switch_id in range(start_id, end_id + 1):
                    # Get the store-prefixed variable name (game_switch.switch_{id}_{name})
                    variable_name = self.collector.get_switch_store_name(switch_id)
                    self._emit(f"$ {variable_name} = {renpy_value}")

            # ── CONTROL_VARIABLES (code 122): Modify variables ──
            # Emits: $ game_vars.var_{id}_{name} = value or $ game_vars.var_{id}_{name} += value
            elif command_code == CMD["CONTROL_VARIABLES"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract range bounds
                start_id, end_id = parameters[0], parameters[1]
                
                # Extract operation type
                # 0=set, 1=add, 2=subtract, 3=multiply, 4=divide, 5=mod
                operation_type = parameters[2]
                
                # Extract operand value
                operand_value = parameters[3]
                
                # Map RPG Maker operation codes to Python operators
                operator_map = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
                operator_symbol = operator_map.get(operation_type, "=")
                
                # Emit assignment for each variable in the range
                for variable_id in range(start_id, end_id + 1):
                    # Get the store-prefixed variable name (game_vars.var_{id}_{name})
                    variable_name = self.collector.get_variable_store_name(variable_id)
                    if operation_type == 0:
                        # Set operation: direct assignment
                        self._emit(f"$ {variable_name} = {operand_value}")
                    else:
                        # Other operations: compound assignment
                        self._emit(f"$ {variable_name} {operator_symbol} {operand_value}")

            # ── CONTROL_SELF_SWITCH (code 123): Toggle event-local switch ──
            # Emits: $ map_{id}_{name}_self_switches.switch_{id}_{name}_{channel} = True/False
            elif command_code == CMD["CONTROL_SELF_SWITCH"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract channel letter (A, B, C, or D)
                channel = parameters[0]
                
                # Convert RPG Maker value to Ren'Py boolean
                # RPG Maker: 0 = ON (True), 1 = OFF (False)
                renpy_value = "True" if parameters[1] == 0 else "False"
                
                # Build descriptive self-switch name: switch_40_under_A
                switch_name = self._self_switch_name(event_id, channel)
                
                # Emit the self-switch assignment using the per-map store
                self._emit(f"$ {self.map_store_name}.{switch_name} = {renpy_value}")

            # ── CHANGE_GOLD (code 125): Add/remove gold ──
            # Emits: $ game_economy.gold += amount or $ game_economy.gold -= amount
            elif command_code == CMD["CHANGE_GOLD"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract gold amount (third parameter)
                gold_amount = parameters[2] if len(parameters) > 2 else 0
                
                # Check operation type (first parameter)
                # 0 = increase, 1 = decrease
                if parameters[0] == 0:
                    self._emit(f"$ game_economy.gold += {gold_amount}")
                else:
                    self._emit(f"$ game_economy.gold -= {gold_amount}")

            # ── WAIT (code 230): Pause execution ──
            # Emits: pause {seconds}
            elif command_code == CMD["WAIT"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract frame count
                frame_count = parameters[0]
                
                # Convert frames to seconds
                # RPG Maker runs at 60 frames per second
                seconds = round(frame_count / 60.0, 2)
                
                # Emit the pause command
                self._emit(f"pause {seconds}")

            # ── PLAY_SE (code 250): Play sound effect ──
            # Emits: play sound "{name}.ogg"
            elif command_code == CMD["PLAY_SE"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract sound effect object (first parameter)
                sound_effect = parameters[0] if parameters else {}
                
                # Get the sound file name
                sound_name = sound_effect.get("name", "")
                
                # Only emit if a sound is specified
                if sound_name:
                    # Emit the play sound command
                    # Note: Assumes .ogg format (may need adjustment)
                    self._emit(f'play sound "{sound_name}.ogg"')

            # ── TRANSFER_PLAYER (code 201): Jump to another map ──
            # Emits: jump map_{id}_{Name}
            elif command_code == CMD["TRANSFER_PLAYER"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract target map ID (second parameter)
                target_map_id = parameters[1]
                
                # Extract target coordinates (for comment)
                target_x, target_y = parameters[2], parameters[3]
                
                # Get the target map's display name
                target_map_name = self.collector.map_names.get(target_map_id, f"Map{target_map_id}")
                
                # Build the target label using safe_map_label for consistency
                target_label = safe_map_label(target_map_id, target_map_name)
                
                # Emit comment showing transfer details
                self._emit(f'# Transfer to {target_map_name} ({target_x}, {target_y})')
                
                # Emit the jump command
                self._emit(f"jump {target_label}")

            # ── PLUGIN_COMMAND (code 356): Handle plugin command ──
            # Emits: varies based on plugin command type
            elif command_code == CMD["PLUGIN_COMMAND"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract plugin command string
                plugin_command_string = parameters[0] if parameters else ""
                
                # Delegate to plugin handler
                self._emit_plugin_command(plugin_command_string)

            # ── SCRIPT (code 355): Raw JavaScript ──
            # Cannot be transpiled, emit as comment
            elif command_code == CMD["SCRIPT"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract script content
                script_content = parameters[0] if parameters else ""
                
                # Emit as comment for manual handling
                self._emit(f"# [Script] {script_content}")

            # ── MOVE_ROUTE / MOVE_PARAM (codes 205, 505): Movement commands ──
            # Not transpiled (visual novel doesn't have sprite movement)
            elif command_code in (CMD["MOVE_ROUTE"], CMD["MOVE_PARAM"]):
                # Skip silently
                pass

            # ── Unknown command: Emit as TODO comment ──
            else:
                # Flush any pending text
                self._flush_text()
                
                # Emit TODO comment with command details
                self._emit(f"# [TODO: code={command_code}] params={parameters}")

            # Increment command index
            command_index += 1

    def _emit_choice_block(
        self,
        commands: list[dict[str, Any]],
        start_index: int,
        choice_labels: list[str],
        cancel_type: int,
        event_id: int,
    ) -> int:
        """Generate a Ren'Py menu block from RPG Maker choice commands.

        Walks through the command list starting after SHOW_CHOICES, collecting
        commands for each WHEN_CHOICE and WHEN_CANCEL branch, then emits them
        as Ren'Py menu options.

        Choice Block Structure:
        After SHOW_CHOICES, the command list contains:
        - WHEN_CHOICE (code 402): Marks start of a choice branch
        - END_CHOICES (code 404): Marks end of the choice block
        - WHEN_CANCEL (code 403): Optional cancel branch

        Scanning Process:
        1. Scan forward from start_index + 1
        2. Collect commands into choice_command_map for each choice index
        3. Collect cancel branch commands separately
        4. Stop at END_CHOICES

        Ren'Py Emission:
        The collected commands are emitted inside each menu option:
            menu:
                "Choice 1":
                    # commands for choice 1
                "Choice 2":
                    # commands for choice 2

        Args:
            commands: Full command array for the event page.
            start_index: Index of the SHOW_CHOICES command.
            choice_labels: List of choice text strings to display.
            cancel_type: Cancel behavior (0=disallow, 1=cancel, 2=branch).
            event_id: The owning event's ID (for nested command processing).

        Returns:
            Updated command index after processing the entire choice block.
            Points to the command after END_CHOICES.

        Example:
            For this RPG Maker command structure:
                SHOW_CHOICES: ["Yes", "No"]
                WHEN_CHOICE: 0
                    SHOW_TEXT: ...
                    TEXT_LINE: "You chose Yes"
                WHEN_CHOICE: 1
                    SHOW_TEXT: ...
                    TEXT_LINE: "You chose No"
                END_CHOICES

            We emit:
                menu:
                    "Yes":
                        "You chose Yes"
                    "No":
                        "You chose No"
        """
        # Emit the menu keyword
        self._emit("menu:")
        
        # Enter the menu block
        self._push()

        # Initialize scanning state
        scan_index = start_index + 1  # Start after SHOW_CHOICES
        choice_command_map: dict[int, list[dict[str, Any]]] = {}  # choice_index → commands
        cancel_commands: list[dict[str, Any]] = []  # cancel branch commands
        current_choice_index: int | None = None  # Which choice we're collecting for
        collected_commands: list[dict[str, Any]] = []  # Current branch's commands
        is_collecting = False  # Are we inside a WHEN_CHOICE/WHEN_CANCEL block?

        # Compute the expected indent level for branch terminator END commands.
        # We use source JSON indents (not Ren'Py output indents) for tracking.
        # Find the SHOW_CHOICES indent from the command at start_index.
        # For nested menus in collected branch commands, the source indents are offset
        # from the parent. We compute the base indent as the minimum indent in the
        # scanned range so that WHEN_CHOICE at the same level as SHOW_CHOICES is found.
        show_choices_indent = commands[start_index].get("indent", 0)
        expected_branch_indent = show_choices_indent       # WHEN_CHOICE indent
        expected_terminator_indent = show_choices_indent + 1  # Branch content/terminator indent

        # Scan forward through commands to collect choice branch contents
        while scan_index < len(commands):
            command = commands[scan_index]
            command_code = command["code"]

            # WHEN_CHOICE: Start collecting for a specific choice
            # Only handle WHEN_CHOICE at our level (same indent as SHOW_CHOICES)
            # Nested WHEN_CHOICE at deeper levels are collected as part of the branch
            if command_code == CMD["WHEN_CHOICE"] and command.get("indent", 0) == expected_branch_indent:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Start collecting for this new choice index
                current_choice_index = command["parameters"][0]
                collected_commands = []
                is_collecting = True

            # WHEN_CANCEL: Start collecting for the cancel branch
            # Only handle WHEN_CANCEL at our level
            elif command_code == CMD["WHEN_CANCEL"] and command.get("indent", 0) == expected_branch_indent:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Reset to collect into cancel_commands
                current_choice_index = None
                collected_commands = cancel_commands
                is_collecting = True

            # END_CHOICES: Stop scanning
            # Only handle END_CHOICES at our level (same indent as SHOW_CHOICES)
            elif command_code == CMD["END_CHOICES"] and command.get("indent", 0) == expected_branch_indent:
                # Save the last choice's commands
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Move past END_CHOICES
                scan_index += 1
                break

            # END: Either a branch terminator or a nested structure terminator
            elif command_code == CMD["END"]:
                # Check if this END terminates the current choice branch
                # A branch terminator END is followed by either:
                #   - Another WHEN_CHOICE (next branch)
                #   - END_CHOICES (end of all branches)
                # A nested structure terminator END is followed by other commands
                # (ELSE, ELSE_BRANCH, more nested commands, etc.)
                # We peek ahead to determine which case this is.
                end_indent = command.get("indent", 0)
                next_index = scan_index + 1
                next_code = commands[next_index]["code"] if next_index < len(commands) else -1

                # This is a branch terminator if:
                # 1. At the expected terminator indent AND followed by WHEN_CHOICE or END_CHOICES
                # 2. Or at the expected terminator indent and is_collecting is True
                is_branch_terminator = (
                    end_indent == expected_terminator_indent
                    and (
                        next_code == CMD["WHEN_CHOICE"]
                        or next_code == CMD["WHEN_CANCEL"]
                        or next_code == CMD["END_CHOICES"]
                        or next_code == CMD["END"]
                    )
                )

                if is_branch_terminator:
                    # Branch terminator: save current branch and continue scanning
                    if current_choice_index is not None:
                        choice_command_map[current_choice_index] = collected_commands
                        collected_commands = []
                        current_choice_index = None
                        is_collecting = False
                    elif collected_commands is cancel_commands:
                        is_collecting = False
                else:
                    # Nested END: collect it as part of the branch
                    if is_collecting:
                        collected_commands.append(command)

            # Any other command: Append to current branch's collection
            else:
                if is_collecting:
                    collected_commands.append(command)

            # Move to next command
            scan_index += 1

        # Emit each choice as a Ren'Py menu option
        for choice_index, choice_text in enumerate(choice_labels):
            # Clean the choice text
            cleaned_choice_text = clean_text(choice_text)
            
            # Emit the choice option
            self._emit(f'"{cleaned_choice_text}":')
            
            # Enter the choice block
            self._push()
            
            # Get the commands for this choice
            choice_commands = choice_command_map.get(choice_index, [])
            
            # Emit the commands
            self._emit_command_list(choice_commands, event_id)
            
            # Flush any pending text
            self._flush_text()
            
            # Exit the choice block
            self._pop()

        # Emit cancel option if behavior allows it and commands exist
        # cancel_type 2 means cancel has its own command branch
        if cancel_type == 2 and cancel_commands:
            self._emit('"(Cancel)":')
            self._push()
            self._emit_command_list(cancel_commands, event_id)
            self._flush_text()
            self._pop()

        # Exit the menu block
        self._pop()
        
        # Return the updated command index
        return scan_index

    def _emit_conditional_block(
        self,
        commands: list[dict[str, Any]],
        start_index: int,
        event_id: int,
    ) -> int:
        """Generate a Ren'Py if/else block from an RPG Maker conditional branch.

        Processes the CONDITIONAL command, then walks forward through the
        command list, emitting sub-commands until END_CONDITIONAL or ELSE
        is encountered. Handles nested conditionals recursively.

        Conditional Block Structure:
        After CONDITIONAL, the command list contains:
        - Sub-commands for the "if" branch
        - ELSE (code 411): Marks start of else branch (optional)
        - END_CONDITIONAL (code 412): Marks end of the block

        Nested Conditionals:
        CONDITIONAL commands can be nested. We track the indent level to
        determine which END_CONDITIONAL matches the current block.

        Scanning Process:
        1. Parse the condition from CONDITIONAL parameters
        2. Emit "if {condition}:"
        3. Scan forward, emitting commands until ELSE or END_CONDITIONAL
        4. If ELSE found, emit "else:" and continue scanning
        5. If END_CONDITIONAL found at the right indent level, stop

        Args:
            commands: Full command array for the event page.
            start_index: Index of the CONDITIONAL command.
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Updated command index after processing the entire conditional block.
            Points to the command after END_CONDITIONAL.

        Example:
            For this RPG Maker command structure:
                CONDITIONAL: switch 5 is ON
                    SHOW_TEXT: ...
                    TEXT_LINE: "Switch is on"
                ELSE
                    SHOW_TEXT: ...
                    TEXT_LINE: "Switch is off"
                END_CONDITIONAL

            We emit:
                if switch_5:
                    "Switch is on"
                else:
                    "Switch is off"
        """
        # Parse the condition from the CONDITIONAL command's parameters
        conditional_command = commands[start_index]
        condition_parameters = conditional_command.get("parameters", [])
        
        # Build the Ren'Py condition expression
        condition_expression = self._parse_condition_expr(condition_parameters, event_id)

        # Emit the if statement
        self._emit(f"if {condition_expression}:")
        
        # Enter the if block
        self._push()

        # Initialize scanning state
        scan_index = start_index + 1  # Start after CONDITIONAL
        expected_indent_depth = 1  # Track nesting to find matching END_CONDITIONAL

        # Scan forward through commands
        while scan_index < len(commands):
            sub_command = commands[scan_index]
            sub_command_code = sub_command["code"]
            sub_command_indent = sub_command.get("indent", 0)

            # ELSE: Switch to else branch at the same indent level
            # The indent check ensures we don't catch ELSE from nested conditionals
            if sub_command_code == CMD["ELSE"] and sub_command_indent < expected_indent_depth:
                # Flush any pending text
                self._flush_text()
                
                # Exit the if block
                self._pop()
                
                # Emit the else statement
                self._emit("else:")
                
                # Enter the else block
                self._push()

            # END_CONDITIONAL: End of this conditional block
            # The indent check ensures we don't catch END_CONDITIONAL from nested conditionals
            elif sub_command_code == CMD["END_CONDITIONAL"] and sub_command_indent < expected_indent_depth:
                # Flush any pending text
                self._flush_text()
                
                # Exit the conditional block
                self._pop()
                
                # Move past END_CONDITIONAL
                scan_index += 1
                break

            # Nested CONDITIONAL: Recurse to handle inner if/else
            elif sub_command_code == CMD["CONDITIONAL"]:
                # Flush any pending text
                self._flush_text()
                
                # Recursively emit the nested conditional
                scan_index = self._emit_conditional_block(commands, scan_index, event_id)
                
                # Skip the increment at the bottom (already advanced by recursive call)
                continue

            # Premature END: Stop processing
            elif sub_command_code == CMD["END"]:
                # Flush any pending text
                self._flush_text()
                
                # Exit the conditional block
                self._pop()
                break

            # Any other command: Emit as a single command
            else:
                self._emit_single_command(sub_command, event_id)

            # Move to next command
            scan_index += 1

        # Return the updated command index
        return scan_index

    def _emit_single_command(self, command: dict[str, Any], event_id: int) -> None:
        """Emit a single command outside the main dispatch loop.

        Used for commands inside conditional blocks and choice branches where
        the full command list processing is not appropriate. Handles a subset
        of command types that commonly appear in these contexts.

        Commands Handled:
        - CONTROL_SWITCHES: Set switches
        - CONTROL_VARIABLES: Modify variables
        - CONTROL_SELF_SWITCH: Toggle self-switches
        - CHANGE_GOLD: Add/remove gold
        - PLUGIN_COMMAND: Handle plugin commands
        - WAIT: Pause execution
        - PLAY_SE: Play sound effect
        - TRANSFER_PLAYER: Jump to another map

        Not Handled:
        - SHOW_TEXT / TEXT_LINE: Use text buffering instead
        - SHOW_CHOICES: Would require recursive menu handling
        - CONDITIONAL: Handled by _emit_conditional_block

        Args:
            command: Single RPG Maker command object (code + parameters).
            event_id: The owning event's ID (for self-switch references).
        """
        # Extract command code and parameters
        command_code = command["code"]
        parameters = command.get("parameters", [])

        # ── CONTROL_SWITCHES: Set switches ──
        if command_code == CMD["CONTROL_SWITCHES"]:
            start_id, end_id, value = parameters[0], parameters[1], parameters[2]
            renpy_value = "True" if value == 0 else "False"
            for switch_id in range(start_id, end_id + 1):
                # Get the store-prefixed variable name (game_switch.switch_{id}_{name})
                variable_name = self.collector.get_switch_store_name(switch_id)
                self._emit(f"$ {variable_name} = {renpy_value}")

        # ── CONTROL_VARIABLES: Modify variables ──
        elif command_code == CMD["CONTROL_VARIABLES"]:
            start_id, end_id = parameters[0], parameters[1]
            operation_type = parameters[2]
            operand_value = parameters[3]
            operator_map = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
            for variable_id in range(start_id, end_id + 1):
                # Get the store-prefixed variable name (game_vars.var_{id}_{name})
                variable_name = self.collector.get_variable_store_name(variable_id)
                if operation_type == 0:
                    self._emit(f"$ {variable_name} = {operand_value}")
                else:
                    self._emit(f"$ {variable_name} {operator_map.get(operation_type, '=')} {operand_value}")

        # ── CONTROL_SELF_SWITCH: Toggle self-switch ──
        elif command_code == CMD["CONTROL_SELF_SWITCH"]:
            channel = parameters[0]
            renpy_value = "True" if parameters[1] == 0 else "False"
            switch_name = self._self_switch_name(event_id, channel)
            self._emit(f"$ {self.map_store_name}.{switch_name} = {renpy_value}")

        # ── CHANGE_GOLD: Add/remove gold ──
        elif command_code == CMD["CHANGE_GOLD"]:
            gold_amount = parameters[2] if len(parameters) > 2 else 0
            if parameters[0] == 0:
                self._emit(f"$ game_economy.gold += {gold_amount}")
            else:
                self._emit(f"$ game_economy.gold -= {gold_amount}")

        # ── PLUGIN_COMMAND: Handle plugin command ──
        elif command_code == CMD["PLUGIN_COMMAND"]:
            plugin_command_string = parameters[0] if parameters else ""
            self._emit_plugin_command(plugin_command_string)

        # ── WAIT: Pause execution ──
        elif command_code == CMD["WAIT"]:
            frame_count = parameters[0]
            seconds = round(frame_count / 60.0, 2)
            self._emit(f"pause {seconds}")

        # ── PLAY_SE: Play sound effect ──
        elif command_code == CMD["PLAY_SE"]:
            sound_effect = parameters[0] if parameters else {}
            sound_name = sound_effect.get("name", "")
            if sound_name:
                self._emit(f'play sound "{sound_name}.ogg"')

        # ── TRANSFER_PLAYER: Jump to another map ──
        elif command_code == CMD["TRANSFER_PLAYER"]:
            target_map_id = parameters[1]
            target_map_name = self.collector.map_names.get(target_map_id, f"Map{target_map_id}")
            target_label = safe_map_label(target_map_id, target_map_name)
            self._emit(f"jump {target_label}")

    def _build_renpy_condition(self, conditions: dict[str, Any], event_id: int) -> str:
        """Convert RPG Maker event page conditions to a Ren'Py expression.

        Builds an `and`-joined expression from all valid conditions on an
        event page. Each condition becomes a check against a Ren'Py variable.

        Condition Types:
        - switch1Valid: Global switch must be True
        - switch2Valid: Second global switch must be True
        - variableValid: Variable must be >= threshold
        - selfSwitchValid: Self-switch must be True
        - itemValid: Player must have 1+ of item

        All conditions are ANDed together (all must be true for the page to run).

        Args:
            conditions: The 'conditions' dict from an event page.
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Ren'Py condition expression (e.g., "game_switch.switch_5 and game_vars.var_3 >= 10").
            Returns empty string if no conditions are set.

        Example:
            >>> conditions = {"switch1Valid": True, "switch1Id": 5}
            >>> self._build_renpy_condition(conditions, 1)
            'game_switch.switch_5'

            >>> conditions = {"switch1Valid": True, "switch1Id": 5, "variableValid": True, "variableId": 3, "variableValue": 10}
            >>> self._build_renpy_condition(conditions, 1)
            'game_switch.switch_5 and game_vars.var_3 >= 10'
        """
        # Initialize the list of condition checks
        condition_checks: list[str] = []

        # Condition type 1: First global switch must be ON
        if conditions.get("switch1Valid"):
            switch_id = conditions["switch1Id"]
            # Get the store-prefixed variable name (game_switch.switch_{id}_{name})
            variable_name = self.collector.get_switch_store_name(switch_id)
            # Check if switch is True (ON)
            condition_checks.append(variable_name)

        # Condition type 2: Second global switch must be ON
        if conditions.get("switch2Valid"):
            switch_id = conditions["switch2Id"]
            # Get the store-prefixed variable name (game_switch.switch_{id}_{name})
            variable_name = self.collector.get_switch_store_name(switch_id)
            condition_checks.append(variable_name)

        # Condition type 3: Variable must meet threshold
        if conditions.get("variableValid"):
            variable_id = conditions["variableId"]
            threshold_value = conditions["variableValue"]
            # Get the store-prefixed variable name (game_vars.var_{id}_{name})
            variable_name = self.collector.get_variable_store_name(variable_id)
            # Check if variable >= threshold
            condition_checks.append(f"{variable_name} >= {threshold_value}")

        # Condition type 4: Self-switch must be ON
        if conditions.get("selfSwitchValid"):
            channel = conditions.get("selfSwitchCh", "A")
            # Build descriptive self-switch name: switch_40_under_A
            switch_name = self._self_switch_name(event_id, channel)
            # Check if self-switch is True using the per-map store
            condition_checks.append(f"{self.map_store_name}.{switch_name}")

        # Condition type 5: Item requirement
        if conditions.get("itemValid"):
            item_id = conditions["itemId"]
            # Check if player has 1+ of item using the items store
            condition_checks.append(f"game_items.item_{item_id} > 0")

        # Join all conditions with "and"
        return " and ".join(condition_checks) if condition_checks else ""

    def _parse_condition_expr(self, parameters: list[Any], event_id: int) -> str:
        """Convert RPG Maker conditional branch parameters to a Ren'Py expression.

        Handles multiple condition types used in CONDITIONAL commands:
        - Type 0: Switch check (ON/OFF)
        - Type 1: Variable comparison (==, >=, <=, >, <, !=)
        - Type 2: Self-switch check (ON/OFF)
        - Type 6: Script expression (passed through)
        - Type 7: Gold comparison

        RPG Maker Comparison Codes:
        For variable/gold comparisons, RPG Maker uses:
        - 0: == (equal) or >= (for gold, depending on context)
        - 1: >= (greater than or equal)
        - 2: <= (less than or equal)
        - 3: > (greater than)
        - 4: < (less than)
        - 5: != (not equal)

        Args:
            parameters: The parameters array from a CONDITIONAL command.
                Format: [condition_type, ...type_specific_params]
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Ren'Py condition expression string.
            Returns "True" for unknown condition types.

        Example:
            >>> # Switch check
            >>> self._parse_condition_expr([0, 5, 0], 1)  # switch 5 is ON
            'game_switch.switch_5'

            >>> # Variable comparison
            >>> self._parse_condition_expr([1, 3, 1, 10], 1)  # var_3 >= 10
            'game_vars.var_3 >= 10'
        """
        # Get the condition type (first parameter)
        condition_type = parameters[0]

        # ── Condition type 0: Switch check ──
        if condition_type == 0:
            # Extract switch ID and expected value
            switch_id = parameters[1]
            expected_value = parameters[2]
            
            # Get the store-prefixed variable name (game_switch.switch_{id}_{name})
            variable_name = self.collector.get_switch_store_name(switch_id)
            
            # Build the condition expression
            if expected_value == 0:
                # Expected ON: switch is True
                return variable_name
            else:
                # Expected OFF: switch is False (use "not")
                return f"not {variable_name}"

        # ── Condition type 1: Variable comparison ──
        elif condition_type == 1:
            # Extract variable ID, comparison type, and value
            variable_id = parameters[1]
            comparison_type = parameters[2]
            comparison_value = parameters[3]
            
            # Map RPG Maker comparison codes to Python operators
            comparison_map = {0: "==", 1: ">=", 2: "<=", 3: ">", 4: "<", 5: "!="}
            comparison_operator = comparison_map.get(comparison_type, "==")
            
            # Get the store-prefixed variable name (game_vars.var_{id}_{name})
            variable_name = self.collector.get_variable_store_name(variable_id)
            
            # Build the condition expression
            return f"{variable_name} {comparison_operator} {comparison_value}"

        # ── Condition type 2: Self-switch check ──
        elif condition_type == 2:
            # Extract channel and expected value
            channel = parameters[1]
            expected_value = parameters[2]
            
            # Build descriptive self-switch name: switch_40_under_A
            switch_name = self._self_switch_name(event_id, channel)
            
            # Build the condition expression using the per-map store
            if expected_value == 0:
                # Expected ON: self-switch is True
                return f"{self.map_store_name}.{switch_name}"
            else:
                # Expected OFF: self-switch is False (use "not")
                return f"not {self.map_store_name}.{switch_name}"

        # ── Condition type 7: Gold comparison ──
        elif condition_type == 7:
            # Extract comparison type and gold amount
            comparison_type = parameters[1]
            gold_amount = parameters[2]
            
            # Map RPG Maker comparison codes to Python operators
            # Note: Gold comparison uses different mapping than variables
            comparison_map = {0: ">=", 1: "<=", 2: "<", 3: ">", 4: "==", 5: "!="}
            comparison_operator = comparison_map.get(comparison_type, ">=")
            
            # Build the condition expression using the economy store
            return f"game_economy.gold {comparison_operator} {gold_amount}"

        # ── Condition type 6: Script expression ──
        elif condition_type == 6:
            # Pass through the script expression as-is
            # This is a raw JavaScript expression that would need manual translation
            return parameters[1] if len(parameters) > 1 else "True"

        # ── Unknown condition type: Fallback ──
        else:
            return "True"

    def _emit_plugin_command(self, plugin_command_string: str) -> None:
        """Handle RPG Maker plugin command strings.

        Known plugin commands are translated to Ren'Py equivalents.
        Unknown plugin commands are logged as comments for manual handling.

        Currently Handled Plugins:
        - Quest: Appends to quest_log and displays as dialogue

        Plugin Command Format:
        Plugin commands are free-form strings. We check for known prefixes
        and handle them accordingly.

        Args:
            plugin_command_string: The raw plugin command string from RPG Maker.
                Example: "Quest Add main_quest_001"

        Note:
            This is a basic implementation. Game-specific plugins would need
            custom handling added here.
        """
        # Check if the command string is empty
        if not plugin_command_string:
            return

        # ── Quest plugin ──
        # Handle quest-related commands by logging and displaying
        if plugin_command_string.startswith("Quest"):
            # Append to quest log for tracking
            self._emit(f'$ game_quest.quest_log.append("{plugin_command_string}")')
            
            # Display the quest notification as dialogue
            self._emit(f'"{plugin_command_string}"')

        # ── Unknown plugin command ──
        # Log as a comment for manual handling
        else:
            self._emit(f'# [Plugin] {plugin_command_string}')

    def _flush_text(self) -> None:
        """Flush the text buffer to emit accumulated dialogue lines.

        Joins all buffered text lines with spaces, then emits a single
        Ren'Py dialogue line. If a speaker is set, includes the speaker's
        variable name; otherwise emits as narrator text.

        Text Buffering Context:
        RPG Maker splits dialogue into SHOW_TEXT + TEXT_LINE commands.
        - SHOW_TEXT sets the speaker and face
        - TEXT_LINE(s) contain the actual text

        We buffer TEXT_LINE content and only emit when:
        - A non-text command appears (flush before processing)
        - The event/page ends (flush after processing)
 - The speaker changes (flush before new SHOW_TEXT)

 Multiline Mode:
 When multiline=True and buffer has 2+ lines, emit as triple-quoted string.
 Example (using TQ to represent triple quotes):
     claire TQ
     Hello there.
     Nice to meet you.
     TQ

 Single-Line Mode (default):
 Join buffer entries with spaces:
     claire "Hello there. Nice to meet you."

 Face ID Handling:
 If a face ID is set, include it after the speaker:
     claire 2 "Hello"
 This allows Ren'Py to select the correct side image variant.
 """
        # Check if the text buffer is empty
        if not self._text_buffer:
            return

        # Check for multiline mode with 2+ lines
        if self.multiline and len(self._text_buffer) >= 2:
            # Emit as triple-quoted string
            self._flush_multiline_text()
            return

        # Single-line or non-multiline: join with spaces
        full_dialogue_text = " ".join(self._text_buffer)
        
        # Clear the text buffer
        self._text_buffer = []

        # Check if the text is empty after joining
        if not full_dialogue_text.strip():
            return

        # In multiline fallback (single line), normalize \n to spaces
        # This handles the case where we expected multiline but got one line
        if self.multiline:
            full_dialogue_text = full_dialogue_text.replace("\\n", " ")

        # Emit the dialogue line
        if self._current_speaker:
            # Get the safe variable name for the speaker
            speaker_variable = safe_var(self._current_speaker)
            
            # Check if we have a face ID
            if self._current_face_id is not None:
                # Emit with face ID: speaker face_id "text"
                self._emit(f'{speaker_variable} {self._current_face_id} "{full_dialogue_text}"')
            else:
                # Emit without face ID: speaker "text"
                self._emit(f'{speaker_variable} "{full_dialogue_text}"')
        else:
            # Narration: emit without speaker prefix
            self._emit(f'"{full_dialogue_text}"')

    def _flush_multiline_text(self) -> None:
        """Emit the text buffer as a Ren'Py triple-quoted multiline string.

 Each buffer entry becomes a separate line inside the triple quotes,
 indented one level deeper than the dialogue statement.

 Output Format with speaker (using TQ for triple quotes):
     speaker 2 TQ
     Line one
     Line two
     Line three
     TQ

 For narration (no speaker):
     TQ
     Line one
     Line two
     TQ
        """
        # Get the buffered lines
        lines = self._text_buffer
        
        # Clear the text buffer
        self._text_buffer = []
        
        # Get the base indentation
        base_indent = self._indent()
        
        # Calculate the content indentation (one level deeper)
        content_indent = base_indent + " "

        # Emit based on speaker presence
        if self._current_speaker:
            # Get the safe variable name for the speaker
            speaker_variable = safe_var(self._current_speaker)
            
            # Build the prefix (speaker + optional face ID)
            prefix = f"{speaker_variable} {self._current_face_id}" if self._current_face_id is not None else speaker_variable
            
            # Emit the opening triple quote
            self.lines.append(f'{base_indent}{prefix} """')
            
            # Emit each line with content indentation
            for line in lines:
                self.lines.append(f"{content_indent}{line}")
            
            # Emit the closing triple quote
            self.lines.append(f'{base_indent}"""')
        else:
            # Narration: emit without speaker prefix
            # Emit the opening triple quote
            self.lines.append(f'{base_indent}"""')
            
            # Emit each line with content indentation
            for line in lines:
                self.lines.append(f"{content_indent}{line}")
            
            # Emit the closing triple quote
            self.lines.append(f'{base_indent}"""')

    def _emit_comment(self, comment_text: str) -> None:
        """Emit a Ren'Py comment line.

        Comments are prefixed with "# " and help document the generated code.

        Args:
            comment_text: The comment content (without the leading '#').
                Will be prefixed with "# " in the output.

        Example:
            >>> self._emit_comment("Page 0")
            # Emits: "# Page 0"
        """
        # Emit the comment with "# " prefix
        self._emit(f"# {comment_text}")
