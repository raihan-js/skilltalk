"""SkillTalk HTTP API + static web UI.  Run: uvicorn app.main:app --reload --port 8000"""
from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import stt
from .config import WEB_DIR, env, skills_dir
from .interview import Interviewer, Session
from .llm import get_llm
from .renderer import render, skill_name, to_zip, write_folder

app = FastAPI(title="SkillTalk", version="0.1.0")
SESSIONS: dict[str, Session] = {}  # in-memory for v1; swap for SQLite/Redis later


def interviewer() -> Interviewer:
    return Interviewer(llm=get_llm())


def get_session(sid: str) -> Session:
    if sid not in SESSIONS:
        raise HTTPException(404, "Session not found (the server may have restarted).")
    return SESSIONS[sid]


class Answer(BaseModel):
    text: str


@app.get("/api/config")
def config():
    return {"stt_provider": stt.provider(), "llm_provider": env("LLM_PROVIDER", "mock")}


@app.post("/api/sessions")
def create_session():
    s, turn = interviewer().start()
    SESSIONS[s.id] = s
    return turn


@app.post("/api/sessions/{sid}/audio")
async def upload_audio(sid: str, file: UploadFile = File(...)):
    """Transcribe only — the UI shows the text so the user can fix it before sending."""
    s = get_session(sid)
    hotwords = []
    if s.current_slot:
        slot = interviewer().bank.by_id.get(s.current_slot)
        hotwords = (slot.hotwords + [o["label"] for o in slot.options]) if slot else []
    suffix = "." + (file.filename or "audio.webm").rsplit(".", 1)[-1]
    try:
        text = stt.transcribe(await file.read(), suffix=suffix, hotwords=hotwords)
    except stt.STTUnavailable as e:
        raise HTTPException(400, str(e))
    return {"text": text}


@app.post("/api/sessions/{sid}/answer")
def answer(sid: str, body: Answer):
    s = get_session(sid)
    turn = interviewer().answer(s, body.text)
    if turn["done"]:
        write_folder(render(s), skills_dir() / skill_name(s))
    return turn


@app.get("/api/sessions/{sid}/skill", response_class=PlainTextResponse)
def preview(sid: str):
    return render(get_session(sid))["SKILL.md"]


@app.get("/api/sessions/{sid}/skill.zip")
def download(sid: str):
    s = get_session(sid)
    name = skill_name(s)
    return Response(to_zip(render(s), name), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{name}.zip"'})


app.mount("/", StaticFiles(directory=WEB_DIR, html=True), name="web")
