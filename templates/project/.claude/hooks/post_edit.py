#!/usr/bin/env python3
"""PostToolUse(Edit|Write|MultiEdit): auto-format the changed file + detect "fix loops".

A fix loop = the agent editing the same file again and again, each "fix" creating a new bug.
It's the #1 source of AI-made mess. After LOOP_THRESHOLD edits to one file in one session, we
interrupt and tell the agent to switch to the bug-loop protocol (reproduce → failing test → root cause).
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import project_dir, read_event, rel, tell_agent  # noqa: E402

LOOP_THRESHOLD = 6
PRETTIER_EXT = {".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs", ".css", ".scss", ".json", ".md", ".html", ".yml", ".yaml"}


def run_quietly(cmd, cwd):
    try:
        subprocess.run(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=40)
    except Exception:
        pass


def format_file(path: Path, root: Path) -> None:
    if not path.exists():
        return
    prettier = root / "node_modules" / ".bin" / "prettier"
    if path.suffix in PRETTIER_EXT and prettier.exists():
        run_quietly([str(prettier), "--write", "--log-level", "silent", str(path)], root)
    elif path.suffix == ".py" and shutil.which("ruff"):
        run_quietly(["ruff", "format", "-q", str(path)], root)
        run_quietly(["ruff", "check", "--fix", "-q", str(path)], root)
    elif path.suffix == ".dart" and shutil.which("dart"):
        run_quietly(["dart", "format", str(path)], root)


def count_edit(root: Path, session: str, key: str) -> int:
    state_dir = root / ".claude" / ".state"
    state_dir.mkdir(parents=True, exist_ok=True)
    f = state_dir / f"edits-{(session or 'default')[:40]}.json"
    try:
        counts = json.loads(f.read_text())
    except Exception:
        counts = {}
    counts[key] = counts.get(key, 0) + 1
    f.write_text(json.dumps(counts))
    return counts[key]


def main() -> None:
    event = read_event()
    ti = event.get("tool_input") or {}
    path = ti.get("file_path")
    if not path:
        sys.exit(0)
    root = project_dir(event)
    format_file(Path(path), root)

    r = rel(path, root)
    n = count_edit(root, event.get("session_id", ""), r)
    if n >= LOOP_THRESHOLD and n % LOOP_THRESHOLD == 0:
        tell_agent(
            f"⚠️ Loop check: `{r}` has been changed {n} times this session. Repeated patching usually means the "
            "real cause hasn't been found and each fix is creating new problems.\n"
            "STOP patching. Follow the bug-loop protocol (see the /fix command or references/guardrails.md):\n"
            "1) Reproduce the problem with one exact command or click-path. 2) Write a failing test for it.\n"
            "3) Find the ROOT cause (read the error + surrounding code; `git diff` against the last working commit).\n"
            "4) Make ONE focused fix, run all checks. If still stuck, revert to the last green commit and explain "
            "the situation to the owner in plain words with 2 options."
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
