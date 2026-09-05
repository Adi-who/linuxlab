# 🐧 LinuxLab
### Interactive Linux Learning Environment

> Learn Linux. Practice commands. Complete challenges. Build real terminal skills.

**Current version: 0.1 (MVP)** — see [Roadmap](#roadmap) for where this is headed.

---

## 1. Project Overview

LinuxLab is a terminal-based Linux learning app written in Python. It teaches
Linux commands through short lessons and then tests retention with an
interactive quiz, all while tracking XP and levels so progress feels
tangible. It's built as a real, incrementally-shipped portfolio project
rather than a single-sitting script.

## 2. Why LinuxLab?

Most people learn Linux by memorizing commands from a cheat sheet and
forgetting them a week later. LinuxLab pairs each concept with immediate
practice and feedback — the same "learn, then do" loop that makes flashcard
apps and coding platforms effective — but scoped to the terminal.

## 3. Features (V0.1)

- Clean, menu-driven CLI
- **Learn mode** — 15 beginner Linux commands across 4 categories, explained
  from zero (meaning, purpose, syntax, examples, related commands)
- **Quiz mode** — 15-question multiple-choice bank, sampled randomly each run
- **Progress tracking** — XP, levels, quiz accuracy, and daily streaks
- **JSON persistence** — progress is saved to `~/.linuxlab/progress.json`
  and reloaded automatically next time you run LinuxLab
- Command lesson data lives in JSON, not hard-coded in Python, so new
  commands can be added without touching the app logic

## 4. Demo

```
╔════════════════════════════╗
║         🐧 LinuxLab        ║
╚════════════════════════════╝

1. Learn
2. Quiz
3. Progress
4. Exit

Choose:
```

*(Screenshots/GIF coming as the terminal UI is polished toward V1.0.)*

## 5. Installation

LinuxLab requires only Python 3.9+ and the standard library — no
dependencies to install for V0.1.

```bash
git clone https://github.com/Adi-who/linuxlab.git
cd linuxlab
```

## 6. Usage

```bash
python linuxlab.py
```

Navigate the menu with the number keys. Progress saves automatically when
you exit or finish a quiz.

## 7. Commands Covered (V0.1)

| Category           | Commands                                              |
|---------------------|--------------------------------------------------------|
| Navigation          | `pwd`, `ls`, `cd`                                       |
| Files & Directories | `mkdir`, `rmdir`, `touch`, `cp`, `mv`, `rm`              |
| File Management     | `cat`, `head`, `tail`, `grep`, `find`                    |
| Permissions         | `chmod`                                                  |

## 8. Challenges

Not yet implemented — the challenge engine and filesystem sandbox arrive in
V0.2–V0.4 (see [Roadmap](#roadmap)).

## 9. Progress System

Progress is stored locally as JSON — nothing leaves your machine.

```
~/.linuxlab/
└── progress.json
```

```json
{
  "xp": 60,
  "level": 1,
  "quizzes_taken": 1,
  "questions_correct": 2,
  "questions_answered": 5,
  "streak": 1,
  "last_active": "2026-09-05"
}
```

Leveling up requires 100 XP per level; each correct quiz answer earns 30 XP.

## 10. Architecture

```
linuxlab/
│
├── linuxlab.py          # CLI entry point and menu loop
├── README.md
├── requirements.txt
├── LICENSE
│
├── commands/             # Lesson data (Learn mode)
│   ├── navigation.json
│   ├── files.json
│   └── permissions.json
│
├── data/
│   └── quiz_questions.json
│
├── core/
│   ├── learn.py           # Loads & formats lessons
│   ├── quiz.py             # Quiz engine
│   └── progress.py         # XP/level/streak tracking + JSON persistence
│
└── tests/
    └── test_progress.py
```

## 11. Tech Stack

Python standard library only: `json`, `pathlib`, `dataclasses`, `unittest`.
`rich` is planned as an optional dependency once the terminal UI is
polished further — not added until it earns its place.

## 12. Testing

```bash
python -m unittest discover -s tests -v
```

8 unit tests currently cover XP accumulation, leveling thresholds, accuracy
calculation, save/reload persistence, and recovery from a corrupted
progress file.

## 13. Roadmap

- [x] **V0.1** — CLI menu, Learn mode, Quiz mode, basic progress, JSON persistence
- [ ] **V0.2** — Challenge engine, categories, difficulty levels, answer validation
- [ ] **V0.3** — Achievements, category-level progress bars, richer streak logic
- [ ] **V0.4** — Safe filesystem sandbox, real filesystem challenges, state validation
- [ ] **V1.0** — 50+ challenges, 100+ commands, polished terminal UI (Rich),
      automated tests + GitHub Actions, screenshots/GIFs, contribution guide

## 14. Contributing

Contributions are welcome once the V0.2 challenge engine lands. For now,
feel free to open issues for bugs or suggest additional beginner-friendly
commands and quiz questions via pull request against the `commands/` or
`data/` JSON files.

## 15. License

[MIT](LICENSE)
