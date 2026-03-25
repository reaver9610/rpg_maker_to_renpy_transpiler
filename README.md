# RPG Maker MV → Ren'Py Transpiler

Converts RPG Maker MV JSON map files into Ren'Py `.rpy` script files.

## Features

- Dialogue and speaker detection
- Choice menus (including cancel branches)
- Conditional branches (switches, variables, self-switches)
- Control switches and variables
- Map transfers
- Gold and item management
- Wait commands and sound effects

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Single file
python transpiler_rpy.py -f inputs/Map001.json

# Multiple files
python transpiler_rpy.py -m inputs/Map001.json inputs/Map002.json

# Directory
python transpiler_rpy.py -d inputs/

# Glob pattern
python transpiler_rpy.py -r "inputs/Map*.json"

# Custom output directory
python transpiler_rpy.py -d inputs/ -o my_output/
```

## Output Files

- `characters.rpy` - Character definitions
- `switches.rpy` - Game state (switches, variables, self-switches, items, gold)
- `map_*.rpy` - Individual map event scripts
- `game_flow.rpy` - Map navigation and game start

## Requirements

- Python 3.10+

## License

MIT License - see LICENSE file for details.

---

Author: Reaver