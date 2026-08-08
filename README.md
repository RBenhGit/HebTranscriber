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

Stages 0-6 (of 7) implemented — see [PROGRESS.md](PROGRESS.md) for what's verified
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
python transcribe.py file.mp3 -o out.txt [--clean] [--transform keypoints] [--export srt]
python dictate.py                    # Stage 3: live mic dictation, CLI
python gui.py                        # Stage 4: desktop GUI
python history.py {recent,search,stats}   # Stage 5: browse past dictation sessions
python vocab.py {add,remove,list}         # Stage 5: names/terms the cleanup step should spell correctly
```

## Choosing a cleanup model

`cleaning.recommend_model()` picks `gemma3:4b` if there's roughly 6.5GB+ RAM free
(enough headroom alongside the ASR model and VAD), otherwise `qwen2.5:1.5b`. Run
`python benchmark.py` on your actual machine — the docs' targets are <1x real-time
for ASR and >15 tok/s for cleanup; if you're short on either, drop to a smaller model
before building further on top. Ollama unloads an idle model after 5 minutes
(`keep_alive="5m"`, set explicitly rather than relying on Ollama's own default).

## Troubleshooting

Issues actually hit while building this, in the order you'll likely hit them:

- **`ffmpeg: command not found`**: install it, but it's not actually required for
  transcription — faster-whisper decodes audio via its own bundled PyAV libraries.
  You only need it for the loudness-normalization step on noisy recordings.
- **`OSError: PortAudio library not found`**: install `libportaudio2`
  (`sudo apt-get install -y libportaudio2` on Debian/Ubuntu). This fails at
  **import time**, not just when you try to record — if `dictate.py`/`gui.py` crash
  immediately, this is almost always why.
- **`pyperclip.PyperclipException`**: install a clipboard tool — `xclip` or `xsel`
  on X11, `wl-clipboard` on Wayland. Check `echo $XDG_SESSION_TYPE` if you're not sure
  which one you're on.
- **Global hotkey (Ctrl+Shift+D) doesn't work / `pip install` fails on `pynput`**:
  `pynput`'s Linux backend needs to compile `evdev` against kernel headers — install
  `build-essential` (Debian/Ubuntu) first, or just skip it; the GUI works fine
  without it, you'll just start/stop recording from the button instead.
- **Ollama request fails with "model requires more system memory than is available"**:
  the model you asked for doesn't fit — see "Choosing a cleanup model" above.
- **Cleanup output has a stray preamble or wraps the text in quotes**: a known
  small-model quirk (observed with `qwen2.5:1.5b`) — see `PROGRESS.md`, Stage 2.
  Don't try to fix it by tightening the prompt further; that has reliably made it
  worse (content loss) rather than better in testing.
- **`flet build windows` (or `macos`)**: cannot be run from Linux — Flutter doesn't
  support cross-compiling desktop targets. Build on the actual target OS, or a
  matching CI runner (e.g. GitHub Actions `windows-latest`).

## Development

```bash
pytest          # run tests
ruff check .    # lint
ruff format .   # format
```

This repo uses the
[Claude Code Starter Kit](https://github.com/RBenhGit/CodeFundation): `CLAUDE.md`
defines the working agreement (principles, commands, hooks) Claude Code follows here.
