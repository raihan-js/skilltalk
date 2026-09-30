# Family Todo App

A simple shared to-do app for my family. The full build playbook is the **`family-todo-app` skill** (`.claude/skills/family-todo-app/SKILL.md`) —
load it for any work on this project.

@PROGRESS.md

## Commands
| What | Command |
|---|---|
| Install | `npm ci` |
| Run locally | `npm run dev` |
| Lint | `npm run lint` |
| Typecheck | `npm run typecheck` |
| Tests | `npm test` |
| Build | `npm run build` |

## How to work here
- **Owner's experience: Beginner.** Explain every technical word the first time you use it, with an everyday comparison. After each milestone add a short "What you learned" note (2–3 lines) linking to the playbook. Never assume I know where a setting or command is — give exact clicks or commands.
- One milestone at a time, on its own branch (`feat/…`, `fix/…`). Small commits. Never push to main — open a PR.
- Definition of done for ANY change: tests added/updated → lint + typecheck + tests + build green →
  `code-reviewer` agent → PR with plain-language description → PROGRESS.md updated.
- Bugs: use `/fix` (bug-loop protocol). A bug that survives one fix goes to the `debugger` agent.
- New features: use `/plan`. New library, service or infrastructure: ask the `architect` agent first,
  then the owner. Stay inside the tech stack in the skill.
- Secrets live only in `.env` (owner edits it). Add names to `.env.example`, tell the owner what to paste where.
- Ask the owner before anything that costs money, deletes data, or goes to production.

## Safety net (installed — don't bypass it)
Hooks in `.claude/settings.json` block dangerous commands and secret leaks, auto-format files, detect fix loops
and run a quality gate before you finish. Git hooks in `.githooks/` and GitHub CI enforce the same for every tool.
If a guardrail blocks you, follow its advice — never try to work around it.
