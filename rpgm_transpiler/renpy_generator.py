"""Core Ren'Py code generator for RPG Maker MV map events.

Converts a single RPG Maker MV map's event data into Ren'Py .rpy script source.
Handles dialogue text, player choices, conditional branches, switch/variable
modifications, map transfers, sound effects, plugin commands, and more.

Also exports three pure helper functions used across the package:
- safe_var(): Converts names to safe Python variable names.
- safe_label(): Converts event names to valid Ren'Py labels.
- clean_text(): Strips RPG Maker escape codes from dialogue text.
"""

# ═══════════════════════════════════════════════════════════════════
# REN'PY CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Any

from .constants import CMD
from .collector import DataCollector


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


class RenPyGenerator:
    """Generates Ren'Py .rpy source files from RPG Maker MV map data.

    Each instance processes one map's events, producing a complete .rpy file
    with labels for each event, dialogue lines, menu choices, conditional
    branches, and state-modifying commands.

    The generator uses an output buffer (self.lines) and indentation tracking
    (_push/_pop) to build properly indented Ren'Py script. A text buffer
    accumulates multi-line dialogue and flushes on command boundaries.
    """

    def __init__(self, map_data: dict[str, Any], collector: DataCollector,
                 map_id: int = 0, all_map_data: dict[int, dict[str, Any]] | None = None) -> None:
        """Initialize the generator with map data and shared metadata.

        Args:
            map_data: Parsed JSON for this specific map.
            collector: Shared DataCollector with character/switch/variable metadata.
            map_id: Numeric ID of this map (from filename).
            all_map_data: All parsed maps, keyed by map ID (for cross-map references).
        """
        self.map_data = map_data
        self.collector = collector
        self.map_id = map_id
        self.all_map_data = all_map_data or {}
        self.lines: list[str] = []           # Output buffer for generated .rpy lines
        self.indent_level = 0                # Current Ren'Py indentation depth
        self._text_buffer: list[str] = []    # Accumulates multi-line dialogue text
        self._current_speaker: str | None = None  # Active speaker name (or None for narration)
        self._current_face: str | None = None     # Active face asset name (or None)

    def _indent(self) -> str:
        """Return the current indentation prefix (4 spaces per level).

        Returns:
            String of spaces matching the current indentation depth.
        """
        return "    " * self.indent_level

    def _emit(self, line: str = "") -> None:
        """Append a line to the output buffer with current indentation.

        Empty lines are emitted without indentation to preserve readability.

        Args:
            line: The Ren'Py script line to append (or empty string for blank line).
        """
        if line:
            self.lines.append(self._indent() + line)
        else:
            self.lines.append("")

    def _push(self) -> None:
        """Increase indentation by one level (4 spaces)."""
        self.indent_level += 1

    def _pop(self) -> None:
        """Decrease indentation by one level (4 spaces), clamped to 0."""
        self.indent_level = max(0, self.indent_level - 1)

    def generate(self) -> str:
        """Generate the complete .rpy source for this map.

        Returns:
            Complete .rpy file content as a single string.
        """
        self._emit_header()
        self._emit_events()
        return "\n".join(self.lines)

    def _emit_header(self) -> None:
        """Write the file header comment block with map name and ID."""
        map_name = self.map_data.get("display_name", "Unknown")
        self._emit(f"# ═══════════════════════════════════════════════════")
        self._emit(f"# {map_name} (Map ID: {self.map_id})")
        self._emit(f"# Auto-generated from RPG Maker MV")
        self._emit(f"# ═══════════════════════════════════════════════════")
        self._emit()

    def _emit_events(self) -> None:
        """Dispatch all events, separating autorun from regular events.

        Autorun events (trigger type 3) fire automatically when the map loads.
        They are grouped under a single `map_{id}_enter` label. Regular events
        (trigger type 0 or 2) get individual callable labels.
        """
        events = self.map_data.get("events", [])
        if not events:
            self._emit("# No events on this map.")
            return

        autorun_events: list[dict[str, Any]] = []
        regular_events: list[dict[str, Any]] = []

        # Classify each event by trigger type
        for event in events:
            if event is None:  # Skip deleted event slots
                continue
            pages = event.get("pages", [])
            # Trigger type 3 = autorun (fires on map entry)
            if pages and pages[0].get("trigger") == 3:
                autorun_events.append(event)
            else:
                regular_events.append(event)

        # Emit autorun events under the map entry label
        if autorun_events:
            self._emit("# ── Autorun sequence ──")
            self._emit(f"label map_{self.map_id}_enter:")
            self._push()
            for autorun_event in autorun_events:
                self._emit_event(autorun_event)
            self._emit("return")
            self._pop()
            self._emit()

        # Emit regular events as individual callable labels
        for regular_event in regular_events:
            self._emit_event(regular_event)

    def _emit_event(self, event: dict[str, Any]) -> None:
        """Generate Ren'Py code for a single RPG Maker event.

        Creates a label for the event and processes its pages. Single-page
        events emit their commands directly; multi-page events generate
        conditional blocks that check which page's conditions are met.

        Args:
            event: Parsed RPG Maker event JSON object with id, name, pages, etc.
        """
        event_id = event["id"]
        event_name = event.get("name", f"EV{event_id:03d}")
        label = safe_label(event_name, event_id)
        pages = event.get("pages", [])

        # Comment header showing event ID, name, and map position
        self._emit(f"# ── Event {event_id}: \"{event_name}\" (pos {event['x']},{event['y']}) ──")
        self._emit()

        if len(pages) == 1:
            # Single page: emit commands directly without conditionals
            self._emit(f"label {label}:")
            self._push()
            self._emit_page(pages[0], event_id)
            self._emit("return")
            self._pop()
        else:
            # Multiple pages: emit if/elif chain checking page conditions
            self._emit(f"label {label}:")
            self._push()
            self._emit_multi_page(pages, event_id)
            self._emit("return")
            self._pop()

        self._emit()

    def _emit_multi_page(self, pages: list[dict[str, Any]], event_id: int) -> None:
        """Generate conditional block for multi-page events.

        RPG Maker events with multiple pages are evaluated in reverse order
        (highest page number first). The first page whose conditions are met
        is the one that executes. We mirror this with an if/elif chain.

        Args:
            pages: List of event page objects (in RPG Maker order, reversed for processing).
            event_id: The owning event's ID (for self-switch references).
        """
        # Iterate in reverse to match RPG Maker's priority (highest page first)
        for reverse_index, page in enumerate(reversed(pages)):
            actual_page_index = len(pages) - 1 - reverse_index

            # Build the Ren'Py condition expression from the page's conditions
            page_conditions = page.get("conditions", {})
            condition_expression = self._build_renpy_condition(page_conditions, event_id)

            # First condition is "if", subsequent are "elif"
            condition_keyword = "if" if reverse_index == 0 else "elif"
            if condition_expression:
                self._emit(f"{condition_keyword} {condition_expression}:")
            else:
                # No conditions = always true (fallback page)
                if reverse_index == 0:
                    self._emit(f"{condition_keyword} True:")
                else:
                    self._emit(f"elif True:  # page {actual_page_index} fallback")

            self._push()
            self._emit_comment(f"Page {actual_page_index}")
            self._emit_page(page, event_id)
            self._pop()

    def _emit_page(self, page: dict[str, Any], event_id: int) -> None:
        """Generate Ren'Py code for a single event page.

        Flushes any pending text, processes the command list, then flushes again
        to emit any trailing dialogue.

        Args:
            page: Parsed event page JSON with 'list' of commands.
            event_id: The owning event's ID (for self-switch references).
        """
        command_list = page.get("list", [])
        self._flush_text()
        self._emit_command_list(command_list, event_id)
        self._flush_text()

    def _emit_command_list(self, commands: list[dict[str, Any]], event_id: int) -> None:
        """Process a list of RPG Maker commands and emit Ren'Py equivalents.

        This is the main command dispatch loop. It walks through the command
        array, handling each command type by emitting the appropriate Ren'Py
        script lines. Text lines are buffered; other commands flush the buffer
        first.

        Args:
            commands: Array of RPG Maker command objects (code + parameters).
            event_id: The owning event's ID (for self-switch references).
        """
        command_index = 0
        while command_index < len(commands):
            command = commands[command_index]
            command_code = command["code"]
            parameters = command.get("parameters", [])

            # END: marks end of command list for this page
            if command_code == CMD["END"]:
                break

            # SHOW_TEXT: sets the speaker and face for subsequent dialogue lines
            elif command_code == CMD["SHOW_TEXT"]:
                self._flush_text()
                face_asset_name = parameters[0] if len(parameters) > 0 else ""
                if face_asset_name:
                    # Look up the display name from collected character data
                    self._current_speaker = self.collector.characters.get(face_asset_name, face_asset_name)
                    self._current_face = face_asset_name
                else:
                    # No face = narration (no speaker)
                    self._current_speaker = None
                    self._current_face = None

            # TEXT_LINE: a single line of dialogue text, appended to buffer
            elif command_code == CMD["TEXT_LINE"]:
                dialogue_text = parameters[0] if parameters else ""
                dialogue_text = clean_text(dialogue_text)
                self._text_buffer.append(dialogue_text)

            # SHOW_CHOICES: displays a player menu with labeled options
            elif command_code == CMD["SHOW_CHOICES"]:
                self._flush_text()
                choice_labels = parameters[0] if parameters else []
                cancel_behavior = parameters[3] if len(parameters) > 3 else 0
                command_index = self._emit_choice_block(
                    commands, command_index, choice_labels, cancel_behavior, event_id
                )

            # CONDITIONAL: if/else branch based on switch, variable, etc.
            elif command_code == CMD["CONDITIONAL"]:
                self._flush_text()
                command_index = self._emit_conditional_block(commands, command_index, event_id)

            # CONTROL_SWITCHES: set a range of switches to True or False
            elif command_code == CMD["CONTROL_SWITCHES"]:
                self._flush_text()
                start_id, end_id, value = parameters[0], parameters[1], parameters[2]
                # RPG Maker: value 0 = ON (True), value 1 = OFF (False)
                renpy_value = "True" if value == 0 else "False"
                for switch_id in range(start_id, end_id + 1):
                    self._emit(f"$ switch_{switch_id} = {renpy_value}")

            # CONTROL_VARIABLES: modify a range of variables with an operation
            elif command_code == CMD["CONTROL_VARIABLES"]:
                self._flush_text()
                start_id, end_id = parameters[0], parameters[1]
                operation_type = parameters[2]
                operand_value = parameters[3]
                # RPG Maker operation codes → Python operators
                operator_map = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
                operator_symbol = operator_map.get(operation_type, "=")
                for variable_id in range(start_id, end_id + 1):
                    if operation_type == 0:
                        self._emit(f"$ var_{variable_id} = {operand_value}")
                    else:
                        self._emit(f"$ var_{variable_id} {operator_symbol} {operand_value}")

            # CONTROL_SELF_SWITCH: toggle a local event switch (A/B/C/D)
            elif command_code == CMD["CONTROL_SELF_SWITCH"]:
                self._flush_text()
                channel = parameters[0]
                # RPG Maker: value 0 = ON (True), value 1 = OFF (False)
                renpy_value = "True" if parameters[1] == 0 else "False"
                self._emit(f"$ selfswitch_{event_id}_{channel} = {renpy_value}")

            # CHANGE_GOLD: add or remove gold from the player
            elif command_code == CMD["CHANGE_GOLD"]:
                self._flush_text()
                gold_amount = parameters[2] if len(parameters) > 2 else 0
                # RPG Maker: operation 0 = increase, 1 = decrease
                if parameters[0] == 0:
                    self._emit(f"$ gold += {gold_amount}")
                else:
                    self._emit(f"$ gold -= {gold_amount}")

            # WAIT: pause execution for a number of frames (60 fps)
            elif command_code == CMD["WAIT"]:
                self._flush_text()
                frame_count = parameters[0]
                seconds = round(frame_count / 60.0, 2)
                self._emit(f"pause {seconds}")

            # PLAY_SE: play a sound effect file
            elif command_code == CMD["PLAY_SE"]:
                self._flush_text()
                sound_effect = parameters[0] if parameters else {}
                sound_name = sound_effect.get("name", "")
                if sound_name:
                    self._emit(f'play sound "{sound_name}.ogg"')

            # TRANSFER_PLAYER: jump to another map's entry label
            elif command_code == CMD["TRANSFER_PLAYER"]:
                self._flush_text()
                target_map_id = parameters[1]
                target_x, target_y = parameters[2], parameters[3]
                target_map_name = self.collector.map_names.get(target_map_id, f"map_{target_map_id}")
                self._emit(f'# Transfer to {target_map_name} ({target_x}, {target_y})')
                self._emit(f"jump map_{target_map_id}_enter")

            # PLUGIN_COMMAND: handle plugin command strings
            elif command_code == CMD["PLUGIN_COMMAND"]:
                self._flush_text()
                plugin_command_string = parameters[0] if parameters else ""
                self._emit_plugin_command(plugin_command_string)

            # SCRIPT: raw JavaScript block (not transpiled, logged as comment)
            elif command_code == CMD["SCRIPT"]:
                self._flush_text()
                script_content = parameters[0] if parameters else ""
                self._emit(f"# [Script] {script_content}")

            # MOVE_ROUTE / MOVE_PARAM: movement data (not transpiled)
            elif command_code in (CMD["MOVE_ROUTE"], CMD["MOVE_PARAM"]):
                pass  # Skip movement commands silently

            # Unknown command: emit as a TODO comment
            else:
                self._flush_text()
                self._emit(f"# [TODO: code={command_code}] params={parameters}")

            command_index += 1

    def _emit_choice_block(self, commands: list[dict[str, Any]], start_index: int,
                           choice_labels: list[str], cancel_type: int,
                           event_id: int) -> int:
        """Generate a Ren'Py menu block from RPG Maker choice commands.

        Walks through the command list starting after SHOW_CHOICES, collecting
        commands for each WHEN_CHOICE and WHEN_CANCEL branch, then emits them
        as Ren'Py menu options.

        Args:
            commands: Full command array for the event page.
            start_index: Index of the SHOW_CHOICES command in the array.
            choice_labels: List of choice text strings to display.
            cancel_type: Cancel behavior (0=disallow, 1=cancel, 2=branch).
            event_id: The owning event's ID (for nested command processing).

        Returns:
            Updated command index after processing the entire choice block.
        """
        self._emit("menu:")
        self._push()

        scan_index = start_index + 1
        choice_command_map: dict[int, list[dict[str, Any]]] = {}
        cancel_commands: list[dict[str, Any]] = []
        current_choice_index: int | None = None
        collected_commands: list[dict[str, Any]] = []
        is_collecting = False

        # Scan forward through commands to collect choice branch contents
        while scan_index < len(commands):
            command = commands[scan_index]
            command_code = command["code"]

            if command_code == CMD["WHEN_CHOICE"]:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                # Start collecting for this new choice index
                current_choice_index = command["parameters"][0]
                collected_commands = []
                is_collecting = True

            elif command_code == CMD["WHEN_CANCEL"]:
                # Save previously collected commands for the prior choice
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                # Cancel branch: collect into separate cancel list
                current_choice_index = None
                collected_commands = cancel_commands
                is_collecting = True

            elif command_code == CMD["END_CHOICES"]:
                # Save the last choice's commands and stop scanning
                if current_choice_index is not None:
                    choice_command_map[current_choice_index] = collected_commands
                scan_index += 1
                break

            elif command_code == CMD["END"]:
                # Premature end of command list
                break

            else:
                # Append command to current branch's collection
                if is_collecting:
                    collected_commands.append(command)

            scan_index += 1

        # Emit each choice as a Ren'Py menu option
        for choice_index, choice_text in enumerate(choice_labels):
            cleaned_choice_text = clean_text(choice_text)
            self._emit(f'"{cleaned_choice_text}":')
            self._push()
            choice_commands = choice_command_map.get(choice_index, [])
            self._emit_command_list(choice_commands, event_id)
            self._flush_text()
            self._pop()

        # Emit cancel option if behavior allows it and commands exist
        if cancel_type == 2 and cancel_commands:
            self._emit(f'"(Cancel)":')
            self._push()
            self._emit_command_list(cancel_commands, event_id)
            self._flush_text()
            self._pop()

        self._pop()
        return scan_index

    def _emit_conditional_block(self, commands: list[dict[str, Any]], start_index: int,
                                event_id: int) -> int:
        """Generate a Ren'Py if/else block from an RPG Maker conditional branch.

        Processes the CONDITIONAL command, then walks forward through the
        command list, emitting sub-commands until END_CONDITIONAL or ELSE
        is encountered. Handles nested conditionals recursively.

        Args:
            commands: Full command array for the event page.
            start_index: Index of the CONDITIONAL command in the array.
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Updated command index after processing the entire conditional block.
        """
        # Parse the condition from the CONDITIONAL command's parameters
        conditional_command = commands[start_index]
        condition_parameters = conditional_command.get("parameters", [])
        condition_expression = self._parse_condition_expr(condition_parameters, event_id)

        self._emit(f"if {condition_expression}:")
        self._push()

        scan_index = start_index + 1
        expected_indent_depth = 1  # Track nesting to find matching END_CONDITIONAL

        while scan_index < len(commands):
            sub_command = commands[scan_index]
            sub_command_code = sub_command["code"]
            sub_command_indent = sub_command.get("indent", 0)

            # ELSE: switch to else branch at the same indent level
            if sub_command_code == CMD["ELSE"] and sub_command_indent < expected_indent_depth:
                self._flush_text()
                self._pop()
                self._emit("else:")
                self._push()

            # END_CONDITIONAL: end of this conditional block
            elif sub_command_code == CMD["END_CONDITIONAL"] and sub_command_indent < expected_indent_depth:
                self._flush_text()
                self._pop()
                scan_index += 1
                break

            # Nested CONDITIONAL: recurse to handle inner if/else
            elif sub_command_code == CMD["CONDITIONAL"]:
                self._flush_text()
                scan_index = self._emit_conditional_block(commands, scan_index, event_id)
                continue  # Skip the increment at the bottom (already advanced by recursive call)

            # Premature END: stop processing
            elif sub_command_code == CMD["END"]:
                self._flush_text()
                self._pop()
                break

            # Any other command: emit as a single command
            else:
                self._emit_single_command(sub_command, event_id)

            scan_index += 1

        return scan_index

    def _emit_single_command(self, command: dict[str, Any], event_id: int) -> None:
        """Emit a single command outside the main dispatch loop.

        Used for commands inside conditional blocks and choice branches where
        the full command list processing is not appropriate. Handles a subset
        of command types that commonly appear in these contexts.

        Args:
            command: Single RPG Maker command object (code + parameters).
            event_id: The owning event's ID (for self-switch references).
        """
        command_code = command["code"]
        parameters = command.get("parameters", [])

        # CONTROL_SWITCHES: set switches to True or False
        if command_code == CMD["CONTROL_SWITCHES"]:
            start_id, end_id, value = parameters[0], parameters[1], parameters[2]
            renpy_value = "True" if value == 0 else "False"
            for switch_id in range(start_id, end_id + 1):
                self._emit(f"$ switch_{switch_id} = {renpy_value}")

        # CONTROL_VARIABLES: modify variables with an operation
        elif command_code == CMD["CONTROL_VARIABLES"]:
            start_id, end_id = parameters[0], parameters[1]
            operation_type = parameters[2]
            operand_value = parameters[3]
            operator_map = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
            for variable_id in range(start_id, end_id + 1):
                if operation_type == 0:
                    self._emit(f"$ var_{variable_id} = {operand_value}")
                else:
                    self._emit(f"$ var_{variable_id} {operator_map.get(operation_type, '=')} {operand_value}")

        # CONTROL_SELF_SWITCH: toggle a local event switch
        elif command_code == CMD["CONTROL_SELF_SWITCH"]:
            channel = parameters[0]
            renpy_value = "True" if parameters[1] == 0 else "False"
            self._emit(f"$ selfswitch_{event_id}_{channel} = {renpy_value}")

        # CHANGE_GOLD: add or remove gold
        elif command_code == CMD["CHANGE_GOLD"]:
            gold_amount = parameters[2] if len(parameters) > 2 else 0
            if parameters[0] == 0:
                self._emit(f"$ gold += {gold_amount}")
            else:
                self._emit(f"$ gold -= {gold_amount}")

        # PLUGIN_COMMAND: handle plugin command strings
        elif command_code == CMD["PLUGIN_COMMAND"]:
            plugin_command_string = parameters[0] if parameters else ""
            self._emit_plugin_command(plugin_command_string)

        # WAIT: pause execution
        elif command_code == CMD["WAIT"]:
            frame_count = parameters[0]
            seconds = round(frame_count / 60.0, 2)
            self._emit(f"pause {seconds}")

        # PLAY_SE: play a sound effect
        elif command_code == CMD["PLAY_SE"]:
            sound_effect = parameters[0] if parameters else {}
            sound_name = sound_effect.get("name", "")
            if sound_name:
                self._emit(f'play sound "{sound_name}.ogg"')

        # TRANSFER_PLAYER: jump to another map
        elif command_code == CMD["TRANSFER_PLAYER"]:
            target_map_id = parameters[1]
            self._emit(f"jump map_{target_map_id}_enter")

    def _build_renpy_condition(self, conditions: dict[str, Any], event_id: int) -> str:
        """Convert RPG Maker event page conditions to a Ren'Py expression.

        Builds an `and`-joined expression from all valid conditions on an
        event page. Each condition becomes a check against a Ren'Py variable.

        Args:
            conditions: The 'conditions' dict from an event page.
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Ren'Py condition expression (e.g., "switch_5 and var_3 >= 10").
            Returns empty string if no conditions are set.
        """
        condition_checks: list[str] = []

        # First global switch condition: check if switch is True
        if conditions.get("switch1Valid"):
            switch_id = conditions["switch1Id"]
            condition_checks.append(f"switch_{switch_id}")

        # Second global switch condition
        if conditions.get("switch2Valid"):
            switch_id = conditions["switch2Id"]
            condition_checks.append(f"switch_{switch_id}")

        # Variable condition: check if variable >= threshold
        if conditions.get("variableValid"):
            variable_id = conditions["variableId"]
            threshold_value = conditions["variableValue"]
            condition_checks.append(f"var_{variable_id} >= {threshold_value}")

        # Self-switch condition: check if local switch is True
        if conditions.get("selfSwitchValid"):
            channel = conditions.get("selfSwitchCh", "A")
            condition_checks.append(f"selfswitch_{event_id}_{channel}")

        # Item condition: check if player has at least one of the item
        if conditions.get("itemValid"):
            item_id = conditions["itemId"]
            condition_checks.append(f"item_{item_id} > 0")

        return " and ".join(condition_checks) if condition_checks else ""

    def _parse_condition_expr(self, parameters: list[Any], event_id: int) -> str:
        """Convert RPG Maker conditional branch parameters to a Ren'Py expression.

        Handles multiple condition types:
        - 0: Switch (ON/OFF check)
        - 1: Variable (comparison with value)
        - 2: Self-switch (local ON/OFF check)
        - 6: Script (raw expression, passed through)
        - 7: Gold (comparison with amount)

        Args:
            parameters: The parameters array from a CONDITIONAL command.
            event_id: The owning event's ID (for self-switch references).

        Returns:
            Ren'Py condition expression string.
        """
        condition_type = parameters[0]

        # Condition type 0: Switch check
        if condition_type == 0:
            switch_id = parameters[1]
            expected_value = parameters[2]
            if expected_value == 0:
                return f"switch_{switch_id}"  # Switch is ON
            else:
                return f"not switch_{switch_id}"  # Switch is OFF

        # Condition type 1: Variable comparison
        elif condition_type == 1:
            variable_id = parameters[1]
            comparison_type = parameters[2]
            comparison_value = parameters[3]
            # RPG Maker comparison codes → Python operators
            comparison_map = {0: "==", 1: ">=", 2: "<=", 3: ">", 4: "<", 5: "!="}
            comparison_operator = comparison_map.get(comparison_type, "==")
            return f"var_{variable_id} {comparison_operator} {comparison_value}"

        # Condition type 2: Self-switch check
        elif condition_type == 2:
            channel = parameters[1]
            expected_value = parameters[2]
            if expected_value == 0:
                return f"selfswitch_{event_id}_{channel}"  # Self-switch is ON
            else:
                return f"not selfswitch_{event_id}_{channel}"  # Self-switch is OFF

        # Condition type 7: Gold comparison
        elif condition_type == 7:
            comparison_type = parameters[1]
            gold_amount = parameters[2]
            # RPG Maker comparison codes → Python operators
            comparison_map = {0: ">=", 1: "<=", 2: "<", 3: ">", 4: "==", 5: "!="}
            comparison_operator = comparison_map.get(comparison_type, ">=")
            return f"gold {comparison_operator} {gold_amount}"

        # Condition type 6: Script expression (pass through as-is)
        elif condition_type == 6:
            return parameters[1] if len(parameters) > 1 else "True"

        # Unknown condition type: always true (fallback)
        else:
            return "True"

    def _emit_plugin_command(self, plugin_command_string: str) -> None:
        """Handle RPG Maker plugin command strings.

        Known plugin commands (e.g., Quest log entries) are translated to
        Ren'Py equivalents. Unknown plugin commands are logged as comments.

        Args:
            plugin_command_string: The raw plugin command string from RPG Maker.
        """
        if not plugin_command_string:
            return

        # Quest plugin: append to quest log and display as dialogue
        if plugin_command_string.startswith("Quest"):
            self._emit(f'$ quest_log.append("{plugin_command_string}")')
            self._emit(f'"{plugin_command_string}"')
        # Unknown plugin command: log as a comment for manual handling
        else:
            self._emit(f'# [Plugin] {plugin_command_string}')

    def _flush_text(self) -> None:
        """Flush the text buffer to emit accumulated dialogue lines.

        Joins all buffered text lines with spaces, then emits a single
        Ren'Py dialogue line. If a speaker is set, includes the speaker's
        variable name; otherwise emits as narrator text.

        This method is called at command boundaries (before any non-text
        command) to ensure dialogue is properly grouped.
        """
        if not self._text_buffer:
            return

        # Join all buffered lines into a single dialogue string
        full_dialogue_text = " ".join(self._text_buffer)
        self._text_buffer = []

        # Skip if the result is empty after joining
        if not full_dialogue_text.strip():
            return

        # Emit with speaker name if one is active, otherwise as narrator
        if self._current_speaker:
            speaker_variable = safe_var(self._current_speaker)
            self._emit(f'{speaker_variable} "{full_dialogue_text}"')
        else:
            self._emit(f'"{full_dialogue_text}"')

    def _emit_comment(self, comment_text: str) -> None:
        """Emit a Ren'Py comment line.

        Args:
            comment_text: The comment content (without the leading '#').
        """
        self._emit(f"# {comment_text}")
