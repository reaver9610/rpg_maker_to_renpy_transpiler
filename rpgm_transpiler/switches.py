"""Generates switches.rpy with default game state variable declarations.

This module creates the switches.rpy file containing `init python:` assignments for
every switch, variable, self-switch, item, and utility variable (gold, quest log)
discovered during the collection phase.

Game State in RPG Maker vs Ren'Py:
RPG Maker MV uses a database-driven approach:
- Switches: Global boolean flags (ON/OFF), referenced by numeric ID
- Variables: Global integers, referenced by numeric ID
- Self-switches: Event-local booleans (A/B/C/D channels)
- Items: Database entries with quantities

Ren'Py uses Python variables:
- We map RPG Maker IDs to named variables: switch_5, var_12
- Self-switches combine event ID and channel: selfswitch_5_A
- Items are simple counters: item_3

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

Output File Structure:
    # ═══════════════════════════════════════════════════
    # GAME STATE — Switches, Variables, Self-Switches
    # Auto-generated from RPG Maker MV
    # ═══════════════════════════════════════════════════

    init python:

        # ── Global Switches ──
        switch_1 = False
        switch_5 = False
        ...

        # ── Variables ──
        var_1 = 0
        var_3 = 0
        ...

        # ── Self-Switches ──
        selfswitch_1_A = False
        selfswitch_5_B = False
        ...

        # ── Items ──
        item_1 = 0
        item_5 = 0
        ...

        # ── Gold ──
        gold = 0

        # ── Quest Log ──
        quest_log = []
"""

from .collector import DataCollector


def generate_switches_rpy(collector: DataCollector) -> str:
    """Generate switches.rpy with default game state variable declarations.

    Creates a .rpy file containing `init python:` assignments for every
    switch, variable, self-switch, item, and utility variable (gold, quest log)
    discovered during the collection phase.

    Initialization Values:
    - Switches: False (RPG Maker OFF state)
    - Variables: 0 (RPG Maker default)
    - Self-switches: False (RPG Maker OFF state)
    - Items: 0 (empty inventory)
    - Gold: 0 (starting with no money)
    - Quest log: [] (empty list)

    Variable Naming Convention:
    All game state variables use snake_case with type prefixes:
    - switch_{id}_{name}: Global switches (e.g., switch_278_guards_insulted)
    - var_{id}_{name}: Global variables (e.g., var_2_claires_defiance)
    - selfswitch_{event_id}_{channel}: Self-switches (e.g., selfswitch_5_A)
    - item_{id}: Item quantities (e.g., item_3)
    - gold: Player currency
    - quest_log: Quest tracking list
    
    When System.json is available, switch and variable names are concatenated
    with their human-readable names for improved code readability.

    Args:
        collector: DataCollector instance populated with switch/variable/item data.
            Required attributes:
            - switch_ids: set of global switch IDs
            - variable_ids: set of global variable IDs
            - self_switches: set of (event_id, channel) tuples
            - item_ids: set of item IDs

    Returns:
        Complete .rpy source string for switches.rpy.
        Ready to be written to a file.

    Example:
        >>> collector = DataCollector()
        >>> # ... populate collector ...
        >>> source = generate_switches_rpy(collector)
        >>> with open("switches.rpy", "w") as f:
        ...     f.write(source)

    Note:
        The generated file is designed to be included in Ren'Py's init phase.
        Variables are accessible throughout the game after the init phase completes.
    """
    # Initialize the output lines list
    output_lines: list[str] = []

    # ── File Header ──
    # Emit a decorative header with section marker
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("# GAME STATE — Switches, Variables, Self-Switches")
    output_lines.append("# Auto-generated from RPG Maker MV")
    output_lines.append("# ═══════════════════════════════════════════════════")
    output_lines.append("")
    
    # ── Init Python Block ──
    # All game state variables are defined in an init python block
    # This ensures they're initialized before any game code runs
    output_lines.append("init python:")
    output_lines.append("")

    # ── Global Switches ──
    # Emit only if there are switches in the collection
    if collector.switch_ids:
        output_lines.append("    # ── Global Switches ──")
        
        # Iterate over switches in sorted order for consistent output
        for switch_id in sorted(collector.switch_ids):
            # Get the concatenated variable name (switch_{id}_{name})
            # Uses System.json names if available
            variable_name = collector.get_switch_name(switch_id)
            
            # Initialize each switch to False (OFF state)
            # In RPG Maker, switches default to OFF when a new game starts
            output_lines.append(f"    {variable_name} = False")
        
        # Add a blank line for readability
        output_lines.append("")

    # ── Variables ──
    # Emit only if there are variables in the collection
    if collector.variable_ids:
        output_lines.append("    # ── Variables ──")
        
        # Iterate over variables in sorted order for consistent output
        for variable_id in sorted(collector.variable_ids):
            # Get the concatenated variable name (var_{id}_{name})
            # Uses System.json names if available
            variable_name = collector.get_variable_name(variable_id)
            
            # Initialize each variable to 0
            # In RPG Maker, variables default to 0 when a new game starts
            output_lines.append(f"    {variable_name} = 0")
        
        # Add a blank line for readability
        output_lines.append("")

    # ── Self-Switches ──
    # Emit only if there are self-switches in the collection
    if collector.self_switches:
        output_lines.append("    # ── Self-Switches ──")
        
        # Iterate over self-switches in sorted order
        # Sorting by (event_id, channel) ensures consistent output
        for event_id, channel in sorted(collector.self_switches):
            # Initialize each self-switch to False (OFF state)
            # The variable name includes both event_id and channel for uniqueness
            output_lines.append(f"    selfswitch_{event_id}_{channel} = False")
        
        # Add a blank line for readability
        output_lines.append("")

    # ── Items ──
    # Emit only if there are items in the collection
    if collector.item_ids:
        output_lines.append("    # ── Items ──")
        
        # Iterate over items in sorted order for consistent output
        for item_id in sorted(collector.item_ids):
            # Initialize each item quantity to 0 (not in inventory)
            output_lines.append(f"    item_{item_id} = 0")
        
        # Add a blank line for readability
        output_lines.append("")

    # ── Gold ──
    # Gold is always initialized (always needed for the game)
    output_lines.append("    # ── Gold ──")
    
    # Initialize gold to 0 (starting with no money)
    # Game designers can modify this value for different starting conditions
    output_lines.append("    gold = 0")
    
    # Add a blank line for readability
    output_lines.append("")

    # ── Quest Log ──
    # Quest log is always initialized (used by plugin commands)
    output_lines.append("    # ── Quest Log ──")
    
    # Initialize quest_log as an empty list
    # Quests are added via plugin commands during gameplay
    output_lines.append("    quest_log = []")
    
    # Add a trailing blank line
    output_lines.append("")

    # Join all lines with newlines and return
    return "\n".join(output_lines)
