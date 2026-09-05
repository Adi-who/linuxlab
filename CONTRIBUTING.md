# Contributing to LinuxLab

Thanks for helping people learn Linux.

## Ways to contribute

- Add a beginner command lesson in `commands/*.json`
- Add a practice task in `data/practice.json`
- Add a sandbox challenge in `challenges/*.json`
- Add a quiz question in `data/quiz_questions.json`
- Improve tests in `tests/`

## Lesson JSON

```json
{
  "command": "mkdir",
  "category": "Files & Directories",
  "meaning": "Make Directory",
  "description": "Creates a new directory.",
  "syntax": "mkdir [directory]",
  "examples": ["mkdir projects"],
  "related": ["rmdir", "ls"],
  "difficulty": "beginner"
}
```

## Challenge JSON

Keep every path inside the sandbox. Prefer filesystem checks (`file`, `dir`, `missing`, `content`, `permissions`) over guessing a single command string.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

Please include a test when you change validation, sandbox commands, or progress logic.

## Style

- Python 3.9+
- Standard library only unless a dependency earns its place
- Small functions, type hints where they help
- No command should be able to leave the sandbox
