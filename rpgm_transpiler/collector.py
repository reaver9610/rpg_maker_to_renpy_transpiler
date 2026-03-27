"""Data collector for RPG Maker MV map files.

This module implements the first-pass scanner that reads all map JSON data to discover
every character name, switch ID, variable ID, self-switch key, item ID, and map transfer
target used across all events. The collected metadata is used by the output file
generators to produce complete Ren'Py definitions.

Why Two Passes?
The transpiler needs to know about ALL game state before generating any output files:
- characters.rpy needs every character name to define Character() objects
- switches.rpy needs every switch/variable ID to initialize default values
- side_images.rpy needs every face asset + face ID combination

Without a collection pass, we'd have to generate output files incrementally, which
would require complex dependency tracking and potentially multiple file rewrites.

Collection Strategy:
1. Iterate over every event in every map
2. For each event page, scan both conditions and commands
3. Record IDs in sets (for switches/variables) and dicts (for characters)
4. Pass the populated collector to output generators

RPG Maker JSON Structure:
Map JSON files have this hierarchy:
{
  "display_name": "Town Square",
  "events": [
    {
      "id": 1,
      "name": "Town Elder",
      "x": 5,
      "y": 8,
      "pages": [
        {
          "conditions": { ... },
          "trigger": 0,
          "list": [ { "code": 101, "parameters": [...] }, ... ]
        }
      ]
    },
    null,  // Deleted events are null
    ...
  ]
}
"""

from __future__ import annotations

import re
from typing import Any

from .constants import CMD


class DataCollector:
    """Scans all map data to collect game state references.

    The DataCollector performs a first-pass scan of all RPG Maker MV map JSON files
    to discover every referenced game state element. This information is needed to
    generate complete Ren'Py initialization files.

    What Gets Collected:
    - Character names: Used in SHOW_TEXT commands to define Ren'Py Character objects
    - Face IDs: Used in side_images.rpy to declare image side {tag} {id} variants
    - Switch IDs: Global boolean flags, initialized to False in switches.rpy
    - Variable IDs: Global integer values, initialized to 0 in switches.rpy
    - Self-switches: Event-local booleans (keyed by event_id + channel), init to False
    - Item IDs: Inventory counters, initialized to 0 in switches.rpy
    - Map IDs: Transfer targets, used in game_flow.rpy for navigation labels
    - Plugin commands: Stored for potential special handling

    Data Structures:
    - characters: dict[face_asset_name → display_name]
        Maps RPG Maker asset filenames to human-readable names
        Example: {"$Claire": "Claire", "!SailorSkipper": "Sailor Skipper"}

    - character_face_ids: dict[face_asset_name → set[face_id]]
        Maps asset names to the specific face image IDs used in dialogue
        Example: {"Claire": {0, 2, 5}} means faces 0, 2, 5 from Claire's sheet are used

    - switch_ids: set[int]
        All global switch IDs referenced anywhere in the game
        Example: {1, 5, 12, 23}

    - variable_ids: set[int]
        All global variable IDs referenced anywhere in the game
        Example: {1, 3, 7}

    - self_switches: dict[map_id → set[tuple[event_id, channel]]]
        All self-switch references, grouped by map
        Example: {1: {(1, "A"), (1, "B")}, 3: {(5, "A")}}

    - item_ids: set[int]
        All item IDs referenced in conditions or change commands
        Example: {1, 5, 12}

    - map_ids: set[int]
        All map IDs that appear in TRANSFER_PLAYER commands or input files
        Example: {1, 2, 5}

    - plugin_commands: list[str]
        All plugin command strings encountered, in order of appearance
        Example: ["Quest Add main_quest", "Quest Complete main_quest"]

    - map_names: dict[map_id → display_name]
        Maps map IDs to their human-readable names for game_flow.rpy
        Example: {1: "Town Square", 2: "Forest Path"}
    """

    def __init__(self) -> None:
        """Initialize empty collections for all discovered game state elements.

        Creates the data structures that will be populated during collection.
        All collections start empty and are filled by the collect_from_map method.

        Attributes Initialized:
            characters (dict): Empty dict to store face_asset → display_name mappings
            character_face_ids (dict): Empty dict to store face_asset → set[face_id] mappings
            switch_ids (set): Empty set for global switch IDs
            variable_ids (set): Empty set for global variable IDs
            self_switches (dict): Empty dict for map_id → set of (event_id, channel) tuples
            item_ids (set): Empty set for item IDs
            map_ids (set): Empty set for map IDs
            plugin_commands (list): Empty list for plugin command strings
            map_names (dict): Empty dict for map_id → display_name mappings
        """
        # Character data: face asset names → cleaned display names
        # Used by generate_characters_rpy() to create Character() definitions
        self.characters: dict[str, str] = {}
        
        # Character face IDs: which specific face images are used per asset
        # Used by generate_side_images_rpy() to create image side declarations
        # The set stores face IDs 0-7 (RPG Maker uses 4x2 grids)
        self.character_face_ids: dict[str, set[int]] = {}
        
        # Global switches: boolean flags that persist across maps
        # Used by generate_global_switches_rpy() to initialize: switch_{id} = False
        self.switch_ids: set[int] = set()
        
        # Global variables: integer values that persist across maps
        # Used by generate_global_variables_rpy() to initialize: var_{id} = 0
        self.variable_ids: set[int] = set()
        
        # Self-switches: event-local boolean flags (A/B/C/D channels)
        # Grouped by map_id: {map_id → set of (event_id, channel_letter)}
        # Used by generate_map_switches_rpy() to create per-map store declarations
        self.self_switches: dict[int, set[tuple[int, str]]] = {}
        
        # Items: inventory counters
        # Used by generate_global_items_rpy() to initialize: item_{id} = 0
        self.item_ids: set[int] = set()
        
        # Map IDs: all maps referenced in transfers or loaded as input
        # Used by generate_game_flow_rpy() to create navigation labels
        self.map_ids: set[int] = set()
        
        # Plugin commands: all plugin command strings encountered
        # Stored in order for potential special handling (e.g., Quest system)
        self.plugin_commands: list[str] = []
        
        # Map names: map_id → display_name for readable navigation labels
        # Used by generate_game_flow_rpy() to comment map labels with names
        self.map_names: dict[int, str] = {}
        
        # System.json data: global game configuration for name resolution
        # Contains switches, variables, terms, and other system settings
        # Loaded from System.json if available in the project directory
        self.system_data: dict | None = None

    @staticmethod
    def _sanitize_name_for_variable(name: str) -> str:
        """Convert a human-readable name to a safe Python variable suffix.

        Transforms names like "Camp entry obtained" or "M: Find the purse"
        into snake_case identifiers suitable for concatenating to variable names.

        Transformation Steps:
        1. Convert to lowercase
        2. Remove/replace special characters (colons, dashes, apostrophes, etc.)
        3. Replace spaces with underscores
        4. Collapse consecutive underscores
        5. Strip leading/trailing underscores

        Args:
            name: Human-readable name from System.json.
                Example: "Camp entry obtained", "M: Find the purse"

        Returns:
            Sanitized snake_case string for variable name concatenation.
            Example: "camp_entry_obtained", "m_find_the_purse"

        Example:
            >>> DataCollector._sanitize_name_for_variable("Camp entry obtained")
            'camp_entry_obtained'
            >>> DataCollector._sanitize_name_for_variable("M: Find the purse")
            'm_find_the_purse'
            >>> DataCollector._sanitize_name_for_variable("S: Guard Blowjob")
            's_guard_blowjob'
            >>> DataCollector._sanitize_name_for_variable("Claire's Defiance")
            'claires_defiance'
        """
        # Step 1: Convert to lowercase
        name = name.lower()
        
        # Step 2: Replace special characters with underscores
        # Handle common patterns: colons, apostrophes, dashes, parentheses, ampersands, hashes
        name = name.replace("'", "")  # Remove apostrophes (claire's → claires)
        name = name.replace('"', '')  # Remove quotes
        name = re.sub(r'[:\-\(\)&#]', '_', name)  # Replace special chars with underscore
        
        # Step 3: Replace remaining non-alphanumeric chars with underscores
        name = re.sub(r'[^a-z0-9_]', '_', name)
        
        # Step 4: Collapse consecutive underscores into single underscore
        name = re.sub(r'_+', '_', name)
        
        # Step 5: Strip leading/trailing underscores
        name = name.strip('_')
        
        return name

    def get_switch_name(self, switch_id: int) -> str:
        """Get a concatenated variable name for a switch ID.

        Returns a safe Ren'Py variable name combining the switch ID with
        its human-readable name from System.json.

        Format: switch_{id}_{sanitized_name}

        Args:
            switch_id: The numeric switch ID (1-based).

        Returns:
            Concatenated variable name suitable for Ren'Py.

        Example:
            >>> # With System.json loaded containing switches[278] = "Guards insulted"
            >>> collector.get_switch_name(278)
            'switch_278_guards_insulted'
            >>> # Without System.json or unknown switch
            >>> collector.get_switch_name(999)
            'switch_999'
        """
        # Get the human-readable name from System.json if available
        raw_name = self._get_switch_raw_name(switch_id)
        
        if raw_name:
            # Sanitize the name for variable concatenation
            sanitized = self._sanitize_name_for_variable(raw_name)
            return f"switch_{switch_id}_{sanitized}"
        else:
            # Fallback: just use the ID without a name
            return f"switch_{switch_id}"

    def get_variable_name(self, variable_id: int) -> str:
        """Get a concatenated variable name for a variable ID.

        Returns a safe Ren'Py variable name combining the variable ID with
        its human-readable name from System.json.

        Format: var_{id}_{sanitized_name}

        Args:
            variable_id: The numeric variable ID (1-based).

        Returns:
            Concatenated variable name suitable for Ren'Py.

        Example:
            >>> # With System.json loaded containing variables[2] = "Claire's Defiance"
            >>> collector.get_variable_name(2)
            'var_2_claires_defiance'
            >>> # Without System.json or unknown variable
            >>> collector.get_variable_name(999)
            'var_999'
        """
        # Get the human-readable name from System.json if available
        raw_name = self._get_variable_raw_name(variable_id)
        
        if raw_name:
            # Sanitize the name for variable concatenation
            sanitized = self._sanitize_name_for_variable(raw_name)
            return f"var_{variable_id}_{sanitized}"
        else:
            # Fallback: just use the ID without a name
            return f"var_{variable_id}"

    def get_switch_store_name(self, switch_id: int) -> str:
        """Get a fully-qualified store-prefixed variable name for a global switch.

        Returns the switch name prefixed with the game_switch store namespace.

        Format: game_switch.switch_{id}_{sanitized_name}

        Args:
            switch_id: The numeric switch ID (1-based).

        Returns:
            Store-prefixed variable name suitable for Ren'Py.

        Example:
            >>> collector.get_switch_store_name(278)
            'game_switch.switch_278_guards_insulted'
            >>> collector.get_switch_store_name(999)
            'game_switch.switch_999'
        """
        return f"game_switch.{self.get_switch_name(switch_id)}"

    def get_variable_store_name(self, variable_id: int) -> str:
        """Get a fully-qualified store-prefixed variable name for a global variable.

        Returns the variable name prefixed with the game_vars store namespace.

        Format: game_vars.var_{id}_{sanitized_name}

        Args:
            variable_id: The numeric variable ID (1-based).

        Returns:
            Store-prefixed variable name suitable for Ren'Py.

        Example:
            >>> collector.get_variable_store_name(2)
            'game_vars.var_2_claires_defiance'
            >>> collector.get_variable_store_name(999)
            'game_vars.var_999'
        """
        return f"game_vars.{self.get_variable_name(variable_id)}"

    def get_self_switch_store_name(self, map_id: int) -> str:
        """Get the Ren'Py named store name for a map's self-switches.

        Returns a store name combining the map ID with its sanitized display name.
        This store is used in per-map self-switch declaration files and in
        self-switch references throughout the generated code.

        Format: map_{id}_{sanitized_name}

        Args:
            map_id: The numeric map ID (1-based).

        Returns:
            Store name suitable for use as a Ren'Py named store namespace.

        Example:
            >>> # With map_names[1] = "Checkpoint"
            >>> collector.get_self_switch_store_name(1)
            'map_1_checkpoint'
            >>> # With map_names[1] = "Outer Valos"
            >>> collector.get_self_switch_store_name(1)
            'map_1_outer_valos'
            >>> # Unknown map
            >>> collector.get_self_switch_store_name(999)
            'map_999'
        """
        raw_name = self.map_names.get(map_id, f"map_{map_id}")
        sanitized = self._sanitize_name_for_variable(raw_name)
        return f"map_{map_id}_{sanitized}"

    def _get_switch_raw_name(self, switch_id: int) -> str | None:
        """Get the raw name of a switch from System.json.

        Args:
            switch_id: The numeric switch ID (1-based).

        Returns:
            The switch name from System.json, or None if not available.
        """
        if self.system_data is None:
            return None
        
        switches = self.system_data.get("switches", [])
        if 0 <= switch_id < len(switches):
            name = switches[switch_id]
            # Return name only if it's non-empty
            return name if name else None
        
        return None

    def _get_variable_raw_name(self, variable_id: int) -> str | None:
        """Get the raw name of a variable from System.json.

        Args:
            variable_id: The numeric variable ID (1-based).

        Returns:
            The variable name from System.json, or None if not available.
        """
        if self.system_data is None:
            return None
        
        variables = self.system_data.get("variables", [])
        if 0 <= variable_id < len(variables):
            name = variables[variable_id]
            # Return name only if it's non-empty
            return name if name else None
        
        return None

    def collect_from_map(self, map_data: dict[str, Any], map_id: int = 0) -> None:
        """Scan a single map's events to collect all referenced data.

        This is the main entry point for collection. It iterates over every event
        in the map and every page within each event, delegating the actual scanning
        to _collect_conditions and _collect_commands.

        Processing Order:
        1. Record the map's display name and ID
        2. Iterate over the events array (skip null entries)
        3. For each event, iterate over its pages
        4. Scan page conditions for switch/variable/item IDs
        5. Scan page commands for all referenced IDs

        Args:
            map_data: Parsed JSON object for one RPG Maker map.
                Expected structure:
                {
                    "display_name": str,
                    "events": [event_dict | null, ...]
                }
            map_id: Numeric identifier for this map.
                Extracted from the filename (e.g., "Map001.json" → 1).
                Used to track which map each self-switch belongs to.

        Example:
            >>> collector = DataCollector()
            >>> with open("Map001.json") as f:
            ...     map_data = json.load(f)
            >>> collector.collect_from_map(map_data, 1)
            >>> print(collector.characters)
            {'$Claire': 'Claire', '!SailorSkipper': 'Sailor Skipper'}
        """
        # Step 1: Record the map's display name for game flow generation
        # The display_name is used in game_flow.rpy comments to identify maps
        # If missing, we fall back to "Map{id}"
        display_name = map_data.get("displayName", f"Map{map_id}")
        
        # Store the name mapping for later use in generate_game_flow_rpy()
        self.map_names[map_id] = display_name
        
        # Add this map's ID to the set of known maps
        # This ensures the map appears in game_flow.rpy even if not referenced in transfers
        self.map_ids.add(map_id)

        # Step 2: Get the events array from the map data
        # RPG Maker stores events as an array where indices are event IDs
        # Deleted events are represented as null (we skip these)
        events = map_data.get("events", [])
        
        # Step 3: Iterate over each event in the map
        for event in events:
            # Skip null entries (deleted events in RPG Maker)
            # RPG Maker uses null to mark deleted event slots in the array
            if event is None:
                continue
            
            # Get the event's numeric ID
            # This ID is used in self-switch keys: selfswitch_{event_id}_{channel}
            event_id = event["id"]
            
            # Step 4: Iterate over each page in the event
            # Events can have multiple pages with different conditions
            # Pages are evaluated in reverse order (highest page number first)
            for page in event.get("pages", []):
                # Step 5: Scan page conditions for switch/variable/item IDs
                # Conditions determine when this page is active
                self._collect_conditions(page.get("conditions", {}), event_id, map_id)
                
                # Step 6: Scan page commands for all referenced IDs
                # Commands are the actual event logic (dialogue, choices, etc.)
                self._collect_commands(page.get("list", []), event_id, map_id)

    def _collect_conditions(self, conditions: dict[str, Any], event_id: int, map_id: int = 0) -> None:
        """Extract switch/variable/item IDs from an event page's condition block.

        RPG Maker event pages can be gated on multiple conditions:
        - Two global switches (switch1 and switch2)
        - One variable comparison (variable >= value)
        - One self-switch (A, B, C, or D)
        - One item requirement (player must have at least one)

        Each condition type is optional. When a condition is enabled (Valid flag true),
        the corresponding ID is recorded for state initialization.

        Condition JSON Structure:
        {
            "switch1Valid": bool,
            "switch1Id": int,
            "switch2Valid": bool,
            "switch2Id": int,
            "variableValid": bool,
            "variableId": int,
            "variableValue": int,
            "selfSwitchValid": bool,
            "selfSwitchCh": str,  # "A", "B", "C", or "D"
            "itemValid": bool,
            "itemId": int
        }

        Args:
            conditions: The 'conditions' dict from an event page JSON object.
            event_id: The owning event's numeric ID.
                Used to create self-switch keys: (event_id, channel).
            map_id: The owning map's numeric ID.
                Used to associate self-switches with their map for per-map store generation.

        Example:
            >>> conditions = {"switch1Valid": True, "switch1Id": 5}
            >>> collector._collect_conditions(conditions, 1, 1)
            >>> print(collector.switch_ids)
            {5}
        """
        # Condition type 1: First global switch must be ON
        # If switch1Valid is True, the page only appears when switch1Id is ON
        if conditions.get("switch1Valid"):
            # Add the switch ID to our set
            # This ensures switches.rpy initializes: switch_{id} = False
            self.switch_ids.add(conditions["switch1Id"])

        # Condition type 2: Second global switch must be ON
        # Similar to switch1, allows two independent switch conditions
        if conditions.get("switch2Valid"):
            self.switch_ids.add(conditions["switch2Id"])

        # Condition type 3: Variable must meet a threshold value
        # The page appears when variableId >= variableValue
        # Note: Only the variable ID is recorded, not the threshold
        # The threshold is used at runtime in conditional checks
        if conditions.get("variableValid"):
            self.variable_ids.add(conditions["variableId"])

        # Condition type 4: A local self-switch must be ON
        # Self-switches are event-local, keyed by (event_id, channel)
        # Channel is one of "A", "B", "C", "D" (default "A" if missing)
        if conditions.get("selfSwitchValid"):
            # Get the channel letter, defaulting to "A"
            channel = conditions.get("selfSwitchCh", "A")
            # Add the (event_id, channel) tuple to our map-specific set
            # This ensures generate_map_switches_rpy() initializes:
            # map_{id}_{name}.switch_{event_id}_{channel} = False
            self.self_switches.setdefault(map_id, set()).add((event_id, channel))

        # Condition type 5: Player must possess at least one of a specific item
        # The page appears when the player has 1+ of itemId
        if conditions.get("itemValid"):
            # Add the item ID to our set
            # This ensures switches.rpy initializes: item_{id} = 0
            self.item_ids.add(conditions["itemId"])

    def _collect_commands(self, commands: list[dict[str, Any]], event_id: int, map_id: int = 0) -> None:
        """Extract all referenced IDs from an event page's command list.

        This method walks through every command in the event page's 'list' array
        and records switch IDs, variable IDs, self-switch keys, character names,
        item IDs, map IDs, and plugin commands based on the command type.

        Command Dispatch:
        Each command has a 'code' field identifying its type. We use the CMD
        dictionary to check codes and extract relevant IDs from parameters.

        Commands Handled:
        - SHOW_TEXT: Extract face asset name (character) and face ID
        - CONTROL_SWITCHES: Extract switch ID range
        - CONTROL_VARIABLES: Extract variable ID range
        - CONTROL_SELF_SWITCH: Extract self-switch channel
        - CONDITIONAL: Extract condition-based IDs (switch, variable, self-switch)
        - TRANSFER_PLAYER: Extract target map ID
        - CHANGE_ITEMS_CMD: Extract item ID
        - PLUGIN_COMMAND: Store command string

        Args:
            commands: The 'list' array of command objects from an event page.
                Each command has: code (int), indent (int), parameters (list)
            event_id: The owning event's numeric ID.
                Used for self-switch keys in CONDITIONAL commands.
            map_id: The owning map's numeric ID.
                Used to associate self-switches with their map.

        Example:
            >>> commands = [
            ...     {"code": 101, "parameters": ["$Claire", 2]},
            ...     {"code": 121, "parameters": [5, 5, 0]}  # switch 5 = ON
            ... ]
            >>> collector._collect_commands(commands, 1, 1)
            >>> print(collector.characters)
            {'$Claire': 'Claire'}
            >>> print(collector.switch_ids)
            {5}
        """
        # Iterate over each command in the command list
        for command in commands:
            # Extract the command code (identifies the command type)
            command_code = command["code"]
            
            # Extract the parameters array (command-specific data)
            parameters = command.get("parameters", [])

            # ── SHOW_TEXT (code 101): Dialogue with face image ──
            # Parameters: [face_name, face_id, background, position]
            # We extract face_name (character identity) and face_id (expression)
            if command_code == CMD["SHOW_TEXT"] and len(parameters) >= 1:
                # Get the face asset name (first parameter)
                # Empty string means no face (narration)
                face_name = parameters[0]
                
                # Get the face ID (second parameter, default 0)
                # Face IDs are 0-7 for the 4x2 grid layout
                face_id = parameters[1] if len(parameters) > 1 else 0
                
                # Only process if a face asset is specified (not narration)
                if face_name:
                    # Convert the face asset name to a readable display name
                    # Example: "$SailorSkipper" → "Sailor Skipper"
                    display_name = self._clean_character_name(face_name)
                    
                    # Store the character mapping: face_name → display_name
                    # This is used by generate_characters_rpy()
                    self.characters[face_name] = display_name
                    
                    # Track which face IDs are used for this character
                    # Multiple dialogue lines may use different face IDs (expressions)
                    # setdefault ensures the set exists before adding
                    self.character_face_ids.setdefault(face_name, set()).add(face_id)

            # ── CONTROL_SWITCHES (code 121): Set switches ON/OFF ──
            # Parameters: [start_id, end_id, operation]
            # Sets a contiguous range of switches to ON (0) or OFF (1)
            elif command_code == CMD["CONTROL_SWITCHES"]:
                # Extract the range bounds
                start_id, end_id = parameters[0], parameters[1]
                
                # Add every switch ID in the range to our set
                # RPG Maker uses inclusive ranges: [5, 7] = switches 5, 6, 7
                for switch_id in range(start_id, end_id + 1):
                    self.switch_ids.add(switch_id)

            # ── CONTROL_VARIABLES (code 122): Modify variables ──
            # Parameters: [start_id, end_id, operation, ...]
            # Modifies a contiguous range of variables with an operation
            elif command_code == CMD["CONTROL_VARIABLES"]:
                # Extract the range bounds
                start_id, end_id = parameters[0], parameters[1]
                
                # Add every variable ID in the range to our set
                for variable_id in range(start_id, end_id + 1):
                    self.variable_ids.add(variable_id)

            # ── CONTROL_SELF_SWITCH (code 123): Toggle event-local switch ──
            # Parameters: [channel, operation]
            # Sets a self-switch (A/B/C/D) to ON (0) or OFF (1)
            elif command_code == CMD["CONTROL_SELF_SWITCH"]:
                # Get the channel letter (A, B, C, or D)
                channel = parameters[0]
                
                # Add the self-switch key to our map-specific set
                # Key format: (event_id, channel), grouped by map_id
                self.self_switches.setdefault(map_id, set()).add((event_id, channel))

            # ── CONDITIONAL (code 111): If/else branch ──
            # Parameters: [condition_type, ...type_specific_params]
            # Branches based on switch, variable, or self-switch state
            elif command_code == CMD["CONDITIONAL"]:
                # Get the condition type (0=switch, 1=variable, 2=self-switch, etc.)
                condition_type = parameters[0]
                
                # Condition type 0: Global switch check
                # Parameters: [0, switch_id, expected_value]
                if condition_type == 0:
                    # Add the switch ID being checked
                    self.switch_ids.add(parameters[1])
                
                # Condition type 1: Variable comparison
                # Parameters: [1, variable_id, comparison_type, value]
                elif condition_type == 1:
                    # Add the variable ID being checked
                    self.variable_ids.add(parameters[1])
                
                # Condition type 2: Self-switch check
                # Parameters: [2, channel, expected_value]
                elif condition_type == 2:
                    # Add the self-switch key being checked, grouped by map
                    self.self_switches.setdefault(map_id, set()).add((event_id, parameters[1]))

            # ── TRANSFER_PLAYER (code 201): Jump to another map ──
            # Parameters: [transfer_type, map_id, x, y, direction, fade]
            # Teleports the player to a target map
            elif command_code == CMD["TRANSFER_PLAYER"]:
                # Get the target map ID (second parameter)
                target_map_id = parameters[1]
                
                # Add the target map to our set
                # This ensures the map has an entry label in game_flow.rpy
                self.map_ids.add(target_map_id)

            # ── CHANGE_ITEMS_CMD (code 317): Add/remove items ──
            # Parameters: [..., item_id, ...]
            # Alternative item change command (plugin-specific variant)
            elif command_code == CMD["CHANGE_ITEMS_CMD"]:
                # Add the item ID being modified
                self.item_ids.add(parameters[1])

            # ── PLUGIN_COMMAND (code 356): Custom plugin command ──
            # Parameters: [command_string]
            # Calls a plugin-defined command (e.g., quest system)
            elif command_code == CMD["PLUGIN_COMMAND"]:
                # Store the plugin command string for potential special handling
                # The list maintains order in case sequence matters
                self.plugin_commands.append(parameters[0])

    @staticmethod
    def _clean_character_name(face_name: str) -> str:
        """Convert an RPG Maker face asset name to a readable display name.

        RPG Maker MV uses asset filenames as character identifiers, which often
        contain special prefixes and camelCase naming. This method transforms
        these into human-readable names suitable for Ren'Py Character definitions.

        RPG Maker Asset Naming Conventions:
        - "$" prefix: Large sprite (typically used for important characters)
        - "!" prefix: No shadow (used for floating characters or special sprites)
        - CamelCase: Standard naming convention (e.g., "SailorSkipper")
        - Numbers: Generic NPCs often numbered (e.g., "People3")

        Transformation Steps:
        1. Remove "$" and "!" prefixes (RPG Maker sprite markers)
        2. Insert spaces at camelCase boundaries (SailorSkipper → Sailor Skipper)
        3. Trim leading/trailing whitespace

        Args:
            face_name: Raw face asset name from RPG Maker JSON.
                Examples: "$Claire", "!SailorSkipper", "GuardPeople3"

        Returns:
            Cleaned display name suitable for Ren'Py Character definitions.
            Examples: "Claire", "Sailor Skipper", "Guard People3"

        Example:
            >>> DataCollector._clean_character_name("$Claire")
            'Claire'
            >>> DataCollector._clean_character_name("!SailorSkipper")
            'Sailor Skipper'
            >>> DataCollector._clean_character_name("GuardPeople3")
            'Guard People3'

        Note:
            This is a static method because it's a pure transformation function
            with no dependency on instance state. It's used during collection
            to create display names from asset names.

        See Also:
            helpers.side_image_tag: Similar transformation for image tags
            (lowercase, underscores instead of spaces)
        """
        # Step 1: Remove RPG Maker asset prefixes
        # "$" indicates a large sprite (used for important characters)
        # "!" indicates no shadow (for floating or special sprites)
        # We strip these as they have no meaning in Ren'Py
        name = face_name.replace("$", "").replace("!", "")
        
        # Step 2: Insert spaces at camelCase boundaries
        # Pattern: lowercase letter followed by uppercase letter
        # Example: "SailorSkipper" matches "rS" → "r S" → "Sailor Skipper"
        # The regex captures two groups and inserts a space between them
        # r"\1 \2" means "keep group 1, add space, keep group 2"
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        
        # Step 3: Trim whitespace and return
        # Handles cases where prefix removal left leading space
        return name.strip()
