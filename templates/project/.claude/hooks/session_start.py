#!/usr/bin/env python3
"""SessionStart: give the agent its bearings — where we are in the plan and which branch it's on.

Anything printed to stdout here is added to the agent's context at the start of every session,
so it never "forgets" the plan between sessions (a big cause of drifting, sloppy projects).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import project_dir, read_event  # noqa: E402


def git(root: Path, *args: str) -> str:
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10).stdout.strip()
    except Exception:
        return ""


def main() -> None:
    root = project_dir(read_event())
    lines = ["[Project guardrails active: safety hooks, quality gate on finish, loop detection.]"]

    progress = root / "PROGRESS.md"
    if progress.exists():
        text = progress.read_text(encoding="utf-8").splitlines()
        lines.append("Current progress (from PROGRESS.md):")
        lines += text[:40]

    branch = git(root, "rev-parse", "--abbrev-ref", "HEAD")
    if branch:
        dirty = bool(git(root, "status", "--porcelain"))
        lines.append(f"Git branch: {branch}{' (uncommitted changes)' if dirty else ''}.")
        if branch in ("main", "master"):
            lines.append("You're on main: before changing code, create a branch: `git switch -c <short-feature-name>`.")
    else:
        lines.append("No git repository yet: do Milestone 0 (engineering foundation) first.")

    lines.append("Rules: small steps · tests before 'done' · explain in plain words · ask before paid services "
                 "· update PROGRESS.md at the end of each milestone.")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
