# ═══════════════════════════════════════════════════════════════════
# RPG Maker MV → Ren'Py Transpiler
# ═══════════════════════════════════════════════════════════════════

import json
import os
import re
from pathlib import Path

from .collector import DataCollector
from .renpy_generator import RenPyGenerator
from .output_files import (
    generate_characters_rpy,
    generate_switches_rpy,
    generate_game_flow_rpy,
)


__all__ = [
    "transpile_to_renpy",
    "DataCollector",
    "RenPyGenerator",
    "generate_characters_rpy",
    "generate_switches_rpy",
    "generate_game_flow_rpy",
]


def transpile_to_renpy(input_paths: list[str], output_dir: str = "outputs"):
    """
    Transpile one or more RPG Maker MV JSON maps to Ren'Py.

    Args:
        input_paths: List of paths to .json map files
        output_dir: Directory to write .rpy files
    """
    os.makedirs(output_dir, exist_ok=True)

    all_map_data: dict[int, dict] = {}
    collector = DataCollector()

    for path in input_paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        stem = Path(path).stem
        match = re.search(r"(\d+)", stem)
        map_id = int(match.group(1)) if match else len(all_map_data) + 1

        all_map_data[map_id] = data
        collector.collect_from_map(data, map_id)

    print(f"[INFO] Collected from {len(all_map_data)} maps:")
    print(f"       {len(collector.characters)} characters")
    print(f"       {len(collector.switch_ids)} switches")
    print(f"       {len(collector.variable_ids)} variables")
    print(f"       {len(collector.self_switches)} self-switches")
    print()

    char_code = generate_characters_rpy(collector)
    char_path = os.path.join(output_dir, "characters.rpy")
    with open(char_path, "w", encoding="utf-8") as f:
        f.write(char_code)
    print(f"[OK] {char_path}")

    switch_code = generate_switches_rpy(collector)
    switch_path = os.path.join(output_dir, "switches.rpy")
    with open(switch_path, "w", encoding="utf-8") as f:
        f.write(switch_code)
    print(f"[OK] {switch_path}")

    for map_id, map_data in sorted(all_map_data.items()):
        gen = RenPyGenerator(
            map_data, collector, map_id, all_map_data
        )
        code = gen.generate()

        name = map_data.get("display_name", f"map_{map_id}")
        safe_name = re.sub(r"[^a-z0-9_]", "_", name.lower())
        filename = f"map_{map_id}_{safe_name}.rpy"
        out_path = os.path.join(output_dir, filename)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"[OK] {out_path}")

    flow_code = generate_game_flow_rpy(all_map_data, collector)
    flow_path = os.path.join(output_dir, "game_flow.rpy")
    with open(flow_path, "w", encoding="utf-8") as f:
        f.write(flow_code)
    print(f"[OK] {flow_path}")

    print(f"\n[DONE] Transpiled {len(all_map_data)} maps to {output_dir}/")