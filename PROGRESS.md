# Progress

Tracks the staged roadmap in `Docs/תכנית-עבודה-פיתוח-מתמלל_1.md`. Update this after
completing a stage, and note any half-finished work here before ending a session.

## Status

**Stage 0 done (with a known hardware caveat); Stage 1 working on real audio, needs
broader validation.** faster-whisper decodes audio via its own bundled PyAV libraries, so a
system `ffmpeg` binary turned out not to be required for basic transcription — it's
still needed for the Stage 1 `loudnorm` noise-normalization risk mitigation, and isn't
installed yet (`sudo apt-get install -y ffmpeg`, blocked here on missing sudo access).

**Dev-machine performance finding**: on this box (4 CPU cores, no GPU, 5.7GB RAM),
neither speed target was met — ASR ran at ~17–20x real-time (target < 1x) and
`qwen2.5:1.5b` cleanup ran at ~5.4 tok/s (target > 15). Confirmed this isn't a
`beam_size` artifact (beam_size=1 only reached 17.06x). Per the user, this machine is
not the deployment target, so this is a documented risk, not a blocker — re-run
`benchmark.py` on the real target hardware before trusting the Stage 0 gate.

## Stages

- [x] **Stage 0 — Environment & feasibility** (2–3 days): faster-whisper, the
      `ivrit-ai/whisper-large-v3-turbo-ct2` model, and Ollama + `qwen2.5:1.5b` are
      installed and working; `benchmark.py` written and verified against a live Ollama
      call and a synthetic audio smoke test (see finding above — re-verify on target
      hardware). `ffmpeg` and `gemma3:4b` still need installing when convenient.
- [~] **Stage 1 — MVP file transcription** (week 1): `src/hebtranscriber/asr/transcriber.py`
      (faster-whisper, `language="he"`, `beam_size=5`, segment callback for progress)
      and CLI `transcribe.py file.mp3 -o output.txt` are implemented, unit-tested
      (mocked `WhisperModel`), and validated against one real clip (`Docs/Transcribe
      test.ogg`, ~15s Hebrew speech): transcript was accurate with no hallucination,
      no material errors. Still needs the work plan's full 5-audio-type manual review
      (WhatsApp recording, Zoom meeting, podcast, lecture, noisy speech) before calling
      the "<10 material errors/min" exit criterion met — only one short, clean clip
      tested so far. No punctuation/filler-cleanup yet — that's Stage 2, not a Stage 1
      defect.
- [ ] **Stage 2 — LLM cleanup layer** (week 2): `cleaner.py` (Ollama REST API), Hebrew
      cleanup system prompt (strip filler words, merge self-corrections, add
      punctuation, no invented content), raw/clean side-by-side mode, 4 transformations
      (key points / formal / short / long), A/B test Gemma 3 4B vs Qwen 2.5 1.5B.
- [ ] **Stage 3 — Live dictation** (week 3): mic capture via sounddevice, Silero VAD
      (0.7–1.0s silence = segment boundary), async processing queue, live terminal
      display, `dictate.py`, clipboard copy via pyperclip. Exit criterion: under 3s
      from speech-stop to clean text for a 30s segment.
- [ ] **Stage 4 — GUI** (weeks 4–5): pick Tauri vs PyQt6/Flet; main screen (record
      button, live transcript, level meter), raw/clean toggle, transformation buttons,
      drag-and-drop file transcription, full RTL layout, global hotkey, settings.
- [ ] **Stage 5 — History, search, personal vocabulary** (week 6): local SQLite session
      table, FTS5 free-text search, personal term dictionary injected into the cleanup
      prompt, session stats, export to TXT/SRT/Markdown.
- [ ] **Stage 6 — Packaging & release** (week 7): PyInstaller/Tauri bundle with
      first-run model download, warm-model optimization, idle LLM unload after 5 min,
      low-resource (8GB RAM, no GPU) testing, README + install/troubleshooting docs.

## Open decisions (from the architecture doc)

- **UI framework**: Tauri vs PyQt6/Flet — decide at the start of Stage 4.
- **Final cleanup model**: Gemma 3 4B vs Qwen 2.5/3 (1.5–4B) vs DictaLM — decide from
  the Stage 2 A/B results.
- **whisper.cpp vs faster-whisper**: reconsider in Stage 6 if a Python-dependency-free
  binary is wanted.
- **Mixed Hebrew/English speech**: validate handling in Stage 1, tune if needed.
