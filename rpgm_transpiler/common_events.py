"""Generates Ren'Py .rpy files for RPG Maker MV common events.

Common events are global scripts shared across all maps. Unlike map events,
they have a flat command list (no per-page structure) and use a `switchId`
field to gate execution. Each common event is split into its own file under
the ``common_events/`` output folder.

Architecture:
The CommonEventGenerator subclasses RenPyGenerator to reuse the full command
dispatch pipeline (dialogue, choices, conditionals, switch/variable control,
etc.). It overrides only the event file generation to handle the flat command
list structure and custom header format.

Trigger Types:
- 0 = Action Button (called manually from events)
- 1 = Autorun (runs automatically, switch-gated)
- 2 = Parallel (runs concurrently)

Switch Gating:
When switchId > 0, the event body is wrapped in an ``if`` check on
``game_switch.switch_{id}``, matching RPG Maker's behavior where the
common event only executes when that switch is ON.

Output Structure:
Each common event produces a subfolder with one .rpy file::

    outputs/common_events/
        common_event_1_quest_log/
            common_event_1_quest_log.rpy
        common_event_2_cheats/
            common_event_2_cheats.rpy
"""

from __future__ import annotations

from typing import Any

from .collector import DataCollector
from .generator import RenPyGenerator
from .helpers import (
    safe_label, join_with_interlines,
)


# ── Trigger type lookup table ──
# Maps numeric trigger codes to human-readable descriptions
# Used in file header comments for documentation
TRIGGER_NAMES: dict[int, str] = {
    0: "Action Button",
    1: "Autorun",
    2: "Parallel",
}


class CommonEventGenerator(RenPyGenerator):
    """Generates Ren'Py source for common events.

    Subclasses RenPyGenerator to reuse the full command dispatch pipeline
    while adapting to the flat command list structure of common events.
    """

    def generate_common_event(
        self,
        event: dict[str, Any],
    ) -> tuple[str, str] | None:
        """Generate a single .rpy file for one common event.

        Creates a label and emits the event's flat command list.
        Returns None if the event has no meaningful content.

        Args:
            event: Parsed common event dict with keys: id, list, name,
                switchId, trigger.

        Returns:
            Two-tuple of (source, label) or None if empty.
            ``source`` is the complete .rpy file content.
            ``label`` is the safe label string (e.g., ``"event_2_cheats"``).
            Returns None when the event contains no meaningful commands.
        """
        # ═══ PROACTIVE FILTERING: Check for meaningful content BEFORE generation ═══
        command_list = event.get("list", [])
        if not self._is_meaningful_command_list(command_list):
            return None
        
        event_id = event["id"]
        event_name = event.get("name", "")
        label = safe_label(event_name, event_id)

        # Save generator state
        saved_lines = self.lines
        saved_indent = self.indent_level
        saved_text_buffer = self._text_buffer
        saved_speaker = self._current_speaker
        saved_face = self._current_face
        saved_face_id = self._current_face_id

        # Create fresh buffer for this file
        self.lines = []
        self.indent_level = 0
        self._text_buffer = []
        self._current_speaker = None
        self._current_face = None
        self._current_face_id = None

        # Emit custom header for common events
        self._emit_common_event_header(event)

        # Emit comment and label
        display_name = event_name if event_name else f"EV{event_id:03d}"
        self._emit(f'# ── Common Event {event_id}: "{display_name}" ──')
        self._emit()
        self._emit(f"label {label}:")
        self._push()

        # Process commands into a body buffer at current indent level
        # This lets us check for empty content before emitting if gates
        saved_lines = self.lines
        saved_indent = self.indent_level
        self.lines = []
        self.indent_level = saved_indent
        self._flush_text()
        self._emit_command_list(command_list, event_id)
        self._flush_text()
        body_lines = self.lines
        self.lines = saved_lines
        self.indent_level = saved_indent

        # Check if the body has any meaningful content
        has_content = any(line.strip() for line in body_lines)

        switch_id = event.get("switchId", 0)
        if switch_id > 0 and has_content:
            # Wrap body in an if gate for the switch condition
            variable_name = self.collector.get_switch_store_name(switch_id)
            self._emit(f"if {variable_name}:")
            self._push()
            # Re-indent body lines one level deeper to be inside the if block
            extra_indent = " " * (self.indent_level * self.indent_width - saved_indent * self.indent_width)
            for body_line in body_lines:
                if body_line.strip():
                    self.lines.append(extra_indent + body_line)
                else:
                    self.lines.append(body_line)
            self._pop()
        elif has_content:
            # No switch gate, emit body directly at current indent level
            for body_line in body_lines:
                self.lines.append(body_line)
        # else: empty body, nothing to emit between label and return

        self._emit("return")
        self._pop()
        self._emit()

        # Join lines and apply interlines
        source = join_with_interlines(self.lines, self.interlines)

        # Restore state
        self.lines = saved_lines
        self.indent_level = saved_indent
        self._text_buffer = saved_text_buffer
        self._current_speaker = saved_speaker
        self._current_face = saved_face
        self._current_face_id = saved_face_id

        # Detect empty events (only header, comment, label, return)
        if self._is_empty_event_source(source):
            return None

        return source, label

    def _emit_common_event_header(self, event: dict[str, Any]) -> None:
        """Write the decorative header for a common event file.

        Includes event ID, name, trigger type, and switch gate information.

        Args:
            event: Parsed common event dict.
        """
        event_id = event["id"]
        event_name = event.get("name", "")
        trigger = event.get("trigger", 0)
        switch_id = event.get("switchId", 0)

        display_name = event_name if event_name else f"(unnamed)"

        trigger_name = TRIGGER_NAMES.get(trigger, f"Unknown ({trigger})")

        self._emit("# ═══════════════════════════════════════════════════")
        self._emit(f"# Common Event {event_id}: \"{display_name}\"")
        self._emit(f"# Trigger: {trigger_name}")
        if switch_id > 0:
            switch_name = self.collector.get_switch_name(switch_id)
            self._emit(f"# Switch Gate: game_switch.{switch_name}")
        self._emit("# Auto-generated from RPG Maker MV")
        self._emit("# ═══════════════════════════════════════════════════")
        self._emit()


def generate_common_events_rpy(
    common_events_data: list[Any],
    collector: DataCollector,
    multiline: bool = False,
    interlines: int = 0,
    indent_width: int = 4,
) -> dict[int, tuple[str, str]]:
    """Generate Ren'Py source files for all common events.

    Iterates over the sparse CommonEvents.json array and produces one
    .rpy file per non-null event. Empty events (no meaningful commands)
    are automatically skipped.

    Args:
        common_events_data: Parsed JSON array from CommonEvents.json.
            Sparse array where index 0 is null, other indices contain
            event dicts with keys: id, list, name, switchId, trigger.
        collector: Shared DataCollector with character/switch/variable metadata.
            Must have already called collect_from_common_events() to populate.
        multiline: If True, emit multi-line dialogue as Ren'Py triple-quoted strings.
        interlines: Number of blank lines to insert between each output line.
        indent_width: Number of spaces per indentation level.

    Returns:
        Dict mapping event_id → (source, label) for each non-empty event.
        ``source`` is the complete .rpy file content.
        ``label`` is the safe label string (e.g., ``"event_2_cheats"``).

    Example:
        >>> collector = DataCollector()
        >>> collector.collect_from_common_events(common_data)
        >>> result = generate_common_events_rpy(common_data, collector)
        >>> for event_id, (source, label) in sorted(result.items()):
        ...     print(f"Event {event_id}: {label} ({len(source)} chars)")
    """
    # Create a minimal generator instance for command processing
    # Common events don't use map_data, map_id, or all_map_data
    # but RenPyGenerator requires them for __init__
    generator = CommonEventGenerator(
        map_data={"events": []},
        collector=collector,
        map_id=0,
        all_map_data={},
        multiline=multiline,
        interlines=interlines,
        map_name="Common Events",
        indent_width=indent_width,
    )

    result: dict[int, tuple[str, str]] = {}

    for event in common_events_data:
        # Skip null entries (sparse array slots)
        if event is None:
            continue

        # Generate the .rpy source for this event
        event_result = generator.generate_common_event(event)

        # Skip empty events (no meaningful content)
        if event_result is not None:
            source, label = event_result
            result[event["id"]] = (source, label)

    return result
