"""Filesystem-state validator tests."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.sandbox import Sandbox
from core.validator import validate


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name) / "sandbox"
        self.root.mkdir()
        self.box = Sandbox(self.root)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_dir_and_file_checks_pass(self):
        self.box.run("mkdir project")
        self.box.run("mkdir project/src")
        self.box.run("mkdir project/docs")
        self.box.run("touch project/README.md")
        result = validate(
            self.box,
            [
                {"type": "dir", "path": "project"},
                {"type": "dir", "path": "project/src"},
                {"type": "dir", "path": "project/docs"},
                {"type": "file", "path": "project/README.md"},
            ],
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.failed, [])

    def test_missing_file_fails(self):
        result = validate(self.box, [{"type": "file", "path": "missing.txt"}])
        self.assertFalse(result.ok)
        self.assertTrue(result.failed)

    def test_content_contains(self):
        self.box.run("echo LinuxLab > README.md")
        result = validate(
            self.box,
            [{"type": "content", "path": "README.md", "contains": "LinuxLab"}],
        )
        self.assertTrue(result.ok)

    def test_content_equals(self):
        self.box.run("echo hello > notes.txt")
        result = validate(
            self.box,
            [{"type": "content", "path": "notes.txt", "equals": "hello\n"}],
        )
        self.assertTrue(result.ok)

    def test_file_count(self):
        self.box.run("touch a.txt")
        self.box.run("touch b.txt")
        result = validate(self.box, [{"type": "file_count", "path": ".", "count": 2}])
        self.assertTrue(result.ok)

    def test_command_accepted(self):
        result = validate(
            self.box,
            [{"type": "command", "accepted": ["mkdir projects"], "given": "mkdir projects"}],
        )
        self.assertTrue(result.ok)

    def test_permissions(self):
        self.box.run("touch script.sh")
        os.chmod(self.root / "script.sh", 0o755)
        result = validate(
            self.box,
            [{"type": "permissions", "path": "script.sh", "mode": "755"}],
        )
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
