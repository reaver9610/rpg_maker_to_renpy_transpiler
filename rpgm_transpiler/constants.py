"""RPG Maker MV command code constants.

Maps the numeric event command codes used in RPG Maker MV JSON map files
to human-readable constant names. These codes identify what each event
command does (e.g., show dialogue, set a switch, transfer the player).
The transpiler uses these names to dispatch command processing in the
collector and Ren'Py generator modules.
"""

# ═══════════════════════════════════════════════════════════════════
# COMMAND CODE REFERENCE
# ═══════════════════════════════════════════════════════════════════

# RPG Maker MV command codes relevant to our transpiler.
# Keys are descriptive names; values are the numeric codes found in JSON.
CMD: dict[str, int] = {
    "END": 0,               # Marks the end of an event page's command list
    "SHOW_TEXT": 101,        # Opens a dialogue window, sets speaker face/name
    "TEXT_LINE": 401,        # A single line of dialogue text within a message
    "SHOW_CHOICES": 102,     # Displays a player choice menu with labeled options
    "WHEN_CHOICE": 402,      # Begins the command block for a specific choice index
    "WHEN_CANCEL": 403,      # Begins the command block for the cancel option
    "END_CHOICES": 404,      # Marks the end of all choice branches
    "CONDITIONAL": 111,      # Starts an if/else conditional branch block
    "ELSE": 411,             # Else branch within a conditional block
    "END_CONDITIONAL": 412,  # Marks the end of a conditional branch block
    "CONTROL_SWITCHES": 121, # Sets a range of global switches to ON/OFF
    "CONTROL_VARIABLES": 122,# Modifies a range of variables with an operation
    "CONTROL_SELF_SWITCH": 123, # Toggles a self-switch (event-local) ON/OFF
    "CHANGE_GOLD": 125,      # Adds or removes gold from the player's inventory
    "CHANGE_ITEMS": 126,     # Adds or removes items from the player's inventory
    "TRANSFER_PLAYER": 201,  # Teleports the player to a target map at coordinates
    "WAIT": 230,             # Pauses execution for a number of frames
    "PLAY_SE": 250,          # Plays a sound effect file
    "CHANGE_ITEMS_CMD": 317, # Alternative item change command (plugin-specific)
    "SCRIPT": 355,           # Executes raw JavaScript (not transpiled)
    "PLUGIN_COMMAND": 356,   # Calls a plugin command string
    "MOVE_ROUTE": 205,       # Defines a movement route for an event/player
    "MOVE_PARAM": 505,       # A single step within a move route definition
}
