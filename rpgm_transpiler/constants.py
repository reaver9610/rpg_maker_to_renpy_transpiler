# ═══════════════════════════════════════════════════════════════════
# COMMAND CODE REFERENCE
# ═══════════════════════════════════════════════════════════════════

# RPG Maker MV command codes relevant to our transpiler
CMD: dict[str, int] = {
    "END": 0,
    "SHOW_TEXT": 101,
    "TEXT_LINE": 401,
    "SHOW_CHOICES": 102,
    "WHEN_CHOICE": 402,
    "WHEN_CANCEL": 403,
    "END_CHOICES": 404,
    "CONDITIONAL": 111,
    "ELSE": 411,
    "END_CONDITIONAL": 412,
    "CONTROL_SWITCHES": 121,
    "CONTROL_VARIABLES": 122,
    "CONTROL_SELF_SWITCH": 123,
    "CHANGE_GOLD": 125,
    "CHANGE_ITEMS": 126,
    "TRANSFER_PLAYER": 201,
    "WAIT": 230,
    "PLAY_SE": 250,
    "CHANGE_ITEMS_CMD": 317,
    "SCRIPT": 355,
    "PLUGIN_COMMAND": 356,
    "MOVE_ROUTE": 205,
    "MOVE_PARAM": 505,
}