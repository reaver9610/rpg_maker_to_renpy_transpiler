# ═══════════════════════════════════════════════════════════════════
# REN'PY CODE GENERATOR
# ═══════════════════════════════════════════════════════════════════

from __future__ import annotations

import re
from typing import Any

from .constants import CMD
from .collector import DataCollector


def safe_var(name: str) -> str:
    """Convert character name to a safe Python variable name."""
    clean = name.replace(" ", "_").replace("-", "_")
    clean = "".join(c for c in clean if c.isalnum() or c == "_")
    return clean


def safe_label(name: str, eid: int) -> str:
    """Convert event name to a valid Ren'Py label."""
    clean = name.strip().replace(" ", "_").replace("-", "_")
    clean = "".join(c for c in clean if c.isalnum() or c == "_")
    if not clean or (not clean[0].isalpha() and clean[0] != "_"):
        clean = f"ev{clean}"
    return f"event_{eid}_{clean}".lower()


def clean_text(text: str) -> str:
    """Remove RPG Maker escape codes from text."""
    text = re.sub(r"\\c$$\d+$$", "", text)
    text = text.replace("\\n", " ")
    text = text.strip()
    text = text.replace('"', '\\"')
    return text


class RenPyGenerator:
    """Generates Ren'Py .rpy source files from RPG Maker MV map data."""

    def __init__(self, map_data: dict, collector: DataCollector,
                 map_id: int = 0, all_map_data: dict[int, dict] | None = None):
        self.map_data = map_data
        self.collector = collector
        self.map_id = map_id
        self.all_map_data = all_map_data or {}
        self.lines: list[str] = []
        self.indent_level = 0
        self._text_buffer: list[str] = []
        self._current_speaker: str | None = None
        self._current_face: str | None = None

    def _indent(self) -> str:
        return "    " * self.indent_level

    def _emit(self, line: str = "") -> None:
        if line:
            self.lines.append(self._indent() + line)
        else:
            self.lines.append("")

    def _push(self) -> None:
        self.indent_level += 1

    def _pop(self) -> None:
        self.indent_level = max(0, self.indent_level - 1)

    def generate(self) -> str:
        self._emit_header()
        self._emit_events()
        return "\n".join(self.lines)

    def _emit_header(self) -> None:
        name = self.map_data.get("display_name", "Unknown")
        self._emit(f"# ═══════════════════════════════════════════════════")
        self._emit(f"# {name} (Map ID: {self.map_id})")
        self._emit(f"# Auto-generated from RPG Maker MV")
        self._emit(f"# ═══════════════════════════════════════════════════")
        self._emit()

    def _emit_events(self) -> None:
        events = self.map_data.get("events", [])
        if not events:
            self._emit("# No events on this map.")
            return

        autorun = []
        regular = []

        for event in events:
            if event is None:
                continue
            pages = event.get("pages", [])
            if pages and pages[0].get("trigger") == 3:
                autorun.append(event)
            else:
                regular.append(event)

        if autorun:
            self._emit("# ── Autorun sequence ──")
            self._emit(f"label map_{self.map_id}_enter:")
            self._push()
            for event in autorun:
                self._emit_event(event)
            self._emit("return")
            self._pop()
            self._emit()

        for event in regular:
            self._emit_event(event)

    def _emit_event(self, event: dict[str, Any]) -> None:
        eid = event["id"]
        ename = event.get("name", f"EV{eid:03d}")
        label = safe_label(ename, eid)
        pages = event.get("pages", [])

        self._emit(f"# ── Event {eid}: \"{ename}\" (pos {event['x']},{event['y']}) ──")
        self._emit()

        if len(pages) == 1:
            self._emit(f"label {label}:")
            self._push()
            self._emit_page(pages[0], eid)
            self._emit("return")
            self._pop()
        else:
            self._emit(f"label {label}:")
            self._push()
            self._emit_multi_page(pages, eid)
            self._emit("return")
            self._pop()

        self._emit()

    def _emit_multi_page(self, pages: list[dict[str, Any]], event_id: int) -> None:
        for i, page in enumerate(reversed(pages)):
            real_idx = len(pages) - 1 - i
            cond = page.get("conditions", {})
            checks = self._build_renpy_condition(cond, event_id)

            keyword = "if" if i == 0 else "elif"
            if checks:
                self._emit(f"{keyword} {checks}:")
            else:
                if i == 0:
                    self._emit(f"{keyword} True:")
                else:
                    self._emit(f"elif True:  # page {real_idx} fallback")

            self._push()
            self._emit_comment(f"Page {real_idx}")
            self._emit_page(page, event_id)
            self._pop()

    def _emit_page(self, page: dict[str, Any], event_id: int) -> None:
        cmd_list = page.get("list", [])
        self._flush_text()
        self._emit_command_list(cmd_list, event_id)
        self._flush_text()

    def _emit_command_list(self, commands: list[dict[str, Any]], event_id: int) -> None:
        i = 0
        while i < len(commands):
            cmd = commands[i]
            code = cmd["code"]
            params = cmd.get("parameters", [])

            if code == CMD["END"]:
                break

            elif code == CMD["SHOW_TEXT"]:
                self._flush_text()
                face = params[0] if len(params) > 0 else ""
                if face:
                    self._current_speaker = self.collector.characters.get(face, face)
                    self._current_face = face
                else:
                    self._current_speaker = None
                    self._current_face = None

            elif code == CMD["TEXT_LINE"]:
                text = params[0] if params else ""
                text = clean_text(text)
                self._text_buffer.append(text)

            elif code == CMD["SHOW_CHOICES"]:
                self._flush_text()
                choices = params[0] if params else []
                cancel_type = params[3] if len(params) > 3 else 0
                i = self._emit_choice_block(commands, i, choices, cancel_type, event_id)

            elif code == CMD["CONDITIONAL"]:
                self._flush_text()
                i = self._emit_conditional_block(commands, i, event_id)

            elif code == CMD["CONTROL_SWITCHES"]:
                self._flush_text()
                start, end, value = params[0], params[1], params[2]
                val = "True" if value == 0 else "False"
                for sid in range(start, end + 1):
                    self._emit(f"$ switch_{sid} = {val}")

            elif code == CMD["CONTROL_VARIABLES"]:
                self._flush_text()
                start, end = params[0], params[1]
                op = params[2]
                operand = params[3]
                ops = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
                op_sym = ops.get(op, "=")
                for vid in range(start, end + 1):
                    if op == 0:
                        self._emit(f"$ var_{vid} = {operand}")
                    else:
                        self._emit(f"$ var_{vid} {op_sym} {operand}")

            elif code == CMD["CONTROL_SELF_SWITCH"]:
                self._flush_text()
                ch = params[0]
                val = "True" if params[1] == 0 else "False"
                self._emit(f"$ selfswitch_{event_id}_{ch} = {val}")

            elif code == CMD["CHANGE_GOLD"]:
                self._flush_text()
                amount = params[2] if len(params) > 2 else 0
                if params[0] == 0:
                    self._emit(f"$ gold += {amount}")
                else:
                    self._emit(f"$ gold -= {amount}")

            elif code == CMD["WAIT"]:
                self._flush_text()
                frames = params[0]
                seconds = round(frames / 60.0, 2)
                self._emit(f"pause {seconds}")

            elif code == CMD["PLAY_SE"]:
                self._flush_text()
                se = params[0] if params else {}
                name = se.get("name", "")
                if name:
                    self._emit(f'play sound "{name}.ogg"')

            elif code == CMD["TRANSFER_PLAYER"]:
                self._flush_text()
                target_map = params[1]
                x, y = params[2], params[3]
                target_name = self.collector.map_names.get(target_map, f"map_{target_map}")
                self._emit(f'# Transfer to {target_name} ({x}, {y})')
                self._emit(f"jump map_{target_map}_enter")

            elif code == CMD["PLUGIN_COMMAND"]:
                self._flush_text()
                cmd_str = params[0] if params else ""
                self._emit_plugin_command(cmd_str)

            elif code == CMD["SCRIPT"]:
                self._flush_text()
                script = params[0] if params else ""
                self._emit(f"# [Script] {script}")

            elif code in (CMD["MOVE_ROUTE"], CMD["MOVE_PARAM"]):
                pass

            else:
                self._flush_text()
                self._emit(f"# [TODO: code={code}] params={params}")

            i += 1

    def _emit_choice_block(self, commands: list, start_idx: int,
                           choices: list[str], cancel_type: int,
                           event_id: int) -> int:
        self._emit("menu:")
        self._push()

        i = start_idx + 1
        choice_results: dict[int, list] = {}
        cancel_commands: list = []
        current_choice: int | None = None
        collected: list = []
        collecting = False

        while i < len(commands):
            cmd = commands[i]
            code = cmd["code"]

            if code == CMD["WHEN_CHOICE"]:
                if current_choice is not None:
                    choice_results[current_choice] = collected
                current_choice = cmd["parameters"][0]
                collected = []
                collecting = True

            elif code == CMD["WHEN_CANCEL"]:
                if current_choice is not None:
                    choice_results[current_choice] = collected
                current_choice = None
                collected = cancel_commands
                collecting = True

            elif code == CMD["END_CHOICES"]:
                if current_choice is not None:
                    choice_results[current_choice] = collected
                i += 1
                break

            elif code == CMD["END"]:
                break

            else:
                if collecting:
                    collected.append(cmd)

            i += 1

        for idx, choice_text in enumerate(choices):
            clean = clean_text(choice_text)
            self._emit(f'"{clean}":')
            self._push()
            cmds = choice_results.get(idx, [])
            self._emit_command_list(cmds, event_id)
            self._flush_text()
            self._pop()

        if cancel_type == 2 and cancel_commands:
            self._emit(f'"(Cancel)":')
            self._push()
            self._emit_command_list(cancel_commands, event_id)
            self._flush_text()
            self._pop()

        self._pop()
        return i

    def _emit_conditional_block(self, commands: list, start_idx: int,
                                event_id: int) -> int:
        cmd = commands[start_idx]
        params = cmd.get("parameters", [])
        condition = self._parse_condition_expr(params, event_id)

        self._emit(f"if {condition}:")
        self._push()

        i = start_idx + 1
        depth = 1

        while i < len(commands):
            sub = commands[i]
            sub_code = sub["code"]
            sub_indent = sub.get("indent", 0)

            if sub_code == CMD["ELSE"] and sub_indent < depth:
                self._flush_text()
                self._pop()
                self._emit("else:")
                self._push()

            elif sub_code == CMD["END_CONDITIONAL"] and sub_indent < depth:
                self._flush_text()
                self._pop()
                i += 1
                break

            elif sub_code == CMD["CONDITIONAL"]:
                self._flush_text()
                i = self._emit_conditional_block(commands, i, event_id)
                continue

            elif sub_code == CMD["END"]:
                self._flush_text()
                self._pop()
                break

            else:
                self._emit_single_command(sub, event_id)

            i += 1

        return i

    def _emit_single_command(self, cmd: dict, event_id: int):
        code = cmd["code"]
        params = cmd.get("parameters", [])

        if code == CMD["CONTROL_SWITCHES"]:
            start, end, value = params[0], params[1], params[2]
            val = "True" if value == 0 else "False"
            for sid in range(start, end + 1):
                self._emit(f"$ switch_{sid} = {val}")

        elif code == CMD["CONTROL_VARIABLES"]:
            start, end = params[0], params[1]
            op = params[2]
            operand = params[3]
            ops = {0: "=", 1: "+=", 2: "-=", 3: "*=", 4: "//=", 5: "%="}
            for vid in range(start, end + 1):
                if op == 0:
                    self._emit(f"$ var_{vid} = {operand}")
                else:
                    self._emit(f"$ var_{vid} {ops.get(op, '=')} {operand}")

        elif code == CMD["CONTROL_SELF_SWITCH"]:
            ch = params[0]
            val = "True" if params[1] == 0 else "False"
            self._emit(f"$ selfswitch_{event_id}_{ch} = {val}")

        elif code == CMD["CHANGE_GOLD"]:
            amount = params[2] if len(params) > 2 else 0
            if params[0] == 0:
                self._emit(f"$ gold += {amount}")
            else:
                self._emit(f"$ gold -= {amount}")

        elif code == CMD["PLUGIN_COMMAND"]:
            cmd_str = params[0] if params else ""
            self._emit_plugin_command(cmd_str)

        elif code == CMD["WAIT"]:
            frames = params[0]
            seconds = round(frames / 60.0, 2)
            self._emit(f"pause {seconds}")

        elif code == CMD["PLAY_SE"]:
            se = params[0] if params else {}
            name = se.get("name", "")
            if name:
                self._emit(f'play sound "{name}.ogg"')

        elif code == CMD["TRANSFER_PLAYER"]:
            target_map = params[1]
            self._emit(f"jump map_{target_map}_enter")

    def _build_renpy_condition(self, cond: dict, event_id: int) -> str:
        checks = []

        if cond.get("switch1Valid"):
            sid = cond["switch1Id"]
            checks.append(f"switch_{sid}")

        if cond.get("switch2Valid"):
            sid = cond["switch2Id"]
            checks.append(f"switch_{sid}")

        if cond.get("variableValid"):
            vid = cond["variableId"]
            val = cond["variableValue"]
            checks.append(f"var_{vid} >= {val}")

        if cond.get("selfSwitchValid"):
            ch = cond.get("selfSwitchCh", "A")
            checks.append(f"selfswitch_{event_id}_{ch}")

        if cond.get("itemValid"):
            iid = cond["itemId"]
            checks.append(f"item_{iid} > 0")

        return " and ".join(checks) if checks else ""

    def _parse_condition_expr(self, params: list, event_id: int) -> str:
        ctype = params[0]

        if ctype == 0:
            sid = params[1]
            val = params[2]
            if val == 0:
                return f"switch_{sid}"
            else:
                return f"not switch_{sid}"

        elif ctype == 1:
            vid = params[1]
            comparison = params[2]
            value = params[3]
            ops = {0: "==", 1: ">=", 2: "<=", 3: ">", 4: "<", 5: "!="}
            op_sym = ops.get(comparison, "==")
            return f"var_{vid} {op_sym} {value}"

        elif ctype == 2:
            ch = params[1]
            val = params[2]
            if val == 0:
                return f"selfswitch_{event_id}_{ch}"
            else:
                return f"not selfswitch_{event_id}_{ch}"

        elif ctype == 7:
            comparison = params[1]
            amount = params[2]
            ops = {0: ">=", 1: "<=", 2: "<", 3: ">", 4: "==", 5: "!="}
            op_sym = ops.get(comparison, ">=")
            return f"gold {op_sym} {amount}"

        elif ctype == 6:
            return params[1] if len(params) > 1 else "True"

        else:
            return "True"

    def _emit_plugin_command(self, cmd_str: str):
        if not cmd_str:
            return

        if cmd_str.startswith("Quest"):
            self._emit(f'$ quest_log.append("{cmd_str}")')
            self._emit(f'"{cmd_str}"')
        else:
            self._emit(f'# [Plugin] {cmd_str}')

    def _flush_text(self):
        if not self._text_buffer:
            return

        full_text = " ".join(self._text_buffer)
        self._text_buffer = []

        if not full_text.strip():
            return

        if self._current_speaker:
            speaker_var = safe_var(self._current_speaker)
            self._emit(f'{speaker_var} "{full_text}"')
        else:
            self._emit(f'"{full_text}"')

    def _emit_comment(self, text: str):
        self._emit(f"# {text}")