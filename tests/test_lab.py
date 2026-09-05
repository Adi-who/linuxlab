"""Lab mode and practice-in-sandbox tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.progress import ProgressManager
from core.sandbox import Sandbox
from core.session import next_activity, seed_sandbox, tree_text
from core.validator import validate


class TestSandboxExtras(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.box = Sandbox(Path(self.tmpdir.name) / "sandbox")

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_seed_creates_files_and_dirs(self):
        seed_sandbox(
            self.box,
            [
                {"path": "documents", "type": "dir"},
                {"path": "documents/notes.txt", "type": "file", "content": "hi\n"},
            ],
        )
        self.assertTrue((self.box.root / "documents").is_dir())
        self.assertEqual((self.box.root / "documents" / "notes.txt").read_text(), "hi\n")

    def test_tree_lists_structure(self):
        self.box.run("mkdir project")
        self.box.run("touch project/README.md")
        text = tree_text(self.box)
        self.assertIn("project", text)
        self.assertIn("README.md", text)

    def test_cwd_check(self):
        self.box.run("mkdir Documents")
        self.box.run("cd Documents")
        result = validate(self.box, [{"type": "cwd", "path": "/Documents"}])
        self.assertTrue(result.ok, result.failed)


class TestNextActivity(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        data_dir = Path(self.tmpdir.name)
        self.manager = ProgressManager(
            data_dir=data_dir, progress_file=data_dir / "progress.json"
        )

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_recommends_learn_first(self):
        activity = next_activity(self.manager)
        self.assertEqual(activity["kind"], "learn")
        self.assertIn("command", activity)

    def test_skips_completed_lessons(self):
        self.manager.mark_lesson_complete("Navigation", "pwd")
        activity = next_activity(self.manager)
        self.assertNotEqual(activity.get("command"), "pwd")


class TestPracticeSandbox(unittest.TestCase):
    def test_mkdir_practice_passes_after_real_command(self):
        from core.practice_mode import load_practice, run_task

        tasks = {item["id"]: item for item in load_practice()}
        task = tasks["mkdir-projects"]
        with tempfile.TemporaryDirectory() as tmp:
            data_dir = Path(tmp) / "data"
            sandbox_root = Path(tmp) / "sandbox"
            manager = ProgressManager(data_dir=data_dir, progress_file=data_dir / "progress.json")
            answers = iter(["mkdir projects", "done", ""])
            output = []
            run_task(
                task,
                manager,
                sandbox_root,
                input_fn=lambda _p: next(answers),
                print_fn=output.append,
            )
            self.assertIn("mkdir-projects", manager.progress.practices_completed)
            self.assertTrue(any("PASS" in line for line in output))


if __name__ == "__main__":
    unittest.main()
