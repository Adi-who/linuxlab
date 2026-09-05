"""Free-play sandbox laboratory."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from core.progress import ProgressManager
from core.sandbox import Sandbox
from core.session import default_lab_files, print_result, seed_sandbox
from core.ui import box, pause

PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def run_lab(
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    print_fn("\n" + box("LAB", width=24))
    print_fn("\nA safe Linux filesystem. Nothing outside this folder can change.")
    print_fn("Try mkdir, ls, cd, touch, cp, mv, rm, cat, grep, find, chmod, echo, tree.")
    print_fn("Type 'reset' to start over, 'quit' to leave.")
    sandbox = Sandbox(sandbox_root)
    sandbox.reset()
    seed_sandbox(sandbox, default_lab_files())
    print_fn(f"\nYou are in {sandbox.virtual_cwd()}")
    print_fn(sandbox.tree().rstrip("\n"))
    commands_run = 0
    while True:
        try:
            typed = input_fn(f"\n{sandbox.virtual_cwd()}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not typed:
            continue
        lower = typed.lower()
        if lower in {"quit", "exit", "back", "done"}:
            break
        if lower == "reset":
            sandbox.reset()
            seed_sandbox(sandbox, default_lab_files())
            print_fn("Sandbox reset.")
            print_fn(sandbox.tree().rstrip("\n"))
            continue
        if lower == "tree":
            print_fn(sandbox.tree().rstrip("\n"))
            continue
        if lower == "help":
            print_fn(sandbox.run("help").output.rstrip("\n"))
            continue
        result = sandbox.run(typed)
        print_result(result, print_fn)
        if result.ok:
            commands_run += 1
    if commands_run:
        if progress.unlock_achievement("first_lab"):
            print_fn("\nAchievement unlocked: First Lab")
        leveled = progress.add_xp(min(20, commands_run * 2))
        print_fn(f"\nLab session saved. +{min(20, commands_run * 2)} XP")
        if leveled:
            print_fn(f"Level up! You are now level {progress.progress.level}")
        progress.log_event("lab", {"commands": commands_run})
        progress.save()
    pause(input_fn=input_fn)
