# Vision

## The problem

Non-technical people now *can* build software with AI coding agents (Claude Code, Codex, Cursor, Gemini CLI…).
But they hit the same wall every time: **the agent is only as good as the instructions it gets.**

- They don't know what to ask for ("framework? database? auth? what's a backend?").
- They don't like typing long specs. They'd rather *talk it through*, like with a freelance developer.
- The agent guesses, picks something random, and the project drifts or breaks halfway.

## The product

A voice-first interviewer that behaves like a patient senior engineer + product manager sitting next to you:

1. **You describe the idea** out loud, messily. That's fine.
2. **It interviews you** — one question at a time, adapting to your answers, skipping what's irrelevant.
3. **Every technical choice comes with options explained in plain words**, e.g.
   > *Where should your data live?*
   > • **Supabase** *(a ready-made online database + logins; free to start, easiest)*
   > • **SQLite** *(a single file on your computer; perfect for personal apps)*
   > • **"You pick for me"** *(I'll choose the safest option and tell you why)*
4. **It produces a skill**: `SKILL.md` + `references/` that tells your coding agent exactly what to build,
   in what order, with which tools, and *how to talk to you* (plain language, ask before paid services…).
5. **One click/command to install** it into Claude Code or any other agent.

## Who it's for

- **Primary:** non-engineers building their first or second app with an AI agent.
- **Secondary:** engineers who want a fast "voice brain-dump → structured spec" before starting a project.
- **Tertiary:** teachers/bootcamps using it to teach how software is planned.

## Why this stands out (vs. existing skill makers and spec generators)

| Existing tools | SkillTalk |
|---|---|
| Text forms / chat, you must know what to type | **Voice-first**, conversational, turn-taking |
| Generic skill templates | **Project-specific** skill built from *your* answers |
| Assume you know tech words | **Every option explained** (bracket notes + tooltips + "why this matters") |
| Stops at "what do you want?" | Also covers **users, scale, money, costs, hosting, AI usage, privacy** |
| Output = one file | Output = **skill folder** + decision log + glossary + build milestones |
| Cloud-only | **Runs fully local** (open STT + local LLM via Ollama) — privacy by default |
| Copy/paste to install | **CLI + MCP server** — your agent can fetch/update the skill itself |
| A spec, then you're on your own | **An engineering foundation the agent installs itself**: safety hooks, guardrails, reviewer/debugger agents, git hooks, CI/CD, branch protection |
| Assumes you know how software is shipped | **Plain-language playbooks** (AI workflow, git/PRs, CI/CD, environments, backups, vertical vs. horizontal scaling, Kubernetes) tailored to *your* scale: NOW / LATER / NOT NEEDED |

### The anti-slop promise

Most AI-built apps fail not because the AI can't code, but because nobody asked it to follow an engineering
process: tests, reviews, small steps, protected main branch, no secrets in code, and *no over-engineering*.
SkillTalk ships that process inside every skill and has the agent enforce it — see `ENGINEERING_FOUNDATION.md`.
The result: no endless fix loops, no leaked keys, no broken production, no Kubernetes for 20 users.

### Signature features (the "wow" list)

1. **Self-installing safety net** — Milestone 0 is done by the agent: hooks, guardrails, CI/CD, GitHub setup.
2. **Fix-loop breaker** — a hook notices when the AI keeps patching the same file and forces a root-cause protocol.
3. **"Pick for me" everywhere** — safe defaults with a one-line reason. Non-technical users never get stuck.
4. **Right-sized engineering** — the scale tier decides what to build now, later, or never.
5. **Decision log** — every choice recorded with *why*, so the agent (and future you) understands it.
6. **Plain-language contract** — explanations tuned to the owner's experience level, "What you learned" notes.
7. **Re-interview / update mode** — "I changed my mind, I want payments now" → updates the existing skill.
8. **Readback** — at the end it reads back a 30-second summary out loud; you can correct by voice.
9. **Multi-language** — talk in your own language; the skill is written in English (or your choice).

## Non-goals (v1)

- Building the app itself (that's the coding agent's job).
- Training a new speech model from scratch.
- Accounts, billing, teams. (Later, maybe.)

## Success = 

A non-engineer goes from "idea in my head" to "Claude Code is building the right thing" in **under 15 minutes**,
without typing more than their project name.
