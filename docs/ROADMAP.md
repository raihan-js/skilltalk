# Roadmap & realistic timeline

Assumes one person building with an AI coding agent, a few focused hours a day.

| Phase | Goal | Time | Done when |
|---|---|---|---|
| **0. Setup** | Repo runs locally, mock mode works | ½ day | `uvicorn` starts, mock interview produces a SKILL.md |
| **1. MVP (text + browser voice)** | Full interview → skill, in the browser | 3–5 days | You can talk to it (browser STT) and download a skill zip that Claude Code loads |
| **2. Local open STT + real LLM** | faster-whisper + Ollama / API | 3–5 days | Works offline; tech-word accuracy checked on 30 of your own clips |
| **3. Distribution** | CLI `install`, MCP server, polished UI, docs site, demo video | 1–2 weeks | `pipx install skilltalk` → `skilltalk talk` works in a terminal |
| **4. Launch (open source)** | GitHub public, Show HN / Reddit / X, Hugging Face Space demo | 2–3 days | First 10 outside users generate skills |
| **5. Voice streaming + TTS** | Real conversation feel (WebSocket, VAD, Kokoro/Piper) | 1–2 weeks | < 1.5 s from you stop talking to it replying |
| **6. Fine-tuned STT (optional)** | Better tech-term accuracy | 2–3 weeks incl. data | Beats base model on your eval set |
| **7. Desktop app** | Tauri wrapper for Win/Mac/Linux | 1–2 weeks | Installer on GitHub Releases |

**Usable, open-sourced MVP: ~2–3 weeks. Polished voice + desktop: ~2 months. Fine-tuning is last, not first.**

## Phase 1 checklist (give these to your agent one at a time)

- [ ] Mock interview end-to-end via API (`pytest` passes)
- [ ] Web UI: start session, show question + option chips with tooltips
- [ ] Browser speech recognition → editable transcript → send
- [ ] Progress bar of covered topics
- [ ] Skill preview panel + download zip
- [ ] "Pick for me" applies default + reason
- [ ] Final readback summary with "change something" loop

## Engineering foundation backlog

- [ ] `skilltalk doctor` — checks a project: hooks installed, CI green, branch protected, backups on, secrets clean.
- [ ] More stack profiles (Django, Rails, SvelteKit, Laravel) with their own CI + quality gate.
- [ ] Rules files for more agents (Windsurf, Copilot instructions, Gemini `GEMINI.md`).
- [ ] Playwright end-to-end starter test generated from the must-have features.
- [ ] Cost estimator per host at the chosen scale tier.
- [ ] "Re-tier" command: when users grow, regenerate the playbook and show what moved from LATER to NOW.

## Ideas backlog

- Templates by app type (SaaS, marketplace, mobile game, AI chatbot, internal tool) that pre-weight questions.
- "Explain like I'm 12" toggle for explanations.
- Export to AGENTS.md / Cursor rules / GEMINI.md from the same spec.
- Public gallery of anonymised example skills.
- Cost estimator table per hosting provider.
- Import an existing repo → interview only about the *change* you want.
