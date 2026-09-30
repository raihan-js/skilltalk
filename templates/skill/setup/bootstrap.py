#!/usr/bin/env python3
"""SkillTalk project bootstrap — installs the engineering foundation into a project folder.

    python3 <skill-dir>/setup/bootstrap.py [project-dir] [--force] [--dry-run]

Safe by default: never overwrites your files. It MERGES .gitignore, CLAUDE.md, AGENTS.md and
.claude/settings.json, and skips any other file that already exists (use --force to replace them).
Standard library only.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
FILES_DIR = SKILL_DIR / "setup" / "files"
MARK_BEGIN = "<!-- skilltalk:begin -->"
MARK_END = "<!-- skilltalk:end -->"


def merge_settings(existing: dict, ours: dict) -> dict:
    out = dict(existing)
    perms = out.setdefault("permissions", {})
    for key, vals in ours.get("permissions", {}).items():
        cur = perms.setdefault(key, [])
        cur.extend(v for v in vals if v not in cur)
    hooks = out.setdefault("hooks", {})
    for event, groups in ours.get("hooks", {}).items():
        cur = hooks.setdefault(event, [])
        have = {h.get("command") for g in cur for h in g.get("hooks", [])}
        for g in groups:
            if not any(h.get("command") in have for h in g.get("hooks", [])):
                cur.append(g)
    for k, v in ours.items():
        out.setdefault(k, v)
    return out


def merge_markdown(existing: str, ours: str) -> str:
    block = f"{MARK_BEGIN}\n{ours.strip()}\n{MARK_END}\n"
    if MARK_BEGIN in existing and MARK_END in existing:
        head, rest = existing.split(MARK_BEGIN, 1)
        return head + block + rest.split(MARK_END, 1)[1].lstrip("\n")
    return existing.rstrip() + "\n\n" + block


def merge_lines(existing: str, ours: str) -> str:
    have = set(existing.splitlines())
    extra = [line for line in ours.splitlines() if line.strip() and line not in have]
    return existing.rstrip() + ("\n\n# Added by SkillTalk\n" + "\n".join(extra) + "\n" if extra else "\n")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("project", nargs="?", default=".")
    ap.add_argument("--force", action="store_true", help="replace existing non-mergeable files")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    root = Path(a.project).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    report: dict[str, list[str]] = {"created": [], "merged": [], "skipped": []}

    def write(dest: Path, text: str, kind: str):
        report[kind].append(dest.relative_to(root).as_posix())
        if not a.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8")

    sources = sorted(p for p in FILES_DIR.rglob("*") if p.is_file())
    refs = SKILL_DIR / "references"
    docs = [(p, Path("docs/skilltalk") / p.name) for p in sorted(refs.glob("*.md"))] if refs.exists() else []

    for src, rel in [(p, p.relative_to(FILES_DIR)) for p in sources] + docs:
        dest = root / rel
        ours = src.read_text(encoding="utf-8")
        name = rel.as_posix()
        if not dest.exists():
            write(dest, ours, "created")
        elif name == ".claude/settings.json":
            try:
                merged = merge_settings(json.loads(dest.read_text(encoding="utf-8")), json.loads(ours))
                write(dest, json.dumps(merged, indent=2) + "\n", "merged")
            except json.JSONDecodeError:
                report["skipped"].append(name + " (invalid JSON — merge by hand)")
        elif name in ("CLAUDE.md", "AGENTS.md"):
            write(dest, merge_markdown(dest.read_text(encoding="utf-8"), ours), "merged")
        elif name == ".gitignore":
            write(dest, merge_lines(dest.read_text(encoding="utf-8"), ours), "merged")
        elif a.force or name.startswith("docs/skilltalk/"):
            write(dest, ours, "created")
        else:
            report["skipped"].append(name)

    if not a.dry_run:
        for hook in (root / ".githooks").glob("*"):
            hook.chmod(hook.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        if not (root / ".git").exists():
            if subprocess.run(["git", "init", "-b", "main"], cwd=root, capture_output=True).returncode != 0:
                subprocess.run(["git", "init"], cwd=root, capture_output=True)
                subprocess.run(["git", "checkout", "-b", "main"], cwd=root, capture_output=True)
        if (root / ".githooks").exists() and shutil.which("git"):
            subprocess.run(["git", "config", "core.hooksPath", ".githooks"], cwd=root, capture_output=True)

    for kind, items in report.items():
        if items:
            print(f"{kind.upper()} ({len(items)}):")
            for i in items:
                print(f"  - {i}")
    if report["skipped"]:
        print("\nSkipped files already existed. Compare them with the versions in "
              f"{FILES_DIR} and merge anything useful (or re-run with --force).")
    print("\n✅ Engineering foundation installed." if not a.dry_run else "\n(dry run — nothing written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
