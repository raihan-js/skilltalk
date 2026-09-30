import json
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.demo import run  # noqa: E402
from app.interview import Interviewer  # noqa: E402
from app.renderer import render, slugify  # noqa: E402


def frontmatter(md: str) -> dict:
    assert md.startswith("---\n"), "frontmatter must be the very first line"
    return yaml.safe_load(md.split("---", 2)[1])


def test_mock_interview_produces_valid_skill():
    s = run()
    files = render(s)
    fm = frontmatter(files["SKILL.md"])
    assert fm["name"] == "family-todo-app"
    assert len(fm["name"]) <= 64
    assert "Use when" in fm["description"]
    assert "Supabase" in files["SKILL.md"]
    assert "references/decisions.md" in files
    assert len(files["SKILL.md"].splitlines()) < 500


def test_skips_irrelevant_questions():
    s = run()
    assert "ai_provider" not in s.slots      # said "Maybe later" to AI
    assert "monetization" not in s.slots     # small group, not public
    assert "mobile_stack" not in s.slots     # website


def test_pick_for_me_uses_default():
    s = run()
    assert s.slots["frontend"] == "Next.js"
    assert "frontend" in s.defaulted


class JunkLLM:
    def chat(self, messages):
        return "sorry, I can't do JSON today"


class GoodLLM:
    """Captures two slots at once, like a real user rambling."""
    def chat(self, messages):
        return "```json\n" + json.dumps({
            "captured": {"idea": "a recipe box", "project_name": "Recipe Box"},
            "say": "Lovely! How comfortable are you with tech?", "question_slot": "experience_level",
            "options": [{"label": "Just me", "explain": "personal"}], "done": False}) + "\n```"


def test_bad_llm_output_falls_back_to_bank():
    iv = Interviewer(llm=JunkLLM())
    s, _ = iv.start()
    turn = iv.answer(s, "A recipe app")
    assert turn["slot"] == "project_name"    # scripted fallback moved on


def test_llm_can_capture_multiple_slots():
    iv = Interviewer(llm=GoodLLM())
    s, _ = iv.start()
    turn = iv.answer(s, "It's called Recipe Box, a place for my recipes")
    assert s.slots["project_name"] == "Recipe Box"
    assert turn["slot"] == "experience_level"
    assert "comfortable" in turn["say"]  # LLM wording kept when it follows the engine


def test_slugify():
    assert slugify("My Cool App!!") == "my-cool-app"
    assert len(slugify("x" * 200)) <= 64
