"""Generates .rpy files for global game state declarations using Ren'Py named stores.

This module creates separate .rpy files for each category of game state discovered
during the collection phase: global switches, global variables, items, economy (gold),
and quest log. Each file uses a dedicated Ren'Py named store for clean namespace
separation.

Additionally, per-event and per-map self-switch declaration files are generated,
placing self-switches in map-specific stores.

Game State in RPG Maker vs Ren'Py:
RPG Maker MV uses a database-driven approach:
- Switches: Global boolean flags (ON/OFF), referenced by numeric ID
- Variables: Global integers, referenced by numeric ID
- Self-switches: Event-local booleans (A/B/C/D channels)
- Items: Database entries with quantities

Ren'Py uses Python variables organized in named stores:
- game_switch: Global switches (e.g., game_switch.switch_5_paid)
- game_vars: Global variables (e.g., game_vars.var_2_defiance)
- map_{id}_{name}: Per-map self-switches (e.g., map_1_checkpoint.switch_3_A)
- game_items: Item quantities (e.g., game_items.item_1)
- game_economy: Player currency (e.g., game_economy.gold)
- game_quest: Quest tracking (e.g., game_quest.quest_log)

Output Files:
    global_switches.rpy     → init python in game_switch:
    global_variables.rpy    → init python in game_vars:
    global_items.rpy        → init python in game_items:
    global_economy.rpy      → init python in game_economy:
    global_quests.rpy       → init python in game_quest:
    map_{id}_{name}_switches.rpy → init python in map_{id}_{name}: (per map)

Initialization Strategy:
All game state defaults to "empty" values:
- Switches: False (OFF)
- Variables: 0
- Self-switches: False (OFF)
- Items: 0 (not in inventory)
- Gold: 0
- Quest log: empty list

This matches RPG Maker's behavior where new games start with all switches OFF
and all variables at 0.
"""

from .collector import DataCollector
from .helpers import join_with_interlines, to_title_case, make_indent


def generate_global_switches_rpy(collector: DataCollector, interlines: int = 0, indent_width: int = 4) -> str:
    """Generate global_switches.rpy with default global switch declarations.

    Creates a .rpy file containing `init python in game_switch:` assignments for every
    global switch discovered during the collection phase.

    Store: game_switch
    Reference: game_switch.switch_{id}_{name}

    Args:
        collector: DataCollector instance populated with switch data.
            Required attributes:
            - switch_ids: set of global switch IDs
            - get_switch_name(switch_id): returns variable name like "switch_5_paid"
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for global_switches.rpy.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector with switch_ids ...
        >>> source = generate_global_switches_rpy(collector)
        >>> with open("global_switches.rpy", "w") as f:
        ...     f.write(source)

    Note:
        The generated file uses a Ren'Py named store (game_switch) so all
        switch references in other .rpy files must be prefixed with game_switch.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GLOBAL SWITCHES")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # ── Global Switches ──
    # Emit only if there are switches in the collection
    if collector.switch_ids:
        # Use the game_switch named store for clean namespace separation
        output_lines.append("init python in game_switch:")
        output_lines.append("")

        # Iterate over switches in sorted order for consistent output
        for switch_id in sorted(collector.switch_ids):
            # Get the concatenated variable name (switch_{id}_{name})
            # Uses System.json names if available
            variable_name = collector.get_switch_name(switch_id)

            # Initialize each switch to False (OFF state)
            # In RPG Maker, switches default to OFF when a new game starts
            output_lines.append(f"{make_indent(indent_width)}{variable_name} = False")

        # Add a trailing blank line
        output_lines.append("")

    # Join all lines with newlines and return
    # Uses join_with_interlines to add blank lines only between code lines,
    # skipping comment lines and empty lines for compact output
    return join_with_interlines(output_lines, interlines)


def generate_global_variables_rpy(collector: DataCollector, interlines: int = 0, indent_width: int = 4) -> str:
    """Generate global_variables.rpy with default global variable declarations.

    Creates a .rpy file containing `init python in game_vars:` assignments for every
    global variable discovered during the collection phase.

    Store: game_vars
    Reference: game_vars.var_{id}_{name}

    Args:
        collector: DataCollector instance populated with variable data.
            Required attributes:
            - variable_ids: set of global variable IDs
            - get_variable_name(variable_id): returns name like "var_2_defiance"
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for global_variables.rpy.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector with variable_ids ...
        >>> source = generate_global_variables_rpy(collector)
        >>> with open("global_variables.rpy", "w") as f:
        ...     f.write(source)

    Note:
        The generated file uses a Ren'Py named store (game_vars) so all
        variable references in other .rpy files must be prefixed with game_vars.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GLOBAL VARIABLES")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # ── Variables ──
    # Emit only if there are variables in the collection
    if collector.variable_ids:
        # Use the game_vars named store for clean namespace separation
        output_lines.append("init python in game_vars:")
        output_lines.append("")

        # Iterate over variables in sorted order for consistent output
        for variable_id in sorted(collector.variable_ids):
            # Get the concatenated variable name (var_{id}_{name})
            # Uses System.json names if available
            variable_name = collector.get_variable_name(variable_id)

            # Initialize each variable to 0
            # In RPG Maker, variables default to 0 when a new game starts
            output_lines.append(f"{make_indent(indent_width)}{variable_name} = 0")

        # Add a trailing blank line
        output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)


def generate_global_items_rpy(collector: DataCollector, interlines: int = 0, indent_width: int = 4) -> str:
    """Generate global_items.rpy with default item/weapon/armor inventory declarations.

    Creates a .rpy file containing `init python in game_items:` assignments for every
    item, weapon, and armor discovered during the collection phase.

    Store: game_items
    Reference: game_items.item_{id}_{name}, game_items.weapon_{id}_{name}, game_items.armor_{id}_{name}

    Args:
        collector: DataCollector instance populated with item/weapon/armor data.
            Required attributes:
            - item_ids: set of item IDs
            - weapon_ids: set of weapon IDs
            - armor_ids: set of armor IDs
            - get_item_name(item_id): returns variable name
            - get_weapon_name(weapon_id): returns variable name
            - get_armor_name(armor_id): returns variable name
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for global_items.rpy.
        Returns empty string if no items, weapons, or armors were collected.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector with item_ids, weapon_ids, armor_ids ...
        >>> source = generate_global_items_rpy(collector)
        >>> with open("global_items.rpy", "w") as f:
        ...     f.write(source)

    Note:
        The generated file uses a Ren'Py named store (game_items) so all
        item references in other .rpy files must be prefixed with game_items.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# INVENTORY")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # Check if any inventory data exists
    has_any = collector.item_ids or collector.weapon_ids or collector.armor_ids
    if not has_any:
        return ""

    # Use the game_items named store for clean namespace separation
    output_lines.append("init python in game_items:")
    output_lines.append("")

    # ── Items ──
    if collector.item_ids:
        # Subsection comment
        output_lines.append(f"{make_indent(indent_width)}# Items")
        # Iterate over items in sorted order for consistent output
        for item_id in sorted(collector.item_ids):
            # Get variable name with optional name suffix
            variable_name = collector.get_item_name(item_id)
            # Initialize each item quantity to 0 (not in inventory)
            output_lines.append(f"{make_indent(indent_width)}{variable_name} = 0")
        # Blank line between subsections
        output_lines.append("")

    # ── Weapons ──
    if collector.weapon_ids:
        # Subsection comment
        output_lines.append(f"{make_indent(indent_width)}# Weapons")
        # Iterate over weapons in sorted order for consistent output
        for weapon_id in sorted(collector.weapon_ids):
            # Get variable name with optional name suffix
            variable_name = collector.get_weapon_name(weapon_id)
            # Initialize each weapon quantity to 0 (not in inventory)
            output_lines.append(f"{make_indent(indent_width)}{variable_name} = 0")
        # Blank line between subsections
        output_lines.append("")

    # ── Armors ──
    if collector.armor_ids:
        # Subsection comment
        output_lines.append(f"{make_indent(indent_width)}# Armors")
        # Iterate over armors in sorted order for consistent output
        for armor_id in sorted(collector.armor_ids):
            # Get variable name with optional name suffix
            variable_name = collector.get_armor_name(armor_id)
            # Initialize each armor quantity to 0 (not in inventory)
            output_lines.append(f"{make_indent(indent_width)}{variable_name} = 0")
        # Blank line between subsections
        output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)


def generate_global_economy_rpy(interlines: int = 0, indent_width: int = 4) -> str:
    """Generate global_economy.rpy with the gold (currency) declaration.

    Creates a .rpy file containing `init python in game_economy:` with the
    gold variable initialized to 0.

    Store: game_economy
    Reference: game_economy.gold

    Args:
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for global_economy.rpy.

    Example:
        >>> source = generate_global_economy_rpy()
        >>> with open("global_economy.rpy", "w") as f:
        ...     f.write(source)

    Note:
        Gold is always emitted regardless of whether any gold-changing commands
        were found in the map data, since the economy system is fundamental
        to most RPG games.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# ECONOMY")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # ── Gold ──
    # Use the game_economy named store for the currency system
    output_lines.append("init python in game_economy:")
    output_lines.append("")

    # Initialize gold to 0 (starting with no money)
    # Game designers can modify this value for different starting conditions
    output_lines.append(f"{make_indent(indent_width)}gold = 0")

    # Add a trailing blank line
    output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)


def generate_global_quests_rpy(interlines: int = 0, indent_width: int = 4) -> str:
    """Generate global_quests.rpy with the quest log declaration.

    Creates a .rpy file containing `init python in game_quest:` with the
    quest_log variable initialized to an empty list.

    Store: game_quest
    Reference: game_quest.quest_log

    Args:
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for global_quests.rpy.

    Example:
        >>> source = generate_global_quests_rpy()
        >>> with open("global_quests.rpy", "w") as f:
        ...     f.write(source)

    Note:
        Quest log is always emitted since it's used by plugin commands
        (e.g., Quest system) that may be present in any map.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# QUEST LOG")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # ── Quest Log ──
    # Use the game_quest named store for quest tracking
    output_lines.append("init python in game_quest:")
    output_lines.append("")

    # Initialize quest_log as an empty list
    # Quests are added via plugin commands during gameplay
    output_lines.append(f"{make_indent(indent_width)}quest_log = []")

    # Add a trailing blank line
    output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)


def generate_map_switches_rpy(
    collector: DataCollector,
    map_id: int,
    map_name: str,
    interlines: int = 0,
    indent_width: int = 4,
) -> str:
    """Generate a per-map self-switch declaration file.

    Creates a .rpy file containing `init python in map_{id}_{name}:` assignments for every
    self-switch that belongs to the specified map.

    Store: ``map_{id}_{sanitized_name}_self_switches``
    Reference: ``map_{id}_{name}_self_switches.switch_{event_id}_{name}_{channel}``

    Self-switches are event-local booleans (A/B/C/D channels) that are unique to
    a specific event on a specific map. Unlike global switches, they don't persist
    across maps and are keyed by both the event ID and the channel letter.

    Args:
        collector: DataCollector instance populated with self-switch data.
            Required attributes:
            - self_switches: dict mapping map_id to dict of event_id → list of channels
            - get_self_switch_store_name(map_id): returns store name like "map_1_checkpoint_self_switches"
        map_id: The numeric ID of this map (from filename or MapInfos.json).
        map_name: The human-readable name of this map for header comments.
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.

    Returns:
        Complete .rpy source string for the per-map self-switch file.
        Returns empty string if no self-switches exist for this map.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector with self_switches data ...
        >>> source = generate_map_switches_rpy(collector, 1, "Checkpoint")
        >>> if source:
        ...     with open("map_1_Checkpoint_switches.rpy", "w") as f:
        ...         f.write(source)

    Note:
        The per-map self-switch file should be placed in the same directory as
        the map's .rpy event file so Ren'Py can find both files together.
    """
    # Check if this map has any self-switches
    # If not, return empty string (no file needs to be generated)
    map_self_switches = collector.self_switches.get(map_id, {})
    if not map_self_switches:
        return ""

    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with map name and ID for debugging
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append(f"# SELF-SWITCHES — Map {map_id}: {map_name}")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # Get the Ren'Py named store name for this map
    # This is used as the store namespace (e.g., "map_1_checkpoint")
    store_name = collector.get_self_switch_store_name(map_id)

    # ── Self-Switches ──
    # Use the per-map named store for self-switch declarations
    output_lines.append(f"init python in {store_name}:")
    output_lines.append("")

    # Iterate over self-switches in sorted order
    # Sorting by (event_id, channel) ensures consistent output
    for event_id, channels in sorted(map_self_switches.items()):
        for channel in sorted(channels):
            # Build a descriptive variable name using the event's safe label
            # Format: switch_{event_id}_{event_name}_{channel}
            # Example: switch_40_under_A (for event 40 "Under", channel A)
            switch_name = collector.get_self_switch_name(map_id, event_id, channel)
            output_lines.append(f"{make_indent(indent_width)}{switch_name} = False")

    # Add a trailing blank line
    output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)


def generate_event_switches_rpy(
    collector: DataCollector,
    map_id: int,
    event_id: int,
    map_name: str,
    event_label: str,
    interlines: int = 0,
    indent_width: int = 4,
) -> str:
    """Generate a per-event self-switch declaration file.

    Creates a .rpy file containing ``init python in map_{id}_{name}:`` assignments for
    the self-switch channels (A/B/C/D) that belong to a single event.

    Store: ``map_{id}_{sanitized_name}_self_switches``
    Reference: ``map_{id}_{name}_self_switches.switch_{event_id}_{name}_{channel}``

    Args:
        collector: DataCollector instance populated with self-switch data.
            Required attributes:
            - self_switches: dict mapping map_id to dict of event_id → list of channels
            - get_self_switch_store_name(map_id): returns store name like "map_1_checkpoint_self_switches"
            - get_self_switch_name(map_id, event_id, channel): returns variable name like "switch_40_under_A"
            - get_event_switches(map_id, event_id): returns sorted [(event_id, channel), ...] list
        map_id: The numeric ID of this map.
        event_id: The numeric ID of this event.
        map_name: The human-readable name of this map for header comments.
        event_label: The safe label of this event (e.g., "event_40_under").
        interlines: Number of blank lines to insert between each output line.
            Default 0 means no extra spacing.
        indent_width: Number of spaces for one indentation level.

    Returns:
        Complete .rpy source string for the per-event self-switch file.
        Returns empty string if no self-switches exist for this event.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector with self_switches data ...
        >>> source = generate_event_switches_rpy(collector, 3, 54, "Refugee Camp", "event_54_striptease")
        >>> if source:
        ...     with open("event_54_striptease_switches.rpy", "w") as f:
        ...         f.write(source)
    """
    # Get the self-switch channels used by this specific event
    # Returns sorted list of (event_id, channel) tuples
    event_switches = collector.get_event_switches(map_id, event_id)
    if not event_switches:
        return ""

    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with event and map info for debugging
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append(f"# SELF-SWITCHES — Event {event_id}: {event_label}")
    output_lines.append(f"# Map {map_id}: {map_name}")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")

    # Get the Ren'Py named store name for this map
    store_name = collector.get_self_switch_store_name(map_id)

    # ── Self-Switches ──
    output_lines.append(f"init python in {store_name}:")
    output_lines.append("")

    # Emit one declaration per channel
    for _, channel in event_switches:
        switch_name = collector.get_self_switch_name(map_id, event_id, channel)
        output_lines.append(f"{make_indent(indent_width)}{switch_name} = False")

    # Add a trailing blank line
    output_lines.append("")

    # Join all lines with newlines and return
    return join_with_interlines(output_lines, interlines)
