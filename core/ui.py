"""Terminal presentation helpers for LinuxLab."""

from __future__ import annotations

from typing import Callable

PrintFn = Callable[[str], None]


def box(title: str, width: int = 32) -> str:
    inner = max(width - 2, len(title) + 4)
    top = "╔" + "═" * inner + "╗"
    bottom = "╚" + "═" * inner + "╝"
    pad = inner - 2 - len(title)
    left = pad // 2
    right = pad - left
    middle = "║ " + (" " * left) + title + (" " * right) + " ║"
    return f"{top}\n{middle}\n{bottom}"


def banner() -> str:
    return box("LinuxLab", width=30)


def hr(width: int = 40) -> str:
    return "─" * width


def choose(
    prompt: str,
    valid: set[str],
    input_fn: Callable[[str], str] = input,
    print_fn: PrintFn = print,
) -> str:
    choice = ""
    while choice not in valid:
        try:
            choice = input_fn(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print_fn("")
            return ""
        if choice not in valid and choice:
            print_fn("Please enter a listed option.")
    return choice


def pause(input_fn: Callable[[str], str] = input) -> None:
    try:
        input_fn("\nPress Enter to continue...")
    except (EOFError, KeyboardInterrupt):
        return


def confirm(prompt: str, input_fn: Callable[[str], str] = input) -> bool:
    try:
        answer = input_fn(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        return False
    return answer in ("", "y", "yes")
