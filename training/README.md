# Phase 4 (optional): fine-tuning the speech model

**Don't start here.** Read `docs/VOICE_PIPELINE.md` first. Base Whisper + vocabulary prompting + LLM correction
is usually enough. Fine-tune only when your eval proves it's needed.

## 1. Build the eval set (week 1)

- 200–500 clips of real people answering SkillTalk questions (opt-in only: `SAVE_AUDIO=true` + consent checkbox).
- Store as `data/eval/<id>.wav` (16 kHz mono) + `data/eval/metadata.jsonl`:
  `{"audio": "0001.wav", "text": "Let's use Supabase and Next.js", "entities": ["Supabase", "Next.js"]}`
- Metrics: **WER** (word error rate, via `jiwer`) and **entity accuracy** (% of tech names spelled exactly right).
  Entity accuracy is the one users feel.

## 2. Training data (week 1–2)

- Consented real clips (keep the eval clips OUT of training).
- Synthetic: generate a few thousand sentences with tech terms from `interview/question_bank.yaml` hotwords
  ("I think Supabase with Google login", "host it on Vercel"), voice them with several open TTS voices (Kokoro,
  Piper) at different speeds, add background noise (MUSAN-style) and room reverb.
- Mix ~70% synthetic / 30% real at first; shift toward real as you collect more.

## 3. Train (week 2)

- **Whisper:** LoRA with Hugging Face `transformers` + `peft` (Seq2SeqTrainer). Freeze the encoder at first,
  LoRA on decoder attention. 1× 24 GB GPU (or a rented cloud GPU for a few hours).
  Convert to CTranslate2 (`ct2-transformers-converter`) so `faster-whisper` can load it.
- **Parakeet (English-only, fastest):** NVIDIA NeMo fine-tuning scripts.

## 4. Ship

- Publish on Hugging Face (e.g. `your-org/skilltalk-whisper-turbo-tech`) with a model card: data sources,
  consent policy, eval results vs. base model, licence (match the base model's licence).
- Users switch with `STT_MODEL=your-org/skilltalk-whisper-turbo-tech`.
- Keep it only if it beats *base + prompting* on your eval set.

## Suggested files to add here later

```
training/
  make_synthetic.py     # sentences → TTS audio + noise
  prepare_dataset.py    # metadata.jsonl → HF Dataset
  train_whisper_lora.py # LoRA fine-tune
  evaluate.py           # WER + entity accuracy, base vs. fine-tuned
```
