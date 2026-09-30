"""SkillTalk MCP server — lets coding agents (Claude Code, Cursor, …) list, read and install your skills,
and install a skill's engineering foundation (hooks, guardrails, CI/CD, playbooks) into a project.

Install:  pip install -r mcp-server/requirements.txt
Add to Claude Code:
    claude mcp add skilltalk -- python /path/to/skilltalk/mcp-server/server.py
"""
from __future__ import annotations

import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cli"))
import skilltalk as st  # noqa: E402  (the CLI module: one source of truth for install logic)

mcp = FastMCP("skilltalk")


@mcp.tool()
def list_skills() -> list[str]:
    """List project skills created with the SkillTalk voice interviewer."""
    return st.list_skills()


@mcp.tool()
def get_skill(name: str) -> str:
    """Return the full SKILL.md of a SkillTalk skill, plus its decisions log and Milestone 0 setup guide."""
    folder = st.resolve(name)
    parts = [(folder / "SKILL.md").read_text(encoding="utf-8")]
    for extra in ("references/decisions.md", "setup/INSTALL.md"):
        if (folder / extra).exists():
            parts.append((folder / extra).read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


@mcp.tool()
def install_skill(name: str, target: str = "project", project_dir: str = ".", bootstrap: bool = False) -> str:
    """Install a SkillTalk skill. target: 'project' (.claude/skills in project_dir), 'claude' (~/.claude/skills),
    or 'agents' (AGENTS.md + git hooks + CI + playbooks into project_dir, for non-Claude agents).
    bootstrap=True also installs the engineering foundation into project_dir right away."""
    return f"Installed at {st.install(name, target, project_dir, bootstrap)}"


@mcp.tool()
def bootstrap_project(name: str, project_dir: str = ".") -> str:
    """Install a skill's engineering foundation into a project: safety hooks, guardrails, helper agents,
    slash commands, git hooks, GitHub CI + Dependabot, PR template, PROGRESS.md and playbooks.
    Never overwrites existing files (merges settings, .gitignore, CLAUDE.md, AGENTS.md)."""
    return st.bootstrap(name, project_dir)


if __name__ == "__main__":
    mcp.run()
