"""Tiny OpenAI-compatible chat client + a 'mock' provider.

Works with Ollama (http://localhost:11434/v1), vLLM, LM Studio and hosted APIs that
expose /chat/completions. Keep this file dependency-light (httpx only).
"""
from __future__ import annotations

import json
import re
from typing import Protocol

import httpx

from .config import env, env_bool


class ChatLLM(Protocol):
    def chat(self, messages: list[dict]) -> str: ...


class OpenAICompatibleLLM:
    def __init__(self) -> None:
        self.base_url = env("LLM_BASE_URL", "http://localhost:11434/v1").rstrip("/")
        self.api_key = env("LLM_API_KEY", "ollama")
        self.model = env("LLM_MODEL", "qwen3:8b")
        self.json_mode = env_bool("LLM_JSON_MODE", True)

    def chat(self, messages: list[dict]) -> str:
        body: dict = {"model": self.model, "messages": messages, "temperature": 0.3}
        if self.json_mode:
            body["response_format"] = {"type": "json_object"}
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=body,
            timeout=90,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]


def get_llm() -> ChatLLM | None:
    """Return a real LLM client, or None for the scripted 'mock' mode."""
    if env("LLM_PROVIDER", "mock").lower() == "mock":
        return None
    return OpenAICompatibleLLM()


def extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model reply (handles ```json fences and chatter)."""
    if not text:
        return None
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S)  # reasoning models
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S)
    candidates = [fenced.group(1)] if fenced else []
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        candidates.append(text[start : end + 1])
    for c in candidates:
        try:
            obj = json.loads(c)
            if isinstance(obj, dict):
                return obj
        except json.JSONDecodeError:
            continue
    return None
