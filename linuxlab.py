#!/usr/bin/env python3
"""LinuxLab — Interactive Linux Learning Environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.challenges import load_challenges, play_challenge, run_challenges
from core.lab import run_lab
from core.learn import present_lesson, run_learn
from core.practice_mode import load_practice, run_practice, run_task
from core.progress import ProgressManager
from core.quiz import run_quiz
from core.session import next_activity
from core.ui import banner, box, choose, pause

VERSION = "1.0"
SANDBOX_DIR = Path.home() / "linuxlab-sandbox"

MAIN_MENU = """
1. Continue
2. Learn
3. Practice
4. Challenges
5. Lab
6. Quiz
7. Progress
8. Exit
"""


def progress_mode(manager: ProgressManager) -> None:
    from core.learn import group_by_category, load_all_commands

    p = manager.progress
    print(box("YOUR PROGRESS", width=32))
    print()
    print(f"Level: {p.level}")
    print(
        f"XP: {p.xp_into_level} / {p.xp_for_next_level}  "
        f"[{manager.bar(p.xp_into_level, p.xp_for_next_level, width=20)}]"
    )
    print(f"Total XP: {p.xp}")
    print()

    grouped = group_by_category(load_all_commands())
    for category, lessons in grouped.items():
        done = len(p.lessons_completed.get(category, []))
        total = len(lessons)
        print(
            f"{category:<22} {manager.bar(done, total, width=10)}  "
            f"{manager.category_percent(category, total)}%"
        )

    challenges = load_challenges()
    print()
    print(f"Challenges: {len(challenges)}")
    print(f"Completed:  {len(p.challenges_completed)}")
    print(f"Practice:   {len(p.practices_completed)}")
    print(f"Quizzes:    {p.quizzes_taken}")
    print(f"Accuracy:   {p.accuracy}%")
    print(f"\nCurrent streak: {p.streak} day(s)")
    if p.achievements:
        print("\nAchievements:")
        labels = {
            "first_quiz": "First Quiz",
            "perfect_quiz": "Perfect Quiz",
            "first_challenge": "First Challenge",
            "first_lab": "First Lab",
        }
        for item in p.achievements:
            print(f"  - {labels.get(item, item)}")
    pause()


def continue_mode(progress: ProgressManager, sandbox_root: Path) -> None:
    activity = next_activity(progress)
    kind = activity.get("kind")
    if kind == "learn":
        print(f"\nNext up: learn `{activity['command']}`")
        present_lesson(activity["lesson"], progress, sandbox_root)
    elif kind == "practice":
        print(f"\nNext up: practice — {activity['title']}")
        task = next(item for item in load_practice() if item["id"] == activity["id"])
        run_task(task, progress, sandbox_root)
    elif kind == "challenge":
        print(f"\nNext up: challenge — {activity['title']}")
        challenge = next(item for item in load_challenges() if item["id"] == activity["id"])
        play_challenge(challenge, progress, sandbox_root)
    else:
        print("\nLessons, practice, and challenges are complete. Time for a quiz.")
        run_quiz(progress, num_questions=8)
        pause()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="linuxlab",
        description="Interactive Linux learning environment for the terminal.",
    )
    parser.add_argument("--version", action="version", version=f"LinuxLab {VERSION}")
    parser.add_argument(
        "--sandbox",
        type=Path,
        default=SANDBOX_DIR,
        help="Sandbox directory for filesystem work (default: ~/linuxlab-sandbox)",
    )
    parser.add_argument(
        "command",
        nargs="?",
        choices=["learn", "practice", "challenge", "lab", "quiz", "progress", "continue"],
        help="Jump straight into a mode",
    )
    return parser.parse_args(argv)


def dispatch(choice: str, progress: ProgressManager, sandbox_root: Path) -> bool:
    """Run one mode. Return False if the user asked to exit."""
    if choice in {"1", "continue"}:
        continue_mode(progress, sandbox_root)
    elif choice in {"2", "learn"}:
        run_learn(progress, sandbox_root)
    elif choice in {"3", "practice"}:
        run_practice(progress, sandbox_root)
    elif choice in {"4", "challenge", "challenges"}:
        run_challenges(progress, sandbox_root)
    elif choice in {"5", "lab"}:
        run_lab(progress, sandbox_root)
    elif choice in {"6", "quiz"}:
        run_quiz(progress, num_questions=8)
        pause()
    elif choice in {"7", "progress"}:
        progress_mode(progress)
    elif choice in {"8", "exit", "quit", ""}:
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    progress = ProgressManager()
    progress.save()

    if args.command:
        dispatch(args.command, progress, args.sandbox)
        progress.save()
        return 0

    print(banner())
    print("Learn Linux. Practice commands. Complete challenges. Build real terminal skills.")
    print("LinuxLab is a working sandbox — your commands change a real (jailed) filesystem.")
    print(f"Version {VERSION}")

    while True:
        print()
        print(banner())
        print(MAIN_MENU)
        choice = choose("Choose: ", {"1", "2", "3", "4", "5", "6", "7", "8"})
        if not dispatch(choice, progress, args.sandbox):
            progress.save()
            print("\nKeep practicing. See you next time.\n")
            return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\nKeep practicing. See you next time.\n")
        sys.exit(0)
