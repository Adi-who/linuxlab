"""CLI smoke tests."""

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class TestCLI(unittest.TestCase):
    def test_help_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "linuxlab.py"), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Linux learning", result.stdout)

    def test_version_exits_zero(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "linuxlab.py"), "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("LinuxLab", result.stdout)

    def test_unknown_subcommand_fails(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "linuxlab.py"), "not-a-mode"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
