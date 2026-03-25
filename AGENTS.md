# AGENTS.md

## Project Overview

Python transpiler that converts RPG Maker MV JSON map files into Ren'Py `.rpy` script files. Converts dialogue, choices, conditional branches, switches, variables, and map transfers.

## Project Structure

```
rpgm_transpiler/           # Package
├── __init__.py            # transpile_to_renpy() orchestrator + re-exports
├── constants.py           # CMD dict (RPG Maker command codes)
├── collector.py           # DataCollector class
├── renpy_generator.py     # RenPyGenerator class + helper functions
└── output_files.py        # generate_characters_rpy(), generate_switches_rpy(), generate_game_flow_rpy()

transpiler_rpy.py          # CLI entry point
setup.py                   # Package setup with entry point
test_scripts/              # Test scripts for CLI options
inputs/                    # Test JSON map files
outputs/                   # Default output directory
renpy_output/              # Alternative output directory (deprecated)
```

## Running the Transpiler

### Development Mode (no install)
```bash
# Single file
PYTHONPATH=. python transpiler_rpy.py -f inputs/Map001.json

# Multiple files
PYTHONPATH=. python transpiler_rpy.py -m inputs/Map001.json inputs/Map002.json

# Directory
PYTHONPATH=. python transpiler_rpy.py -d inputs/

# Glob pattern
PYTHONPATH=. python transpiler_rpy.py -r "inputs/Map*.json"
```

### Global Install
```bash
pip install -e .
```

Then run globally:
```bash
# Single file
rpgm-transpile -f inputs/Map001.json

# Multiple files
rpgm-transpile -m inputs/Map001.json inputs/Map002.json

# Directory
rpgm-transpile -d inputs/

# Glob pattern
rpgm-transpile -r "inputs/Map*.json"
```

### CLI Options
- `-f, --file FILE` - Transpile a single file
- `-m, --multiple FILES...` - Transpile multiple files (space-separated)
- `-d, --dir DIRECTORY` - Transpile all `.json` files in a directory
- `-r, --regex PATTERN` - Transpile files matching a glob pattern
- `-o, --output OUTPUT_DIR` - Output directory for generated .rpy files (default: outputs)

Output goes to `outputs/` by default.

## Testing

There is no test framework configured. No pytest, unittest, or other test runner exists.

### Test Scripts
Test scripts are in `test_scripts/` directory:

```bash
# Dev mode (uses PYTHONPATH)
./test_scripts/test_single_file.sh
./test_scripts/test_multiple_files.sh
./test_scripts/test_folder.sh
./test_scripts/test_regex.sh

# Global mode (uses installed rpgm-transpile)
./test_scripts/test_single_file.sh --global
./test_scripts/test_multiple_files.sh --global
./test_scripts/test_folder.sh --global
./test_scripts/test_regex.sh --global
```

### Manual Verification
To verify changes manually:
1. Run the transpiler on test fixtures: `PYTHONPATH=. python transpiler_rpy.py -d inputs/`
2. Inspect generated `.rpy` files in `renpy_output/`
3. Verify Ren'Py syntax correctness manually

Test data lives in `inputs/` as `.json` map files (`Map001.json`, `Map002.json`). These are real RPG Maker MV exports, not unit tests.

## Linting / Formatting

No linter or formatter is configured (no ruff, flake8, black, mypy, etc.). If adding one, the codebase uses:
- Python 3.10+ syntax (PEP 604 union types: `int | None`, `dict[int, dict]`)
- Type hints on method signatures and class attributes
- 4-space indentation, ~100 char line limit

## Code Style

### Package Modules
- `constants.py` — `CMD` dict mapping RPG Maker command codes to readable names
- `collector.py` — `DataCollector` class scans map JSON to collect character names, switch/variable IDs, self-switches, items
- `renpy_generator.py` — `RenPyGenerator` class generates `.rpy` source from a single map's event data; also exports `safe_var()`, `safe_label()`, `clean_text()` helper functions
- `output_files.py` — file generator functions: `generate_characters_rpy()`, `generate_switches_rpy()`, `generate_game_flow_rpy()`
- `__init__.py` — `transpile_to_renpy()` orchestrator function; re-exports public API

### Naming
- Classes: PascalCase (`DataCollector`, `RenPyGenerator`)
- Functions/methods: snake_case (`collect_from_map`, `_emit_conditional_block`)
- Private methods: prefix with underscore (`_emit`, `_flush_text`)
- Module-level helpers: no underscore prefix (`safe_var`, `safe_label`, `clean_text`)
- Constants: UPPER_SNAKE_CASE in `CMD` dict
- RPG Maker IDs in variable names: `switch_id`, `map_id`, `event_id`, `self_switch_ch`

### Types
- Use `dict`, `list`, `set`, `tuple` (lowercase) for type annotations (Python 3.9+)
- Use `X | None` instead of `Optional[X]` (Python 3.10+)
- Annotate class attributes in `__init__` with inline type comments or annotations

### Imports
- Standard library only — no third-party dependencies
- Group: stdlib imports alphabetically, no blank lines between groups (single group)
- `from X import Y` preferred for specific items
- Relative imports within package: `from .constants import CMD`

### Error Handling
- Minimal error handling — uses `sys.exit(1)` for CLI usage errors
- Uses `.get()` with defaults for safe dict access on JSON data
- `None` checks on events: `if event is None: continue`
- No custom exceptions defined

### General Patterns
- Text accumulation pattern: buffer text lines, flush on command boundaries (`_flush_text()`)
- Indentation tracking: `_push()`/`_pop()` for Ren'Py indentation
- Pure functions as module-level exports: `safe_var()`, `safe_label()`, `clean_text()`
- Use `re.sub()` for regex replacements, `str.replace()` for simple substitutions
- Output generation: build `list[str]` of lines, join with `"\n"` at the end

### Formatting
- 4-space indentation
- Section dividers: `# ═══...═══` for major sections, `# ──...───` for subsections
- Docstrings on public classes and key methods (triple-quoted, imperative mood)
- Inline comments with `#` for non-obvious logic
