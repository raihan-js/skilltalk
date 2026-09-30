#!/usr/bin/env python3
"""Stop: the quality gate. Before the agent says "done", run lint / typecheck / tests on changed code.

- Checks come from .claude/quality-gate.json and only run once the project actually has them
  (e.g. a "lint" script in package.json), so a brand-new empty repo isn't blocked.
- If a check fails, the agent is sent back to fix it — ONCE. On the second attempt
  (stop_hook_active=true) we let it stop, so we never create an endless loop; the agent must then
  explain the failure to the owner instead of pretending it's done.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import project_dir, read_event, tell_agent  # noqa: E402


def has_changes(root: Path) -> bool:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, timeout=15)
        return out.returncode != 0 or bool(out.stdout.strip())
    except Exception:
        return True


def npm_scripts(root: Path) -> dict:
    try:
        return json.loads((root / "package.json").read_text()).get("scripts", {})
    except Exception:
        return {}


def applicable(check: dict, root: Path) -> bool:
    if "when_script" in check and check["when_script"] not in npm_scripts(root):
        return False
    if "when_file" in check and not (root / check["when_file"]).exists():
        return False
    if "when_cmd" in check and not shutil.which(check["when_cmd"]):
        return False
    return True


def main() -> None:
    event = read_event()
    root = project_dir(event)
    if event.get("stop_hook_active"):
        sys.exit(0)  # already sent back once → don't loop forever
    cfg_path = root / ".claude" / "quality-gate.json"
    try:
        cfg = json.loads(cfg_path.read_text())
    except Exception:
        sys.exit(0)
    if not cfg.get("enabled", True) or not has_changes(root):
        sys.exit(0)

    for check in cfg.get("checks", []):
        if not applicable(check, root):
            continue
        try:
            res = subprocess.run(check["cmd"], shell=True, cwd=root, capture_output=True, text=True,
                                 timeout=check.get("timeout", 180))
        except subprocess.TimeoutExpired:
            tell_agent(f"Quality gate: '{check['name']}' took too long. Make the check faster or mention it to the owner.")
        if res.returncode != 0:
            tail = "\n".join((res.stdout + "\n" + res.stderr).strip().splitlines()[-40:])
            tell_agent(
                f"❌ Quality gate failed: {check['name']} (`{check['cmd']}`)\n{tail}\n\n"
                "Don't finish yet. Fix the cause (not the test). If you can't fix it in this attempt, stop and tell "
                "the owner in plain words what is broken, why, and 2 options — never claim the work is done."
            )
    sys.exit(0)


if __name__ == "__main__":
    main()
