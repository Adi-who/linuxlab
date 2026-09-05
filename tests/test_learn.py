"""Learn-mode data loading tests."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.learn import format_lesson, group_by_category, load_all_commands


class TestLearn(unittest.TestCase):
    def test_loads_bundled_commands(self):
        commands = load_all_commands()
        names = {c["command"] for c in commands}
        for required in ("pwd", "ls", "cd", "mkdir", "chmod"):
            self.assertIn(required, names)
        self.assertGreaterEqual(len(commands), 15)

    def test_group_by_category(self):
        grouped = group_by_category(
            [
                {"command": "pwd", "category": "Navigation"},
                {"command": "ls", "category": "Navigation"},
                {"command": "mkdir", "category": "Files & Directories"},
            ]
        )
        self.assertEqual(len(grouped["Navigation"]), 2)
        self.assertEqual(len(grouped["Files & Directories"]), 1)

    def test_format_lesson_includes_core_fields(self):
        text = format_lesson(
            {
                "command": "cd",
                "meaning": "Change Directory",
                "description": "Move between directories.",
                "syntax": "cd [directory]",
                "examples": ["cd Documents"],
                "related": ["pwd", "ls"],
            }
        )
        self.assertIn("cd", text)
        self.assertIn("Change Directory", text)
        self.assertIn("cd Documents", text)
        self.assertIn("pwd", text)

    def test_skips_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            (folder / "good.json").write_text(
                json.dumps([{"command": "pwd", "category": "Navigation"}]),
                encoding="utf-8",
            )
            (folder / "bad.json").write_text("{not json", encoding="utf-8")
            commands = load_all_commands(folder)
            self.assertEqual(len(commands), 1)
            self.assertEqual(commands[0]["command"], "pwd")


if __name__ == "__main__":
    unittest.main()
