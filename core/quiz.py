"""
core/quiz.py

A small multiple-choice quiz engine. Questions are loaded from
data/quiz_questions.json and asked in random order.
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Callable, List, Optional

QUESTIONS_FILE = Path(__file__).resolve().parent.parent / "data" / "quiz_questions.json"

XP_PER_CORRECT_ANSWER = 30


def load_questions(path: Path = QUESTIONS_FILE) -> List[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_quiz(
    progress_manager,
    num_questions: int = 5,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> None:
    """
    Runs an interactive multiple-choice quiz, updating progress_manager
    as questions are answered, then saves progress at the end.
    """
    all_questions = load_questions()
    if not all_questions:
        print_fn("No quiz questions found. Add some to data/quiz_questions.json.")
        return

    num_questions = min(num_questions, len(all_questions))
    questions = random.sample(all_questions, num_questions)
    score = 0

    for i, q in enumerate(questions, start=1):
        print_fn("")
        print_fn(f"Question {i}/{num_questions}")
        print_fn("")
        print_fn(q["question"])
        print_fn("")
        for letter in sorted(q["options"]):
            print_fn(f"  {letter}. {q['options'][letter]}")

        answer = ""
        while answer not in q["options"]:
            answer = input_fn("\nYour answer: ").strip().upper()

        correct = answer == q["answer"]
        progress_manager.record_quiz_answer(correct)

        if correct:
            score += 1
            leveled_up = progress_manager.add_xp(XP_PER_CORRECT_ANSWER)
            print_fn("\n✅ Correct!")
            print_fn(f"\n{q.get('explanation', '')}")
            if leveled_up:
                print_fn(f"\n🎉 Level up! You're now level {progress_manager.progress.level}")
        else:
            print_fn("\n❌ Not quite.")
            print_fn(f"Correct answer: {q['answer']}. {q.get('explanation', '')}")

    progress_manager.record_quiz_completed()
    progress_manager.save()

    print_fn("")
    print_fn(f"Score: {score}/{num_questions}")
    print_fn(f"XP: {progress_manager.progress.xp}")
