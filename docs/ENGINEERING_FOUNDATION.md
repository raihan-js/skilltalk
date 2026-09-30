# The engineering foundation (SkillTalk's anti-slop layer)

## The problem we're solving

Non-engineers can now build software with AI agents, but most projects end the same way: a pile of code nobody
understands, bugs that multiply with every "fix", leaked API keys, surprise bills, and over-engineered setups
(Kubernetes for 20 users) copied from tutorials. The cause isn't the AI — it's that the **engineering process**
professionals take for granted (version control, reviews, tests, CI/CD, environments, scaling judgment) is
invisible to beginners, so nobody asks the AI to follow it.

SkillTalk fixes that by shipping the process **inside every generated skill**, and having the coding agent install
and enforce it itself. The owner doesn't need to know what a pre-push hook is; they just never get burned by
pushing broken code to production.

## Three layers of defence

| Layer | Works with | What it does |
|---|---|---|
| **1. Agent layer** — Claude Code hooks, settings, subagents, commands | Claude Code | Blocks dangerous actions *before* they happen, auto-formats, detects fix loops, runs a quality gate before the agent may say "done", gives the agent specialised reviewers and a debugging protocol |
| **2. Git layer** — `.githooks/` | Every tool and human | Secret scan + lint before each commit; no direct pushes to main |
| **3. Platform layer** — GitHub CI, Dependabot, branch protection, host previews | Everyone | Every change is checked by a robot before merge; preview links for testing; production deploys only from main |

Plus the **knowledge layer**: plain-language playbooks tailored to the project (what to do NOW, LATER, or never).

## What's generated (per project, from the interview)

```
<skill>/setup/
├── INSTALL.md        Milestone 0 steps the agent performs itself (tools check → skeleton → bootstrap → verify →
│                     GitHub + branch protection → hosting → explain to owner)
├── bootstrap.py      Installs files/ into the project. Never overwrites; merges settings/.gitignore/CLAUDE/AGENTS
└── files/
    ├── CLAUDE.md, AGENTS.md, PROGRESS.md, .gitignore, .env.example, .editorconfig
    ├── .claude/settings.json          hooks wiring + deny reading .env
    ├── .claude/quality-gate.json      stack-specific checks for the stop hook
    ├── .claude/hooks/                 guard_bash · guard_files · post_edit · stop_gate · session_start
    ├── .claude/agents/                architect · test-writer · code-reviewer · debugger · security-auditor
    ├── .claude/commands/              /plan · /fix · /ship · /explain · /status
    ├── .githooks/                     pre-commit · pre-push
    ├── .github/workflows/ci.yml       node | python | flutter variant
    ├── .github/dependabot.yml, pull_request_template.md, ISSUE_TEMPLATE/bug_report.md
    └── .cursor/rules/project.mdc      (only when the owner uses Cursor)
<skill>/references/
    ai-workflow.md · engineering-playbook.md · guardrails.md · shipping-checklist.md · decisions · glossary · transcript
```

## The hooks, and the failure each one prevents

| Hook (event) | Prevents |
|---|---|
| `session_start.py` (SessionStart) | Context loss between sessions — injects PROGRESS.md + branch + rules |
| `guard_bash.py` (PreToolUse: Bash) | Destroyed work & leaks — recursive deletes of root/home, force-push, pushing to main, `--no-verify`, `reset --hard`, `curl \| sh`, sudo, DB drops/resets, printing `.env`, manual prod deploys |
| `guard_files.py` (PreToolUse: Edit/Write) | Secrets in code (key patterns), editing `.env`, hand-editing lockfiles, the agent weakening its own guardrails |
| `post_edit.py` (PostToolUse) | Style drift (auto-format) and **fix loops** — after 6 edits to one file it interrupts with the bug-loop protocol |
| `stop_gate.py` (Stop) | "It's done!" when it isn't — runs lint/typecheck/tests on changed code; sends the agent back **once**, never loops forever |

Design rules for hooks: standard-library Python only; every block message says **why** and **what to do
instead** (so the agent recovers without the owner); checks only run once the project has them (a new empty repo
isn't blocked); anything that could loop has an exit (`stop_hook_active`).

## The scale tier & engineering playbook

`backend/app/project_profile.py` derives a tier from the interview:

- users `Under 100` → **Starter**, `100 to 10,000` → **Growth**, `More than 10,000` → **Scale**
- reliability `Business-critical` bumps it up one tier

`templates/skill/engineering_topics.yaml` holds ~20 topics (git, PRs, CI, CD, environments, secrets, tests,
migrations, backups, monitoring, security, rate limits, CDN/caching, vertical scaling, horizontal scaling, queues,
Docker, Kubernetes, cost control, rollback, accessibility/SEO). Each has an analogy, a plain explanation and a
NOW / LATER / NOT NEEDED verdict per tier. The playbook explicitly tells the agent what **not** to build — the
cheapest way to prevent over-engineering.

## Extending it

- New guardrail rule → `templates/project/.claude/hooks/guard_bash.py` `RULES` + a test in
  `backend/tests/test_foundation.py` (both "blocks" and "allows" cases).
- New stack → `project_profile.py` (`detect_profile`, `quality_gate`, `SCAFFOLD`) + a `ci.<id>.yml`.
- New engineering topic → `engineering_topics.yaml` (keep it jargon-free).
- New coding agent → decide which files it gets in `renderer._project_files`, add its rules file template.
