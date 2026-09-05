"""Progress, XP, streaks, achievements, and persistence tests."""

import json
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.progress import ProgressManager, XP_PER_LEVEL


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
        self.assertTrue(self.manager.progress_file.with_suffix(".json.bak").exists())

    def test_category_progress_updates(self):
        self.manager.mark_lesson_complete("Navigation", "pwd")
        self.manager.mark_lesson_complete("Navigation", "ls")
        self.assertEqual(self.manager.category_percent("Navigation", total=3), 66)
        self.assertIn("pwd", self.manager.progress.lessons_completed["Navigation"])

    def test_challenge_completion_is_idempotent(self):
        first = self.manager.complete_challenge("files-1")
        second = self.manager.complete_challenge("files-1")
        self.assertTrue(first)
        self.assertFalse(second)
        self.assertEqual(self.manager.progress.challenges_completed, ["files-1"])

    def test_practice_completion(self):
        self.manager.complete_practice("mkdir-projects")
        self.assertIn("mkdir-projects", self.manager.progress.practices_completed)

    def test_streak_starts_at_one_on_first_visit(self):
        self.assertEqual(self.manager.progress.streak, 1)
        self.assertEqual(self.manager.progress.last_active, date.today().isoformat())

    def test_consecutive_day_increments_streak(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        self.manager.progress.last_active = yesterday
        self.manager.progress.streak = 3
        self.manager._update_streak()
        self.assertEqual(self.manager.progress.streak, 4)

    def test_missed_day_resets_streak(self):
        old = (date.today() - timedelta(days=3)).isoformat()
        self.manager.progress.last_active = old
        self.manager.progress.streak = 9
        self.manager._update_streak()
        self.assertEqual(self.manager.progress.streak, 1)

    def test_same_day_does_not_double_count_streak(self):
        self.manager.progress.streak = 2
        self.manager._update_streak()
        self.assertEqual(self.manager.progress.streak, 2)

    def test_achievements_unlock(self):
        unlocked = self.manager.unlock_achievement("first_quiz")
        self.assertTrue(unlocked)
        self.assertIn("first_quiz", self.manager.progress.achievements)
        self.assertFalse(self.manager.unlock_achievement("first_quiz"))

    def test_history_appends_events(self):
        self.manager.log_event("quiz", {"score": 4, "total": 5})
        self.manager.save()
        history_path = self.manager.data_dir / "history.json"
        self.assertTrue(history_path.exists())
        events = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertEqual(events[-1]["kind"], "quiz")
        self.assertEqual(events[-1]["score"], 4)

    def test_progress_bar_clamps(self):
        bar = self.manager.bar(7, 10, width=10)
        self.assertEqual(len(bar), 10)
        self.assertIn("█", bar)
        empty = self.manager.bar(0, 10, width=10)
        self.assertEqual(empty, "░" * 10)


if __name__ == "__main__":
    unittest.main()
