"""Central config: paths + environment variables (loaded from ../.env if present)."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # repo root (skilltalk/)

try:  # optional: load .env from repo root
    from dotenv import load_dotenv

    load_dotenv(ROOT / ".env")
except ImportError:  # pragma: no cover
    pass

INTERVIEW_DIR = ROOT / "interview"
TEMPLATES_DIR = ROOT / "templates"
WEB_DIR = ROOT / "web"


def env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    return env(name, str(default)).lower() in {"1", "true", "yes", "on"}


def skilltalk_home() -> Path:
    return Path(os.path.expanduser(env("SKILLTALK_HOME", "~/.skilltalk")))


def skills_dir() -> Path:
    d = skilltalk_home() / "skills"
    d.mkdir(parents=True, exist_ok=True)
    return d
