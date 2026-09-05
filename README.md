# LinuxLab

### Interactive Linux Learning Environment

Learn Linux. Practice commands. Complete challenges. Build real terminal skills.

**Current version: 1.0** — a working terminal product. You type real Linux commands in a jailed sandbox, the filesystem changes, and LinuxLab validates the result.

---

## 1. Project overview

LinuxLab is a terminal-based Linux learning app written in Python. It teaches beginner commands through short lessons, then asks you to type the command, then sends you into a jailed sandbox to complete a realistic filesystem mission. Progress is stored locally as JSON.

This is a portfolio-quality CLI product, not a one-file tutorial script.

## 2. Why LinuxLab?

Most people learn Linux by memorizing a cheat sheet and forgetting it a week later. LinuxLab uses a tighter loop:

```
Learn -> Practice -> Challenge -> Validate -> Earn XP -> Track Progress
```

You see the idea, type the command, then prove it against a real (but safe) filesystem.

## 3. Features

- Menu-driven CLI (`python3 linuxlab.py`)
- **Continue** — picks the next unfinished lesson, practice, or challenge
- **Learn** — beginner lessons, then optional try-it in the sandbox
- **Practice** — guided tasks that run real sandbox commands (`mkdir` actually creates a folder)
- **Challenges** — missions inside `~/linuxlab-sandbox/`
- **Lab** — free-play terminal with a starter home layout
- **Quiz** — multiple-choice bank with explanations
- **Progress** — XP, levels, streaks, category bars, achievements
- **Safety** — allow-listed commands only; paths cannot leave the sandbox
- Standard library only (Python 3.9+)

## 4. Demo

```
╔════════════════════════════╗
║         LinuxLab           ║
╚════════════════════════════╝

1. Continue
2. Learn
3. Practice
4. Challenges
5. Lab
6. Quiz
7. Progress
8. Exit

Choose:
```

Challenge example:

```
Mission:

Create this structure:

project/
├── src/
├── docs/
└── README.md

/$ mkdir project
/$ mkdir project/src
/$ mkdir project/docs
/$ touch project/README.md
/$ done

PASS
+40 XP
```

## 5. Installation

```bash
git clone https://github.com/Adi-who/linuxlab.git
cd linuxlab
python3 linuxlab.py
```

No extra packages are required for the current version.

## 6. Usage

```bash
python3 linuxlab.py
python3 linuxlab.py continue
python3 linuxlab.py lab
python3 linuxlab.py practice
python3 linuxlab.py --sandbox /tmp/linuxlab-sandbox
```

Inside a challenge:

- type normal beginner commands (`mkdir`, `touch`, `mv`, ...)
- `hint` shows the next hint
- `done` validates the filesystem
- `quit` leaves the mission
- `help` lists allowed commands

LinuxLab never runs arbitrary shell pipelines. Pipes, `&&`, and absolute system paths are rejected.

## 7. Commands covered

| Category | Commands |
| --- | --- |
| Navigation | `pwd`, `ls`, `cd` |
| Files & Directories | `mkdir`, `rmdir`, `touch`, `cp`, `mv`, `rm` |
| File Management | `cat`, `head`, `tail`, `grep`, `find` |
| Permissions | `chmod` |
| Processes | `ps`, `top`, `kill` |
| Networking | `ping`, `curl` |
| Package Management | `apt` |
| System Information | `whoami`, `uname`, `df`, `du` |
| Git | `git status`, `git add`, `git commit` |

The sandbox currently simulates the first four categories so practice stays safe.

## 8. Challenges

Ten filesystem missions ship in `challenges/`:

- Starter Project
- Backup Notes
- Empty Drafts
- Copy Then Rename
- Clean the Trash
- Write a README
- Nested Workspace
- Make it Executable
- Log Hunt
- Home Layout

Each challenge seeds files inside the sandbox, then validates the resulting tree (existence, location, content, permissions, counts).

## 9. Progress system

Progress stays on your machine:

```
~/.linuxlab/
├── progress.json
└── history.json
```

Tracked fields include XP, level, quiz accuracy, streaks, completed lessons, completed challenges, and achievements.

Leveling uses 100 XP per level. Typical rewards:

- Lesson: +5 XP
- Practice: +10 to +15 XP
- Quiz answer: +30 XP
- Challenge: +30 to +60 XP

## 10. Architecture

```
linuxlab/
├── linuxlab.py
├── commands/            lesson JSON
├── challenges/          mission JSON
├── data/                quiz + practice JSON
├── core/
│   ├── learn.py
│   ├── practice.py
│   ├── practice_mode.py
│   ├── quiz.py
│   ├── challenges.py
│   ├── sandbox.py
│   ├── session.py
│   ├── lab.py
│   ├── validator.py
│   ├── progress.py
│   └── ui.py
└── tests/
```

Lessons and missions live in JSON so new content can be added without rewriting Python.

## 11. Tech stack

Python 3.9+ standard library: `argparse`, `pathlib`, `json`, `shutil`, `unittest`, `dataclasses`.

`rich` is intentionally not a dependency yet.

## 12. Testing

```bash
python3 -m unittest discover -s tests -v
```

GitHub Actions runs the same suite on Python 3.9, 3.11, and 3.12.

## 13. Roadmap

- [x] **V0.1** — CLI menu, Learn, Quiz, basic progress, JSON persistence
- [x] **V0.2** — Challenge engine, categories, difficulty, validation, XP
- [x] **V0.3** — Persistent XP, levels, accuracy, streaks, achievements
- [x] **V0.4** — Safe sandbox, filesystem missions, state validation
- [x] **V1.0** — Real sandbox practice, free Lab, Continue path, CLI subcommands, tests

## 14. Contributing

See `CONTRIBUTING.md`.

## 15. License

[MIT](LICENSE)
