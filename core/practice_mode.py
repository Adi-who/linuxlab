"""Guided practice that runs real sandbox commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.progress import ProgressManager
from core.sandbox import Sandbox
from core.session import print_result, seed_sandbox, tree_text
from core.ui import box, choose, pause
from core.validator import validate

PRACTICE_FILE = Path(__file__).resolve().parent.parent / "data" / "practice.json"
PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def load_practice(path: Path = PRACTICE_FILE) -> list[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def run_practice(
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    tasks = load_practice()
    if not tasks:
        print_fn("No practice tasks found.")
        return

    while True:
        print_fn("\nPRACTICE — pick a task:\n")
        for i, task in enumerate(tasks, start=1):
            done = "done" if task["id"] in progress.progress.practices_completed else "open"
            print_fn(f"{i}. {task['title']}  ({done})")
        print_fn(f"{len(tasks) + 1}. Back to main menu")
        valid = {str(n) for n in range(1, len(tasks) + 2)}
        choice = choose("\nChoose: ", valid, input_fn=input_fn, print_fn=print_fn)
        if not choice:
            return
        idx = int(choice) - 1
        if idx == len(tasks):
            return
        run_task(tasks[idx], progress, sandbox_root, input_fn, print_fn)


def run_task(
    task: dict,
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    print_fn("\n" + box("PRACTICE", width=28))
    print_fn("\nTask:")
    print_fn(task["prompt"])
    print_fn("\nThis is a real sandbox. Type Linux commands, then type 'done'.")
    print_fn("Commands: hint | tree | reset | done | quit")
    _play(task, progress, sandbox_root, input_fn, print_fn)


def _play(
    task: dict,
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn,
    print_fn: PrintFn,
) -> None:
    sandbox = Sandbox(sandbox_root)
    sandbox.reset()
    seed_sandbox(sandbox, task.get("setup") or [])
    if task.get("start"):
        try:
            sandbox.cwd = sandbox.resolve(task["start"])
        except Exception:
            sandbox.cwd = sandbox.root
    hints = [task.get("hint", "")] + list(task.get("hints") or [])
    hints = [h for h in hints if h]
    hint_index = 0
    print_fn(f"\nSandbox ready. You are in {sandbox.virtual_cwd()}")
    print_fn(tree_text(sandbox).rstrip("\n"))

    while True:
        try:
            typed = input_fn(f"\n{sandbox.virtual_cwd()}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\nLeaving practice.")
            return
        if not typed:
            continue
        lower = typed.lower()
        if lower in {"quit", "exit", "back"}:
            return
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
        if lower == "reset":
            print_fn("Resetting sandbox...")
            return _play(task, progress, sandbox_root, input_fn, print_fn)
        if lower == "done":
            result = validate(sandbox, task.get("checks") or [])
            if result.ok:
                xp = int(task.get("xp", 10))
                first = progress.complete_practice(task["id"])
                leveled = False
                if first:
                    leveled = progress.add_xp(xp)
                    print_fn("\nPASS")
                    print_fn(f"+{xp} XP")
                else:
                    print_fn("\nPASS — already completed, no extra XP")
                if leveled:
                    print_fn(f"Level up! You are now level {progress.progress.level}")
                progress.log_event("practice", {"id": task["id"]})
                progress.save()
                pause(input_fn=input_fn)
                return
            print_fn("\nNot yet:")
            for item in result.failed:
                print_fn(f"  - {item}")
            print_fn("Keep going, or type 'hint' / 'reset' / 'quit'.")
            continue
        print_result(sandbox.run(typed), print_fn)
