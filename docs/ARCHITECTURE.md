# Architecture

## Components

```
┌──────────────────────── web/ (browser) ─────────────────────────┐
│ Push-to-talk button · live transcript (editable) · option chips │
│ with tooltips · progress bar (topics covered) · skill preview   │
└───────────────┬───────────────────────────────▲─────────────────┘
                │ audio (webm) or text          │ next turn JSON
                ▼                               │
┌──────────────────────── backend/ (FastAPI) ─────────────────────┐
│ stt.py        Speech → text (faster-whisper / browser / API)    │
│ interview.py  Interview engine (state machine + LLM turns)      │
│ llm.py        OpenAI-compatible client (Ollama, APIs) + mock    │
│ renderer.py   Spec → skill folder: SKILL.md, playbooks, setup/  │
│ project_profile.py  stack profile · scale tier · explain style  │
│ store.py      Sessions + finished skills on disk (~/.skilltalk) │
└───────────────┬─────────────────────────────────────────────────┘
                │ writes skills to ~/.skilltalk/skills/<name>/
                ▼
┌──── mcp-server/ ────┐     ┌──── cli/ ──────────────────────────┐
│ list_skills         │     │ skilltalk install <name|zip>       │
│ get_skill           │     │   --target claude|project|agents   │
│ install_skill       │     └────────────────────────────────────┘
└─────────────────────┘
```

## The key design decision: hybrid interview engine

A pure "let the LLM chat" approach forgets topics and rambles. A pure form is boring and can't adapt.
SkillTalk uses both:

- **Question bank (`interview/question_bank.yaml`)** = the *checklist* of slots a good skill needs
  (idea, users, features, platform, frontend, backend, data, auth, AI, hosting, scale, money, budget, timeline…).
  Each slot has plain-language options, explanations, `hotwords` for STT, a safe default, and an optional
  `ask_if` condition (e.g. only ask about AI models if the app uses AI).
- **LLM** = the *conversation*: it reads what the user said, extracts values for *any* slots mentioned
  (users often answer 3 questions at once), rephrases the next question naturally, and explains options
  for this specific project.
- **Engine** = the *referee*: picks which slot is next (first unfilled + relevant), validates LLM JSON,
  and falls back to the question bank wording if the LLM misbehaves. With `LLM_PROVIDER=mock` it runs on the
  bank alone — useful for UI dev and tests.

## Turn contract (LLM → engine)

```json
{
  "captured": { "frontend": "Next.js", "users_count": "about 50 family members" },
  "say": "Nice — a family to-do app. Next: where should the data live?",
  "question_slot": "database",
  "options": [
    {"label": "Supabase", "explain": "a ready-made online database with logins built in; free to start"},
    {"label": "SQLite", "explain": "a single file on one computer; simplest, but only for you"},
    {"label": "Pick for me", "explain": "I'll choose the safest option and tell you why"}
  ],
  "done": false
}
```

## Data flow

1. `POST /api/sessions` → new session; returns first question.
2. `POST /api/sessions/{id}/audio` (multipart) → STT → transcript returned for confirmation.
3. `POST /api/sessions/{id}/answer` `{text}` → engine turn → next question (or `done`).
4. `GET  /api/sessions/{id}/skill` → rendered preview (markdown).
5. `GET  /api/sessions/{id}/skill.zip` → downloadable skill folder. Also saved to `~/.skilltalk/skills/`.

## Later: streaming voice mode

Swap steps 2–3 for a WebSocket: stream mic chunks, VAD detects end-of-turn, server streams back text + TTS audio.
Keep the same engine; only the transport changes.

## Desktop / terminal integration (Phase 3)

- **CLI** (`cli/skilltalk.py`): `skilltalk talk` opens mic in the terminal, runs the same engine, writes the skill
  straight into `./.claude/skills/`. This is the "voice for any coding agent" story.
- **MCP server**: lets Claude Code/Cursor/etc. call `list_skills`/`get_skill`/`install_skill`.
- **Desktop app**: wrap `web/` + backend with Tauri (small, cross-platform: Windows, macOS, Linux).
