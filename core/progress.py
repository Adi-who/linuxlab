"""
core/progress.py

Handles LinuxLab's persistent progress: XP, level, quiz stats, and streaks.
Data is stored as JSON in the user's home directory under ~/.linuxlab/.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path

DATA_DIR = Path.home() / ".linuxlab"
PROGRESS_FILE = DATA_DIR / "progress.json"

XP_PER_LEVEL = 100  # XP required to advance one level


@dataclass
class Progress:
    xp: int = 0
    level: int = 1
    quizzes_taken: int = 0
    questions_correct: int = 0
    questions_answered: int = 0
    streak: int = 0
    last_active: str = ""  # ISO date string, e.g. "2026-09-05"

    @property
    def accuracy(self) -> float:
        if self.questions_answered == 0:
            return 0.0
        return round(100 * self.questions_correct / self.questions_answered, 1)

    @property
    def xp_into_level(self) -> int:
        return self.xp % XP_PER_LEVEL

    @property
    def xp_for_next_level(self) -> int:
        return XP_PER_LEVEL


class ProgressManager:
    """Loads, updates, and saves the learner's progress to disk."""

    def __init__(self, data_dir: Path = DATA_DIR, progress_file: Path = PROGRESS_FILE):
        self.data_dir = data_dir
        self.progress_file = progress_file
        self.progress: Progress = self._load()
        self._update_streak()

    # -- persistence -------------------------------------------------

    def _load(self) -> Progress:
        if self.progress_file.exists():
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    raw = json.load(f)
                return Progress(**{**asdict(Progress()), **raw})
            except (json.JSONDecodeError, TypeError):
                # Corrupt file: back it up and start fresh rather than crashing.
                backup = self.progress_file.with_suffix(".json.bak")
                self.progress_file.replace(backup)
                return Progress()
        return Progress()

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w", encoding="utf-8") as f:
            json.dump(asdict(self.progress), f, indent=2)

    # -- streak logic --------------------------------------------------

    def _update_streak(self) -> None:
        today = date.today().isoformat()
        if self.progress.last_active == today:
            return  # already counted today
        if self.progress.last_active:
            last = date.fromisoformat(self.progress.last_active)
            gap = (date.today() - last).days
            if gap == 1:
                self.progress.streak += 1
            elif gap > 1:
                self.progress.streak = 1
            # gap == 0 already handled above
        else:
            self.progress.streak = 1
        self.progress.last_active = today

    # -- XP / leveling ---------------------------------------------------

    def add_xp(self, amount: int) -> bool:
        """Adds XP and returns True if the learner leveled up."""
        self.progress.xp += amount
        new_level = 1 + self.progress.xp // XP_PER_LEVEL
        leveled_up = new_level > self.progress.level
        self.progress.level = new_level
        return leveled_up

    # -- quiz tracking -----------------------------------------------------

    def record_quiz_answer(self, correct: bool) -> None:
        self.progress.questions_answered += 1
        if correct:
            self.progress.questions_correct += 1

    def record_quiz_completed(self) -> None:
        self.progress.quizzes_taken += 1
