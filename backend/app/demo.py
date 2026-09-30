"""Scripted demo: runs a full mock interview and prints (or writes) the generated skill.

    python -m app.demo            # print SKILL.md
    python -m app.demo --write    # regenerate examples/family-todo-app/
"""
from __future__ import annotations

import sys

from .config import ROOT
from .interview import Interviewer
from .renderer import render, skill_name, write_folder

ANSWERS = [
    "I want a simple shared to-do app for my family. We keep forgetting chores and groceries, "
    "so everyone should see the list and tick things off from their phones.",
    "Family Todo App",
    "Beginner, I've never coded",
    "A small group, just my family",
    "Under 100",
    "Annoying — the family relies on it for the weekly shop",
    "Shared lists, add and tick off tasks, assign a task to a person, due dates, reminders by email",
    "A shopping mode that sorts groceries by aisle; a weekly chore rotation",
    "Website",
    "Bright and friendly, big buttons, something like Todoist but simpler",
    "Pick for me",          # frontend
    "Pick for me",          # backend
    "Supabase",             # database
    "Google login",         # auth
    "Maybe later",          # AI
    "Vercel",               # hosting
    "Claude Code",          # AI coding agent
    "$0",                   # budget
    "About 2 weeks",
    "No",                   # sensitive data
    "My mum isn't techy, so it has to be super obvious.",
    "Yes, looks good",
]


def run():
    iv = Interviewer(llm=None)
    s, turn = iv.start()
    for a in ANSWERS:
        if turn["done"]:
            break
        turn = iv.answer(s, a)
    assert turn["done"], f"interview did not finish; stuck at {turn['slot']}"
    return s


def main() -> None:
    s = run()
    files = render(s)
    if "--write" in sys.argv:
        dest = write_folder(files, ROOT / "examples" / skill_name(s))
        print(f"Wrote {dest}")
    else:
        print(files["SKILL.md"])


if __name__ == "__main__":
    main()
