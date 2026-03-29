# RPG Maker MV → Ren'Py Transpiler

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-alpha-orange.svg)](https://github.com/reaver9610/rpg_maker_to_renpy_transpiler)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/reaver9610/rpg_maker_to_renpy_transpiler.svg)](https://github.com/reaver9610/rpg_maker_to_renpy_transpiler/issues)

A Python transpiler that converts RPG Maker MV JSON map files into Ren'Py `.rpy` script files. Designed to help port RPG Maker games to the Ren'Py visual novel engine by converting dialogue, choices, conditional branches, switches, variables, and map transfers.

## Features

### Core Transpilation

- ✅ Dialogue and speaker detection from face assets
- ✅ Choice menus with cancel branch support
- ✅ Conditional branches (switches, variables, self-switches)
- ✅ Control switches and variables
- ✅ Map transfers with automatic label generation
- ✅ Gold and item management
- ✅ Wait commands and sound effects
- ✅ Plugin command handling

### Output Organization

- ✅ Hierarchical map folder structure (from MapInfos.json)
- ✅ Split event files with fully qualified local labels
- ✅ Ren'Py named stores for game state management
- ✅ Self-switch files per event
- ✅ Side image declarations for character portraits
- ✅ Empty event filtering (skips decorative elements)

### CLI Options

- ✅ Multiple input modes (single file, multiple files, directory, glob pattern)
- ✅ Custom output directory
- ✅ Configurable indentation width (`-s N`)
- ✅ Character case options (`-c` with sub-flags)
- ✅ Interline spacing control (`-n N`)
- ✅ Multi-line dialogue format (`-f --multiline`)

## Requirements

- Python 3.10+
- No third-party dependencies

## Installation

### Development Install

```bash
# Clone the repository
git clone https://github.com/reaver9610/rpg_maker_to_renpy_transpiler.git
cd rpg_maker_to_renpy_transpiler

# Install in development mode
pip install -e .
```

### Run Without Installing

```bash
# Using PYTHONPATH
PYTHONPATH=. python transpiler_rpy.py -i --file inputs/Map001.json
```

## Quick Start

```bash
# Transpile all maps in a directory
rpgm-transpile -i --directory inputs/

# Or run without installing
PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/

# Output will be in outputs/
```

## Usage

### Input Options

```bash
# Single file
rpgm-transpile -i --file inputs/Map001.json

# Multiple files
rpgm-transpile -i --multiple inputs/Map001.json inputs/Map002.json

# Directory (all Map*.json files)
rpgm-transpile -i --directory inputs/

# Glob pattern
rpgm-transpile -i --regex "inputs/Map*.json"
```

### Output Options

```bash
# Custom output directory
rpgm-transpile -i --directory inputs/ -o my_game/

# Default: outputs/
```

### Format Options

```bash
# Single-line dialogue (default)
rpgm-transpile -i --file inputs/Map001.json -f --single

# Multi-line dialogue (Ren'Py triple-quoted strings)
rpgm-transpile -i --file inputs/Map001.json -f --multiline
```

### Indentation Options

```bash
# Default: 4 spaces per indent level
rpgm-transpile -i --file inputs/Map001.json

# Custom indent width (2 spaces)
rpgm-transpile -i --file inputs/Map001.json -s 2
```

### Case Options

Control character variable names, display names, and image tags:

```bash
# Default: Title case variable/display, lowercase image
# define Claire = Character("Claire", image="claire")
rpgm-transpile -i --file inputs/Map001.json

# Lowercase variable names only
rpgm-transpile -i --file inputs/Map001.json -c --lower

# Uppercase variable names
rpgm-transpile -i --file inputs/Map001.json -c --upper

# Full lowercase (var, display, image)
rpgm-transpile -i --file inputs/Map001.json -c --lower --lower-display --lower-image

# Mixed: uppercase var, title display, lowercase image
rpgm-transpile -i --file inputs/Map001.json -c --upper --title-display --lower-image
```

| Flag | Effect | Example |
|------|--------|---------|
| `--lower` | Lowercase variable names | `claire` |
| `--title` | Title case variable names (default) | `Claire` |
| `--upper` | Uppercase variable names | `CLAIRE` |
| `--lower-display` | Lowercase display names | `"claire"` |
| `--title-display` | Title case display names (default) | `"Claire"` |
| `--upper-display` | Uppercase display names | `"CLAIRE"` |
| `--lower-image` | Lowercase image tags (default) | `image="claire"` |
| `--title-image` | Title case image tags | `image="Claire"` |
| `--upper-image` | Uppercase image tags | `image="CLAIRE"` |

### Interlines Options

Add blank lines between output lines for readability:

```bash
# Default: no extra blank lines
rpgm-transpile -i --file inputs/Map001.json

# Add 1 blank line between lines in map files
rpgm-transpile -i --file inputs/Map001.json -n 1

# Add 2 blank lines, applies to maps by default
rpgm-transpile -i --file inputs/Map001.json -n 2

# Apply to specific files
rpgm-transpile -i --file inputs/Map001.json -n 1 --characters --global-switches

# Apply to all files
rpgm-transpile -i --file inputs/Map001.json -n 1 --all
```

| Flag | Target |
|------|--------|
| `--maps` | Map files only (default when using `-n`) |
| `--characters` | `characters.rpy` |
| `--global-switches` | `global_switches.rpy` |
| `--global-variables` | `global_variables.rpy` |
| `--global-items` | `global_items.rpy` |
| `--global-economy` | `global_economy.rpy` |
| `--global-quests` | `global_quests.rpy` |
| `--side-images` | `side_images.rpy` |
| `--game-flow` | `game_flow.rpy` |
| `--all` | All output files |

## Output Structure

```
outputs/
├── characters.rpy              # Character definitions
├── global_switches.rpy         # Global switches store
├── global_variables.rpy        # Global variables store
├── global_items.rpy            # Items store
├── global_economy.rpy          # Gold/economy store
├── global_quests.rpy           # Quest log store
├── side_images.rpy             # Side image declarations
├── game_flow.rpy               # Game entry point
├── common_events/              # Common events (if any)
│   └── event_1_quests/
│       └── event_1_quests.rpy
└── maps/                       # Map files (hierarchical)
    └── map_206_Prologue/
        └── map_46_Home_Refugee_Camp/
            └── map_3_Refugee_Camp/
                └── map_1_Checkpoint/
                    ├── map_1_Checkpoint.rpy           # Map placeholder
                    └── map_1_Checkpoint_events/       # Events subfolder
                        ├── map_1_Checkpoint_event_3_auto/
                        │   ├── map_1_Checkpoint_event_3_auto.rpy
                        │   └── map_1_Checkpoint_event_3_auto_switches.rpy
                        └── map_1_Checkpoint_event_2_ev002/
                            └── map_1_Checkpoint_event_2_ev002.rpy
```

### Output Files

| File | Purpose |
|------|---------|
| `characters.rpy` | Ren'Py `Character()` definitions with auto-assigned colors |
| `global_switches.rpy` | `init python in game_switch:` block for global switches |
| `global_variables.rpy` | `init python in game_vars:` block for global variables |
| `global_items.rpy` | `init python in game_items:` block for item quantities |
| `global_economy.rpy` | `init python in game_economy:` block for gold |
| `global_quests.rpy` | `init python in game_quest:` block for quest log |
| `side_images.rpy` | `image side {char} {face_id}` declarations |
| `game_flow.rpy` | `label start:` entry point with map jumps |

### Store Reference Patterns

| Concept | Store | Example Reference |
|---------|-------|-------------------|
| Global Switch | `game_switch` | `game_switch.switch_5_paid` |
| Global Variable | `game_vars` | `game_vars.var_2_defiance` |
| Self-Switch | `map_{id}_{name}_self_switches` | `map_3_refugee_camp_self_switches.switch_40_under_A` |
| Item | `game_items` | `game_items.item_1` |
| Gold | `game_economy` | `game_economy.gold` |
| Quest Log | `game_quest` | `game_quest.quest_log` |

## How It Works

1. **Collection Phase**: Scans JSON map files to collect:
   - Character names from face assets
   - Switch/variable IDs and names (from System.json)
   - Self-switches used by events
   - Items and quest references

2. **Generation Phase**: Processes each map to generate:
   - Character definitions with auto-colors
   - Global stores for game state
   - Side image declarations
   - Event files with local labels
   - Game flow entry point

3. **Output Organization**:
   - Maps are organized hierarchically (from MapInfos.json)
   - Events use fully qualified local labels (`map_Name.event_id`)
   - Self-switches have separate files per event

## Project Structure

```
rpg_maker_to_renpy_transpiler/
├── rpgm_transpiler/            # Main package
│   ├── __init__.py             # Orchestrator + re-exports
│   ├── constants.py            # RPG Maker command codes (CMD dict)
│   ├── collector.py            # DataCollector class
│   ├── helpers.py              # Utility functions
│   ├── generator.py            # RenPyGenerator class
│   ├── characters.py           # Character output generator
│   ├── switches.py             # State management generators
│   ├── game_flow.py            # Game flow generator
│   └── side_images.py          # Side image generator
├── transpiler_rpy.py           # CLI entry point
├── setup.py                    # Package configuration
├── test_scripts/               # Test shell scripts
│   ├── input/                  # Input option tests
│   ├── format/                 # Format option tests
│   ├── output/                 # Output option tests
│   ├── indent/                 # Indent option tests
│   ├── case/                   # Case option tests
│   ├── interlines/             # Interlines option tests
│   └── combined/               # Combined option tests
├── inputs/                     # Test JSON map files
├── outputs/                    # Default output directory
├── AGENTS.md                   # Development documentation
├── CHANGELOG.md                # Version history
├── LICENSE                     # MIT License
└── README.md                   # This file
```

## Troubleshooting

### Common Issues

**"No .json files found"**

- Ensure your map files are named `Map*.json` (e.g., `Map001.json`, `Map002.json`)
- `MapInfos.json` and `System.json` are loaded automatically from the same directory

**"Character not found in dialogue"**

- Characters are detected from face asset names in SHOW_TEXT commands
- Check that face assets exist in your RPG Maker project's `img/faces/` folder
- Character names are derived from the face filename (e.g., `$Claire.png` → `Claire`)

**"Empty event files"**

- Events with only `label` + `return` are automatically filtered as they represent decorative elements (torches, glows, etc.)
- This is expected behavior - approximately 36% of events are filtered

**"Self-switches not working in Ren'Py"**

- Self-switches use Ren'Py named stores (`map_{id}_{name}_self_switches`)
- Ensure all `global_*.rpy` files are in your Ren'Py project's `game/` directory

**"Map names showing as 'Unknown'"**

- Ensure `MapInfos.json` is present in the same directory as your map files
- Map names are loaded from `MapInfos.json` for hierarchical structure

## FAQ

**Q: Can I use this with RPG Maker MZ?**

A: RPG Maker MZ uses a similar JSON format for maps. While not officially tested, basic maps should work. Some MZ-specific features may not be supported.

**Q: How do I customize character colors?**

A: Edit `_get_character_color()` in `rpgm_transpiler/characters.py`. The function maps character names to Ren'Py color strings.

**Q: Can I transpile a single event instead of a whole map?**

A: No, the transpiler processes entire maps. However, you can delete unwanted event files from the output.

**Q: How do I handle RPG Maker variables in dialogue (`\V[1]`)?**

A: Variable interpolation in dialogue is not yet supported (see Roadmap). You'll need to manually convert these to Ren'Py's `[var_name]` syntax.

**Q: Why are there two versions of each switch/variable name?**

A: The output uses both numeric IDs (`switch_5`) and descriptive names (`switch_5_paid`) when System.json is present. This helps with readability and debugging.

## Roadmap

### Planned Features

- [ ] Variable interpolation in dialogue (`\V[N]` → `[var_N]`)
- [ ] Actor name placeholders (`\N[N]` → `[char_N]`)
- [ ] Icon support in dialogue (`\I[N]`)
- [ ] Picture command handling
- [ ] Screen tint/fade effects
- [ ] Parallax background support
- [ ] Battle event conversion
- [ ] Common event extraction improvements
- [ ] Ren'Py 8+ ATL animation generation

### Considerations

- [ ] RPG Maker MZ compatibility testing
- [ ] Plugin command handlers for popular RPG Maker plugins
- [ ] GUI wrapper for non-technical users

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

1. Fork and clone the repository
   ```bash
   git clone https://github.com/YOUR_USERNAME/rpg_maker_to_renpy_transpiler.git
   cd rpg_maker_to_renpy_transpiler
   ```

2. Install in development mode
   ```bash
   pip install -e .
   ```

3. Run test scripts to verify your setup
   ```bash
   ./test_scripts/input/test_single_file.sh
   ```

### Code Style

- Python 3.10+ syntax (PEP 604 union types: `X | None`)
- Type hints on method signatures and class attributes
- 4-space indentation
- ~100 character line limit
- Standard library only (no third-party dependencies)

### Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear, descriptive commit messages
3. Run relevant test scripts to verify functionality
4. Update documentation (AGENTS.md, README.md) if needed
5. Submit PR with a description of changes

## Acknowledgments

- Built for the [Ren'Py Visual Novel Engine](https://www.renpy.org/)
- Converts maps from [RPG Maker MV](https://www.rpgmakerweb.com/products/rpg-maker-mv)
- Inspired by the need to port RPG Maker games to Ren'Py

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**Reaver**

- GitHub: [@reaver9610](https://github.com/reaver9610)
- Repository: [rpg_maker_to_renpy_transpiler](https://github.com/reaver9610/rpg_maker_to_renpy_transpiler)
