#!/usr/bin/env python3
"""Stage 3 CLI: live dictation. Speak, pause, get clean text; Ctrl+C to finish
and copy the full session to the clipboard.

Requires the system PortAudio library (`libportaudio2`) and a clipboard tool
(e.g. `xclip` on X11) — see PROGRESS.md for this environment's status.

Usage: python dictate.py [--llm-model MODEL]
"""

import argparse
import queue
import sys
import threading

import pyperclip

from hebtranscriber.asr import transcribe
from hebtranscriber.audio.capture import microphone_frames
from hebtranscriber.audio.vad import segment_utterances
from hebtranscriber.cleaning import DEFAULT_MODEL, clean


def _capture_utterances(utterance_queue: queue.Queue) -> None:
    """Runs in a background thread so mic capture never blocks on
    transcription/cleanup, which are much slower than real-time on
    underpowered hardware."""
    for utterance in segment_utterances(microphone_frames()):
        utterance_queue.put(utterance)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--llm-model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    utterance_queue: queue.Queue = queue.Queue()
    threading.Thread(target=_capture_utterances, args=(utterance_queue,), daemon=True).start()

    print("Listening... speak, then pause. Ctrl+C to finish.", file=sys.stderr)
    session_parts = []
    try:
        while True:
            utterance = utterance_queue.get()
            result = transcribe(utterance)
            if not result.text.strip():
                continue
            print(f"[raw] {result.text}", file=sys.stderr)
            cleaned = clean(result.text, model=args.llm_model)
            print(cleaned)
            session_parts.append(cleaned)
    except KeyboardInterrupt:
        pass

    full_text = " ".join(session_parts)
    if full_text:
        pyperclip.copy(full_text)
        print(f"\nCopied {len(full_text)} chars to clipboard.", file=sys.stderr)
    else:
        print("\nNo speech captured.", file=sys.stderr)


if __name__ == "__main__":
    main()
