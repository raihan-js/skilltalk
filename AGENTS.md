# AGENTS.md — instructions for AI coding agents working on SkillTalk

You are helping build **SkillTalk**: an open-source, voice-first interviewer that turns a spoken app idea into an
Agent Skill (`SKILL.md` folder) for AI coding agents. Read `docs/VISION.md` and `docs/ARCHITECTURE.md` first.

## The human you work with

The maintainer may not be a professional engineer. So:
- Explain what you're doing in 1–3 plain sentences before big changes. No jargon without a short explanation.
- Work in **small steps**; after each step, tell them exactly how to test it (a command or a click).
- **Ask before** adding a dependency that costs money, needs a GPU, or requires an account/API key.
- Never delete files or rewrite large parts without saying so first.

## Stack (keep it boring)

- **Backend:** Python 3.11+, FastAPI, Pydantic v2, Jinja2, PyYAML, httpx. Tests: pytest.
- **STT:** `faster-whisper` (optional import — the app must run without it), browser Web Speech API fallback.
- **LLM:** any OpenAI-compatible `/chat/completions` endpoint (Ollama, vLLM, hosted APIs). `mock` provider for dev.
- **Frontend:** plain HTML + CSS + vanilla JS in `web/` (no build step) for v1. Don't introduce React/Next
  unless the maintainer asks.
- **MCP server:** Python `mcp` SDK (FastMCP).
- Config through environment variables only (`.env`, see `.env.example`). No secrets in code.

## Commands

```bash
cd backend && pip install -r requirements.txt           # install
uvicorn app.main:app --reload --port 8000               # run (serves web/ at /)
pytest -q                                               # tests (must pass before you say "done")
python -m app.demo                                      # run a scripted mock interview → prints SKILL.md
python -m app.demo --write                              # regenerate examples/family-todo-app/
python ../mcp-server/server.py                          # run MCP server (stdio)
python ../cli/skilltalk.py install <skill-dir> --target claude
python ../cli/skilltalk.py bootstrap <skill-dir> --project-dir /tmp/try   # install the foundation into a test project
```

## Where things live

- `interview/question_bank.yaml` — the slots the interview must cover. **Add questions here, not in Python.**
- `interview/system_prompt.md` — interviewer persona + JSON turn contract.
- `templates/skill/SKILL.md.j2` — the generated skill's main file. `templates/skill/references/*.j2` — playbooks.
- `templates/skill/engineering_topics.yaml` — engineering concepts + NOW/LATER/NOT NEEDED per scale tier.
- `templates/skill/setup/` — `INSTALL.md.j2` (Milestone 0) and `bootstrap.py` (installs the foundation).
- `templates/project/` — every file that ends up in the user's project: hooks, settings, subagents, commands,
  git hooks, CI variants, CLAUDE/AGENTS/PROGRESS templates. `.j2` files are rendered, others copied as-is.
- `backend/app/interview.py` — engine (slot selection, merging captured values, LLM fallback).
- `backend/app/project_profile.py` — stack profile, scale tier, explanation style, quality-gate checks.
- `backend/app/renderer.py` — spec → skill folder / zip.
- `examples/family-todo-app/` — golden example output. Regenerate it whenever templates change.
- `docs/ENGINEERING_FOUNDATION.md` — why each guardrail exists. Read before touching hooks.

## Rules for code

1. The engine must **never crash on bad LLM output**: validate JSON, fall back to the question bank.
2. Everything must work with `LLM_PROVIDER=mock` and without `faster-whisper` installed (tests rely on this).
3. Generated `SKILL.md` must have valid YAML frontmatter as the very first line (`---`), with `name`
   (lowercase, hyphens, ≤ 64 chars, same as folder name) and `description` (what + when to use).
   Keep the SKILL.md body under ~500 lines; push detail into `references/`.
4. User-facing text (questions, explanations) must be understandable by a non-engineer. Brackets for quick
   explanations: `Supabase (a ready-made online database with logins built in)`.
5. Audio is never persisted unless `SAVE_AUDIO=true`.
6. Add or update a test for every behaviour change in `backend/tests/`.
7. **Generated hooks** (`templates/project/.claude/hooks/`) use the Python standard library only, must never
   crash on unexpected input, must explain *why* and *what to do instead* when blocking, and must never be able
   to loop forever. Every new guard rule gets a "blocks" and an "allows" test in `tests/test_foundation.py`.
8. Generated playbooks must stay jargon-free; explain every term with an everyday analogy.

## Definition of done for any task

- Tests pass (`pytest -q`), app starts, you've told the maintainer how to see the change.
- Docs updated if behaviour or config changed.
