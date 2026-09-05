"""Helpers for matching guided practice answers."""

from __future__ import annotations

import re


def normalize_command(command: str) -> str:
    text = " ".join(command.strip().split())
    text = re.sub(r"/$", "", text)
    return text


def matches_command(given: str, accepted: list[str]) -> bool:
    needle = normalize_command(given)
    return any(needle == normalize_command(option) for option in accepted)
