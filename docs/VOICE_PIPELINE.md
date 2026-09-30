# Voice pipeline — and the honest truth about fine-tuning

## TL;DR

**You do not need to fine-tune a voice model to launch.** The "smart" part of SkillTalk (asking good questions,
explaining options, writing the skill) is done by a *text* LLM. The voice model only has one job: turn speech into
accurate text. Today's open speech-to-text (STT) models already do that very well.

Fine-tuning is a **Phase 4** optimisation, only worth it if you measure that tech words
("Supabase", "Next.js", "Postgres", "OAuth") are being mis-heard.

## The pipeline

```
Mic ─► VAD (detect when you stop talking) ─► STT model ─► text ─► Interviewer LLM ─► next question (text)
                                                                                    └─► TTS (optional: speak it)
```

| Stage | Default (local, free) | Alternatives | Notes |
|---|---|---|---|
| VAD | Silero VAD (built into faster-whisper) | WebRTC VAD, browser | Decides "user finished speaking". |
| STT | **Whisper large-v3-turbo via `faster-whisper`** | Parakeet TDT (NVIDIA NeMo, fastest, English), Canary-Qwen 2.5B (best English accuracy), Qwen3-ASR (52 languages), Moonshine (tiny, on-device), Voxtral (Mistral, audio understanding) | Whisper turbo = best balance of multilingual + speed + tooling. |
| STT (zero-setup) | Browser Web Speech API | — | For the `browser` mode / demos. Not private, Chrome-dependent. |
| LLM | Any OpenAI-compatible endpoint: **Ollama** locally (e.g. a Qwen / Llama / Gemma instruct model), or a hosted API (Claude, etc.) | — | Must reliably output JSON. |
| TTS (optional) | Browser `speechSynthesis` | Kokoro, Piper (open, local) | Reading questions aloud makes it feel like a real conversation. |

Model names move fast — check the Hugging Face Open ASR Leaderboard before release and keep the model a config value
(`STT_MODEL=...`), never hard-coded.

## Cheap accuracy wins (do these BEFORE any fine-tuning)

1. **Vocabulary prompting.** Whisper accepts an `initial_prompt`; pass a list of tech words relevant to the current
   question ("React, Next.js, Supabase, Firebase, Postgres, Stripe, Vercel…"). This alone fixes most mis-hearings.
   Implemented in `backend/app/stt.py` (`hotwords` per question in `interview/question_bank.yaml`).
2. **LLM correction.** The interviewer LLM sees the options it just offered, so "super base" → Supabase is trivial.
   The system prompt tells it to normalise product names.
3. **Show the transcript.** Always show the user what was heard, editable, before sending. Trust + a free fix.
4. **Options as buttons.** Users can tap an option chip instead of speaking the hard word.

## When (and how) to fine-tune — Phase 4

Only if, after the steps above, your eval shows tech-term errors > ~5%.

1. **Build an eval set first**: 200–500 real, consented clips of people answering SkillTalk questions + correct
   transcripts. Measure WER and *entity accuracy* (did we get "Supabase" right?).
2. **Data**: consented user clips (opt-in checkbox) + synthetic clips (TTS voices reading tech sentences, many
   accents/speeds, with noise added).
3. **Method**: LoRA fine-tune of Whisper (Hugging Face `transformers` + `peft`), or NeMo fine-tuning for Parakeet.
   A single 24 GB GPU for a few hours is enough for LoRA on a few thousand clips.
4. **Ship** as an optional model (`STT_MODEL=skilltalk/whisper-turbo-tech`) on Hugging Face under an open licence.
5. **Re-run the eval**; keep it only if it beats base + prompting.

See `training/README.md` for the concrete plan.

## Privacy defaults

- Audio is processed and **discarded** by default. Nothing saved unless the user opts in to "help improve SkillTalk".
- Fully local mode (faster-whisper + Ollama) sends **nothing** to the internet.
