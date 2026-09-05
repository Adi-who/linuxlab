"""Persistent XP, levels, streaks, achievements, and category progress."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, fields
from datetime import date, datetime
from pathlib import Path

DATA_DIR = Path.home() / ".linuxlab"
PROGRESS_FILE = DATA_DIR / "progress.json"
XP_PER_LEVEL = 100


@dataclass
class Progress:
    xp: int = 0
    level: int = 1
    quizzes_taken: int = 0
    questions_correct: int = 0
    questions_answered: int = 0
    streak: int = 0
    last_active: str = ""
    lessons_completed: dict = field(default_factory=dict)
    challenges_completed: list = field(default_factory=list)
    practices_completed: list = field(default_factory=list)
    achievements: list = field(default_factory=list)
    challenges_attempted: int = 0

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

    def __init__(self, data_dir: Path = DATA_DIR, progress_file: Path | None = None):
        self.data_dir = Path(data_dir)
        self.progress_file = Path(progress_file) if progress_file else self.data_dir / "progress.json"
        self.progress: Progress = self._load()
        self._update_streak()

    def _load(self) -> Progress:
        if self.progress_file.exists():
            try:
                raw = json.loads(self.progress_file.read_text(encoding="utf-8"))
                allowed = {item.name for item in fields(Progress)}
                merged = {**asdict(Progress()), **{k: v for k, v in raw.items() if k in allowed}}
                return Progress(**merged)
            except (json.JSONDecodeError, TypeError, ValueError):
                backup = self.progress_file.with_suffix(".json.bak")
                self.progress_file.replace(backup)
                return Progress()
        return Progress()

    def save(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.progress_file.write_text(
            json.dumps(asdict(self.progress), indent=2) + "\n",
            encoding="utf-8",
        )

    def _update_streak(self) -> None:
        today = date.today().isoformat()
        if self.progress.last_active == today:
            return
        if self.progress.last_active:
            last = date.fromisoformat(self.progress.last_active)
            gap = (date.today() - last).days
            if gap == 1:
                self.progress.streak += 1
            elif gap > 1:
                self.progress.streak = 1
        else:
            self.progress.streak = 1
        self.progress.last_active = today

    def add_xp(self, amount: int) -> bool:
        self.progress.xp += amount
        new_level = 1 + self.progress.xp // XP_PER_LEVEL
        leveled_up = new_level > self.progress.level
        self.progress.level = new_level
        return leveled_up

    def record_quiz_answer(self, correct: bool) -> None:
        self.progress.questions_answered += 1
        if correct:
            self.progress.questions_correct += 1

    def record_quiz_completed(self) -> None:
        self.progress.quizzes_taken += 1

    def mark_lesson_complete(self, category: str, command: str) -> bool:
        completed = self.progress.lessons_completed.setdefault(category, [])
        if command in completed:
            return False
        completed.append(command)
        return True

    def category_percent(self, category: str, total: int | None = None) -> int:
        done = len(self.progress.lessons_completed.get(category, []))
        if not total:
            return 0
        return int(100 * done / total)

    def complete_challenge(self, challenge_id: str) -> bool:
        if challenge_id in self.progress.challenges_completed:
            return False
        self.progress.challenges_completed.append(challenge_id)
        return True

    def complete_practice(self, practice_id: str) -> bool:
        if practice_id in self.progress.practices_completed:
            return False
        self.progress.practices_completed.append(practice_id)
        return True

    def unlock_achievement(self, achievement_id: str) -> bool:
        if achievement_id in self.progress.achievements:
            return False
        self.progress.achievements.append(achievement_id)
        return True

    def log_event(self, kind: str, payload: dict | None = None) -> None:
        history_file = self.data_dir / "history.json"
        events: list[dict] = []
        if history_file.exists():
            try:
                loaded = json.loads(history_file.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    events = loaded
            except json.JSONDecodeError:
                events = []
        event = {"kind": kind, "at": datetime.now().isoformat(timespec="seconds")}
        if payload:
            event.update(payload)
        events.append(event)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        history_file.write_text(json.dumps(events, indent=2) + "\n", encoding="utf-8")

    @staticmethod
    def bar(value: float, total: float, width: int = 10) -> str:
        if total <= 0:
            return "░" * width
        ratio = max(0.0, min(1.0, value / total))
        filled = int(round(width * ratio))
        filled = min(width, max(0, filled))
        return "█" * filled + "░" * (width - filled)
