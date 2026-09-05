"""
tests/test_progress.py

Unit tests for core.progress. Uses a temporary directory so tests never
touch the real ~/.linuxlab/ folder.
"""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.progress import ProgressManager, XP_PER_LEVEL  # noqa: E402


class TestProgressManager(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        data_dir = Path(self.tmpdir.name)
        self.manager = ProgressManager(
            data_dir=data_dir, progress_file=data_dir / "progress.json"
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_starts_at_level_one_with_zero_xp(self):
        self.assertEqual(self.manager.progress.level, 1)
        self.assertEqual(self.manager.progress.xp, 0)

    def test_add_xp_increases_total(self):
        self.manager.add_xp(30)
        self.assertEqual(self.manager.progress.xp, 30)

    def test_level_up_triggers_at_threshold(self):
        leveled_up = self.manager.add_xp(XP_PER_LEVEL)
        self.assertTrue(leveled_up)
        self.assertEqual(self.manager.progress.level, 2)

    def test_no_level_up_below_threshold(self):
        leveled_up = self.manager.add_xp(XP_PER_LEVEL - 1)
        self.assertFalse(leveled_up)
        self.assertEqual(self.manager.progress.level, 1)

    def test_accuracy_calculation(self):
        self.manager.record_quiz_answer(True)
        self.manager.record_quiz_answer(True)
        self.manager.record_quiz_answer(False)
        self.assertAlmostEqual(self.manager.progress.accuracy, 66.7, places=1)

    def test_accuracy_with_no_answers_is_zero(self):
        self.assertEqual(self.manager.progress.accuracy, 0.0)

    def test_save_and_reload_persists_progress(self):
        self.manager.add_xp(50)
        self.manager.record_quiz_answer(True)
        self.manager.save()

        reloaded = ProgressManager(
            data_dir=self.manager.data_dir, progress_file=self.manager.progress_file
        )
        self.assertEqual(reloaded.progress.xp, 50)
        self.assertEqual(reloaded.progress.questions_correct, 1)

    def test_corrupt_progress_file_falls_back_to_fresh_state(self):
        self.manager.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.manager.progress_file, "w") as f:
            f.write("{not valid json")

        recovered = ProgressManager(
            data_dir=self.manager.data_dir, progress_file=self.manager.progress_file
        )
        self.assertEqual(recovered.progress.xp, 0)


if __name__ == "__main__":
    unittest.main()
