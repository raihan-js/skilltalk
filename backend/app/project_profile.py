"""Derive engineering facts from the interview: tech-stack profile, scale tier, explanation style."""
from __future__ import annotations

from dataclasses import asdict, dataclass

SCAFFOLD = {
    "next": "Use the official Next.js starter with TypeScript, ESLint, Tailwind and the App Router, npm as package "
            "manager (e.g. `npx create-next-app@latest <folder> --ts --eslint --tailwind --app --use-npm` — check "
            "`--help` for the current flags).",
    "vite": "Use the official Vite React + TypeScript starter (`npm create vite@latest <folder> -- --template react-ts`), "
            "then add ESLint if the template doesn't include it.",
    "expo": "Use the official Expo starter with TypeScript (`npx create-expo-app@latest <folder>`), then add ESLint "
            "(`npx expo lint`) and Jest (`jest-expo`).",
    "html": "Create a minimal `index.html`, `styles.css`, `main.js` plus a `package.json` whose scripts run Prettier "
            "(format/lint), Vitest (tests) and a static build/copy step.",
    "desktop": "Use the official Tauri starter (`npm create tauri-app@latest`) with a React + TypeScript frontend — "
               "small installers for Windows, macOS and Linux.",
    "flutter": "Run `flutter create .` (or into a temp folder) and keep the default lint rules (`flutter_lints`).",
    "python": "Create a FastAPI project: `app/main.py`, `tests/`, and a `pyproject.toml` with fastapi, uvicorn, and "
              "dev extras ruff + pytest + httpx.",
}


@dataclass
class Profile:
    id: str                   # node | python | flutter  (drives CI + hooks)
    flavour: str              # next | vite | expo | html | desktop | flutter | python
    install: str
    dev: str
    lint: str
    typecheck: str
    test: str
    build: str
    public_env_prefix: str
    scaffold: str

    def dict(self) -> dict:
        return asdict(self)


def detect_profile(v: dict) -> Profile:
    text = " ".join(str(v.get(k, "")) for k in ("frontend", "mobile_stack", "backend", "platform", "extras")).lower()
    platform = v.get("platform", "Website")

    if "flutter" in text:
        return Profile("flutter", "flutter", "flutter pub get", "flutter run", "flutter analyze", "flutter analyze",
                       "flutter test", "flutter build web", "", SCAFFOLD["flutter"])
    if any(w in text for w in ("python", "fastapi", "django", "flask")) and "Plain HTML" in v.get("frontend", "Plain HTML"):
        return Profile("python", "python", 'pip install -e ".[dev]"', "uvicorn app.main:app --reload",
                       "ruff check .", "ruff check .", "pytest -q", "python -m compileall -q app", "", SCAFFOLD["python"])

    node = dict(install="npm ci", lint="npm run lint", typecheck="npm run typecheck", test="npm test",
                build="npm run build")
    if platform == "Phone app":
        return Profile("node", "expo", dev="npx expo start", public_env_prefix="EXPO_PUBLIC_",
                       scaffold=SCAFFOLD["expo"], **{**node, "build": "npx expo export"})
    if platform == "Desktop app":
        return Profile("node", "desktop", dev="npm run tauri dev", public_env_prefix="VITE_",
                       scaffold=SCAFFOLD["desktop"], **node)
    fe = v.get("frontend", "Next.js")
    if "Vite" in fe:
        return Profile("node", "vite", dev="npm run dev", public_env_prefix="VITE_", scaffold=SCAFFOLD["vite"], **node)
    if "HTML" in fe:
        return Profile("node", "html", dev="npx serve .", public_env_prefix="", scaffold=SCAFFOLD["html"], **node)
    return Profile("node", "next", dev="npm run dev", public_env_prefix="NEXT_PUBLIC_", scaffold=SCAFFOLD["next"], **node)


def quality_gate(p: Profile) -> dict:
    if p.id == "python":
        checks = [
            {"name": "Lint", "cmd": "ruff check .", "when_cmd": "ruff"},
            {"name": "Tests", "cmd": "pytest -q -x", "when_cmd": "pytest", "when_file": "tests"},
        ]
    elif p.id == "flutter":
        checks = [
            {"name": "Analyze", "cmd": "flutter analyze", "when_cmd": "flutter"},
            {"name": "Tests", "cmd": "flutter test", "when_cmd": "flutter", "when_file": "test", "timeout": 300},
        ]
    else:
        checks = [
            {"name": "Lint", "cmd": "npm run lint --silent", "when_script": "lint"},
            {"name": "Typecheck", "cmd": "npm run typecheck --silent", "when_script": "typecheck"},
            {"name": "Unit tests", "cmd": "npm test --silent", "when_script": "test", "timeout": 300},
        ]
    return {"enabled": True, "_about": "Checks run by .claude/hooks/stop_gate.py before the agent finishes. "
            "A check only runs once the project has it (script/file/command exists).", "checks": checks}


def dependabot(p: Profile) -> str:
    eco = {"node": "npm", "python": "pip", "flutter": "pub"}[p.id]
    return (
        "# Dependabot opens pull requests to keep libraries up to date and patch security holes.\n"
        "version: 2\nupdates:\n"
        f'  - package-ecosystem: "{eco}"\n    directory: "/"\n    schedule:\n      interval: "weekly"\n'
        "    open-pull-requests-limit: 5\n    groups:\n      minor-and-patch:\n        update-types: [\"minor\", \"patch\"]\n"
        '  - package-ecosystem: "github-actions"\n    directory: "/"\n    schedule:\n      interval: "monthly"\n'
    )


TIERS = [
    {"id": "starter", "label": "Starter",
     "why": "small user base — managed hosting and free tiers cover everything; keep it simple."},
    {"id": "growth", "label": "Growth",
     "why": "real users rely on it — add monitoring, separate environments and backups you've tested."},
    {"id": "scale", "label": "Scale",
     "why": "large or business-critical — plan capacity, alerts and rollbacks from the start."},
]


def scale_tier(v: dict) -> dict:
    users = v.get("users_count", "Under 100")
    level = 2 if "More than" in users or "10,000+" in users else 1 if "100 to" in users else 0
    if v.get("reliability") == "Business-critical":
        level = min(level + 1, 2)
    return TIERS[level]


EXPLAIN_STYLE = {
    "Beginner": ("Explain every technical word the first time you use it, with an everyday comparison. After each "
                 "milestone add a short \"What you learned\" note (2–3 lines) linking to the playbook. Never assume "
                 "I know where a setting or command is — give exact clicks or commands."),
    "Some experience": ("Explain new concepts briefly (one sentence) and link to the playbook for depth. Give exact "
                        "commands for anything I need to run."),
    "Developer": "Be concise and technical. Skip basic explanations unless I ask; still flag risks and costs.",
}


def experience(v: dict) -> tuple[str, str]:
    level = v.get("experience_level", "Beginner")
    key = next((k for k in EXPLAIN_STYLE if k.lower() in level.lower()), "Beginner")
    return key, EXPLAIN_STYLE[key]
