"""Transpilation logger with file output and statistics tracking.

Provides a centralized logger that captures all transpiler messages (info, OK,
warnings) with timestamps to a uniquely-named log file. Also tracks job
statistics (maps processed, events generated, files written, etc.) and
provides a summary report at the end of a transpilation run.

Each run produces a separate log file named ``transpile_YYYYMMDD_HHMMSS.log``
inside a ``logs/`` directory.

Usage:
    >>> logger = TranspilerLogger()
    >>> logger.info("Loaded System.json")
    [INFO] Loaded System.json
    >>> logger.ok("outputs/characters.rpy")
    [OK] outputs/characters.rpy
    >>> logger.warn("Skipping bad file")
    [WARN] Skipping bad file
    >>> logger.track_file_written()
    >>> logger.print_summary()
    >>> logger.print_errors()
"""

from __future__ import annotations

import os
from datetime import datetime


class TranspilerLogger:
    """Logger that prints to console and writes to a timestamped log file.

    Captures all messages (info, OK, warn) with timestamps into an internal
    buffer, which is flushed to a unique log file at the end of the run.
    Also tracks transpilation statistics for a final summary report.

    Attributes:
        log_dir: Directory where log files are written. Defaults to "logs".
        log_file_path: Absolute path to the generated log file, set after
            :meth:`finalize` is called.
    """

    def __init__(self, log_dir: str = "logs", verbose: str = "all") -> None:
        """Initialize the logger with a target log directory.

        Creates the log directory if it does not exist. Generates a unique
        timestamped filename for this run's log file.

        Args:
            log_dir: Directory to write log files into. Created if missing.
            verbose: Console verbosity level. ``"all"`` (default) prints
                INFO, OK, and WARN messages. ``"warn"`` prints only WARN
                messages, suppressing INFO and OK. The log file always
                receives all messages regardless of this setting.
        """
        # Store the log directory path
        self.log_dir: str = log_dir

        # Store the verbosity level ("all" or "warn")
        self.verbose: str = verbose

        # Create the log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)

        # Generate a unique timestamped log filename
        # Format: transpile_20260331_143052.log
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file_path: str = os.path.join(log_dir, f"transpile_{timestamp}.log")

        # Internal buffer of log lines (timestamped entries)
        self._log_lines: list[str] = []

        # Collected warnings and errors for end-of-run display
        self._warnings: list[str] = []

        # ── Statistics counters ──
        self._stats: dict[str, int] = {
            "maps_processed": 0,
            "events_generated": 0,
            "autorun_events": 0,
            "regular_events": 0,
            "common_events_generated": 0,
            "files_written": 0,
            "warnings": 0,
        }

    # ═══════════════════════════════════════════════════════════════════
    # Message Recording
    # ═══════════════════════════════════════════════════════════════════

    def _timestamp(self) -> str:
        """Return the current time as a formatted timestamp string.

        Returns:
            Current time in ``YYYY-MM-DD HH:MM:SS`` format.
        """
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _append_log(self, level: str, message: str) -> None:
        """Append a timestamped entry to the internal log buffer.

        Args:
            level: Log level tag (e.g., "INFO", "OK", "WARN").
            message: The message text to log.
        """
        entry = f"[{self._timestamp()}] [{level}] {message}"
        self._log_lines.append(entry)

    def info(self, message: str) -> None:
        """Print an informational message to console and log it.

        Console output is only shown when ``verbose`` is ``"all"``.
        The message is always written to the log file.

        Args:
            message: The informational message to display and record.
        """
        if self.verbose == "all":
            formatted = f"[INFO] {message}"
            print(formatted)
        self._append_log("INFO", message)

    def ok(self, message: str) -> None:
        """Print a success message to console and log it.

        Console output is only shown when ``verbose`` is ``"all"``.
        The message is always written to the log file.

        Args:
            message: The success message (typically a file path) to display
                and record.
        """
        if self.verbose == "all":
            formatted = f"[OK] {message}"
            print(formatted)
        self._append_log("OK", message)

    def warn(self, message: str) -> None:
        """Print a warning message to console, log it, and store for summary.

        Warnings are collected separately so they can be re-displayed at
        the end of the run for visibility.

        Args:
            message: The warning message to display, record, and store.
        """
        formatted = f"[WARN] {message}"
        print(formatted)
        self._append_log("WARN", message)
        self._warnings.append(message)
        self._stats["warnings"] += 1

    # ═══════════════════════════════════════════════════════════════════
    # Statistics Tracking
    # ═══════════════════════════════════════════════════════════════════

    def track_file_written(self) -> None:
        """Increment the files-written counter by one."""
        self._stats["files_written"] += 1

    def track_map(self) -> None:
        """Increment the maps-processed counter by one."""
        self._stats["maps_processed"] += 1

    def track_event(self, is_autorun: bool = False) -> None:
        """Increment the events-generated counter.

        Args:
            is_autorun: If True, also increments the autorun counter.
                Otherwise increments the regular events counter.
        """
        self._stats["events_generated"] += 1
        if is_autorun:
            self._stats["autorun_events"] += 1
        else:
            self._stats["regular_events"] += 1

    def track_common_event(self) -> None:
        """Increment the common-events-generated counter by one."""
        self._stats["common_events_generated"] += 1

    def get_stats(self) -> dict[str, int]:
        """Return a copy of the current statistics dictionary.

        Returns:
            Dictionary with keys: maps_processed, events_generated,
            autorun_events, regular_events, common_events_generated,
            files_written, warnings.
        """
        return dict(self._stats)

    # ═══════════════════════════════════════════════════════════════════
    # Summary and Error Reporting
    # ═══════════════════════════════════════════════════════════════════

    def print_summary(self) -> None:
        """Print a formatted summary table of transpilation statistics.

        Displays the count of maps processed, events generated (broken down
        by autorun and regular), common events, files written, and warnings.

        Example output::

            ═══════════════════════════════════════
            Transpilation Summary
            ═══════════════════════════════════════
            Maps processed:         3
            Events generated:       12
              Autorun:              2
              Regular:              10
            Common events:          8
            Files written:          34
            Warnings:               1
            ═══════════════════════════════════════
        """
        divider = "═" * 42
        stats = self._stats

        # Build the summary lines
        lines = [
            "",
            divider,
            "Transpilation Summary",
            divider,
            f"  Maps processed:       {stats['maps_processed']}",
            f"  Events generated:     {stats['events_generated']}",
            f"    Autorun:            {stats['autorun_events']}",
            f"    Regular:            {stats['regular_events']}",
            f"  Common events:        {stats['common_events_generated']}",
            f"  Files written:        {stats['files_written']}",
            f"  Warnings:             {stats['warnings']}",
            divider,
        ]

        summary_text = "\n".join(lines)
        print(summary_text)

        # Also log the summary to the log file
        self._append_log(
            "SUMMARY",
            f"Maps: {stats['maps_processed']}, "
            f"Events: {stats['events_generated']} "
            f"(autorun: {stats['autorun_events']}, "
            f"regular: {stats['regular_events']}), "
            f"Common events: {stats['common_events_generated']}, "
            f"Files: {stats['files_written']}, "
            f"Warnings: {stats['warnings']}",
        )

    def print_errors(self) -> None:
        """Print all collected warnings/errors at the end of the run.

        Only prints if there are warnings to display. Uses a bordered format
        for visibility.

        Example output::

            ── Errors / Warnings ──────────────────────
            Skipping invalid JSON file: inputs/bad.json (Expecting value...)
            Could not load System.json: [Errno 2] No such file or directory
            ───────────────────────────────────────────
        """
        if not self._warnings:
            return

        border = "─" * 42
        lines = [
            "",
            "─ Errors / Warnings " + "─" * 22,
        ]
        for warning in self._warnings:
            lines.append(f"  {warning}")
        lines.append(border)

        print("\n".join(lines))

    # ═══════════════════════════════════════════════════════════════════
    # Finalization
    # ═══════════════════════════════════════════════════════════════════

    def finalize(self) -> str:
        """Flush the log buffer to the log file on disk.

        Writes all accumulated timestamped log entries to the unique log file
        created for this run. Should be called once at the end of the
        transpilation pipeline.

        Returns:
            The absolute path to the written log file.
        """
        with open(self.log_file_path, "w", encoding="utf-8") as log_file:
            log_file.write("\n".join(self._log_lines) + "\n")
        return self.log_file_path
