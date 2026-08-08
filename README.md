# HebTranscriber (מתמלל)

Local, fully offline Hebrew transcription desktop app, in the style of Google AI Edge
Eloquent — but built as two purpose-specific models instead of one multimodal model, so
Hebrew accuracy doesn't get traded away for convenience.

## How it works

```
mic / audio file (16kHz)
        │
        ▼
Silero VAD — detects speech/silence, triggers cleanup on pause
        │
        ▼
faster-whisper + ivrit-ai/whisper-large-v3-turbo-ct2   (raw text: fillers, false starts)
        │
        ▼
local LLM via Ollama (Gemma 3 4B / Qwen)   (cleanup, punctuation, intent-based rewrite)
        │
        ▼
clean text → clipboard │ transformations (key points/formal/short/long) │ local history
```

No audio ever leaves the device. Full design rationale — including why ASR and cleanup
are kept as two separate models — is in
[Docs/מסמך-ארכיטקטורה-מתמלל_1.md](Docs/מסמך-ארכיטקטורה-מתמלל_1.md). The staged build
plan is in [Docs/תכנית-עבודה-פיתוח-מתמלל_1.md](Docs/תכנית-עבודה-פיתוח-מתמלל_1.md).

## Status

Stages 0-4 (of 7) implemented — see [PROGRESS.md](PROGRESS.md) for what's verified
versus what still needs hands-on testing on real hardware.

## Requirements

- Python 3.11+
- [Ollama](https://ollama.com/) running locally
- [ffmpeg](https://ffmpeg.org/) on `PATH` — only needed for noise-normalization, not
  basic transcription (faster-whisper decodes audio itself)
- `libportaudio2` (Debian/Ubuntu) — for microphone capture
- A clipboard tool: `xclip`/`xsel` on X11, `wl-clipboard` on Wayland

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"       # add ".[dev,hotkey]" for the GUI's global hotkey
ollama pull qwen2.5:1.5b      # or gemma3:4b if your hardware handles it — see PROGRESS.md
```

## Usage

```bash
python benchmark.py file.mp3         # Stage 0: check ASR/LLM speed on your hardware
python transcribe.py file.mp3 -o out.txt [--clean] [--transform keypoints]
python dictate.py                    # Stage 3: live mic dictation, CLI
python gui.py                        # Stage 4: desktop GUI
```

## Development

```bash
pytest          # run tests
ruff check .    # lint
ruff format .   # format
```

This repo uses the
[Claude Code Starter Kit](https://github.com/RBenhGit/CodeFundation): `CLAUDE.md`
defines the working agreement (principles, commands, hooks) Claude Code follows here.
