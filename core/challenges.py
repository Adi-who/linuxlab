"""Challenge missions that run inside the LinuxLab sandbox."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable

from core.progress import ProgressManager
from core.sandbox import Sandbox
from core.session import print_result, seed_sandbox
from core.ui import box, choose, confirm, pause
from core.validator import validate

CHALLENGES_DIR = Path(__file__).resolve().parent.parent / "challenges"
PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def load_challenges(folder: Path = CHALLENGES_DIR) -> list[dict]:
    challenges: list[dict] = []
    if not folder.exists():
        return challenges
    for json_file in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(json_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, list):
            challenges.extend(payload)
    return challenges


def _seed(sandbox: Sandbox, files: list[dict]) -> None:
    seed_sandbox(sandbox, files)


def play_challenge(
    challenge: dict,
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    _play_challenge(challenge, progress, sandbox_root, input_fn, print_fn)


def run_challenges(
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
) -> None:
    challenges = load_challenges()
    if not challenges:
        print_fn("No challenges found. Check the challenges/ folder.")
        return

    while True:
        print_fn("\nCHALLENGES\n")
        for i, challenge in enumerate(challenges, start=1):
            done = "done" if challenge["id"] in progress.progress.challenges_completed else "open"
            print_fn(
                f"{i}. [{challenge.get('difficulty', 'beginner')}] "
                f"{challenge['title']}  ({done})"
            )
        print_fn(f"{len(challenges) + 1}. Back to main menu")
        valid = {str(n) for n in range(1, len(challenges) + 2)}
        choice = choose("\nChoose: ", valid, input_fn=input_fn, print_fn=print_fn)
        if not choice:
            return
        idx = int(choice) - 1
        if idx == len(challenges):
            return
        _play_challenge(challenges[idx], progress, sandbox_root, input_fn, print_fn)


def _play_challenge(
    challenge: dict,
    progress: ProgressManager,
    sandbox_root: Path,
    input_fn: InputFn,
    print_fn: PrintFn,
) -> None:
    print_fn("\n" + box(f"LEVEL — {challenge['title'].upper()}", width=36))
    print_fn("\nMission:\n")
    print_fn(challenge["mission"])
    if challenge.get("tree"):
        print_fn("")
        print_fn(challenge["tree"])
    print_fn("\nRules:")
    print_fn("  - Use Linux commands inside the sandbox")
    print_fn("  - Type 'hint' for a hint, 'done' to submit, 'quit' to leave")
    print_fn("  - Nothing outside the sandbox can be changed")
    if not confirm("\nStart Mission? [Y/n] ", input_fn=input_fn):
        return

    sandbox = Sandbox(sandbox_root)
    sandbox.reset()
    _seed(sandbox, challenge.get("setup") or [])
    progress.progress.challenges_attempted += 1
    progress.save()

    hints = challenge.get("hints") or []
    hint_index = 0
    print_fn(f"\nSandbox ready. You are in {sandbox.virtual_cwd()}")
    print_fn("Allowed commands: pwd ls cd mkdir rmdir touch cp mv rm cat head tail grep find chmod echo tree help")
    print_fn("Type real Linux commands. Then type 'done' to validate.")

    while True:
        try:
            typed = input_fn(f"\n{sandbox.virtual_cwd()}$ ").strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("\nLeaving mission.")
            return
        if not typed:
            continue
        lower = typed.lower()
        if lower in {"quit", "exit"}:
            print_fn("Mission aborted.")
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
            sandbox.reset()
            _seed(sandbox, challenge.get("setup") or [])
            print_fn("Sandbox reset.")
            continue
        if lower == "done":
            result = validate(sandbox, challenge.get("checks") or [])
            if result.ok:
                xp = int(challenge.get("xp", 40))
                first = progress.complete_challenge(challenge["id"])
                leveled = False
                if first:
                    leveled = progress.add_xp(xp)
                    progress.unlock_achievement("first_challenge")
                    print_fn("\nPASS")
                    print_fn(f"+{xp} XP")
                else:
                    print_fn("\nPASS — already completed, no extra XP")
                if leveled:
                    print_fn(f"Level up! You are now level {progress.progress.level}")
                progress.log_event("challenge", {"id": challenge["id"], "ok": True})
                progress.save()
            else:
                print_fn("\nNot yet. The sandbox is missing:")
                for item in result.failed:
                    print_fn(f"  - {item}")
                print_fn("Keep going, or type 'quit'.")
            if result.ok:
                pause(input_fn=input_fn)
                return
            continue

        print_result(sandbox.run(typed), print_fn)
