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

from typing import Any

from .constants import CMD
from .collector import DataCollector
from .helpers import safe_var, safe_label, clean_text, clean_text_preserve_lines


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
                    $ gold -= 50
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
        This method returns the appropriate number of spaces for the current
        indentation level.

        Returns:
            String of spaces matching the current indentation depth.
            Example: level 2 → "        " (8 spaces)

        Example:
            >>> self.indent_level = 2
            >>> self._indent()
            '        '  # 8 spaces
        """
        # Calculate spaces: 4 spaces per indent level
        return " " * self.indent_level

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

    def generate(self) -> str:
        """Generate the complete .rpy source for this map.

        Main entry point for the generator. Orchestrates the emission of
        the file header and all events, then returns the accumulated output.

        Process:
        1. Emit header comment with map name and ID
        2. Process all events (autorun events first, then regular events)
        3. Join accumulated lines with newlines

        Returns:
            Complete .rpy file content as a single string.
            Ready to be written to a file.

        Example:
            >>> source = generator.generate()
            >>> print(source)
            # ═══════════════════════════════════════════════════
            # Town Square (Map ID: 1)
            # ...
        """
        # Step 1: Emit the file header
        # This includes the map name, ID, and generation notice
        self._emit_header()
        
        # Step 2: Emit all events
        # This processes autorun and regular events
        self._emit_events()
        
        # Step 3: Join all lines with newlines and return
        # This produces the final .rpy file content
        # If interlines > 0, insert that many blank lines between each line
        if self.interlines > 0:
            # Create separator with interlines blank lines plus one newline
            # interlines=1 means "\n\n" (one blank line between content)
            separator = "\n" * (self.interlines + 1)
            return separator.join(self.lines)
        else:
            # Default behavior: single newline between lines
            return "\n".join(self.lines)

    def _emit_header(self) -> None:
        """Write the file header comment block.

        Emits a decorative header with the map's display name and ID.
        This helps identify which map the file corresponds to when
        reading the generated Ren'Py code.

        Header Format:
            # ═══════════════════════════════════════════════════
            # {map_name} (Map ID: {map_id})
            # Auto-generated from RPG Maker MV
            # ═══════════════════════════════════════════════════

        The double-line characters (═) visually separate the header from content.
        """
        # Use the map name stored during initialization
        # Priority: provided map_name > displayName from map_data > "Unknown"
        map_name = self.map_name
        
        # Emit the top border
        self._emit("# ═══════════════════════════════════════════════════")
        
        # Emit the map name and ID
        self._emit(f"# {map_name} (Map ID: {self.map_id})")
        
        # Emit the generation notice
        self._emit("# Auto-generated from RPG Maker MV")
        
        # Emit the bottom border
        self._emit("# ═══════════════════════════════════════════════════")
        
        # Emit a blank line for spacing
        self._emit()

    def _emit_events(self) -> None:
        """Dispatch all events, separating autorun from regular events.

        RPG Maker events have a 'trigger' type that determines when they fire:
        - Trigger 0: Action button (player must press interact)
        - Trigger 1: Player touch (fires on collision)
        - Trigger 2: Event touch (fires when event collides with player)
        - Trigger 3: Autorun (fires automatically when map loads)
        - Trigger 4: Parallel (runs in background)

        Autorun events (trigger 3) are special: they execute automatically
        when the player enters the map. We group all autorun events under
        a single map_{id}_enter label for easy navigation.

        Regular events (trigger 0 or 2) are emitted as individual callable
        labels, one per event.

        Emission Order:
        1. Autorun events under map_{id}_enter
        2. Regular events as individual labels

        Event Array Structure:
        RPG Maker stores events as an array where indices are event IDs.
        Deleted events are null entries (skipped during processing).
        """
        # Get the events array from the map data
        events = self.map_data.get("events", [])
        
        # Check if there are any events
        if not events:
            # No events: emit a comment and return
            self._emit("# No events on this map.")
            return

        # Separate events into autorun and regular categories
        autorun_events: list[dict[str, Any]] = []
        regular_events: list[dict[str, Any]] = []

        # Classify each event by its trigger type
        for event in events:
            # Skip null entries (deleted events)
            if event is None:
                continue
            
            # Get the event's pages
            pages = event.get("pages", [])
            
            # Check the first page's trigger type
            # Trigger type 3 = autorun (fires on map entry)
            # We check the first page because RPG Maker evaluates pages in reverse order
            # (highest numbered page first), but the trigger is set on page 0
            if pages and pages[0].get("trigger") == 3:
                # Autorun event: add to autorun list
                autorun_events.append(event)
            else:
                # Regular event: add to regular list
                regular_events.append(event)

        # ── Emit Autorun Events ──
        # Autorun events are grouped under a single map_{id}_enter label
        if autorun_events:
            # Emit section header comment
            self._emit("# ── Autorun sequence ──")
            
            # Emit the map entry label
            # This label is jumped to from game_flow.rpy
            self._emit(f"label map_{self.map_id}_enter:")
            
            # Enter the label block (increase indentation)
            self._push()
            
            # Emit each autorun event's commands
            for autorun_event in autorun_events:
                self._emit_event(autorun_event)
            
            # Emit return statement to exit the label
            self._emit("return")
            
            # Exit the label block (decrease indentation)
            self._pop()
            
            # Emit a blank line for spacing
            self._emit()

        # ── Emit Regular Events ──
        # Regular events get individual callable labels
        for regular_event in regular_events:
            self._emit_event(regular_event)

    def _emit_event(self, event: dict[str, Any]) -> None:
        """Generate Ren'Py code for a single RPG Maker event.

        Creates a label for the event and processes its pages. The label
        name is derived from the event's name and ID using safe_label().

        Single-Page Events:
        Events with one page emit their commands directly without conditionals.
        The page's commands are processed and emitted under the label.

        Multi-Page Events:
        Events with multiple pages generate an if/elif chain that checks
        each page's conditions. The first page whose conditions are met
        is the one that executes.

        RPG Maker Page Evaluation:
        Pages are evaluated in reverse order (highest page number first).
        The first page whose conditions are all true wins. We mirror this
        with an if/elif chain where the last page is the "if" and earlier
        pages are "elif" branches.

        Args:
            event: Parsed RPG Maker event JSON object.
                Expected structure:
                {
                    "id": int,
                    "name": str,
                    "x": int,
                    "y": int,
                    "pages": [page_dict, ...]
                }

        Event Label Format:
            # ── Event {id}: "{name}" (pos {x},{y}) ──
            label event_{id}_{sanitized_name}:
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
        label = safe_label(event_name, event_id)
        
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
            self._emit(f"label {label}:")
            self._push()
            self._emit_page(pages[0], event_id)
            self._emit("return")
            self._pop()
        else:
            # Multiple pages: emit if/elif chain checking page conditions
            # RPG Maker evaluates pages in reverse order (highest first)
            self._emit(f"label {label}:")
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
            # Emits: $ switch_{id}_{name} = True/False
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
                    # Get the concatenated variable name (switch_{id}_{name})
                    variable_name = self.collector.get_switch_name(switch_id)
                    self._emit(f"$ {variable_name} = {renpy_value}")

            # ── CONTROL_VARIABLES (code 122): Modify variables ──
            # Emits: $ var_{id}_{name} = value or $ var_{id}_{name} += value
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
                    # Get the concatenated variable name (var_{id}_{name})
                    variable_name = self.collector.get_variable_name(variable_id)
                    if operation_type == 0:
                        # Set operation: direct assignment
                        self._emit(f"$ {variable_name} = {operand_value}")
                    else:
                        # Other operations: compound assignment
                        self._emit(f"$ {variable_name} {operator_symbol} {operand_value}")

            # ── CONTROL_SELF_SWITCH (code 123): Toggle event-local switch ──
            # Emits: $ selfswitch_{event_id}_{channel} = True/False
            elif command_code == CMD["CONTROL_SELF_SWITCH"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract channel letter (A, B, C, or D)
                channel = parameters[0]
                
                # Convert RPG Maker value to Ren'Py boolean
                # RPG Maker: 0 = ON (True), 1 = OFF (False)
                renpy_value = "True" if parameters[1] == 0 else "False"
                
                # Emit the self-switch assignment
                self._emit(f"$ selfswitch_{event_id}_{channel} = {renpy_value}")

            # ── CHANGE_GOLD (code 125): Add/remove gold ──
            # Emits: $ gold += amount or $ gold -= amount
            elif command_code == CMD["CHANGE_GOLD"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract gold amount (third parameter)
                gold_amount = parameters[2] if len(parameters) > 2 else 0
                
                # Check operation type (first parameter)
                # 0 = increase, 1 = decrease
                if parameters[0] == 0:
                    self._emit(f"$ gold += {gold_amount}")
                else:
                    self._emit(f"$ gold -= {gold_amount}")

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
            # Emits: jump map_{id}_enter
            elif command_code == CMD["TRANSFER_PLAYER"]:
                # Flush any pending text
                self._flush_text()
                
                # Extract target map ID (second parameter)
                target_map_id = parameters[1]
                
                # Extract target coordinates (for comment)
                target_x, target_y = parameters[2], parameters[3]
                
                # Get the target map's display name (for comment)
                target_map_name = self.collector.map_names.get(target_map_id, f"map_{target_map_id}")
                
                # Emit comment showing transfer details
                self._emit(f'# Transfer to {target_map_name} ({target_x}, {target_y})')
                
                # Emit the jump command
                self._emit(f"jump map_{target_map_id}_enter")

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

        # Scan forward through commands to collect choice branch contents
        while scan_index < len(commands):
            command = commands[scan_index]
            command_code = command["code"]

            # WHEN_CHOICE: Start collecting for a specific choice
            if command_code == CMD["WHEN_CHOICE"]:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Start collecting for this new choice index
                current_choice_index = command["parameters"][0]
                collected_commands = []
                is_collecting = True

            # WHEN_CANCEL: Start collecting for the cancel branch
            elif command_code == CMD["WHEN_CANCEL"]:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Reset to collect into cancel_commands
                current_choice_index = None
                collected_commands = cancel_commands
                is_collecting = True

            # END_CHOICES: Stop scanning
            elif command_code == CMD["END_CHOICES"]:
                # Save the last choice's commands
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                
                # Move past END_CHOICES
                scan_index += 1
                break

            # END: Premature end of command list
            elif command_code == CMD["END"]:
                break

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
                # Get the concatenated variable name (switch_{id}_{name})
                variable_name = self.collector.get_switch_name(switch_id)
                self._emit(f"$ {variable_name} = {renpy_value}")

        # ── CONTROL_VARIABLES: Modify variables ──
        elif command_code == CMD["CONTROL_VARIABLES"]:
            start_id, end_id = parameters[0], parameters[1]
            operation_type = parameters[2]
            operand_value = parameters[3]
            operator_map = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
            for variable_id in range(start_id, end_id + 1):
                # Get the concatenated variable name (var_{id}_{name})
                variable_name = self.collector.get_variable_name(variable_id)
                if operation_type == 0:
                    self._emit(f"$ {variable_name} = {operand_value}")
                else:
                    self._emit(f"$ {variable_name} {operator_map.get(operation_type, '=')} {operand_value}")

        # ── CONTROL_SELF_SWITCH: Toggle self-switch ──
        elif command_code == CMD["CONTROL_SELF_SWITCH"]:
            channel = parameters[0]
            renpy_value = "True" if parameters[1] == 0 else "False"
            self._emit(f"$ selfswitch_{event_id}_{channel} = {renpy_value}")

        # ── CHANGE_GOLD: Add/remove gold ──
        elif command_code == CMD["CHANGE_GOLD"]:
            gold_amount = parameters[2] if len(parameters) > 2 else 0
            if parameters[0] == 0:
                self._emit(f"$ gold += {gold_amount}")
            else:
                self._emit(f"$ gold -= {gold_amount}")

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
            self._emit(f"jump map_{target_map_id}_enter")

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
            Ren'Py condition expression (e.g., "switch_5 and var_3 >= 10").
            Returns empty string if no conditions are set.

        Example:
            >>> conditions = {"switch1Valid": True, "switch1Id": 5}
            >>> self._build_renpy_condition(conditions, 1)
            'switch_5'

            >>> conditions = {"switch1Valid": True, "switch1Id": 5, "variableValid": True, "variableId": 3, "variableValue": 10}
            >>> self._build_renpy_condition(conditions, 1)
            'switch_5 and var_3 >= 10'
        """
        # Initialize the list of condition checks
        condition_checks: list[str] = []

        # Condition type 1: First global switch must be ON
        if conditions.get("switch1Valid"):
            switch_id = conditions["switch1Id"]
            # Get the concatenated variable name (switch_{id}_{name})
            variable_name = self.collector.get_switch_name(switch_id)
            # Check if switch is True (ON)
            condition_checks.append(variable_name)

        # Condition type 2: Second global switch must be ON
        if conditions.get("switch2Valid"):
            switch_id = conditions["switch2Id"]
            # Get the concatenated variable name (switch_{id}_{name})
            variable_name = self.collector.get_switch_name(switch_id)
            condition_checks.append(variable_name)

        # Condition type 3: Variable must meet threshold
        if conditions.get("variableValid"):
            variable_id = conditions["variableId"]
            threshold_value = conditions["variableValue"]
            # Get the concatenated variable name (var_{id}_{name})
            variable_name = self.collector.get_variable_name(variable_id)
            # Check if variable >= threshold
            condition_checks.append(f"{variable_name} >= {threshold_value}")

        # Condition type 4: Self-switch must be ON
        if conditions.get("selfSwitchValid"):
            channel = conditions.get("selfSwitchCh", "A")
            # Check if self-switch is True
            condition_checks.append(f"selfswitch_{event_id}_{channel}")

        # Condition type 5: Item requirement
        if conditions.get("itemValid"):
            item_id = conditions["itemId"]
            # Check if player has 1+ of item
            condition_checks.append(f"item_{item_id} > 0")

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
            'switch_5'

            >>> # Variable comparison
            >>> self._parse_condition_expr([1, 3, 1, 10], 1)  # var_3 >= 10
            'var_3 >= 10'
        """
        # Get the condition type (first parameter)
        condition_type = parameters[0]

        # ── Condition type 0: Switch check ──
        if condition_type == 0:
            # Extract switch ID and expected value
            switch_id = parameters[1]
            expected_value = parameters[2]
            
            # Get the concatenated variable name (switch_{id}_{name})
            variable_name = self.collector.get_switch_name(switch_id)
            
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
            
            # Get the concatenated variable name (var_{id}_{name})
            variable_name = self.collector.get_variable_name(variable_id)
            
            # Build the condition expression
            return f"{variable_name} {comparison_operator} {comparison_value}"

        # ── Condition type 2: Self-switch check ──
        elif condition_type == 2:
            # Extract channel and expected value
            channel = parameters[1]
            expected_value = parameters[2]
            
            # Build the condition expression
            if expected_value == 0:
                # Expected ON: self-switch is True
                return f"selfswitch_{event_id}_{channel}"
            else:
                # Expected OFF: self-switch is False (use "not")
                return f"not selfswitch_{event_id}_{channel}"

        # ── Condition type 7: Gold comparison ──
        elif condition_type == 7:
            # Extract comparison type and gold amount
            comparison_type = parameters[1]
            gold_amount = parameters[2]
            
            # Map RPG Maker comparison codes to Python operators
            # Note: Gold comparison uses different mapping than variables
            comparison_map = {0: ">=", 1: "<=", 2: "<", 3: ">", 4: "==", 5: "!="}
            comparison_operator = comparison_map.get(comparison_type, ">=")
            
            # Build the condition expression
            return f"gold {comparison_operator} {gold_amount}"

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
            self._emit(f'$ quest_log.append("{plugin_command_string}")')
            
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
