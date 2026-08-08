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

Not started — see [PROGRESS.md](PROGRESS.md) for the current stage and what's next.

## Requirements

- Python 3.11+
- [ffmpeg](https://ffmpeg.org/) on `PATH`
- [Ollama](https://ollama.com/) running locally

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
ollama pull gemma3:4b
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
