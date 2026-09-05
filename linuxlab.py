#!/usr/bin/env python3
"""LinuxLab — Interactive Linux Learning Environment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from core.challenges import run_challenges
from core.learn import run_learn
from core.practice_mode import run_practice
from core.progress import ProgressManager
from core.quiz import run_quiz
from core.ui import banner, box, choose, pause

VERSION = "0.4"
SANDBOX_DIR = Path.home() / "linuxlab-sandbox"

MAIN_MENU = """
1. Learn
2. Practice
3. Challenges
4. Quiz
5. Progress
6. Exit
"""


def progress_mode(manager: ProgressManager) -> None:
    from core.learn import group_by_category, load_all_commands
    from core.challenges import load_challenges

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
        print(f"{category:<22} {manager.bar(done, total, width=10)}  {manager.category_percent(category, total)}%")

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
        }
        for item in p.achievements:
            print(f"  - {labels.get(item, item)}")
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
        help="Sandbox directory for filesystem challenges (default: ~/linuxlab-sandbox)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    progress = ProgressManager()
    progress.save()

    print(banner())
    print("Learn Linux. Practice commands. Complete challenges. Build real terminal skills.")
    print("LinuxLab is a learning sandbox — it never touches system directories.")
    print(f"Version {VERSION}")

    while True:
        print()
        print(banner())
        print(MAIN_MENU)
        choice = choose("Choose: ", {"1", "2", "3", "4", "5", "6"})
        if choice == "1":
            run_learn(progress)
        elif choice == "2":
            run_practice(progress)
        elif choice == "3":
            run_challenges(progress, args.sandbox)
        elif choice == "4":
            run_quiz(progress, num_questions=8)
            pause()
        elif choice == "5":
            progress_mode(progress)
        elif choice in {"6", ""}:
            progress.save()
            print("\nKeep practicing. See you next time.\n")
            return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n\nKeep practicing. See you next time.\n")
        sys.exit(0)
