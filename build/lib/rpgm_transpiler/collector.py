# ═══════════════════════════════════════════════════════════════════
# COLLECTOR — extracts all characters, switches, variables
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Any

from .constants import CMD


class DataCollector:
    """
    Scans all map data first to collect:
    - Character names used in dialogue
    - Switch IDs referenced
    - Variable IDs referenced
    - Self-switch keys used
    - Item IDs referenced
    - Transfer targets (map connections)
    """

    def __init__(self):
        self.characters: dict[str, str] = {}
        self.switch_ids: set[int] = set()
        self.variable_ids: set[int] = set()
        self.self_switches: set[tuple[int, str]] = set()
        self.item_ids: set[int] = set()
        self.map_ids: set[int] = set()
        self.plugin_commands: list[str] = []
        self.map_names: dict[int, str] = {}

    def collect_from_map(self, map_data: dict[str, Any], map_id: int = 0) -> None:
        """Scan a single map's events to collect all referenced data."""
        display_name = map_data.get("display_name", f"Map{map_id}")
        self.map_names[map_id] = display_name
        self.map_ids.add(map_id)

        events = map_data.get("events", [])
        for event in events:
            if event is None:
                continue
            eid = event["id"]
            for page in event.get("pages", []):
                self._collect_conditions(page.get("conditions", {}), eid)
                self._collect_commands(page.get("list", []), eid)

    def _collect_conditions(self, cond: dict[str, Any], event_id: int) -> None:
        if cond.get("switch1Valid"):
            self.switch_ids.add(cond["switch1Id"])
        if cond.get("switch2Valid"):
            self.switch_ids.add(cond["switch2Id"])
        if cond.get("variableValid"):
            self.variable_ids.add(cond["variableId"])
        if cond.get("selfSwitchValid"):
            ch = cond.get("selfSwitchCh", "A")
            self.self_switches.add((event_id, ch))
        if cond.get("itemValid"):
            self.item_ids.add(cond["itemId"])

    def _collect_commands(self, commands: list[dict[str, Any]], event_id: int) -> None:
        for cmd in commands:
            code = cmd["code"]
            params = cmd.get("parameters", [])

            if code == CMD["SHOW_TEXT"] and len(params) >= 1:
                face = params[0]
                if face:
                    name = self._clean_character_name(face)
                    self.characters[face] = name

            elif code == CMD["CONTROL_SWITCHES"]:
                start, end = params[0], params[1]
                for sid in range(start, end + 1):
                    self.switch_ids.add(sid)

            elif code == CMD["CONTROL_VARIABLES"]:
                start, end = params[0], params[1]
                for vid in range(start, end + 1):
                    self.variable_ids.add(vid)

            elif code == CMD["CONTROL_SELF_SWITCH"]:
                ch = params[0]
                self.self_switches.add((event_id, ch))

            elif code == CMD["CONDITIONAL"]:
                ctype = params[0]
                if ctype == 0:
                    self.switch_ids.add(params[1])
                elif ctype == 1:
                    self.variable_ids.add(params[1])
                elif ctype == 2:
                    self.self_switches.add((event_id, params[1]))

            elif code == CMD["TRANSFER_PLAYER"]:
                target_map = params[1]
                self.map_ids.add(target_map)

            elif code == CMD["CHANGE_ITEMS_CMD"]:
                self.item_ids.add(params[1])

            elif code == CMD["PLUGIN_COMMAND"]:
                self.plugin_commands.append(params[0])

    @staticmethod
    def _clean_character_name(face: str) -> str:
        """Convert RPG Maker face name to display name."""
        name = face.replace("$", "").replace("!", "")
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        return name.strip()