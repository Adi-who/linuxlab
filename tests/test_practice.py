"""Practice-mode command matching tests."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.practice import matches_command, normalize_command


class TestPracticeMatching(unittest.TestCase):
    def test_normalize_collapses_whitespace(self):
        self.assertEqual(normalize_command("  mkdir   projects  "), "mkdir projects")

    def test_exact_match(self):
        self.assertTrue(matches_command("mkdir projects", ["mkdir projects"]))

    def test_whitespace_tolerant_match(self):
        self.assertTrue(matches_command("mkdir    projects", ["mkdir projects"]))

    def test_trailing_slash_optional(self):
        self.assertTrue(matches_command("mkdir projects/", ["mkdir projects"]))

    def test_rejects_wrong_command(self):
        self.assertFalse(matches_command("touch projects", ["mkdir projects"]))

    def test_accepts_any_listed_variant(self):
        self.assertTrue(
            matches_command("mkdir ./projects", ["mkdir projects", "mkdir ./projects"])
        )


if __name__ == "__main__":
    unittest.main()
