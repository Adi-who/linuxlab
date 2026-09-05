#!/usr/bin/env python3
"""
LinuxLab — Interactive Linux Learning Environment
Version 0.1

Run with:
    python linuxlab.py
"""

from __future__ import annotations

from core.learn import format_lesson, group_by_category, load_all_commands
from core.progress import ProgressManager
from core.quiz import run_quiz

BANNER = r"""
╔════════════════════════════╗
║         🐧 LinuxLab        ║
╚════════════════════════════╝
"""

MAIN_MENU = """
1. Learn
2. Quiz
3. Progress
4. Exit
"""


def pause() -> None:
    input("\nPress Enter to continue...")


def choose(prompt: str, valid: set[str]) -> str:
    """Repeatedly asks until the user enters one of the valid choices."""
    choice = ""
    while choice not in valid:
        choice = input(prompt).strip()
    return choice


def learn_mode() -> None:
    commands = load_all_commands()
    if not commands:
        print("No lessons found. Check the commands/ folder.")
        return

    grouped = group_by_category(commands)
    categories = list(grouped.keys())

    while True:
        print("\n📚 LEARN — choose a category:\n")
        for i, cat in enumerate(categories, start=1):
            print(f"{i}. {cat}")
        print(f"{len(categories) + 1}. Back to main menu")

        choice = choose("\nChoose: ", {str(n) for n in range(1, len(categories) + 2)})
        idx = int(choice) - 1
        if idx == len(categories):
            return

        category_commands = grouped[categories[idx]]
        for cmd in category_commands:
            print("\n" + format_lesson(cmd))
            pause()


def quiz_mode(progress_manager: ProgressManager) -> None:
    print("\n🐧 Linux Quiz\n")
    run_quiz(progress_manager, num_questions=5)
    pause()


def progress_mode(progress_manager: ProgressManager) -> None:
    p = progress_manager.progress
    bar_len = 20
    filled = int(bar_len * (p.xp_into_level / p.xp_for_next_level))
    bar = "█" * filled + "░" * (bar_len - filled)

    print("\n╔══════════════════════════════╗")
    print("║       📊 YOUR PROGRESS       ║")
    print("╚══════════════════════════════╝\n")
    print(f"Level: {p.level}")
    print(f"XP: {p.xp_into_level} / {p.xp_for_next_level}  [{bar}]")
    print(f"\nQuizzes taken: {p.quizzes_taken}")
    print(f"Questions answered: {p.questions_answered}")
    print(f"Accuracy: {p.accuracy}%")
    print(f"\n🔥 Current Streak: {p.streak} day(s)")
    pause()


def main() -> None:
    progress_manager = ProgressManager()

    print(BANNER)
    print("Welcome to LinuxLab — Learn Linux. Practice commands. Build real skills.")

    while True:
        print(BANNER)
        print(MAIN_MENU)
        choice = choose("Choose: ", {"1", "2", "3", "4"})

        if choice == "1":
            learn_mode()
        elif choice == "2":
            quiz_mode(progress_manager)
        elif choice == "3":
            progress_mode(progress_manager)
        elif choice == "4":
            progress_manager.save()
            print("\n👋 Keep practicing. See you next time!\n")
            break


if __name__ == "__main__":
    main()
