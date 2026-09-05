"""
core/learn.py

Loads command lessons from the commands/ JSON files and organizes
them by category for Learn Mode.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

COMMANDS_DIR = Path(__file__).resolve().parent.parent / "commands"


def load_all_commands(commands_dir: Path = COMMANDS_DIR) -> List[dict]:
    """Loads every command lesson from every JSON file in commands_dir."""
    commands: List[dict] = []
    if not commands_dir.exists():
        return commands
    for json_file in sorted(commands_dir.glob("*.json")):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                commands.extend(json.load(f))
        except json.JSONDecodeError:
            continue
    return commands


def group_by_category(commands: List[dict]) -> Dict[str, List[dict]]:
    """Groups a flat list of command lessons by their 'category' field."""
    grouped: Dict[str, List[dict]] = {}
    for cmd in commands:
        grouped.setdefault(cmd.get("category", "Other"), []).append(cmd)
    return grouped


def format_lesson(cmd: dict) -> str:
    """Formats a single command lesson as readable terminal text."""
    lines = [
        f"🐧 COMMAND: {cmd['command']}",
        "",
        "Meaning:",
        cmd.get("meaning", ""),
        "",
        "Purpose:",
        cmd.get("description", ""),
        "",
        "Syntax:",
        cmd.get("syntax", ""),
        "",
        "Example:",
    ]
    lines.extend(cmd.get("examples", []))
    related = cmd.get("related", [])
    if related:
        lines.append("")
        lines.append("Related commands:")
        lines.extend(related)
    return "\n".join(lines)
