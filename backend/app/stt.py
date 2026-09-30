"""Speech-to-text. The app must run without faster-whisper installed (it's imported lazily)."""
from __future__ import annotations

import tempfile
from functools import lru_cache
from pathlib import Path

import httpx

from .config import env


class STTUnavailable(RuntimeError):
    pass


def provider() -> str:
    return env("STT_PROVIDER", "browser").lower()


@lru_cache(maxsize=1)
def _local_model():
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError as e:  # pragma: no cover
        raise STTUnavailable("faster-whisper is not installed: pip install faster-whisper") from e
    return WhisperModel(
        env("STT_MODEL", "large-v3-turbo"),
        device=env("STT_DEVICE", "auto"),
        compute_type=env("STT_COMPUTE_TYPE", "int8"),
    )


def build_prompt(hotwords: list[str] | None) -> str | None:
    """Whisper's initial_prompt biases it toward these spellings (cheap accuracy win for tech words)."""
    if not hotwords:
        return None
    return "Glossary: " + ", ".join(hotwords) + "."


def transcribe(audio: bytes, suffix: str = ".webm", hotwords: list[str] | None = None) -> str:
    p = provider()
    if p == "browser":
        raise STTUnavailable("STT_PROVIDER=browser: transcription happens in the browser.")
    language = env("STT_LANGUAGE") or None

    if p == "remote":
        r = httpx.post(
            env("STT_REMOTE_URL", "http://localhost:9000/v1").rstrip("/") + "/audio/transcriptions",
            headers={"Authorization": f"Bearer {env('STT_REMOTE_API_KEY')}"} if env("STT_REMOTE_API_KEY") else {},
            files={"file": (f"audio{suffix}", audio)},
            data={k: v for k, v in {"model": env("STT_MODEL", "whisper-1"), "prompt": build_prompt(hotwords),
                                     "language": language}.items() if v},
            timeout=120,
        )
        r.raise_for_status()
        return r.json().get("text", "").strip()

    # local faster-whisper (decodes webm/ogg/mp3/wav via bundled PyAV)
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as f:
        f.write(audio)
        f.flush()
        segments, _info = _local_model().transcribe(
            Path(f.name).as_posix(),
            initial_prompt=build_prompt(hotwords),
            language=language,
            vad_filter=True,
            beam_size=5,
        )
        return " ".join(s.text.strip() for s in segments).strip()
