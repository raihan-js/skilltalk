"""Shared helpers for SkillTalk project hooks (standard library only, Python 3.8+).

Hook contract (Claude Code): the event arrives as JSON on stdin.
Exit 0 = allow / fine. Exit 2 = block (PreToolUse) or send the message on stderr back to the agent.
"""
import json
import os
import sys
from pathlib import Path


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def project_dir(event: dict) -> Path:
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or event.get("cwd") or os.getcwd()).resolve()


def block(message: str) -> None:
    """Stop the action and tell the agent why + what to do instead."""
    sys.stderr.write("🛑 BLOCKED by project guardrail: " + message.strip() + "\n")
    sys.exit(2)


def tell_agent(message: str) -> None:
    """Non-blocking feedback after something already happened (PostToolUse / Stop)."""
    sys.stderr.write(message.strip() + "\n")
    sys.exit(2)


def rel(path: str, root: Path) -> str:
    try:
        return Path(path).resolve().relative_to(root).as_posix()
    except Exception:
        return Path(path).as_posix()
