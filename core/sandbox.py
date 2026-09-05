"""Safe, simulated Linux command environment confined to a sandbox directory."""

from __future__ import annotations

import fnmatch
import shlex
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ALLOWED_COMMANDS = {
    "pwd",
    "ls",
    "cd",
    "mkdir",
    "rmdir",
    "touch",
    "cp",
    "mv",
    "rm",
    "cat",
    "head",
    "tail",
    "grep",
    "find",
    "chmod",
        "echo",
        "help",
        "clear",
        "tree",
    }

FORBIDDEN_ROOTS = {
    "etc",
    "usr",
    "bin",
    "sbin",
    "boot",
    "dev",
    "proc",
    "sys",
    "root",
    "var",
    "lib",
    "lib64",
    "tmp",
    "opt",
    "mnt",
    "media",
    "run",
    "snap",
}

UNSAFE_TOKENS = ("|", ";", "&&", "||", "`", "$(", "&")


class SandboxError(Exception):
    """Raised when a path would leave the sandbox."""


@dataclass
class CommandResult:
    ok: bool
    output: str = ""
    error: str = ""


class Sandbox:
    """A jailed virtual filesystem that understands beginner Linux commands."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.cwd = self.root
        self.history: list[str] = []

    def tree(self) -> str:
        lines = ["/"]
        def walk(path: Path, prefix: str) -> None:
            children = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            for index, child in enumerate(children):
                last = index == len(children) - 1
                connector = "└── " if last else "├── "
                name = child.name + ("/" if child.is_dir() else "")
                lines.append(prefix + connector + name)
                if child.is_dir():
                    walk(child, prefix + ("    " if last else "│   "))
        walk(self.root, "")
        return "\n".join(lines) + "\n"

    def virtual_cwd(self) -> str:
        rel = self.cwd.resolve().relative_to(self.root)
        text = rel.as_posix()
        return "/" if text == "." else f"/{text}"

    def resolve(self, user_path: str) -> Path:
        if user_path in ("", ".", "./"):
            candidate = self.cwd
        elif user_path in ("~", "$HOME"):
            candidate = self.root
        elif user_path.startswith("/"):
            first = user_path.lstrip("/").split("/", 1)[0]
            if first in FORBIDDEN_ROOTS:
                raise SandboxError("Path is outside the LinuxLab sandbox.")
            candidate = (self.root / user_path.lstrip("/")).resolve()
        else:
            candidate = (self.cwd / user_path).resolve()

        root = self.root.resolve()
        try:
            candidate.relative_to(root)
        except ValueError as exc:
            raise SandboxError("Path is outside the LinuxLab sandbox.") from exc
        return candidate

    def reset(self) -> None:
        if self.root.exists():
            for child in self.root.iterdir():
                if child.is_dir() and not child.is_symlink():
                    shutil.rmtree(child)
                else:
                    child.unlink()
        else:
            self.root.mkdir(parents=True, exist_ok=True)
        self.cwd = self.root

    def run(self, command: str) -> CommandResult:
        raw = command.strip()
        if not raw:
            return CommandResult(ok=True)
        if any(token in raw for token in UNSAFE_TOKENS):
            return CommandResult(
                ok=False,
                error="Pipes, chaining, and shell expansion are disabled in LinuxLab.",
            )
        try:
            tokens = shlex.split(raw)
        except ValueError as exc:
            return CommandResult(ok=False, error=str(exc))
        if not tokens:
            return CommandResult(ok=True)

        name = tokens[0]
        if name not in ALLOWED_COMMANDS:
            return CommandResult(
                ok=False,
                error=f"Command not allowed in the sandbox: {name}",
            )
        try:
            result = self._dispatch(name, tokens[1:], raw)
        except SandboxError as exc:
            return CommandResult(ok=False, error=str(exc))
        except OSError as exc:
            return CommandResult(ok=False, error=str(exc))
        if result.ok:
            self.history.append(raw)
        return result

    def _dispatch(self, name: str, args: list[str], raw: str) -> CommandResult:
        handlers = {
            "pwd": self._pwd,
            "ls": self._ls,
            "cd": self._cd,
            "mkdir": self._mkdir,
            "rmdir": self._rmdir,
            "touch": self._touch,
            "cp": self._cp,
            "mv": self._mv,
            "rm": self._rm,
            "cat": self._cat,
            "head": self._head,
            "tail": self._tail,
            "grep": self._grep,
            "find": self._find,
            "chmod": self._chmod,
            "echo": self._echo,
            "help": self._help,
            "clear": lambda _args: CommandResult(ok=True),
            "tree": lambda _args: CommandResult(ok=True, output=self.tree()),
        }
        return handlers[name](args)

    def _pwd(self, _args: list[str]) -> CommandResult:
        return CommandResult(ok=True, output=self.virtual_cwd() + "\n")

    def _ls(self, args: list[str]) -> CommandResult:
        flags, paths = _split_flags(args)
        long_fmt = "l" in flags
        show_all = "a" in flags
        targets = paths or ["."]
        chunks: list[str] = []
        for target in targets:
            path = self.resolve(target)
            if not path.exists():
                return CommandResult(ok=False, error=f"ls: cannot access '{target}': No such file or directory")
            if path.is_file():
                chunks.append(self._format_entry(path, long_fmt))
                continue
            names = []
            for child in sorted(path.iterdir(), key=lambda p: p.name):
                if child.name.startswith(".") and not show_all:
                    continue
                names.append(self._format_entry(child, long_fmt))
            if show_all:
                names = [self._format_entry(path, long_fmt, display=".")] + names
            chunks.append("\n".join(names))
        output = "\n\n".join(chunk for chunk in chunks if chunk)
        return CommandResult(ok=True, output=(output + "\n") if output else "")

    def _format_entry(self, path: Path, long_fmt: bool, display: str | None = None) -> str:
        name = display or path.name
        if not long_fmt:
            return name + ("/" if path.is_dir() and display is None else "")
        mode = stat.filemode(path.stat().st_mode)
        size = path.stat().st_size
        return f"{mode} {size:>6} {name}"

    def _cd(self, args: list[str]) -> CommandResult:
        target = args[0] if args else "/"
        path = self.resolve(target)
        if not path.exists():
            return CommandResult(ok=False, error=f"cd: {target}: No such file or directory")
        if not path.is_dir():
            return CommandResult(ok=False, error=f"cd: {target}: Not a directory")
        self.cwd = path
        return CommandResult(ok=True)

    def _mkdir(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(ok=False, error="mkdir: missing operand")
        parents = "-p" in args
        names = [a for a in args if not a.startswith("-")]
        if not names:
            return CommandResult(ok=False, error="mkdir: missing operand")
        for name in names:
            path = self.resolve(name)
            if parents:
                path.mkdir(parents=True, exist_ok=True)
            else:
                if path.exists():
                    return CommandResult(ok=False, error=f"mkdir: cannot create directory '{name}': File exists")
                if not path.parent.exists():
                    return CommandResult(
                        ok=False,
                        error=f"mkdir: cannot create directory '{name}': No such file or directory",
                    )
                path.mkdir()
        return CommandResult(ok=True)

    def _rmdir(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(ok=False, error="rmdir: missing operand")
        for name in args:
            path = self.resolve(name)
            if not path.exists():
                return CommandResult(ok=False, error=f"rmdir: failed to remove '{name}': No such file or directory")
            if not path.is_dir():
                return CommandResult(ok=False, error=f"rmdir: failed to remove '{name}': Not a directory")
            try:
                path.rmdir()
            except OSError:
                return CommandResult(ok=False, error=f"rmdir: failed to remove '{name}': Directory not empty")
        return CommandResult(ok=True)

    def _touch(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(ok=False, error="touch: missing file operand")
        for name in args:
            path = self.resolve(name)
            if not path.parent.exists():
                return CommandResult(ok=False, error=f"touch: cannot touch '{name}': No such file or directory")
            path.touch()
        return CommandResult(ok=True)

    def _cp(self, args: list[str]) -> CommandResult:
        recursive = "-r" in args or "-R" in args
        names = [a for a in args if not a.startswith("-")]
        if len(names) < 2:
            return CommandResult(ok=False, error="cp: missing destination")
        dest = self.resolve(names[-1])
        sources = [self.resolve(n) for n in names[:-1]]
        if len(sources) > 1 and not dest.is_dir():
            return CommandResult(ok=False, error="cp: target is not a directory")
        for src in sources:
            if not src.exists():
                return CommandResult(ok=False, error=f"cp: cannot stat '{src.name}': No such file or directory")
            target = dest / src.name if dest.is_dir() or dest.exists() and dest.is_dir() else dest
            if dest.exists() and dest.is_dir():
                target = dest / src.name
            if src.is_dir():
                if not recursive:
                    return CommandResult(ok=False, error=f"cp: -r not specified; omitting directory '{src.name}'")
                shutil.copytree(src, target, dirs_exist_ok=True)
            else:
                if dest.exists() and dest.is_dir():
                    shutil.copy2(src, dest / src.name)
                else:
                    if not dest.parent.exists():
                        return CommandResult(ok=False, error="cp: destination directory does not exist")
                    shutil.copy2(src, dest)
        return CommandResult(ok=True)

    def _mv(self, args: list[str]) -> CommandResult:
        names = [a for a in args if not a.startswith("-")]
        if len(names) < 2:
            return CommandResult(ok=False, error="mv: missing destination")
        src = self.resolve(names[0])
        dest = self.resolve(names[1])
        if not src.exists():
            return CommandResult(ok=False, error=f"mv: cannot stat '{names[0]}': No such file or directory")
        if dest.exists() and dest.is_dir():
            dest = dest / src.name
        if not dest.parent.exists():
            return CommandResult(ok=False, error="mv: destination directory does not exist")
        src.rename(dest)
        return CommandResult(ok=True)

    def _rm(self, args: list[str]) -> CommandResult:
        recursive = "-r" in args or "-R" in args or "-rf" in args or "-fr" in args
        names = [a for a in args if not a.startswith("-")]
        if not names:
            return CommandResult(ok=False, error="rm: missing operand")
        for name in names:
            path = self.resolve(name)
            if path == self.root:
                return CommandResult(ok=False, error="rm: refusing to remove the sandbox root")
            if not path.exists():
                return CommandResult(ok=False, error=f"rm: cannot remove '{name}': No such file or directory")
            if path.is_dir() and not recursive:
                return CommandResult(ok=False, error=f"rm: cannot remove '{name}': Is a directory")
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
        return CommandResult(ok=True)

    def _cat(self, args: list[str]) -> CommandResult:
        if not args:
            return CommandResult(ok=False, error="cat: missing file operand")
        parts = []
        for name in args:
            path = self.resolve(name)
            if not path.exists() or not path.is_file():
                return CommandResult(ok=False, error=f"cat: {name}: No such file or directory")
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        return CommandResult(ok=True, output="".join(parts))

    def _head(self, args: list[str]) -> CommandResult:
        return self._head_or_tail(args, head=True)

    def _tail(self, args: list[str]) -> CommandResult:
        return self._head_or_tail(args, head=False)

    def _head_or_tail(self, args: list[str], head: bool) -> CommandResult:
        count = 10
        names = []
        i = 0
        while i < len(args):
            if args[i] in ("-n", "--lines") and i + 1 < len(args):
                try:
                    count = int(args[i + 1])
                except ValueError:
                    return CommandResult(ok=False, error="invalid line count")
                i += 2
                continue
            if args[i].startswith("-n") and args[i] != "-n":
                try:
                    count = int(args[i][2:])
                except ValueError:
                    return CommandResult(ok=False, error="invalid line count")
                i += 1
                continue
            names.append(args[i])
            i += 1
        if not names:
            return CommandResult(ok=False, error="missing file operand")
        path = self.resolve(names[0])
        if not path.is_file():
            return CommandResult(ok=False, error=f"{names[0]}: No such file")
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)
        sliced = lines[:count] if head else lines[-count:]
        return CommandResult(ok=True, output="".join(sliced))

    def _grep(self, args: list[str]) -> CommandResult:
        recursive = "-r" in args or "-R" in args
        names = [a for a in args if not a.startswith("-")]
        if len(names) < 1:
            return CommandResult(ok=False, error="grep: missing pattern")
        pattern = names[0]
        targets = names[1:] or ["."]
        hits: list[str] = []
        for target in targets:
            path = self.resolve(target)
            files = _iter_files(path, recursive=recursive or path.is_dir())
            for file_path in files:
                try:
                    text = file_path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                for line in text.splitlines():
                    if pattern in line:
                        prefix = ""
                        if path.is_dir() or len(targets) > 1:
                            rel = file_path.resolve().relative_to(self.root).as_posix()
                            prefix = f"{rel}:"
                        hits.append(prefix + line)
        output = "\n".join(hits)
        return CommandResult(ok=True, output=(output + "\n") if output else "")

    def _find(self, args: list[str]) -> CommandResult:
        start = "."
        pattern = None
        i = 0
        while i < len(args):
            if args[i] == "-name" and i + 1 < len(args):
                pattern = args[i + 1]
                i += 2
                continue
            if not args[i].startswith("-"):
                start = args[i]
            i += 1
        root = self.resolve(start)
        if not root.exists():
            return CommandResult(ok=False, error=f"find: '{start}': No such file or directory")
        items = [root] if root.is_file() else [root, *root.rglob("*")]
        matches = []
        for item in items:
            if pattern is not None and not fnmatch.fnmatch(item.name, pattern):
                continue
            resolved = item.resolve()
            rel = "/" if resolved == self.root else "/" + resolved.relative_to(self.root).as_posix()
            matches.append(rel)
        output = "\n".join(matches)
        return CommandResult(ok=True, output=(output + "\n") if output else "")

    def _chmod(self, args: list[str]) -> CommandResult:
        names = [a for a in args if not a.startswith("-")]
        if len(names) < 2:
            return CommandResult(ok=False, error="chmod: missing operand")
        mode_text, target_name = names[0], names[1]
        path = self.resolve(target_name)
        if not path.exists():
            return CommandResult(ok=False, error=f"chmod: cannot access '{target_name}': No such file or directory")
        current = path.stat().st_mode
        if mode_text in ("+x", "u+x", "a+x"):
            path.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
            return CommandResult(ok=True)
        try:
            mode = int(mode_text, 8)
        except ValueError:
            return CommandResult(ok=False, error=f"chmod: invalid mode: '{mode_text}'")
        path.chmod(mode)
        return CommandResult(ok=True)

    def _echo(self, args: list[str]) -> CommandResult:
        if ">" in args:
            idx = args.index(">")
            text = " ".join(args[:idx])
            if idx + 1 >= len(args):
                return CommandResult(ok=False, error="echo: missing filename after >")
            path = self.resolve(args[idx + 1])
            if not path.parent.exists():
                return CommandResult(ok=False, error="echo: directory does not exist")
            path.write_text(text + "\n", encoding="utf-8")
            return CommandResult(ok=True)
        return CommandResult(ok=True, output=(" ".join(args) + "\n") if args else "\n")

    def _help(self, _args: list[str]) -> CommandResult:
        listing = " ".join(sorted(ALLOWED_COMMANDS))
        return CommandResult(
            ok=True,
            output=(
                "LinuxLab sandbox — a safe practice filesystem.\n"
                f"Allowed commands: {listing}\n"
                "Type 'done' to submit a challenge, 'hint' for a hint, 'quit' to leave.\n"
            ),
        )


def _split_flags(args: Iterable[str]) -> tuple[str, list[str]]:
    flags = ""
    paths: list[str] = []
    for arg in args:
        if arg.startswith("-") and arg != "-":
            flags += arg.lstrip("-")
        else:
            paths.append(arg)
    return flags, paths


def _iter_files(path: Path, recursive: bool) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        return []
    if recursive:
        return [p for p in path.rglob("*") if p.is_file()]
    return [p for p in path.iterdir() if p.is_file()]
