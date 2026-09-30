# CLAUDE.md

@AGENTS.md

## Claude Code specifics

- Use plan mode for anything touching more than 3 files; show the plan in plain language first.
- Custom commands for this repo live in `.claude/commands/`:
  - `/next-step` — pick the next unchecked item in `docs/ROADMAP.md` Phase checklist and do only that.
  - `/try-skill` — run the mock demo and install the generated skill into `./.claude/skills/` to test it here.
- After changing anything in `templates/`, regenerate `examples/family-todo-app/` with `python -m app.demo --write`.
- Changing a generated hook? Read `docs/ENGINEERING_FOUNDATION.md` first and run `pytest tests/test_foundation.py`.
- Dogfooding: SkillTalk's own output is a Claude Code skill — if a generated skill feels wrong when you load it,
  fix the template, not the example.
