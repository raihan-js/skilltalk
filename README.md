# SkillTalk 🎙️ → 📄

**Talk about the app you want to build. Get a perfect `SKILL.md` your AI coding agent can follow —
plus the engineering safety net that stops AI-built projects from turning into slop.**

SkillTalk is an open-source, voice-first "project interviewer". You press a button and describe your idea out loud
("I want a to-do app for my family"). SkillTalk asks you smart follow-up questions — one at a time, in plain language,
with a friendly explanation for every technical choice — and turns the conversation into a ready-to-install
**Agent Skill** (`SKILL.md` + reference files) for Claude Code, Codex, Cursor, Gemini CLI, or any agent that reads
Markdown instructions.

Built for people who are **not engineers**: founders, designers, teachers, marketers, students.

### What every generated skill contains

- **The build plan** — features, stack (every choice explained), architecture, milestones with "test it by…".
- **An engineering foundation the agent installs itself (Milestone 0)** — Claude Code hooks that block destructive
  commands and secret leaks, auto-format, break fix loops and run a quality gate before "done"; helper agents
  (architect, test-writer, code-reviewer, debugger, security-auditor); commands (`/plan`, `/fix`, `/ship`,
  `/explain`, `/status`); git hooks; GitHub CI/CD, Dependabot, PR templates, branch protection.
- **Plain-language playbooks** — how to work with AI, how shipping works (git, PRs, CI/CD, environments, backups),
  how scaling works (vertical, horizontal, queues, Docker, Kubernetes) — each marked **NOW / LATER / NOT NEEDED**
  for *this* project's scale, so the AI never over-engineers.

See `docs/ENGINEERING_FOUNDATION.md` for why each guardrail exists.

---

## How it works (30-second version)

```
 🎤 You speak ──► Speech-to-Text (open model, runs locally) ──► Interviewer AI
                                                                   │  asks the next question
                                                                   │  explains options in plain words
                                                                   ▼
                                                   Structured project spec (JSON)
                                                                   │
                                                                   ▼
                                          📄 SKILL.md  +  references/  +  AGENTS.md
                                                                   │
                        ┌──────────────────────────┬───────────────┴──────────┐
                        ▼                          ▼                          ▼
                 Download .zip          `skilltalk install` CLI        MCP server (agent pulls it)
```

## Quick start (developer)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example ../.env          # pick your LLM (local Ollama or an API)
uvicorn app.main:app --reload --port 8000
# open http://localhost:8000
pytest -q                           # interview, rendering, hooks, git safety, bootstrap
```

No API key and no GPU? Set `LLM_PROVIDER=mock` and `STT_PROVIDER=browser` in `.env` — the whole flow still works
(scripted questions + your browser's built-in speech recognition) so you can build the UI first.

## Repo map

| Path | What it is |
|---|---|
| `AGENTS.md` | **Start here if you're an AI agent.** Rules, architecture, commands. |
| `CLAUDE.md` | Claude Code–specific notes (imports `AGENTS.md`). |
| `docs/VISION.md` | The idea, who it's for, what makes it different. |
| `docs/ARCHITECTURE.md` | Components and data flow. |
| `docs/VOICE_PIPELINE.md` | Which speech model, and the truth about fine-tuning. |
| `docs/INTERVIEW_DESIGN.md` | How the interviewer asks questions and explains things. |
| `docs/SKILL_FORMAT.md` | What the generated skill looks like and where it gets installed. |
| `docs/ENGINEERING_FOUNDATION.md` | The anti-slop layer: hooks, guardrails, CI/CD, scale tiers. |
| `docs/ROADMAP.md` | Milestones and realistic timeline. |
| `interview/` | Question bank (YAML) + interviewer system prompt. |
| `templates/skill/` | Skill templates: `SKILL.md`, playbooks, engineering topics, Milestone 0 setup + bootstrap. |
| `templates/project/` | Files installed into the user's project: hooks, settings, agents, commands, git hooks, CI. |
| `backend/` | FastAPI server: STT, interview engine, skill renderer. |
| `web/` | Minimal web UI (push-to-talk, option chips with tooltips). |
| `mcp-server/` | MCP server so coding agents can list/fetch/install your skills. |
| `cli/` | `skilltalk install` / `bootstrap` — installs skills and their engineering foundation. |
| `examples/` | Example generated skill (a family to-do app) — open it to see the full output. |
| `training/` | Phase-4 (optional) speech model fine-tuning plan. |

## License

[Apache-2.0](LICENSE)
