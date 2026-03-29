# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive README.md documentation for GitHub
- MIT LICENSE file
- CHANGELOG.md for version tracking

## [0.1.0] - 2026-03-29

### Added
- `-c, --case` CLI flag with sub-options for character name casing
  - `--lower`, `--title`, `--upper` for variable names (default: title)
  - `--lower-display`, `--title-display`, `--upper-display` for display names (default: title)
  - `--lower-image`, `--title-image`, `--upper-image` for image tags (default: lower)
- `-s, --indent-width N` CLI option for configurable indentation (default: 4 spaces)
- `_self_switches` suffix to per-map self-switch store names for clarity

### Changed
- Updated AGENTS.md with complete CLI documentation
- Updated test scripts for case and indent options

## [0.1.0-alpha.3] - 2026-03-28

### Added
- Split maps and events into separate `.rpy` files with fully qualified local labels
- Ren'Py named stores for switches, variables, and self-switches
  - `game_switch` store for global switches
  - `game_vars` store for global variables
  - `map_{id}_{name}_self_switches` store per map

### Changed
- Skip interlines spacing around comment and empty lines
- Improved output file organization with events subfolders

## [0.1.0-alpha.2] - 2026-03-26

### Added
- Hierarchical folder structure for map `.rpy` files based on MapInfos.json
- `-n, --interlines` CLI option for blank line spacing control
  - Target flags: `--maps`, `--characters`, `--global-switches`, etc.
  - `--all` flag to apply interlines to all output files
- Switch/variable name concatenation with System.json identifiers
  - Switches: `switch_{id}_{name}` format
  - Variables: `var_{id}_{name}` format

### Changed
- Refactored CLI to use nested sub-flags for input and format options
- Fixed Python 3.13 docstring syntax
- Fixed map names in Ren'Py comment headers
- Updated test scripts to current CLI options

## [0.1.0-alpha.1] - 2026-03-25

### Added
- Initial implementation
- Command codes constant mapping (`CMD` dict in `constants.py`)
- `DataCollector` class for RPG Maker JSON scanning
  - Character face asset collection
  - Switch/variable ID tracking
  - Self-switch detection
  - Item and quest tracking
- `RenPyGenerator` class for Ren'Py code generation
  - Dialogue emission with text buffering
  - Choice menu handling with cancel branches
  - Conditional branch processing
  - Event page condition evaluation
- Output file generators:
  - `generate_characters_rpy()` - Character definitions with auto-colors
  - `generate_global_switches_rpy()` - Global switches store
  - `generate_global_variables_rpy()` - Global variables store
  - `generate_global_items_rpy()` - Items store
  - `generate_global_economy_rpy()` - Gold/economy store
  - `generate_global_quests_rpy()` - Quest log store
  - `generate_side_images_rpy()` - Side image declarations
  - `generate_game_flow_rpy()` - Game flow/entry point
- CLI entry point with `argparse`
  - `-i, --input` with `--file`, `--multiple`, `--directory`, `--regex`
  - `-o, --output` for custom output directory
  - `-f, --format` with `--single` (default) and `--multiline`
- Package setup with entry point (`rpgm-transpile`)
- Multi-line dialogue support with Ren'Py triple-quoted strings
- Ren'Py side image generation for character portraits
- Test scripts organized by category (input, format, output, etc.)

### Project Structure
- `rpgm_transpiler/` - Main package
  - `__init__.py` - Orchestrator and re-exports
  - `constants.py` - RPG Maker command codes
  - `collector.py` - Data collection from JSON
  - `helpers.py` - Utility functions
  - `generator.py` - Code generation
  - `characters.py` - Character output
  - `switches.py` - State management output
  - `game_flow.py` - Game flow output
  - `side_images.py` - Side image output
- `transpiler_rpy.py` - CLI entry point
- `test_scripts/` - Test shell scripts
- `inputs/` - Test JSON map files
- `outputs/` - Default output directory

---

## Version History Summary

| Version | Date | Summary |
|---------|------|---------|
| 0.1.0 | 2026-03-29 | Case options, indent width, documentation |
| 0.1.0-alpha.3 | 2026-03-28 | Named stores, split event files |
| 0.1.0-alpha.2 | 2026-03-26 | Hierarchical structure, interlines |
| 0.1.0-alpha.1 | 2026-03-25 | Initial implementation |
