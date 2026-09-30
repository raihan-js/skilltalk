"""Turn a finished interview (slots) into an Agent Skill folder.

Output layout (see docs/SKILL_FORMAT.md):
    SKILL.md
    references/  decisions, glossary, transcript, ai-workflow, engineering-playbook, guardrails, shipping-checklist
    setup/       INSTALL.md, bootstrap.py, files/  ← the engineering foundation copied into the project
"""
from __future__ import annotations

import io
import json
import re
import shutil
import zipfile
from functools import lru_cache
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

from .config import TEMPLATES_DIR
from .interview import Bank, Session, default_bank
from .project_profile import dependabot, detect_profile, experience, quality_gate, scale_tier

SKILL_T = TEMPLATES_DIR / "skill"
PROJECT_T = TEMPLATES_DIR / "project"
LOOP_THRESHOLD = 6  # keep in sync with templates/project/.claude/hooks/post_edit.py

STACK_SLOTS = ["platform", "frontend", "mobile_stack", "backend", "database", "auth",
               "ai_provider", "hosting", "monetization"]
BADGES = {"now": "🟢 NOW", "later": "🟡 LATER", "skip": "⚪ NOT NEEDED"}

GLOSSARY = {
    "frontend": "The part of the app people see and click.",
    "backend": "Code running on a server behind the scenes: saves data, checks logins, talks to AI.",
    "database": "Where the app permanently saves information.",
    "API": "A way for one program to ask another program to do something.",
    "deploy": "Putting your app on the internet so others can use it.",
    "environment variables (.env)": "A private settings file for secrets like API keys. Never shared publicly.",
    "MVP": "Minimum viable product — the smallest version that is genuinely useful.",
    "free tier": "The free plan of a paid service, with usage limits.",
    "repository (repo)": "The project folder, tracked with git so every change can be undone.",
    "commit": "A saved snapshot of the project with a short note about what changed.",
    "branch": "A side copy of the project where new work happens without touching the live version.",
    "pull request (PR)": "A request to merge a branch into main, showing every change and running the checks first.",
    "CI (continuous integration)": "Robot checks (lint, types, tests, build) that run automatically on every PR.",
    "CD (continuous deployment)": "Automatic publishing: merging into main deploys the new version.",
    "lint": "An automatic check for style problems and common mistakes in code.",
    "typecheck": "An automatic check that data of the right kind is used everywhere (e.g. a number, not text).",
    "hook": "A small script that runs automatically at a certain moment (before a command, after an edit…).",
    "subagent": "A specialised AI helper with one job, e.g. reviewing code or hunting a bug.",
    "migration": "A saved, repeatable script that changes the structure of the database.",
    "vertical scaling": "Making one machine bigger (more CPU/memory).",
    "horizontal scaling": "Adding more machines that share the work.",
    "Kubernetes": "A system for running many containers across many machines. Powerful, complex, rarely needed early.",
    "rollback": "Going back to the previous working version after a bad release.",
}


def slugify(text: str, max_len: int = 64) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (text or "my-app").lower()).strip("-")
    return (slug[:max_len].rstrip("-")) or "my-app"


def split_list(text: str | None) -> list[str]:
    if not text or text.strip().lower() in {"none yet", "none", "no", "nothing"}:
        return []
    parts = re.split(r"\n|;|,|\s*\d+[.)]\s+", text)
    return [p.strip(" .-•") for p in parts if p and p.strip(" .-•")]


def first_sentence(text: str, limit: int = 180) -> str:
    s = re.split(r"(?<=[.!?])\s", (text or "").strip())[0]
    return s if len(s) <= limit else s[: limit - 1].rstrip() + "…"


@lru_cache(maxsize=1)
def engineering_topics() -> list[dict]:
    return yaml.safe_load((SKILL_T / "engineering_topics.yaml").read_text(encoding="utf-8"))["topics"]


def _topic_applies(t: dict, v: dict) -> bool:
    when = t.get("when")
    return (when is None
            or (when == "website" and v.get("platform") == "Website")
            or (when == "backend" and "No backend" not in v.get("backend", ""))
            or (when == "public" and v.get("target_users") == "The public")
            or (when == "ai" and v.get("uses_ai") == "Yes")
            or (when == "payments" and v.get("monetization", "Free") != "Free"))


def tailored_topics(v: dict, tier_id: str) -> list[dict]:
    out = []
    for t in engineering_topics():
        if not _topic_applies(t, v):
            continue
        tier = t["tiers"][tier_id]
        out.append({**t, "status": tier["status"], "badge": BADGES[tier["status"]], "note": tier["note"]})
    return out


def _why(bank: Bank, session: Session, slot_id: str) -> str:
    slot = bank.by_id[slot_id]
    if slot_id in session.defaulted:
        return slot.default_reason or "Safe default."
    return slot.option_explain(session.slots[slot_id]) or "Chosen by the project owner."


def _architecture(v: dict) -> str:
    client = v.get("frontend") or v.get("mobile_stack") or v.get("platform", "App")
    lines = ["```", f"[ User's {v.get('platform', 'browser').lower()} ]", f"        │  {client}", "        ▼"]
    if "No backend" in v.get("backend", ""):
        lines.append("  Data stays on the device (no server)")
    else:
        lines.append(f"  {v.get('database', 'Backend')}  (data" + (" + logins" if "auth" in v else "") + ")")
    if v.get("uses_ai") == "Yes":
        lines.append(f"  Server-side call ──► {v.get('ai_provider', 'AI API')}  (API key never in the browser)")
    if v.get("monetization") and v.get("monetization") != "Free":
        lines.append("  Payments ──► Stripe (test mode first)")
    lines.append("")
    lines.append("  GitHub (branch → PR → CI checks) ──merge──► " + (v.get("hosting") or "hosting") + " (auto-deploy)")
    lines.append("```")
    return "\n".join(lines)


def _milestones(v: dict, features: list[str]) -> list[dict]:
    m = [
        {"title": "Engineering foundation", "what": "Follow setup/INSTALL.md: app skeleton, safety hooks, git hooks, "
         "GitHub repo, CI/CD, PROGRESS.md. The agent does this itself.",
         "test": "seeing the green CI check on GitHub and the agent's 5-bullet summary of the safety net."},
        {"title": "Screens with pretend data", "what": "Build the main screens for every must-have using fake sample data.",
         "test": "clicking through every screen on the preview link, on a laptop and a phone."},
    ]
    if "No backend" not in v.get("backend", ""):
        m.append({"title": "Real data", "what": f"Connect {v.get('database', 'the database')} with migrations; "
                  "save/load real data; separate dev and production databases.",
                  "test": "adding something, refreshing the page, and seeing it's still there."})
    if "auth" in v:
        m.append({"title": "Logins", "what": f"Add {v['auth']}; server-side permission checks; tests proving people "
                  "only see data they're allowed to see.",
                  "test": "logging in with two accounts and checking each sees only what they should."})
    for f in features:
        m.append({"title": f"Feature: {f}", "what": f"Make “{f}” fully work end to end, with tests.",
                  "test": f"using “{f}” on the preview link exactly like a real user would."})
    if v.get("uses_ai") == "Yes":
        m.append({"title": "AI feature", "what": f"Connect {v.get('ai_provider', 'the AI provider')} from the server "
                  "with a per-user usage limit and a spending cap.",
                  "test": "trying the AI feature and checking the API key is not visible in the browser."})
    if v.get("monetization") and v["monetization"] != "Free":
        m.append({"title": "Payments (test mode)", "what": f"Add {v['monetization']} with Stripe test mode and "
                  "verified webhooks.", "test": "paying with Stripe's test card 4242 4242 4242 4242."})
    m.append({"title": "Launch", "what": "Security audit, shipping checklist, production deploy via PR, "
              "plain-language README.", "test": "opening the live link on your phone and ticking the launch checklist."})
    return m


def _env() -> Environment:
    return Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), keep_trailing_newline=True,
                       undefined=StrictUndefined)


def _render_str(env: Environment, path: Path, ctx: dict) -> str:
    rel = path.relative_to(TEMPLATES_DIR).as_posix()
    return re.sub(r"\n{3,}", "\n\n", env.get_template(rel).render(**ctx))


def build_context(session: Session, bank: Bank) -> dict:
    v = {k: val for k, val in session.slots.items()}
    title = v.get("project_name") or "My App"
    idea_short = first_sentence(v.get("idea", "an app")).rstrip(".")
    idea_short = re.sub(r"^(i|we)\s+(want|would like|'d like|need)\s+(to\s+(build|make|create)\s+)?", "",
                        idea_short, flags=re.I) or idea_short
    features = split_list(v.get("core_features"))
    tier = scale_tier(v)
    topics = tailored_topics(v, tier["id"])
    exp, style = experience(v)
    agent = v.get("coding_agent", "Claude Code")
    profile = detect_profile(v)
    return {
        "s": _Slots(v), "title": title, "name": slugify(title), "idea_short": idea_short,
        "description": json.dumps(
            f'Build and extend "{title}": {idea_short}. Use when working on this project\'s features, screens, data, '
            "tech stack, setup, testing or deployment.", ensure_ascii=False),
        "core_features": features or ["(to be decided with the owner)"],
        "later_features": split_list(v.get("later_features")) or ["Nothing yet"],
        "stack": [{"topic": bank.by_id[k].topic, "choice": v[k], "why": _why(bank, session, k)}
                  for k in STACK_SLOTS if k in v],
        "architecture": _architecture(v), "milestones": _milestones(v, features),
        "tier": tier, "topics": topics,
        "scale_now": [t for t in topics if t["status"] == "now" and t["id"] in
                      {"backups", "monitoring", "security", "rate_limits", "environments", "cost_control"}],
        "scale_skip": [t for t in topics if t["status"] == "skip"],
        "experience": exp, "explain_style": style,
        "agent": agent, "agent_is_claude": "Claude" in agent,
        "p": profile.dict(), "budget": v.get("budget", "$0"), "loop_threshold": LOOP_THRESHOLD,
    }


class _Slots(dict):
    """dict with attribute access that returns '' for missing slots (templates stay simple)."""
    def __getattr__(self, key):
        return self.get(key, "")


def _project_files(env: Environment, ctx: dict, plan_body: str) -> dict[str, str]:
    """Render templates/project → setup/files/ (what bootstrap.py copies into the user's project)."""
    out: dict[str, str] = {}
    profile_id = ctx["p"]["id"]
    for src in sorted(p for p in PROJECT_T.rglob("*") if p.is_file()):
        rel = src.relative_to(PROJECT_T).as_posix()
        if rel.startswith(".claude/") and not ctx["agent_is_claude"]:
            continue
        if rel.startswith(".cursor/") and ctx["agent"] != "Cursor":
            continue
        if rel.startswith(".github/workflows/ci."):
            if rel != f".github/workflows/ci.{profile_id}.yml":
                continue
            rel = ".github/workflows/ci.yml"
        if rel.endswith(".j2"):
            out[rel[:-3]] = _render_str(env, src, {**ctx, "plan_body": plan_body})
        else:
            out[rel] = src.read_text(encoding="utf-8")
    if not ctx["agent_is_claude"]:
        out.pop("CLAUDE.md", None)
    else:
        out[".claude/quality-gate.json"] = json.dumps(quality_gate(detect_profile(dict(ctx["s"]))), indent=2) + "\n"
    out[".github/dependabot.yml"] = dependabot(detect_profile(dict(ctx["s"])))
    return {f"setup/files/{k}": v for k, v in out.items()}


def render(session: Session, bank: Bank | None = None) -> dict[str, str]:
    """Return {relative_path: file_content} for the whole skill folder."""
    bank = bank or default_bank()
    env = _env()
    ctx = build_context(session, bank)
    v = session.slots

    skill_md = _render_str(env, SKILL_T / "SKILL.md.j2", ctx)
    files = {"SKILL.md": skill_md}
    for src in sorted((SKILL_T / "references").glob("*.j2")):
        files[f"references/{src.name[:-3]}"] = _render_str(env, src, ctx)
    files["setup/INSTALL.md"] = _render_str(env, SKILL_T / "setup" / "INSTALL.md.j2", ctx)
    files["setup/bootstrap.py"] = (SKILL_T / "setup" / "bootstrap.py").read_text(encoding="utf-8")

    decisions = ["# Decisions\n", "Every choice from the interview, with the reason.\n",
                 "| Topic | Decision | Why | Picked by |", "|---|---|---|---|"]
    for slot in bank.slots:
        if slot.id in v:
            by = "SkillTalk default" if slot.id in session.defaulted else "Owner"
            val = str(v[slot.id]).replace("|", "/").replace("\n", " ")
            why = (slot.default_reason if slot.id in session.defaulted else slot.option_explain(v[slot.id])) or slot.why
            decisions.append(f"| {slot.topic} | {val} | {why} | {by} |")
    decisions.append(f"| Scale tier | {ctx['tier']['label']} | {ctx['tier']['why']} | SkillTalk (from users + reliability) |")
    files["references/decisions.md"] = "\n".join(decisions) + "\n"

    glossary = ["# Glossary (plain language)\n"] + [f"- **{k}** — {d}" for k, d in GLOSSARY.items()]
    for k in STACK_SLOTS:
        if k in v and (ex := bank.by_id[k].option_explain(v[k])):
            glossary.append(f"- **{v[k]}** — {ex}.")
    files["references/glossary.md"] = "\n".join(glossary) + "\n"

    transcript = ["# Interview transcript\n"]
    transcript += [f"**{'You' if t['role'] == 'user' else 'SkillTalk'}:** {t['text']}\n" for t in session.transcript]
    files["references/interview-transcript.md"] = "\n".join(transcript)

    plan_body = skill_md.split("---", 2)[2].lstrip().replace("references/", "docs/skilltalk/")
    plan_body = plan_body.replace("setup/INSTALL.md", "docs/skilltalk/INSTALL.md")
    files.update(_project_files(env, ctx, plan_body))
    files["references/INSTALL.md"] = files["setup/INSTALL.md"]  # also lands in docs/skilltalk/ for non-Claude agents
    return files


def skill_name(session: Session) -> str:
    return slugify(session.slots.get("project_name", "my-app"))


EXECUTABLE = ("setup/bootstrap.py", "setup/files/.githooks/", "setup/files/.claude/hooks/")


def write_folder(files: dict[str, str], dest: Path) -> Path:
    if dest.exists():
        shutil.rmtree(dest)
    for rel, content in files.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        if rel.startswith(EXECUTABLE):
            p.chmod(0o755)
    return dest


def to_zip(files: dict[str, str], folder_name: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for rel, content in files.items():
            info = zipfile.ZipInfo(f"{folder_name}/{rel}")
            info.external_attr = (0o755 if rel.startswith(EXECUTABLE) else 0o644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, content)
    return buf.getvalue()
