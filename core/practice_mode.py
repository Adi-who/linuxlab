"""Guided practice tasks with expected-command validation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.practice import matches_command
from core.progress import ProgressManager
from core.ui import choose, pause

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
        _run_task(tasks[idx], progress, input_fn, print_fn)


def _run_task(
    task: dict,
    progress: ProgressManager,
    input_fn: InputFn,
    print_fn: PrintFn,
) -> None:
    print_fn("\nPRACTICE\n")
    print_fn("Current directory:")
    print_fn(task.get("cwd", "/home/user/linuxlab"))
    print_fn("\nTask:")
    print_fn(task["prompt"])
    print_fn("\nHint:")
    print_fn(task.get("hint", ""))
    print_fn("")
    attempts = 0
    while True:
        try:
            answer = input_fn("$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\nLeaving practice.")
            return
        if answer.lower() in {"quit", "exit", "back"}:
            return
        attempts += 1
        if matches_command(answer, task.get("accepted") or []):
            xp = int(task.get("xp", 10))
            first = progress.complete_practice(task["id"])
            leveled = False
            if first:
                leveled = progress.add_xp(xp)
            print_fn("\nPASS")
            print_fn("\nExpected:")
            print_fn((task.get("accepted") or [answer])[0])
            print_fn("\nYour answer:")
            print_fn(answer)
            if first:
                print_fn(f"\n+{xp} XP")
            else:
                print_fn("\nAlready completed — no extra XP")
            if leveled:
                print_fn(f"Level up! You are now level {progress.progress.level}")
            progress.log_event("practice", {"id": task["id"]})
            progress.save()
            pause(input_fn=input_fn)
            return
        print_fn("Not quite. Try again, or type 'quit'.")
        if attempts >= 2 and task.get("hint"):
            print_fn(f"Hint: {task['hint']}")
