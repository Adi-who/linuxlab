"""Modular filesystem and command validation for LinuxLab challenges."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.practice import matches_command
from core.sandbox import Sandbox, SandboxError


@dataclass
class ValidationResult:
    ok: bool
    failed: list[str] = field(default_factory=list)


def validate(sandbox: Sandbox, checks: list[dict]) -> ValidationResult:
    failed: list[str] = []
    for check in checks:
        message = _run_check(sandbox, check)
        if message:
            failed.append(message)
    return ValidationResult(ok=not failed, failed=failed)


def _run_check(sandbox: Sandbox, check: dict) -> str | None:
    kind = check.get("type")
    handlers = {
        "file": _check_file,
        "dir": _check_dir,
        "missing": _check_missing,
        "content": _check_content,
        "file_count": _check_file_count,
        "permissions": _check_permissions,
        "command": _check_command,
        "location": _check_file,
    }
    handler = handlers.get(kind)
    if handler is None:
        return f"Unknown check type: {kind}"
    return handler(sandbox, check)


def _resolve(sandbox: Sandbox, raw_path: str) -> Path | None:
    try:
        return sandbox.resolve(raw_path)
    except SandboxError:
        return None


def _check_file(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", ""))
    if path is None or not path.is_file():
        return f"Expected file: {check.get('path')}"
    return None


def _check_dir(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", ""))
    if path is None or not path.is_dir():
        return f"Expected directory: {check.get('path')}"
    return None


def _check_missing(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", ""))
    if path is not None and path.exists():
        return f"Expected missing path: {check.get('path')}"
    return None


def _check_content(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", ""))
    if path is None or not path.is_file():
        return f"Expected file: {check.get('path')}"
    text = path.read_text(encoding="utf-8", errors="replace")
    if "contains" in check and check["contains"] not in text:
        return f"{check.get('path')} should contain {check['contains']!r}"
    if "equals" in check and text != check["equals"]:
        return f"{check.get('path')} has unexpected contents"
    return None


def _check_file_count(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", "."))
    if path is None or not path.exists():
        return f"Expected path: {check.get('path')}"
    if path.is_file():
        count = 1
    else:
        count = sum(1 for child in path.iterdir() if child.is_file())
    expected = int(check.get("count", 0))
    if count != expected:
        return f"Expected {expected} file(s) in {check.get('path')}, found {count}"
    return None


def _check_permissions(sandbox: Sandbox, check: dict) -> str | None:
    path = _resolve(sandbox, check.get("path", ""))
    if path is None or not path.exists():
        return f"Expected path: {check.get('path')}"
    actual = oct(path.stat().st_mode)[-3:]
    expected = str(check.get("mode", "")).lstrip("0") or "0"
    actual_norm = actual.lstrip("0") or "0"
    expected_norm = expected.lstrip("0") or "0"
    if actual_norm != expected_norm and actual != str(check.get("mode")):
        return f"{check.get('path')} permissions are {actual}, expected {check.get('mode')}"
    return None


def _check_command(sandbox: Sandbox, check: dict) -> str | None:
    given = check.get("given", "")
    accepted = check.get("accepted", [])
    if not matches_command(given, accepted):
        return "Command did not match the expected answer"
    return None
