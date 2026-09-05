"""Quiz engine tests using injected I/O."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.progress import ProgressManager
from core.quiz import load_questions, run_quiz


class TestQuiz(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        data_dir = Path(self.tmpdir.name)
        self.manager = ProgressManager(
            data_dir=data_dir, progress_file=data_dir / "progress.json"
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_loads_bundled_questions(self):
        questions = load_questions()
        self.assertGreaterEqual(len(questions), 15)
        sample = questions[0]
        self.assertIn("question", sample)
        self.assertIn("options", sample)
        self.assertIn("answer", sample)

    def test_perfect_quiz_awards_xp(self):
        questions_path = Path(self.tmpdir.name) / "quiz.json"
        questions_path.write_text(
            json.dumps(
                [
                    {
                        "question": "Which command prints the working directory?",
                        "options": {"A": "ls", "B": "pwd", "C": "cd", "D": "mkdir"},
                        "answer": "B",
                        "explanation": "pwd -> Print Working Directory",
                        "category": "Navigation",
                    }
                ]
            ),
            encoding="utf-8",
        )
        answers = iter(["b"])
        output = []
        run_quiz(
            self.manager,
            num_questions=1,
            questions_path=questions_path,
            input_fn=lambda _prompt: next(answers),
            print_fn=output.append,
        )
        self.assertEqual(self.manager.progress.questions_correct, 1)
        self.assertGreater(self.manager.progress.xp, 0)
        self.assertEqual(self.manager.progress.quizzes_taken, 1)
        self.assertTrue(any("Correct" in line for line in output))

    def test_wrong_answer_does_not_award_xp(self):
        questions_path = Path(self.tmpdir.name) / "quiz.json"
        questions_path.write_text(
            json.dumps(
                [
                    {
                        "question": "Which command lists files?",
                        "options": {"A": "ls", "B": "pwd", "C": "cd", "D": "mkdir"},
                        "answer": "A",
                        "explanation": "ls lists files.",
                        "category": "Navigation",
                    }
                ]
            ),
            encoding="utf-8",
        )
        answers = iter(["B"])
        run_quiz(
            self.manager,
            num_questions=1,
            questions_path=questions_path,
            input_fn=lambda _prompt: next(answers),
            print_fn=lambda _line: None,
        )
        self.assertEqual(self.manager.progress.xp, 0)
        self.assertEqual(self.manager.progress.questions_correct, 0)
        self.assertEqual(self.manager.progress.questions_answered, 1)


if __name__ == "__main__":
    unittest.main()
