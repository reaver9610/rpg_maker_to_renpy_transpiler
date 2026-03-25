"""Data collector for RPG Maker MV map files.

First-pass scanner that reads all map JSON data to discover every character name,
switch ID, variable ID, self-switch key, item ID, and map transfer target used
across all events. The collected metadata is used by the output file generators
to produce complete Ren'Py definitions (Character objects, default state
variables, game flow labels).
"""

# ═══════════════════════════════════════════════════════════════════
# COLLECTOR — extracts all characters, switches, variables
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Any

from .constants import CMD


class DataCollector:
    """Scans all map data first to collect:
    - Character names used in dialogue
    - Switch IDs referenced
    - Variable IDs referenced
    - Self-switch keys used
    - Item IDs referenced
    - Transfer targets (map connections)
    """

    def __init__(self) -> None:
        """Initialize empty collections for all discovered game state elements.

        Attributes:
            characters: Maps RPG Maker face asset names to cleaned display names
                        (e.g., "$Claire" → "Claire").
            switch_ids: Set of all global switch IDs referenced across events.
            variable_ids: Set of all global variable IDs referenced across events.
            self_switches: Set of (event_id, channel_letter) tuples for local switches.
            item_ids: Set of all item IDs referenced in conditional checks or changes.
            map_ids: Set of all map IDs that appear in transfer commands or input files.
            plugin_commands: Ordered list of all plugin command strings encountered.
            map_names: Maps map_id → display_name from the map JSON metadata.
        """
        self.characters: dict[str, str] = {}
        self.switch_ids: set[int] = set()
        self.variable_ids: set[int] = set()
        self.self_switches: set[tuple[int, str]] = set()
        self.item_ids: set[int] = set()
        self.map_ids: set[int] = set()
        self.plugin_commands: list[str] = []
        self.map_names: dict[int, str] = {}

    def collect_from_map(self, map_data: dict[str, Any], map_id: int = 0) -> None:
        """Scan a single map's events to collect all referenced data.

        Iterates over every event and every page within each event, delegating
        condition scanning and command scanning to dedicated helper methods.

        Args:
            map_data: Parsed JSON object for one RPG Maker map.
            map_id: Numeric identifier for this map (extracted from filename).
        """
        # Record the map's display name for game flow generation
        display_name = map_data.get("display_name", f"Map{map_id}")
        self.map_names[map_id] = display_name
        self.map_ids.add(map_id)

        # Scan each event's pages for conditions and commands
        events = map_data.get("events", [])
        for event in events:
            if event is None:  # RPG Maker uses null for deleted event slots
                continue
            event_id = event["id"]
            for page in event.get("pages", []):
                self._collect_conditions(page.get("conditions", {}), event_id)
                self._collect_commands(page.get("list", []), event_id)

    def _collect_conditions(self, conditions: dict[str, Any], event_id: int) -> None:
        """Extract switch/variable/item IDs from an event page's condition block.

        Event pages can be gated on: two global switches, one variable comparison,
        one self-switch, or one item requirement. Each valid condition is recorded
        so the output generators can declare default values for all referenced state.

        Args:
            conditions: The 'conditions' dict from an event page JSON object.
            event_id: The owning event's numeric ID (for self-switch keys).
        """
        # Condition type: first global switch must be ON
        if conditions.get("switch1Valid"):
            self.switch_ids.add(conditions["switch1Id"])

        # Condition type: second global switch must be ON
        if conditions.get("switch2Valid"):
            self.switch_ids.add(conditions["switch2Id"])

        # Condition type: variable must meet a threshold value
        if conditions.get("variableValid"):
            self.variable_ids.add(conditions["variableId"])

        # Condition type: a local self-switch must be ON
        if conditions.get("selfSwitchValid"):
            channel = conditions.get("selfSwitchCh", "A")
            self.self_switches.add((event_id, channel))

        # Condition type: player must possess at least one of a specific item
        if conditions.get("itemValid"):
            self.item_ids.add(conditions["itemId"])

    def _collect_commands(self, commands: list[dict[str, Any]], event_id: int) -> None:
        """Extract all referenced IDs from an event page's command list.

        Walks through every command in the list and records switch IDs, variable
        IDs, self-switch keys, character names, item IDs, map IDs, and plugin
        commands based on the command's code type.

        Args:
            commands: The 'list' array of command objects from an event page.
            event_id: The owning event's numeric ID (for self-switch keys).
        """
        for command in commands:
            command_code = command["code"]
            parameters = command.get("parameters", [])

            # SHOW_TEXT: first parameter is the face asset name (speaker identity)
            if command_code == CMD["SHOW_TEXT"] and len(parameters) >= 1:
                face_name = parameters[0]
                if face_name:  # Empty string means no speaker (narration)
                    display_name = self._clean_character_name(face_name)
                    self.characters[face_name] = display_name

            # CONTROL_SWITCHES: sets a contiguous range of switches to ON/OFF
            elif command_code == CMD["CONTROL_SWITCHES"]:
                start_id, end_id = parameters[0], parameters[1]
                for switch_id in range(start_id, end_id + 1):
                    self.switch_ids.add(switch_id)

            # CONTROL_VARIABLES: modifies a contiguous range of variables
            elif command_code == CMD["CONTROL_VARIABLES"]:
                start_id, end_id = parameters[0], parameters[1]
                for variable_id in range(start_id, end_id + 1):
                    self.variable_ids.add(variable_id)

            # CONTROL_SELF_SWITCH: toggles a local event switch (A/B/C/D)
            elif command_code == CMD["CONTROL_SELF_SWITCH"]:
                channel = parameters[0]
                self.self_switches.add((event_id, channel))

            # CONDITIONAL: branches based on switch, variable, or self-switch
            elif command_code == CMD["CONDITIONAL"]:
                condition_type = parameters[0]
                if condition_type == 0:  # Switch condition
                    self.switch_ids.add(parameters[1])
                elif condition_type == 1:  # Variable condition
                    self.variable_ids.add(parameters[1])
                elif condition_type == 2:  # Self-switch condition
                    self.self_switches.add((event_id, parameters[1]))

            # TRANSFER_PLAYER: target map ID is parameters[1]
            elif command_code == CMD["TRANSFER_PLAYER"]:
                target_map_id = parameters[1]
                self.map_ids.add(target_map_id)

            # CHANGE_ITEMS_CMD: adds/removes an item by ID
            elif command_code == CMD["CHANGE_ITEMS_CMD"]:
                self.item_ids.add(parameters[1])

            # PLUGIN_COMMAND: stores the plugin command string for later use
            elif command_code == CMD["PLUGIN_COMMAND"]:
                self.plugin_commands.append(parameters[0])

    @staticmethod
    def _clean_character_name(face_name: str) -> str:
        """Convert an RPG Maker face asset name to a readable display name.

        RPG Maker uses asset filenames as character identifiers (e.g., "$Claire",
        "!GuardPeople3"). This method strips special prefixes, inserts spaces at
        camelCase boundaries, and trims whitespace.

        Args:
            face_name: Raw face asset name from the JSON (e.g., "$SailorSkipper").

        Returns:
            Cleaned display name suitable for Ren'Py Character definitions
            (e.g., "Sailor Skipper").
        """
        # Remove RPG Maker asset prefixes: $ = large sprite, ! = no shadow
        name = face_name.replace("$", "").replace("!", "")
        # Insert spaces at camelCase boundaries: "SailorSkipper" → "Sailor Skipper"
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        return name.strip()
