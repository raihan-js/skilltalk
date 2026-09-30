"""Interview engine: the 'referee' between the question bank and the LLM.

- The question bank (YAML) decides WHAT must be covered.
- The LLM (optional) makes it conversational and captures multiple answers at once.
- The engine decides WHICH slot is next, validates LLM output, and falls back to the bank.
"""
from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass, field
from functools import lru_cache

import yaml

from .config import INTERVIEW_DIR
from .llm import ChatLLM, extract_json

PICK_FOR_ME = "Pick for me"
DONT_KNOW = re.compile(
    r"\b(pick for me|you (choose|pick|decide)|i don'?t know|dunno|not sure what|no idea|whatever you think|skip)\b",
    re.I,
)
AFFIRM = re.compile(
    r"\b(yes|yep|yeah|looks good|sounds good|perfect|correct|that'?s right|all good|no changes?|done|great)\b", re.I
)


def _mentions(text: str, label: str) -> bool:
    """True if the user's text mentions an option: 'Supabase' matches 'Supabase (Postgres)'."""
    for core in {label, label.split(" (")[0]}:
        if re.search(r"(?<!\w)" + re.escape(core.strip()) + r"(?!\w)", text, re.I):
            return True
    return False


# --------------------------------------------------------------------------- question bank
@dataclass
class Slot:
    id: str
    topic: str
    ask: str
    why: str = ""
    options: list[dict] = field(default_factory=list)
    default: str | None = None
    default_reason: str = ""
    hotwords: list[str] = field(default_factory=list)
    ask_if: dict | None = None
    required: bool = False

    def option_explain(self, value: str) -> str | None:
        for o in self.options:
            if o["label"].lower() == str(value).lower():
                return o.get("explain")
        return None

    def ui_options(self) -> list[dict]:
        opts = [o for o in self.options if o["label"] != PICK_FOR_ME]
        if opts and self.default:
            opts.append({"label": PICK_FOR_ME, "explain": "I'll choose the safest option and tell you why"})
        return opts


class Bank:
    def __init__(self, slots: list[Slot]):
        self.slots = slots
        self.by_id = {s.id: s for s in slots}

    @classmethod
    def load(cls, path=None) -> "Bank":
        data = yaml.safe_load((path or INTERVIEW_DIR / "question_bank.yaml").read_text(encoding="utf-8"))
        return cls([Slot(**s) for s in data["slots"]])

    def applicable(self, slot: Slot, filled: dict) -> bool:
        cond = slot.ask_if
        if not cond:
            return True
        value = filled.get(cond["slot"])
        if value is None:
            ref = self.by_id.get(cond["slot"])
            if ref is not None and not self.applicable(ref, filled):
                return False  # the slot it depends on was skipped → skip this too
            return "not_in" in cond  # unknown yet → only 'not_in' style questions stay
        if "in" in cond:
            return any(v.lower() in str(value).lower() for v in cond["in"])
        if "not_in" in cond:
            return not any(v.lower() in str(value).lower() for v in cond["not_in"])
        return True

    def remaining(self, filled: dict) -> list[Slot]:
        return [s for s in self.slots if s.id not in filled and self.applicable(s, filled)]

    def next_slot(self, filled: dict) -> Slot | None:
        rem = self.remaining(filled)
        return rem[0] if rem else None

    def active(self, filled: dict) -> list[Slot]:
        return [s for s in self.slots if self.applicable(s, filled)]


@lru_cache(maxsize=1)
def default_bank() -> Bank:
    return Bank.load()


@lru_cache(maxsize=1)
def system_prompt() -> str:
    return (INTERVIEW_DIR / "system_prompt.md").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- session
@dataclass
class Session:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    slots: dict[str, str] = field(default_factory=dict)
    defaulted: set[str] = field(default_factory=set)
    transcript: list[dict] = field(default_factory=list)
    current_slot: str | None = None
    confirming: bool = False
    done: bool = False


class Interviewer:
    def __init__(self, llm: ChatLLM | None = None, bank: Bank | None = None):
        self.llm = llm
        self.bank = bank or default_bank()

    # ---- public API --------------------------------------------------------
    def start(self) -> tuple[Session, dict]:
        s = Session()
        first = self.bank.next_slot(s.slots)
        intro = "Hi! I'm SkillTalk. I'll ask you a few simple questions and turn your idea into instructions an AI coding assistant can follow. "
        return s, self._ask(s, first, prefix=intro)

    def answer(self, s: Session, text: str) -> dict:
        text = (text or "").strip()
        if s.done:
            return self._turn(s, "We're all done — your skill is ready to download.", None)
        s.transcript.append({"role": "user", "text": text, "slot": s.current_slot})

        if s.confirming:
            if AFFIRM.search(text) and not re.search(r"\b(but|change|except|actually)\b", text, re.I):
                s.done = True
                return self._turn(s, "Wonderful! Your skill is ready. Download it or install it into your coding agent.", None)
            self._apply_changes(s, text)
            return self._readback(s, prefix="Updated. ")

        if self.llm is not None:
            turn = self._llm_turn(s, text)
            if turn is not None:
                return turn
        return self._scripted_turn(s, text)

    # ---- scripted (mock / fallback) ---------------------------------------
    def _scripted_turn(self, s: Session, text: str) -> dict:
        slot = self.bank.by_id.get(s.current_slot or "")
        prefix = ""
        if slot:
            prefix = self._fill(s, slot, text)
        return self._advance(s, prefix)

    def _fill(self, s: Session, slot: Slot, text: str) -> str:
        """Store an answer for one slot. Returns a short reflection sentence."""
        if not text or DONT_KNOW.search(text) or text.lower() == PICK_FOR_ME.lower():
            if slot.default is not None:
                s.slots[slot.id] = slot.default
                s.defaulted.add(slot.id)
                return f"I'll go with {slot.default}. {slot.default_reason} "
            return ""
        match = next((o["label"] for o in slot.options
                      if o["label"] != PICK_FOR_ME and _mentions(text, o["label"])), None)
        s.slots[slot.id] = match or text
        s.defaulted.discard(slot.id)
        return "Got it. "

    # ---- LLM turn ----------------------------------------------------------
    def _llm_turn(self, s: Session, text: str) -> dict | None:
        remaining = self.bank.remaining(s.slots)
        context = {
            "filled_slots": s.slots,
            "current_slot": s.current_slot,
            "remaining_slots_in_order": [
                {"id": r.id, "ask": r.ask, "why": r.why, "default": r.default,
                 "options": [o["label"] for o in r.options]} for r in remaining
            ],
            "next_slot": remaining[0].id if remaining else None,
            "all_required_filled": all(x.id in s.slots for x in self.bank.active(s.slots) if x.required),
        }
        messages = [{"role": "system", "content": system_prompt()}]
        for t in s.transcript[-12:-1]:
            messages.append({"role": "user" if t["role"] == "user" else "assistant", "content": t["text"]})
        messages.append({"role": "user", "content": f"ENGINE CONTEXT:\n{json.dumps(context)}\n\nUSER SAID:\n{text}"})
        try:
            data = extract_json(self.llm.chat(messages))
        except Exception:  # network, timeout, bad status → scripted fallback
            return None
        if not data:
            return None

        captured = data.get("captured") or {}
        if isinstance(captured, dict):
            for k, v in captured.items():
                slot = self.bank.by_id.get(k)
                if slot is None or v in (None, "", []):
                    continue
                v = ", ".join(map(str, v)) if isinstance(v, list) else str(v)
                if v.lower() == PICK_FOR_ME.lower() and slot.default is not None:
                    s.slots[k] = slot.default
                    s.defaulted.add(k)
                else:
                    s.slots[k] = v
                    s.defaulted.discard(k)

        nxt = self.bank.next_slot(s.slots)
        if nxt is None:
            return self._readback(s, prefix="Thanks, that's everything I need. ")
        say = str(data.get("say") or "").strip()
        if data.get("question_slot") != nxt.id or not say:
            return self._ask(s, nxt)  # LLM drifted → use bank wording
        opts = data.get("options") if isinstance(data.get("options"), list) else nxt.ui_options()
        opts = [o for o in opts if isinstance(o, dict) and o.get("label")] or nxt.ui_options()
        s.current_slot = nxt.id
        return self._turn(s, say, nxt, options=opts)

    def _apply_changes(self, s: Session, text: str) -> None:
        if self.llm is not None:
            try:
                data = extract_json(self.llm.chat([
                    {"role": "system", "content": "Extract changes the user wants to their project answers. "
                     'Reply ONLY JSON: {"captured": {"<slot_id>": "<new value>"}}. Slot ids: '
                     + ", ".join(self.bank.by_id)},
                    {"role": "user", "content": f"Current answers: {json.dumps(s.slots)}\nUser says: {text}"},
                ]))
                captured = (data or {}).get("captured") or {}
                changed = False
                for k, v in captured.items():
                    if k in self.bank.by_id and v:
                        s.slots[k] = str(v)
                        s.defaulted.discard(k)
                        changed = True
                if changed:
                    return
            except Exception:
                pass
        extra = s.slots.get("extras", "")
        s.slots["extras"] = (extra + "; " if extra and extra != "Nothing else" else "") + f"Change requested: {text}"

    # ---- helpers -----------------------------------------------------------
    def _advance(self, s: Session, prefix: str = "") -> dict:
        nxt = self.bank.next_slot(s.slots)
        if nxt is None:
            return self._readback(s, prefix=prefix + "That's everything I need. ")
        return self._ask(s, nxt, prefix=prefix)

    def _ask(self, s: Session, slot: Slot | None, prefix: str = "") -> dict:
        if slot is None:
            return self._readback(s, prefix)
        s.current_slot = slot.id
        return self._turn(s, prefix + slot.ask, slot, options=slot.ui_options())

    def _readback(self, s: Session, prefix: str = "") -> dict:
        s.confirming, s.current_slot = True, None
        v = s.slots
        lines = [
            f"{v.get('project_name', 'Your app')}: {v.get('idea', '')}".strip(),
            f"For {v.get('target_users', 'your users')}, as a {v.get('platform', 'website').lower()}.",
            f"Must-haves: {v.get('core_features', 'to be decided')}.",
        ]
        stack = [v[k] for k in ("frontend", "mobile_stack", "database", "auth", "ai_provider", "hosting") if k in v]
        if stack:
            lines.append("Built with " + ", ".join(stack) + ".")
        lines.append(f"Budget {v.get('budget', '$0')} a month, first version in {v.get('timeline', 'about 2 weeks')}.")
        say = prefix + "Here's what I heard: " + " ".join(lines) + " Does that sound right, or would you change anything?"
        return self._turn(s, say, None, options=[
            {"label": "Yes, looks good", "explain": "create my skill"},
            {"label": "Change something", "explain": "just say what to change"},
        ])

    def _turn(self, s: Session, say: str, slot: Slot | None, options: list[dict] | None = None) -> dict:
        s.transcript.append({"role": "assistant", "text": say, "slot": slot.id if slot else None})
        active = self.bank.active(s.slots)
        return {
            "session_id": s.id,
            "say": say,
            "slot": slot.id if slot else None,
            "topic": slot.topic if slot else ("Done" if s.done else "Review"),
            "why": slot.why if slot else "",
            "options": options or [],
            "hotwords": slot.hotwords if slot else [],
            "progress": {"covered": sum(1 for a in active if a.id in s.slots), "total": len(active)},
            "confirming": s.confirming and not s.done,
            "done": s.done,
        }
