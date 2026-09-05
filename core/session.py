"""Shared sandbox session helpers used by practice, lab, and challenges."""

from __future__ import annotations

from typing import Callable

from core.progress import ProgressManager
from core.sandbox import Sandbox

PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]

META_COMMANDS = {"hint", "done", "quit", "exit", "back", "skip", "reset", "tree", "help"}


def seed_sandbox(sandbox: Sandbox, files: list[dict] | None) -> None:
    for item in files or []:
        path = sandbox.resolve(item["path"])
        path.parent.mkdir(parents=True, exist_ok=True)
        if item.get("type") == "dir":
            path.mkdir(parents=True, exist_ok=True)
        else:
            path.write_text(item.get("content", ""), encoding="utf-8")


def tree_text(sandbox: Sandbox) -> str:
    return sandbox.tree()


def print_result(result, print_fn: PrintFn) -> None:
    if result.output:
        print_fn(result.output.rstrip("\n"))
    if not result.ok:
        print_fn(result.error or "Command failed.")


def run_repl(
    sandbox: Sandbox,
    input_fn: InputFn,
    print_fn: PrintFn,
    *,
    hints: list[str] | None = None,
    on_done=None,
    intro: str = "",
) -> str:
    """Interactive sandbox prompt. Returns the exit reason: done, quit, or eof."""
    hints = hints or []
    hint_index = 0
    if intro:
        print_fn(intro)
    print_fn("Type commands as you would in a real terminal.")
    print_fn("Extra: hint | tree | reset | done | quit")
    while True:
        try:
            typed = input_fn(f"\n{sandbox.virtual_cwd()}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\nLeaving the sandbox.")
            return "eof"
        if not typed:
            continue
        lower = typed.lower()
        if lower in {"quit", "exit", "back"}:
            return "quit"
        if lower == "hint":
            if hint_index < len(hints):
                print_fn(f"Hint: {hints[hint_index]}")
                hint_index += 1
            else:
                print_fn("No more hints.")
            continue
        if lower == "tree":
            print_fn(sandbox.tree().rstrip("\n"))
            continue
        if lower == "help":
            print_fn(sandbox.run("help").output.rstrip("\n"))
            continue
        if lower == "reset":
            return "reset"
        if lower == "done":
            if on_done is None:
                return "done"
            if on_done():
                return "done"
            continue
        print_result(sandbox.run(typed), print_fn)


def next_activity(progress: ProgressManager) -> dict:
    from core.learn import group_by_category, load_all_commands

    commands = load_all_commands()
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
    for category in categories:
        completed = set(progress.progress.lessons_completed.get(category, []))
        for cmd in grouped[category]:
            if cmd.get("command") not in completed:
                return {
                    "kind": "learn",
                    "category": category,
                    "command": cmd.get("command"),
                    "lesson": cmd,
                }
    from core.practice_mode import load_practice

    for task in load_practice():
        if task["id"] not in progress.progress.practices_completed:
            return {"kind": "practice", "id": task["id"], "title": task["title"]}
    from core.challenges import load_challenges

    for challenge in load_challenges():
        if challenge["id"] not in progress.progress.challenges_completed:
            return {"kind": "challenge", "id": challenge["id"], "title": challenge["title"]}
    return {"kind": "quiz"}


def default_lab_files() -> list[dict]:
    return [
        {"path": "Documents", "type": "dir"},
        {"path": "Downloads", "type": "dir"},
        {"path": "archive", "type": "dir"},
        {"path": "Documents/notes.txt", "type": "file", "content": "learn linux every day\n"},
        {"path": "README.md", "type": "file", "content": "Welcome to the LinuxLab sandbox.\n"},
        {"path": "logfile.txt", "type": "file", "content": "info started\nerror disk full\ninfo done\n"},
        {"path": "script.sh", "type": "file", "content": "#!/bin/sh\necho hello\n"},
    ]
