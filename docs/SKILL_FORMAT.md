# Skill format (what SkillTalk outputs)

SkillTalk outputs an **Agent Skill** — the open format used by Claude Code and a growing list of other agents:
a folder containing `SKILL.md` (YAML frontmatter + Markdown instructions) plus supporting files — here, a full
engineering foundation the coding agent installs itself (see `docs/ENGINEERING_FOUNDATION.md`).

```
family-todo-app/
├── SKILL.md                        # frontmatter + build playbook; starts with Milestone 0
├── references/
│   ├── ai-workflow.md              # how to build with AI without creating a mess (owner + agent)
│   ├── engineering-playbook.md     # git, CI/CD, environments, scaling, Kubernetes… NOW / LATER / NOT NEEDED
│   ├── guardrails.md               # rules, bug-loop protocol, definition of done
│   ├── shipping-checklist.md       # launch checklist tailored to the answers
│   ├── INSTALL.md                  # copy of setup/INSTALL.md (lands in docs/skilltalk/ for any agent)
│   ├── decisions.md · glossary.md · interview-transcript.md
└── setup/
    ├── INSTALL.md                  # Milestone 0, step by step (the agent does it)
    ├── bootstrap.py                # installs files/ into the project, merging safely
    └── files/                      # hooks, settings, subagents, commands, git hooks, CI, templates, CLAUDE/AGENTS/PROGRESS
```

## Frontmatter

```yaml
---
name: family-todo-app          # lowercase + hyphens, ≤ 64 chars, MUST equal folder name
description: "Build and extend \"Family Todo App\": … Use when working on this project's features, screens,
  data, tech stack, setup, testing or deployment."
---
```

Only `name` and `description` are used because they're part of the open standard and load everywhere.
The `description` says **what + when**, which is how the agent decides to load the skill.

## Where it gets installed

| Target | Result | Command |
|---|---|---|
| Claude Code, all projects | `~/.claude/skills/<name>/` — agent runs Milestone 0 in the project | `skilltalk install <dir> --target claude` |
| Claude Code, one project | `<project>/.claude/skills/<name>/` (+ `--bootstrap` to install the foundation now) | `--target project --project-dir .` |
| Other agents (Codex, Cursor, Gemini CLI…) | foundation installed into the project: `AGENTS.md`, git hooks, CI, `docs/skilltalk/` | `--target agents --project-dir .` |
| Any | just the foundation | `skilltalk bootstrap <dir> --project-dir .` |

## What adapts to the interview

| Answer | Changes |
|---|---|
| Experience level | How the agent explains (every term + "What you learned" notes ↔ concise) |
| Users + reliability | Scale tier → which playbook topics are NOW / LATER / NOT NEEDED, launch checklist items |
| Platform / frontend / mobile toolkit | Stack profile: scaffold command, lint/test/build commands, CI variant, env var prefix |
| AI builder | Claude Code gets hooks/agents/commands; Cursor gets a rules file; everyone gets git hooks + CI + AGENTS.md |
| Database, auth, AI, payments, privacy | `.env.example`, milestones, security checks, launch checklist |
