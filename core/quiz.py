"""Multiple-choice quiz engine."""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Callable, List

from core.progress import ProgressManager
from core.ui import box

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "quiz_questions.json"
XP_PER_CORRECT_ANSWER = 30
PrintFn = Callable[[str], None]
InputFn = Callable[[str], str]


def load_questions(path: Path = QUESTIONS_FILE) -> List[dict]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return payload if isinstance(payload, list) else []


def run_quiz(
    progress_manager: ProgressManager,
    num_questions: int = 5,
    input_fn: InputFn = input,
    print_fn: PrintFn = print,
    questions_path: Path | None = None,
) -> None:
    all_questions = load_questions(questions_path or QUESTIONS_FILE)
    if not all_questions:
        print_fn("No quiz questions found. Add some to data/quiz_questions.json.")
        return

    num_questions = min(max(1, num_questions), len(all_questions))
    questions = random.sample(all_questions, num_questions)
    score = 0

    print_fn("\n" + box("Linux Quiz", width=30))

    for i, q in enumerate(questions, start=1):
        print_fn("")
        print_fn(f"Question {i}/{num_questions}")
        print_fn("")
        print_fn(q["question"])
        print_fn("")
        options = q.get("options") or {}
        for letter in sorted(options):
            print_fn(f"  {letter}. {options[letter]}")

        answer = ""
        while answer not in options:
            try:
                answer = input_fn("\nYour answer: ").strip().upper()
            except (EOFError, KeyboardInterrupt):
                print_fn("\nQuiz paused.")
                return
            if answer not in options:
                print_fn("Enter A, B, C, or D.")

        correct = answer == q["answer"]
        progress_manager.record_quiz_answer(correct)

        if correct:
            score += 1
            leveled_up = progress_manager.add_xp(XP_PER_CORRECT_ANSWER)
            print_fn("\nCorrect!")
            print_fn(f"\n{q.get('explanation', '')}")
            if leveled_up:
                print_fn(f"\nLevel up! You are now level {progress_manager.progress.level}")
        else:
            print_fn("\nNot quite.")
            print_fn(f"Correct answer: {q['answer']}. {q.get('explanation', '')}")

    progress_manager.record_quiz_completed()
    if progress_manager.unlock_achievement("first_quiz"):
        print_fn("\nAchievement unlocked: First Quiz")
    if score == num_questions:
        progress_manager.unlock_achievement("perfect_quiz")
        print_fn("\nAchievement unlocked: Perfect Quiz")
    progress_manager.log_event("quiz", {"score": score, "total": num_questions})
    progress_manager.save()

    print_fn("")
    print_fn(f"Score: {score}/{num_questions}")
    print_fn(f"XP: {progress_manager.progress.xp}")
    print_fn(f"Accuracy: {progress_manager.progress.accuracy}%")
