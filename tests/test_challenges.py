"""End-to-end challenge validation against bundled missions."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.challenges import load_challenges, _seed
from core.sandbox import Sandbox
from core.validator import validate


class TestChallenges(unittest.TestCase):
    def test_bundled_challenges_exist(self):
        challenges = load_challenges()
        self.assertGreaterEqual(len(challenges), 8)
        ids = {item["id"] for item in challenges}
        self.assertIn("files-1", ids)

    def test_starter_project_can_be_solved(self):
        with tempfile.TemporaryDirectory() as tmp:
            box = Sandbox(Path(tmp) / "sandbox")
            box.run("mkdir project")
            box.run("mkdir project/src")
            box.run("mkdir project/docs")
            box.run("touch project/README.md")
            challenge = next(item for item in load_challenges() if item["id"] == "files-1")
            result = validate(box, challenge["checks"])
            self.assertTrue(result.ok, result.failed)

    def test_backup_notes_uses_setup_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            box = Sandbox(Path(tmp) / "sandbox")
            challenge = next(item for item in load_challenges() if item["id"] == "files-2")
            _seed(box, challenge["setup"])
            self.assertTrue(box.run("mv documents/notes.txt backups/").ok)
            result = validate(box, challenge["checks"])
            self.assertTrue(result.ok, result.failed)

    def test_write_readme_with_echo(self):
        with tempfile.TemporaryDirectory() as tmp:
            box = Sandbox(Path(tmp) / "sandbox")
            challenge = next(item for item in load_challenges() if item["id"] == "files-6")
            self.assertTrue(box.run("mkdir docs").ok)
            self.assertTrue(box.run("echo LinuxLab > docs/README.md").ok)
            result = validate(box, challenge["checks"])
            self.assertTrue(result.ok, result.failed)


if __name__ == "__main__":
    unittest.main()
