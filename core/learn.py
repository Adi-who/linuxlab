"""Load and display JSON command lessons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List

from core.progress import ProgressManager
from core.ui import choose, pause

COMMANDS_DIR = Path(__file__).resolve().parent.parent / "commands"
PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def load_all_commands(commands_dir: Path = COMMANDS_DIR) -> List[dict]:
    commands: List[dict] = []
    if not commands_dir.exists():
        return commands
    for json_file in sorted(commands_dir.glob("*.json")):
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            commands.extend(payload)
    return commands


def group_by_category(commands: List[dict]) -> Dict[str, List[dict]]:
    grouped: Dict[str, List[dict]] = {}
    for cmd in commands:
        grouped.setdefault(cmd.get("category", "Other"), []).append(cmd)
    return grouped


def format_lesson(cmd: dict) -> str:
    lines = [
        f"COMMAND: {cmd.get('command', '')}",
        "",
        "Meaning:",
        str(cmd.get("meaning", "")),
        "",
        "Purpose:",
        str(cmd.get("description", "")),
        "",
        "Syntax:",
        str(cmd.get("syntax", "")),
        "",
        "Example:",
    ]
    examples = cmd.get("examples") or []
    if isinstance(examples, str):
        examples = [examples]
    lines.extend(examples)
    related = cmd.get("related") or []
    if related:
        lines.append("")
        lines.append("Related commands:")
        lines.extend(related)
    tip = cmd.get("tip")
    if tip:
        lines.extend(["", "Tip:", str(tip)])
    return "\n".join(lines)


def run_learn(
    progress: ProgressManager,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    commands = load_all_commands()
    if not commands:
        print_fn("No lessons found. Check the commands/ folder.")
        return

    grouped = group_by_category(commands)
    preferred = [
        "Navigation",
        "Files & Directories",
        "File Management",
        "Permissions",
        "Processes",
        "Networking",
        "Package Management",
        "System Information",
        "Git",
    ]
    categories = [name for name in preferred if name in grouped]
    categories.extend(name for name in grouped if name not in categories)

    while True:
        print_fn("\nLEARN — choose a category:\n")
        for i, cat in enumerate(categories, start=1):
            total = len(grouped[cat])
            done = len(progress.progress.lessons_completed.get(cat, []))
            print_fn(f"{i}. {cat}  ({done}/{total})")
        print_fn(f"{len(categories) + 1}. Back to main menu")

        valid = {str(n) for n in range(1, len(categories) + 2)}
        choice = choose("\nChoose: ", valid, input_fn=input_fn, print_fn=print_fn)
        if not choice:
            return
        idx = int(choice) - 1
        if idx == len(categories):
            return

        category = categories[idx]
        for cmd in grouped[category]:
            print_fn("\n" + format_lesson(cmd))
            if progress.mark_lesson_complete(category, cmd.get("command", "")):
                leveled = progress.add_xp(5)
                print_fn("\n+5 XP for completing this lesson")
                if leveled:
                    print_fn(f"Level up! You are now level {progress.progress.level}")
                progress.save()
            pause(input_fn=input_fn)
