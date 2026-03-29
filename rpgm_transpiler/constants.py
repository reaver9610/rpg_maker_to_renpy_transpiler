"""RPG Maker MV command code constants.

Maps the numeric event command codes used in RPG Maker MV JSON map files
to human-readable constant names. These codes identify what each event
command does (e.g., show dialogue, set a switch, transfer the player).
The transpiler uses these names to dispatch command processing in the
collector and Ren'Py generator modules.

RPG Maker MV Event Command Structure:
- Each event page contains a 'list' array of command objects
- Each command object has: code (int), indent (int), parameters (list)
- The 'code' field determines the command type
- The 'parameters' array contains command-specific data

Command Hierarchy:
- Block commands (SHOW_TEXT, SHOW_CHOICES, CONDITIONAL) start a new block
- Nested commands (TEXT_LINE, WHEN_CHOICE, ELSE) appear inside blocks
- Termination commands (END, END_CHOICES, END_CONDITIONAL) close blocks
"""

# ═══════════════════════════════════════════════════════════════════
# COMMAND CODE REFERENCE
# ═══════════════════════════════════════════════════════════════════

# RPG Maker MV command codes relevant to our transpiler.
# Keys are descriptive names used throughout the codebase for readability.
# Values are the numeric codes found in JSON 'code' fields.
#
# This dictionary serves as the single source of truth for command dispatch.
# When processing a command, we look up: CMD["SHOW_TEXT"] → 101
# Then compare against the command's 'code' field to identify the type.
#
# Not all RPG Maker commands are included—only those relevant to dialogue,
# game state, and navigation. Commands like "Show Picture" or "Screen Fade"
# are skipped and would need manual handling in the generated Ren'Py code.
CMD: dict[str, int] = {
    # ═══════════════════════════════════════════════════════════════
    # BLOCK TERMINATION
    # ═══════════════════════════════════════════════════════════════
    
    # END (code 0): Marks the end of an event page's command list.
    # Every command list ends with this. When we encounter it, we stop processing.
    # The collector and generator both use this to know when to break their loops.
    "END": 0,
    
    # ═══════════════════════════════════════════════════════════════
    # DIALOGUE COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # SHOW_TEXT (code 101): Opens a dialogue window with a speaker's face image.
    # Parameters: [face_name, face_id, background, position_type]
    # - face_name: Asset filename (e.g., "$Claire") or empty string for narration
    # - face_id: Index within the face sheet (0-7 for the 4x2 grid)
    # - background: Window background type (0=normal, 1=dim, 2=transparent)
    # - position_type: Window position (0=top, 1=middle, 2=bottom)
    # This command sets the speaker context for subsequent TEXT_LINE commands.
    # The generator tracks the current speaker and flushes text on speaker change.
    "SHOW_TEXT": 101,
    
    # TEXT_LINE (code 401): A single line of dialogue text within a message.
    # Parameters: [text_string]
    # - text_string: The actual dialogue text, possibly with escape codes
    # RPG Maker splits multi-line messages into separate TEXT_LINE commands.
    # The generator buffers these and flushes them as a single Ren'Py dialogue line.
    # Escape codes like \c[3] (color) are stripped by clean_text().
    "TEXT_LINE": 401,
    
    # ═══════════════════════════════════════════════════════════════
    # CHOICE COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # SHOW_CHOICES (code 102): Displays a player choice menu with labeled options.
    # Parameters: [choice_list, position_type, background, cancel_type, default_choice]
    # - choice_list: Array of choice text strings
    # - position_type: Window position (same as SHOW_TEXT)
    # - background: Window background type
    # - cancel_type: 0=disallow cancel, 1=cancel, 2=cancel branch (WHEN_CANCEL)
    # - default_choice: Index of the default selection (or -1 for none)
    # This starts a choice block. Subsequent WHEN_CHOICE commands define each branch.
    # The generator emits a Ren'Py 'menu:' block with the choice texts as options.
    "SHOW_CHOICES": 102,
    
    # WHEN_CHOICE (code 402): Begins the command block for a specific choice index.
    # Parameters: [choice_index]
    # - choice_index: The 0-based index of the choice this block handles
    # Commands after WHEN_CHOICE (until the next WHEN_CHOICE or END_CHOICES)
    # are executed when the player selects that choice.
    # The generator collects these commands and emits them inside the menu option.
    "WHEN_CHOICE": 402,
    
    # WHEN_CANCEL (code 403): Begins the command block for the cancel option.
    # Parameters: [] (no parameters)
    # Only present when SHOW_CHOICES has cancel_type=2.
    # Commands here execute when the player presses cancel/escape.
    # The generator emits these as a "(Cancel)" menu option if present.
    "WHEN_CANCEL": 403,
    
    # END_CHOICES (code 404): Marks the end of all choice branches.
    # Parameters: [] (no parameters)
    # Signals that the choice block is complete.
    # The generator stops collecting choice commands when it sees this.
    "END_CHOICES": 404,
    
    # ═══════════════════════════════════════════════════════════════
    # CONDITIONAL BRANCH COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # CONDITIONAL (code 111): Starts an if/else conditional branch block.
    # Parameters: [condition_type, ...type_specific_params]
    # Condition types:
    # - 0: Switch check (switch_id, expected_value where 0=ON, 1=OFF)
    # - 1: Variable check (variable_id, comparison_type, value)
    # - 2: Self-switch check (channel_letter, expected_value)
    # - 6: Script expression (JavaScript string)
    # - 7: Gold check (comparison_type, gold_amount)
    # The generator emits a Ren'Py 'if' statement with the translated condition.
    # Nested CONDITIONALs are handled recursively.
    "CONDITIONAL": 111,
    
    # ELSE (code 411): Else branch within a conditional block.
    # Parameters: [] (no parameters)
    # Commands after ELSE (until END_CONDITIONAL) execute when the condition is false.
    # The generator emits a Ren'Py 'else:' block.
    "ELSE": 411,
    
    # END_CONDITIONAL (code 412): Marks the end of a conditional branch block.
    # Parameters: [] (no parameters)
    # Signals that the if/else block is complete.
    # The generator stops collecting conditional commands when it sees this.
    "END_CONDITIONAL": 412,
    
    # ═══════════════════════════════════════════════════════════════
    # GAME STATE CONTROL COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # CONTROL_SWITCHES (code 121): Sets a range of global switches to ON/OFF.
    # Parameters: [start_id, end_id, operation_type]
    # - start_id: First switch ID in the range (inclusive)
    # - end_id: Last switch ID in the range (inclusive)
    # - operation_type: 0=ON (True), 1=OFF (False), 2=toggle (not implemented)
    # Switches are global booleans that persist across maps.
    # The generator emits: $ switch_{id} = True/False
    "CONTROL_SWITCHES": 121,
    
    # CONTROL_VARIABLES (code 122): Modifies a range of variables with an operation.
    # Parameters: [start_id, end_id, operation_type, operand_source, operand_value, ...]
    # - start_id: First variable ID in the range (inclusive)
    # - end_id: Last variable ID in the range (inclusive)
    # - operation_type: 0=set, 1=add, 2=subtract, 3=multiply, 4=divide, 5=mod
    # - operand_source: Where the operand comes from (0=constant, 1=variable, etc.)
    # - operand_value: The value to operate with (if source is constant)
    # Variables are global integers that persist across maps.
    # The generator emits: $ var_{id} = value or $ var_{id} += value
    "CONTROL_VARIABLES": 122,
    
    # CONTROL_SELF_SWITCH (code 123): Toggles a self-switch (event-local) ON/OFF.
    # Parameters: [channel_letter, operation_type]
    # - channel_letter: "A", "B", "C", or "D" (the four self-switch channels)
    # - operation_type: 0=ON (True), 1=OFF (False), 2=toggle (not implemented)
    # Self-switches are local to a specific event on a specific map.
    # The generator emits: $ selfswitch_{event_id}_{channel} = True/False
    "CONTROL_SELF_SWITCH": 123,
    
    # ═══════════════════════════════════════════════════════════════
    # INVENTORY COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # CHANGE_GOLD (code 125): Adds or removes gold from the player's inventory.
    # Parameters: [operation_type, operand_source, amount_or_variable_id]
    # - operation_type: 0=increase, 1=decrease
    # - operand_source: 0=constant, 1=variable
    # - amount_or_variable_id: The amount or variable ID containing the amount
    # Gold is a single global integer representing player currency.
    # The generator emits: $ gold += amount or $ gold -= amount
    "CHANGE_GOLD": 125,
    
    # CHANGE_ITEMS (code 126): Adds or removes items from the player's inventory.
    # Parameters: [operation_type, item_id, operand_source, amount_or_variable_id]
    # - operation_type: 0=increase, 1=decrease
    # - item_id: The database ID of the item
    # - operand_source: 0=constant, 1=variable
    # - amount_or_variable_id: The quantity to add/remove
    # Items are tracked as integers (quantity owned).
    # The collector records item_ids for state initialization.
    "CHANGE_ITEMS": 126,
    
    # CHANGE_WEAPONS (code 127): Adds or removes weapons from the player's inventory.
    # Parameters: [operation_type, weapon_id, operand_source, amount_or_variable_id]
    # - operation_type: 0=increase, 1=decrease
    # - weapon_id: The database ID of the weapon
    # - operand_source: 0=constant, 1=variable
    # - amount_or_variable_id: The quantity to add/remove
    # Weapons are tracked as integers (quantity owned).
    # The collector records weapon_ids for state initialization.
    "CHANGE_WEAPONS": 127,
    
    # CHANGE_ARMORS (code 128): Adds or removes armors from the player's inventory.
    # Parameters: [operation_type, armor_id, operand_source, amount_or_variable_id]
    # - operation_type: 0=increase, 1=decrease
    # - armor_id: The database ID of the armor
    # - operand_source: 0=constant, 1=variable
    # - amount_or_variable_id: The quantity to add/remove
    # Armors are tracked as integers (quantity owned).
    # The collector records armor_ids for state initialization.
    "CHANGE_ARMORS": 128,
    
    # CHANGE_ITEMS_CMD (code 317): Alternative item change command (plugin-specific).
    # Parameters: [unknown, item_id, ...]
    # This appears in some plugin-augmented maps as an alternative to CHANGE_ITEMS.
    "CHANGE_ITEMS_CMD": 317,
    
    # ═══════════════════════════════════════════════════════════════
    # NAVIGATION COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # TRANSFER_PLAYER (code 201): Teleports the player to a target map at coordinates.
    # Parameters: [transfer_type, map_id, x, y, direction, fade_type]
    # - transfer_type: 0=direct, 1=from variables (we assume direct)
    # - map_id: Target map's database ID
    # - x: Target X coordinate (tile position)
    # - y: Target Y coordinate (tile position)
    # - direction: Player facing direction after transfer (2=down, 4=left, 6=right, 8=up)
    # - fade_type: 0=black, 1=white, 2=no fade
    # This is the primary map navigation command.
    # The generator emits: jump map_{map_id}_enter
    "TRANSFER_PLAYER": 201,

    # ═══════════════════════════════════════════════════════════════
    # SCREEN EFFECTS
    # ═══════════════════════════════════════════════════════════════

    # TINT_SCREEN (code 221): Tints the screen to a specified color.
    # Parameters: [red, green, blue, strength, duration, wait_flag]
    # Used for visual effects like fading to black or sepia tones.
    "TINT_SCREEN": 221,

    # FLASH_SCREEN (code 222): Flashes the screen with a white overlay.
    # Parameters: [power, duration, wait_flag]
    # Often used after TINT_SCREEN to restore normal colors.
    "FLASH_SCREEN": 222,

    # ═══════════════════════════════════════════════════════════════
    # TIMING AND AUDIO COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # WAIT (code 230): Pauses execution for a number of frames.
    # Parameters: [frame_count]
    # - frame_count: Number of 60fps frames to wait
    # RPG Maker runs at 60 frames per second, so 60 frames = 1 second.
    # The generator converts to seconds: pause {seconds}
    "WAIT": 230,
    
    # PLAY_SE (code 250): Plays a sound effect file.
    # Parameters: [sound_object]
    # - sound_object: Dict with 'name', 'volume', 'pitch', 'pan'
    # The generator extracts the sound name and emits: play sound "{name}.ogg"
    # Note: Ren'Py uses .ogg format; RPG Maker may use .wav or .ogg.
    "PLAY_SE": 250,
    
    # ═══════════════════════════════════════════════════════════════
    # EXTENSIBILITY COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    # SCRIPT (code 355): Executes raw JavaScript (not transpiled).
    # Parameters: [script_string] (may span multiple SCRIPT commands)
    # JavaScript cannot run in Ren'Py, so this is emitted as a comment.
    # The generator emits: # [Script] {script_string}
    # Manual translation is required for complex scripts.
    "SCRIPT": 355,
    
    # PLUGIN_COMMAND (code 356): Calls a plugin command string.
    # Parameters: [command_string]
    # - command_string: Plugin-specific command (e.g., "Quest Add quest_001")
    # Plugin commands are game-specific extensions.
    # The generator has limited handling for known plugins (e.g., Quest).
    # Unknown plugins are emitted as comments for manual handling.
    "PLUGIN_COMMAND": 356,
    
    # ═══════════════════════════════════════════════════════════════
    # MOVEMENT COMMANDS (NOT TRANSPILED)
    # ═══════════════════════════════════════════════════════════════
    
    # MOVE_ROUTE (code 205): Defines a movement route for an event/player.
    # Parameters: [target_type, route_object]
    # Movement routes are visual novel incompatible (no sprite movement).
    # The generator skips these silently—they don't affect dialogue/flow.
    "MOVE_ROUTE": 205,
    
    # MOVE_PARAM (code 505): A single step within a move route definition.
    # Parameters: [move_code, ...params]
    # These follow MOVE_ROUTE commands and are skipped together.
    "MOVE_PARAM": 505,
}
