#!/usr/bin/env python3
"""PreToolUse(Bash): block commands that destroy work, leak secrets or skip the safety process.

Each rule explains WHY and WHAT TO DO INSTEAD, so the agent can recover on its own.
The project owner can still run any of these commands themselves in their own terminal.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import block, read_event  # noqa: E402

RULES = [
    (r"\brm\s+(-\S+\s+)*-\S*[rR]\S*\s+(-\S+\s+)*(/|~|\$HOME|\.\.|\*)(/?\*?)(\s|$)",
     "Recursive delete of the root, home, parent or everything is never needed. Delete specific paths only."),
    (r"\bgit\s+push\b[^;&|]*\s(--force(?!-with-lease)|-f)(\s|$)",
     "Force-push rewrites shared history and can erase work. Make a new commit instead "
     "(or use --force-with-lease on your OWN feature branch only)."),
    (r"\bgit\s+push\b[^;&|]*[\s:](main|master)(\s|$)",
     "Never push straight to main. Push a feature branch and open a pull request so CI checks it: "
     "`git push -u origin <branch>` then `gh pr create --fill`."),
    (r"\bgit\s+(commit|push)\b[^;&|]*--no-verify",
     "Skipping the git safety hooks is not allowed. Fix what the hook reported instead."),
    (r"\bgit\s+reset\s+--hard\b",
     "`git reset --hard` throws away uncommitted work. Use `git stash` (recoverable), or ask the owner first."),
    (r"\bgit\s+clean\s+-\S*f",
     "`git clean -f` permanently deletes untracked files. List them with `git clean -n` and ask the owner."),
    (r"\b(curl|wget)\b[^|;&]*\|\s*(sudo\s+)?(ba|z|)sh\b",
     "Piping a download straight into a shell runs unreviewed code. Download it, read it, then run it, "
     "or use the official package manager."),
    (r"(^|[;&|]\s*)sudo\s",
     "No sudo from the AI agent. If a system package is needed, tell the owner the exact command and why."),
    (r"\bchmod\s+(-R\s+)?(0?777|a\+rwx)\b",
     "World-writable permissions are a security hole. Use the minimal permission needed (e.g. 755 or 644)."),
    (r"(?i)\b(drop\s+(database|schema|table)|truncate\s+table)\b",
     "Destructive database command. Write a migration, make sure a backup exists, and get the owner's OK."),
    (r"\b(prisma\s+migrate\s+reset|supabase\s+db\s+reset\b[^;&|]*--linked|rails\s+db:(drop|reset))",
     "This wipes a database. Only ever run it against a local dev database, and ask the owner first."),
    (r"\b(cat|less|more|head|tail|bat|type|nl)\b[^;&|]*\.env(\.local|\.production|\.prod|\.development)?(\s|$|['\"])",
     "Don't print secret files — their contents would end up in the chat log. "
     "Check which variables exist with `grep -o '^[A-Z_]*' .env` if you must."),
    (r"\b(vercel\s+(deploy\s+)?--prod|netlify\s+deploy\s+[^;&|]*--prod|npm\s+publish|firebase\s+deploy)\b",
     "Production deploys happen automatically when a pull request is merged into main (after CI passes). "
     "Ask the owner if they really want a manual production deploy."),
]


def main() -> None:
    event = read_event()
    cmd = (event.get("tool_input") or {}).get("command", "")
    for pattern, why in RULES:
        if re.search(pattern, cmd):
            block(f"{why}\nCommand was: {cmd[:200]}")
    sys.exit(0)


if __name__ == "__main__":
    main()
