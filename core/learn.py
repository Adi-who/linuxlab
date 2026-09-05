"""Load and display JSON command lessons, with optional sandbox try-it."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, List

from core.progress import ProgressManager
from core.sandbox import ALLOWED_COMMANDS, Sandbox
from core.session import default_lab_files, print_result, seed_sandbox
from core.ui import choose, confirm, pause

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


def present_lesson(
    cmd: dict,
    progress: ProgressManager,
    sandbox_root: Path | None = None,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    print_fn("\n" + format_lesson(cmd))
    category = cmd.get("category", "Other")
    name = cmd.get("command", "")
    if progress.mark_lesson_complete(category, name):
        leveled = progress.add_xp(5)
        print_fn("\n+5 XP for completing this lesson")
        if leveled:
            print_fn(f"Level up! You are now level {progress.progress.level}")
        progress.save()
    first = name.split()[0] if name else ""
    if sandbox_root is not None and first in ALLOWED_COMMANDS:
        if confirm("\nTry this command in the sandbox? [Y/n] ", input_fn=input_fn):
            _try_command(cmd, sandbox_root, input_fn, print_fn)
            return
    pause(input_fn=input_fn)


def _try_command(
    cmd: dict,
    sandbox_root: Path,
    input_fn: InputFn,
    print_fn: PrintFn,
) -> None:
    sandbox = Sandbox(sandbox_root)
    sandbox.reset()
    seed_sandbox(sandbox, default_lab_files())
    example = ""
    examples = cmd.get("examples") or []
    if examples:
        example = examples[0]
    print_fn(f"\nSandbox ready at {sandbox.virtual_cwd()}")
    print_fn(sandbox.tree().rstrip("\n"))
    if example:
        print_fn(f"\nTry something like: {example}")
    print_fn("Type 'quit' when you are done.")
    while True:
        try:
            typed = input_fn(f"\n{sandbox.virtual_cwd()}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            return
        if not typed or typed.lower() in {"quit", "exit", "done", "back"}:
            return
        if typed.lower() == "tree":
            print_fn(sandbox.tree().rstrip("\n"))
            continue
        print_result(sandbox.run(typed), print_fn)


def run_learn(
    progress: ProgressManager,
    sandbox_root: Path | None = None,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
    start_command: str | None = None,
) -> None:
    commands = load_all_commands()
    if not commands:
        print_fn("No lessons found. Check the commands/ folder.")
        return

    if start_command:
        match = next((c for c in commands if c.get("command") == start_command), None)
        if match:
            present_lesson(match, progress, sandbox_root, input_fn, print_fn)
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
            present_lesson(cmd, progress, sandbox_root, input_fn, print_fn)
