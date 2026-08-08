# Progress

Tracks the staged roadmap in `Docs/תכנית-עבודה-פיתוח-מתמלל_1.md`. Update this after
completing a stage, and note any half-finished work here before ending a session.

## Status

**Stages 0-5 implemented; Stage 0 has a known hardware caveat, and Stages 1/3/4 need
hands-on verification this environment can't provide (no real audio, no display).
Stage 5 is fully real-tested (SQLite, not mocked).**
faster-whisper decodes audio via its own bundled PyAV libraries, so a
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
- [~] **Stage 2 — LLM cleanup layer** (week 2): `src/hebtranscriber/cleaning/cleaner.py`
      (Ollama `/api/chat`), word-chunking with context-only overlap (no duplicated
      output), 4 transformations (keypoints/formal/short/long), `transcribe.py --clean`
      and `--transform`. Unit-tested (mocked); live-tested against real transcript text.
      **A/B testing blocked on this machine**: `gemma2:latest` (5.4GB) needs 6.4GB RAM,
      this box has 5.8GB total — Ollama refuses to even load it. `gemma:2b` (1.7GB)
      timed out past 120s. Only `qwen2.5:1.5b` runs at all here.
      **Known qwen2.5:1.5b quirk**: consistently prepends a short label + wraps the
      answer in quotes (e.g. `בלי תמלול: "..."`) despite an explicit "no preamble, no
      quotes" rule; every attempt to prompt this away traded it for a worse failure —
      switching prompt wording to be stricter caused the model to instead *stop
      cleaning and echo a hallucinated one-line summary* of the input. Reverted to the
      version that reliably preserves full, correct content with the cosmetic
      preamble/quotes, rather than a version that's clean-looking but sometimes drops
      content. Content preservation and no invented facts is the harder, more
      important half of the Stage 2 exit criterion — treat the label/quotes as a
      presentation detail to strip once a properly-sized model is available, not
      something to keep prompt-engineering around on a 1.5B model.
      **This needs re-testing on real target hardware with `gemma3:4b`** (per the work
      plan's own A/B recommendation) before deciding the final cleanup model or
      investing in output-parsing workarounds.
- [~] **Stage 3 — Live dictation** (week 3): `src/hebtranscriber/audio/vad.py`
      (Silero VAD, 800ms silence = segment boundary, flushes any trailing buffered
      speech at stream end) is real-tested — not mocked — against both synthetic
      silence and the real test clip (correctly found ~21s of the ~22s clip is
      speech, split into 2 utterances at a natural pause). `src/hebtranscriber/asr`
      now caches the loaded Whisper model (`lru_cache`) and accepts in-memory
      float32 arrays, not just file paths — required so live utterances don't reload
      a multi-GB model each time. `dictate.py` wires mic → VAD → transcribe → clean →
      clipboard with capture running in a background thread so recording never blocks
      on the (slow, on this hardware) processing pipeline.
      **Could not verify end-to-end**: this shell session has no audio/display
      session at all (bare TTY, no X11/Wayland) — not just missing packages. Two
      system libraries are also missing and blocked on `sudo`: `libportaudio2`
      (`sounddevice` raises `OSError: PortAudio library not found` on **import**,
      before even trying to open a stream) and a clipboard tool (no `xclip`/`xsel`/
      `wl-copy` found; `pyperclip.copy()` will fail without one — check your desktop's
      display server to pick the right one, e.g. `xclip` for X11, `wl-clipboard` for
      Wayland). `src/hebtranscriber/audio/capture.py` (the sounddevice wrapper) is
      therefore the one piece of Stage 3 with **no automated test coverage** — it's a
      thin device adapter, deliberately kept separate from `vad.py` so importing the
      testable VAD logic doesn't crash on machines without PortAudio.
      **You'll need to run `dictate.py` yourself** once those system packages are
      installed, to confirm actual mic latency and the <3s speech-stop-to-clean-text
      exit criterion — that can't be measured from here.
      Also: the docs describe raw text appearing *while speaking* and being replaced
      by clean text in place; this MVP instead prints raw then clean sequentially
      per utterance (no in-place terminal overwrite). True live partial transcription
      and in-place replacement are more naturally a Stage 4 GUI concern.
- [~] **Stage 4 — GUI** (weeks 4–5): **framework: Flet** (user's choice — pure Python,
      no Rust/Node toolchain, unlike Tauri which needs one). `src/hebtranscriber/gui/app.py`
      has: record button, live transcript, an RMS-based level meter, raw/clean switch,
      4 transformation buttons, a settings dialog (mic device, cleanup model — populated
      live from `cleaning.list_models()`, VAD threshold slider), full RTL (`page.rtl =
      True`), and a global hotkey (Ctrl+Shift+D, via optional `pynput`).
      **Substitution**: Flet 0.86.5 has no stable OS-level file-drop API (only in-app
      `DragTarget`/`Draggable` between Flet controls) — used a native file-picker
      dialog (`ft.FilePicker`) instead, which achieves the same goal (get a file path
      without typing it) through a documented, working API.
      **`pynput` is an optional dependency** (`pip install -e ".[hotkey]"`), not core:
      its Linux backend needs to compile `evdev` against kernel headers (a C compiler),
      which this machine (and plausibly others) lacks. The GUI already degrades
      gracefully without it (status message, not a crash) — same pattern as the mic
      import failing gracefully.
      **Verified**: the whole app builds and serves successfully — smoke-tested by
      running it in `ft.AppView.WEB_BROWSER` mode and confirming HTTP 200, which
      exercises every code path at startup (live Ollama call, gracefully-empty mic
      list, gracefully-failed hotkey setup) without a display or window system.
      **Could not verify**: actual visual layout/RTL correctness, the record button's
      live behavior, the native desktop window (`FLET_APP` view, the default), the
      file picker's native dialog, and clipboard copy — Flutter web renders to a
      canvas, so raw HTTP fetches show only a loader shell, not real UI content, and
      this environment still lacks a display, PortAudio, and a clipboard tool (see
      Stage 3). **Run `python gui.py` yourself** to see and test the actual UI.
- [x] **Stage 5 — History, search, personal vocabulary** (week 6):
      `src/hebtranscriber/storage/` — `history.py` (SQLite sessions table + FTS5 search,
      one shared db file via `_db.py`), `vocabulary.py` (personal term list), `export.py`
      (TXT/Markdown/SRT). `cleaning.clean()` takes an optional `vocabulary` list injected
      into the system prompt ("fix the spelling of the following terms..."). Wired into
      `dictate.py` (saves each session, passes vocabulary) and the GUI's dictation and
      file-transcription paths (same). New CLIs: `history.py {recent,search,stats}`,
      `vocab.py {add,remove,list}`; `transcribe.py` gained `--export {md,srt}`.
      Unit-tested with real SQLite (via `tmp_path`, not mocked) — 14 tests covering
      session save/search/stats, vocabulary CRUD, and TXT/MD/SRT formatting exactly.
      **Verified live**: `vocab.py add/list/remove` and `history.py stats` run correctly
      against the real on-disk db. `transcribe.py --export srt` verified end-to-end
      against `Docs/Transcribe test.ogg`.
      **Design note**: history is scoped to dictation sessions (`dictate.py`/GUI live
      recording) rather than one-off file transcriptions — "words per minute" only
      means something for live speech, not arbitrary pre-recorded files.
- [ ] **Stage 6 — Packaging & release** (week 7): PyInstaller/Tauri bundle with
      first-run model download, warm-model optimization, idle LLM unload after 5 min,
      low-resource (8GB RAM, no GPU) testing, README + install/troubleshooting docs.

## Open decisions (from the architecture doc)

- **UI framework**: ~~Tauri vs PyQt6/Flet~~ — decided: **Flet** (Stage 4).
- **Final cleanup model**: Gemma 3 4B vs Qwen 2.5/3 (1.5–4B) vs DictaLM — decide from
  the Stage 2 A/B results.
- **whisper.cpp vs faster-whisper**: reconsider in Stage 6 if a Python-dependency-free
  binary is wanted.
- **Mixed Hebrew/English speech**: validate handling in Stage 1, tune if needed.
