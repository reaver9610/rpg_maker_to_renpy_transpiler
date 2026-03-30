# AGENTS.md

## Project Overview

Python transpiler that converts RPG Maker MV JSON map files into Ren'Py `.rpy` script files. Converts dialogue, choices, conditional branches, switches, variables, and map transfers.

## Project Structure

```
rpgm_transpiler/           # Package
├── __init__.py            # transpile_to_renpy() orchestrator + re-exports
├── constants.py           # CMD dict (RPG Maker command codes)
├── collector.py           # DataCollector class
├── helpers.py             # Pure utility functions (safe_var, safe_label, clean_text, side_image_tag)
├── generator.py           # RenPyGenerator class (map event → Ren'Py conversion)
├── characters.py          # generate_characters_rpy() + _get_character_color()
├── switches.py            # generate_global_*_rpy() + generate_map_switches_rpy()
├── game_flow.py           # generate_game_flow_rpy()
└── side_images.py         # generate_side_images_rpy()

transpiler_rpy.py          # CLI entry point
setup.py                   # Package setup with entry point
test_scripts/              # Test scripts for CLI options
inputs/                    # Test JSON map files
outputs/                   # Default output directory
renpy_output/              # Alternative output directory (deprecated)
```

### Output File Structure (Ren'Py Named Stores)

Event filenames include the full descriptive name derived from the RPG Maker event name
via `safe_label()`. Format: `{map_label}_{event_label}.rpy` where `event_label` is the
sanitized `event_{id}_{name}` (e.g., `event_40_under`, `event_57_auto`).

```
outputs/
  characters.rpy                                    # define claire = Character(...)
  global_switches.rpy                               # init python in game_switch:
  global_variables.rpy                              # init python in game_vars:
  global_items.rpy                                  # init python in game_items:
  global_economy.rpy                                # init python in game_economy:
  global_quests.rpy                                 # init python in game_quest:
  side_images.rpy                                   # image side claire 0 = ...
  audio.rpy                                         # define audio.bgm_X = "audio/bgm/X.ogg"
  pictures.rpy                                      # image bg picture_X = "img/pictures/X.png"
  game_flow.rpy                                     # label start: jump map_1_Checkpoint
  maps/
    map_1_Checkpoint/
      map_1_Checkpoint.rpy                              # label map_1_Checkpoint: call .event_3_intro; return
      map_1_Checkpoint_events/                          # events subfolder
        map_1_Checkpoint_event_3_intro/                 # event folder
          map_1_Checkpoint_event_3_intro.rpy            # label map_1_Checkpoint.event_3_intro: ...
          map_1_Checkpoint_event_3_intro_switches.rpy   # init python in map_1_checkpoint_self_switches:
        map_1_Checkpoint_event_2_ev002/                 # event folder (no switches)
          map_1_Checkpoint_event_2_ev002.rpy            # label map_1_Checkpoint.event_2_ev002: ...
        map_1_Checkpoint_event_4_torch/                 # event folder
          map_1_Checkpoint_event_4_torch.rpy            # label map_1_Checkpoint.event_4_torch: ...
    map_3_Refugee_Camp/
      map_3_Refugee_Camp.rpy
      map_3_Refugee_Camp_events/
        map_3_Refugee_Camp_event_57_auto/
          map_3_Refugee_Camp_event_57_auto.rpy
          map_3_Refugee_Camp_event_57_auto_switches.rpy
        map_3_Refugee_Camp_event_1_ev001/
          map_3_Refugee_Camp_event_1_ev001.rpy
```

### Local Label Convention

Events use Ren'Py **fully qualified local labels** declared in separate files:

```rpy
# Map placeholder (map_3_Refugee_Camp.rpy)
label map_3_Refugee_Camp:
    call .event_57_auto
    call .event_39_roadblock
    return

# Autorun event (map_3_Refugee_Camp_event_57_auto.rpy)
label map_3_Refugee_Camp.event_57_auto:
    Claire "Welcome!"
    return

# Regular event (map_3_Refugee_Camp_event_11_torch.rpy)
label map_3_Refugee_Camp.event_11_torch:
    return
```

- **Declaration**: `label {global_label}.{local_label}:` in the event file (e.g., `label map_3_Refugee_Camp.event_11:`)
- **Short-form call**: `call .event_X_name` within the same global label namespace
- **Cross-file call**: `call map_3_Refugee_Camp.event_11` from anywhere
- **Map label naming**: `safe_map_label(map_id, map_name)` → `map_{id}_{Title_Case_Name}`

### Empty Event Filtering

Events with no meaningful commands (only `label` + `return`) are automatically
skipped. These represent decorative RPG Maker elements (torches, glowns, etc.)
with no dialogue or gameplay logic. Approximately 36% of events are filtered.

Detection: after generating source, check for any non-comment, non-label,
non-return lines. If none found, the event file is not written.

### Store Reference Patterns

| Concept | Store | Example Reference |
|---|---|---|
| Global Switch | `game_switch` | `game_switch.switch_5_paid` |
| Global Variable | `game_vars` | `game_vars.var_2_defiance` |
| Self-Switch | `map_{id}_{name}_self_switches` | `map_3_refugee_camp_self_switches.switch_40_under_A` |
| Item | `game_items` | `game_items.item_1` |
| Gold | `game_economy` | `game_economy.gold` |
| Quest Log | `game_quest` | `game_quest.quest_log` |
| Picture Image | — | `image bg picture_Poster = "img/pictures/Poster.png"` |
| Picture Slot | — | `show bg picture_X as picture_N` / `hide picture_N onlayer pictures` |
| Map Label | — | `label map_3_Refugee_Camp:` |
| Event Local Label | — | `label map_3_Refugee_Camp.event_11:` |

## Running the Transpiler

### Development Mode (no install)
```bash
# Single file
PYTHONPATH=. python transpiler_rpy.py -i --file inputs/Map001.json

# Multiple files
PYTHONPATH=. python transpiler_rpy.py -i --multiple inputs/Map001.json inputs/Map002.json

# Directory
PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/

# Glob pattern
PYTHONPATH=. python transpiler_rpy.py -i --regex "inputs/Map*.json"

# Custom output directory
PYTHONPATH=. python transpiler_rpy.py -i --file inputs/Map001.json -o outputs/

# Multiline format
PYTHONPATH=. python transpiler_rpy.py -i --file inputs/Map001.json -f --multiline
```

### Global Install
```bash
pip install -e .
```

Then run globally:
```bash
# Single file
rpgm-transpile -i --file inputs/Map001.json

# Multiple files
rpgm-transpile -i --multiple inputs/Map001.json inputs/Map002.json

# Directory
rpgm-transpile -i --directory inputs/

# Glob pattern
rpgm-transpile -i --regex "inputs/Map*.json"

# Custom output directory
rpgm-transpile -i --file inputs/Map001.json -o outputs/

# Multiline format
rpgm-transpile -i --file inputs/Map001.json -f --multiline
```

### CLI Options
- `-i, --input` - Input source (required, use with one of the following sub-options):
  - `--file FILE` - Transpile a single file
  - `--multiple FILES...` - Transpile multiple files (space-separated)
  - `--directory DIR` - Transpile all `.json` files in a directory
  - `--regex PATTERN` - Transpile files matching a glob pattern
- `-o, --output OUTPUT_DIR` - Output directory for generated .rpy files (default: outputs)
- `-s, --indent-width N` - Number of spaces per indentation level (default: 4)
- `-n, --interlines N` - Number of blank lines between each line in output (default: 0)
  - `--maps` - Apply interlines to map files only (default when -n is used)
  - `--characters` - Apply interlines to characters.rpy
  - `--global-switches` - Apply interlines to global_switches.rpy
  - `--global-variables` - Apply interlines to global_variables.rpy
  - `--global-items` - Apply interlines to global_items.rpy
  - `--global-economy` - Apply interlines to global_economy.rpy
  - `--global-quests` - Apply interlines to global_quests.rpy
  - `--side-images` - Apply interlines to side_images.rpy
  - `--game-flow` - Apply interlines to game_flow.rpy
  - `--common-events` - Apply interlines to common event files
  - `--audio` - Apply interlines to audio.rpy
  - `--pictures` - Apply interlines to pictures.rpy
  - `--all` - Apply interlines to all output files
- `-f, --format` - Format options (use with one of the following sub-options):
  - `--single` - Emit single-line dialogue (default)
  - `--multiline` - Emit multi-line dialogue as Ren'Py triple-quoted strings
- `-c, --case` - Character case options (use with sub-options):
  - `--lower` - Lowercase variable names (e.g., `claire`)
  - `--title` - Title case variable names (e.g., `Claire`) [default]
  - `--upper` - Uppercase variable names (e.g., `CLAIRE`)
  - `--lower-display` - Lowercase display names
  - `--title-display` - Title case display names [default]
  - `--upper-display` - Uppercase display names
  - `--lower-image` - Lowercase image tags [default]
  - `--title-image` - Title case image tags
  - `--upper-image` - Uppercase image tags

Output goes to `outputs/` by default.

## Testing

There is no test framework configured. No pytest, unittest, or other test runner exists.

### Test Scripts
Test scripts are in `test_scripts/` directory, organized by category:

```bash
# Input options (test_scripts/input/)
./test_scripts/input/test_single_file.sh
./test_scripts/input/test_multiple_files.sh
./test_scripts/input/test_directory.sh
./test_scripts/input/test_regex.sh

# Interlines options (test_scripts/interlines/)
./test_scripts/interlines/test_interlines_default.sh
./test_scripts/interlines/test_interlines_targets.sh
./test_scripts/interlines/test_interlines_all.sh
./test_scripts/interlines/test_interlines_pictures.sh
./test_scripts/interlines/test_interlines_double_spacing.sh

# Format options (test_scripts/format/)
./test_scripts/format/test_multiline_format.sh

# Output options (test_scripts/output/)
./test_scripts/output/test_output_dir.sh

# Indent width options (test_scripts/indent/)
./test_scripts/indent/test_indent_width_default.sh
./test_scripts/indent/test_indent_width_custom.sh

# Case options (test_scripts/case/)
./test_scripts/case/test_case_default.sh
./test_scripts/case/test_case_lower.sh
./test_scripts/case/test_case_upper.sh
./test_scripts/case/test_case_full_lowercase.sh

# Combined options (test_scripts/combined/)
./test_scripts/combined/test_multiline_output.sh
./test_scripts/combined/test_indent_and_case.sh

# Global mode (uses installed rpgm-transpile)
./test_scripts/input/test_single_file.sh --global
./test_scripts/interlines/test_interlines_pictures.sh --global
```

#### Test Scripts Overview

| Script | Purpose |
|--------|---------|
| `test_scripts/input/test_single_file.sh` | Single file input with `-i --file` |
| `test_scripts/input/test_multiple_files.sh` | Multiple files input with `-i --multiple` |
| `test_scripts/input/test_directory.sh` | Directory input with `-i --directory` |
| `test_scripts/input/test_regex.sh` | Glob pattern input with `-i --regex` |
| `test_scripts/interlines/test_interlines_default.sh` | Test `-n 1` (defaults to maps only) |
| `test_scripts/interlines/test_interlines_targets.sh` | Test `-n 1 --characters --global-switches --pictures` |
| `test_scripts/interlines/test_interlines_all.sh` | Test `-n 1 --all` flag |
| `test_scripts/interlines/test_interlines_pictures.sh` | Test `-n 1 --pictures` for pictures.rpy |
| `test_scripts/interlines/test_interlines_double_spacing.sh` | Test `-n 2 --pictures` double spacing |
| `test_scripts/format/test_multiline_format.sh` | Test `-f --multiline` format |
| `test_scripts/output/test_output_dir.sh` | Test custom output directory `-o` |
| `test_scripts/indent/test_indent_width_default.sh` | Test default 4-space indent |
| `test_scripts/indent/test_indent_width_custom.sh` | Test custom `-s 2` indent |
| `test_scripts/case/test_case_default.sh` | Test default title case |
| `test_scripts/case/test_case_lower.sh` | Test `-c --lower` lowercase |
| `test_scripts/case/test_case_upper.sh` | Test `-c --upper` uppercase |
| `test_scripts/case/test_case_full_lowercase.sh` | Test all-lowercase mode |
| `test_scripts/combined/test_multiline_output.sh` | Test multiline + custom output + interlines |
| `test_scripts/combined/test_indent_and_case.sh` | Test indent + case combination |
| `test_scripts/indent/test_indent_width_default.sh` | Test default indent width (4 spaces) |
| `test_scripts/indent/test_indent_width_custom.sh` | Test `-s 2` custom indent width |
| `test_scripts/case/test_case_default.sh` | Test default case (title var/display, lower image) |
| `test_scripts/case/test_case_lower.sh` | Test `-c --lower` for lowercase variable names |
| `test_scripts/case/test_case_upper.sh` | Test `-c --upper` for uppercase variable names |
| `test_scripts/case/test_case_full_lowercase.sh` | Test `-c --lower --lower-display --lower-image` |
| `test_scripts/combined/test_multiline_output.sh` | Test combined options: multiline + custom output + interlines |
| `test_scripts/combined/test_indent_and_case.sh` | Test combined `-s 2 -c --lower` options |

### Manual Verification
To verify changes manually:
1. Run the transpiler on test fixtures: `PYTHONPATH=. python transpiler_rpy.py -i --directory inputs/`
2. Inspect generated `.rpy` files in `outputs/`
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
- `helpers.py` — Pure utility functions: `safe_var()`, `safe_label()`, `safe_map_label()`, `clean_text()`, `clean_text_preserve_lines()`, `side_image_tag()`
- `generator.py` — `RenPyGenerator` class + `MapGenerationResult` dataclass; generates split `.rpy` source from a single map's event data
- `characters.py` — `generate_characters_rpy()` + `_get_character_color()` helper
- `switches.py` — `generate_global_switches_rpy()`, `generate_global_variables_rpy()`, `generate_global_items_rpy()`, `generate_global_economy_rpy()`, `generate_global_quests_rpy()`, `generate_map_switches_rpy()`
- `game_flow.py` — `generate_game_flow_rpy()`
- `side_images.py` — `generate_side_images_rpy()`
- `__init__.py` — `transpile_to_renpy()` orchestrator function; re-exports public API

### Naming
- Classes: PascalCase (`DataCollector`, `RenPyGenerator`)
- Functions/methods: snake_case (`collect_from_map`, `_emit_conditional_block`)
- Private methods: prefix with underscore (`_emit`, `_flush_text`)
- Module-level helpers: no underscore prefix (`safe_var`, `safe_label`, `safe_map_label`, `clean_text`)
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
- Pure functions as module-level exports: `safe_var()`, `safe_label()`, `safe_map_label()`, `clean_text()`
- Use `re.sub()` for regex replacements, `str.replace()` for simple substitutions
- Output generation: build `list[str]` of lines, join with `"\n"` at the end
- Split file output: one `.rpy` per map (placeholder), per event (autorun + regular)
- Events subfolder: `{map_label_name}_events/` holds all event `.rpy` files
- Empty event filtering: events with only `label` + `return` are skipped (decorative elements)
- Local labels: fully qualified form `label map_{id}_{Name}.event_{id}_{name}:` in event files
- Short-form calls: `call .event_{id}_{name}` within the same global label namespace
- Map label naming: `safe_map_label()` → `map_{id}_{Title_Case_Name}` (consistent across files)
- `MapGenerationResult`: dataclass returned by `generate()` with `map_label`, `autorun` dict, `events` dict

### Formatting
- 4-space indentation
- Section dividers: `# ═══...═══` for major sections, `# ──...───` for subsections
- Docstrings on public classes and key methods (triple-quoted, imperative mood)
- Inline comments with `#` for non-obvious logic

### Documentation
- Always document with detail every python function
- Always document with detail every python statment (every line of code)

### Consideration
- Give me an descriptive git commit summary and description for every change or changes made in project after any modification in source code are made
