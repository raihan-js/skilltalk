#!/usr/bin/env python3
"""skilltalk CLI — install generated skills and their engineering foundation. Standard library only.

    python cli/skilltalk.py list
    python cli/skilltalk.py install <skill-folder|skill.zip|name> --target claude
    python cli/skilltalk.py install family-todo-app --target project --project-dir ~/code/todo [--bootstrap]
    python cli/skilltalk.py install family-todo-app --target agents  --project-dir ~/code/todo
    python cli/skilltalk.py bootstrap family-todo-app --project-dir ~/code/todo

Targets:
  claude   ~/.claude/skills/<name>/                 Claude Code, all projects. The agent installs the
                                                     foundation itself in Milestone 0.
  project  <project-dir>/.claude/skills/<name>/     Claude Code, one project (add --bootstrap to install the
                                                     foundation right away instead of leaving it to the agent).
  agents   <project-dir>/                           Codex, Cursor, Gemini CLI, …: installs AGENTS.md, git hooks,
                                                     CI and the playbooks (docs/skilltalk/) directly.

`bootstrap` = run the skill's setup/bootstrap.py: copies hooks, guardrails, helper agents, CI/CD, templates and
playbooks into the project without overwriting your files (it merges settings, .gitignore, CLAUDE.md, AGENTS.md).

Roadmap: `skilltalk talk` — run the voice interview right in the terminal.
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HOME_SKILLS = Path(os.path.expanduser(os.getenv("SKILLTALK_HOME", "~/.skilltalk"))) / "skills"


def list_skills() -> list[str]:
    return sorted(p.name for p in HOME_SKILLS.glob("*") if (p / "SKILL.md").exists()) if HOME_SKILLS.exists() else []


def resolve(source: str) -> Path:
    """Accept a folder, a .zip, or the name of a skill saved in ~/.skilltalk/skills/."""
    p = Path(os.path.expanduser(source))
    if p.is_dir() and (p / "SKILL.md").exists():
        return p
    if p.suffix == ".zip" and p.exists():
        tmp = Path(tempfile.mkdtemp(prefix="skilltalk-"))
        with zipfile.ZipFile(p) as z:
            z.extractall(tmp)
        found = next(tmp.rglob("SKILL.md"), None)
        if not found:
            raise SystemExit(f"No SKILL.md inside {p}")
        return found.parent
    if (HOME_SKILLS / source / "SKILL.md").exists():
        return HOME_SKILLS / source
    raise SystemExit(f"Can't find skill '{source}'. Saved skills: {', '.join(list_skills()) or 'none'}")


def skill_name(folder: Path) -> str:
    for line in (folder / "SKILL.md").read_text(encoding="utf-8").splitlines()[1:10]:
        if line.startswith("name:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return folder.name


def bootstrap(source: str, project_dir: str = ".") -> str:
    folder = resolve(source)
    script = folder / "setup" / "bootstrap.py"
    if not script.exists():
        raise SystemExit(f"{folder} has no setup/bootstrap.py (was it made with an older SkillTalk?)")
    res = subprocess.run([sys.executable, str(script), os.path.expanduser(project_dir)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise SystemExit(res.stderr or res.stdout)
    return res.stdout


def install(source: str, target: str = "claude", project_dir: str = ".", run_bootstrap: bool = False) -> Path:
    folder = resolve(source)
    name = skill_name(folder)
    project = Path(os.path.expanduser(project_dir)).resolve()

    if target in ("claude", "project"):
        base = Path.home() / ".claude" / "skills" if target == "claude" else project / ".claude" / "skills"
        dest = base / name
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(folder, dest)
        if run_bootstrap:
            print(bootstrap(str(dest), str(project)))
        return dest / "SKILL.md"

    if target == "agents":
        print(bootstrap(str(folder), str(project)))
        return project / "AGENTS.md"

    raise SystemExit(f"Unknown target '{target}'. Use claude, project or agents.")


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="skilltalk", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="list skills saved by the SkillTalk app")
    ins = sub.add_parser("install", help="install a skill into a coding agent")
    ins.add_argument("source")
    ins.add_argument("--target", choices=["claude", "project", "agents"], default="claude")
    ins.add_argument("--project-dir", default=".")
    ins.add_argument("--bootstrap", action="store_true", help="also install the engineering foundation now")
    bs = sub.add_parser("bootstrap", help="install a skill's engineering foundation into a project")
    bs.add_argument("source")
    bs.add_argument("--project-dir", default=".")
    args = ap.parse_args(argv)

    if args.cmd == "list":
        print("\n".join(list_skills()) or "No skills yet — finish an interview in the SkillTalk app first.")
    elif args.cmd == "bootstrap":
        print(bootstrap(args.source, args.project_dir))
    elif args.cmd == "install":
        path = install(args.source, args.target, args.project_dir, args.bootstrap)
        print(f"Installed → {path}")
        if args.target != "agents":
            print('Next, open your project in Claude Code and say: "Use the skill and start Milestone 0."')
        else:
            print('Next, tell your coding agent: "Read AGENTS.md and start Milestone 0."')


if __name__ == "__main__":
    main(sys.argv[1:])
