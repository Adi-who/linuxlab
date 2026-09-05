"""Sandbox path jail and simulated command tests."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.sandbox import Sandbox, SandboxError


class TestSandbox(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name) / "sandbox"
        self.root.mkdir()
        self.box = Sandbox(self.root)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_pwd_starts_at_sandbox_root(self):
        result = self.box.run("pwd")
        self.assertTrue(result.ok)
        self.assertEqual(result.output.strip(), "/")

    def test_mkdir_and_ls(self):
        self.assertTrue(self.box.run("mkdir projects").ok)
        listing = self.box.run("ls")
        self.assertIn("projects", listing.output)

    def test_touch_creates_file(self):
        self.assertTrue(self.box.run("touch notes.txt").ok)
        self.assertTrue((self.root / "notes.txt").is_file())

    def test_cd_and_relative_mkdir(self):
        self.box.run("mkdir projects")
        self.box.run("cd projects")
        self.box.run("mkdir src")
        self.assertTrue((self.root / "projects" / "src").is_dir())
        self.assertEqual(self.box.run("pwd").output.strip(), "/projects")

    def test_rejects_escape_via_dotdot(self):
        result = self.box.run("cd ..")
        self.assertFalse(result.ok)
        self.assertIn("sandbox", result.error.lower())

    def test_rejects_absolute_path_outside_sandbox(self):
        result = self.box.run("mkdir /etc/linuxlab-hack")
        self.assertFalse(result.ok)
        self.assertFalse(Path("/etc/linuxlab-hack").exists())

    def test_mv_moves_file(self):
        self.box.run("mkdir documents")
        self.box.run("mkdir backups")
        self.box.run("touch documents/notes.txt")
        result = self.box.run("mv documents/notes.txt backups/")
        self.assertTrue(result.ok)
        self.assertFalse((self.root / "documents" / "notes.txt").exists())
        self.assertTrue((self.root / "backups" / "notes.txt").is_file())

    def test_cp_copies_file(self):
        self.box.run("touch notes.txt")
        self.assertTrue(self.box.run("cp notes.txt backup.txt").ok)
        self.assertTrue((self.root / "notes.txt").is_file())
        self.assertTrue((self.root / "backup.txt").is_file())

    def test_echo_redirect_writes_file(self):
        result = self.box.run("echo hello world > notes.txt")
        self.assertTrue(result.ok)
        self.assertEqual((self.root / "notes.txt").read_text(encoding="utf-8"), "hello world\n")

    def test_unknown_command_is_rejected(self):
        result = self.box.run("python -c 'print(1)'")
        self.assertFalse(result.ok)

    def test_empty_command_is_ok_noop(self):
        result = self.box.run("   ")
        self.assertTrue(result.ok)

    def test_rm_file(self):
        self.box.run("touch gone.txt")
        self.assertTrue(self.box.run("rm gone.txt").ok)
        self.assertFalse((self.root / "gone.txt").exists())

    def test_rmdir_rejects_nonempty(self):
        self.box.run("mkdir box")
        self.box.run("touch box/a.txt")
        result = self.box.run("rmdir box")
        self.assertFalse(result.ok)
        self.assertTrue((self.root / "box").is_dir())


class TestSandboxResolve(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tmpdir.name) / "sandbox"
        self.root.mkdir()
        self.box = Sandbox(self.root)

    def tearDown(self):
        self.tmpdir.cleanup()

    def test_resolve_keeps_paths_inside_root(self):
        target = self.box.resolve("projects/src")
        self.assertTrue(str(target).startswith(str(self.root.resolve())))

    def test_resolve_raises_on_escape(self):
        with self.assertRaises(SandboxError):
            self.box.resolve("../outside")


if __name__ == "__main__":
    unittest.main()
