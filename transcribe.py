#!/usr/bin/env python3
"""Stage 1+2 CLI: transcribe a Hebrew audio/video file, optionally cleaning it up.

Usage:
    python transcribe.py path/to/file.mp3 -o output.txt
    python transcribe.py path/to/file.mp3 -o output.txt --clean
    python transcribe.py path/to/file.mp3 -o output.txt --transform keypoints
"""

import argparse
import sys
from pathlib import Path

from hebtranscriber.asr import transcribe
from hebtranscriber.cleaning import DEFAULT_MODEL, clean, transform


def _sibling_path(output: str, suffix: str) -> str:
    path = Path(output)
    return str(path.with_suffix(f".{suffix}{path.suffix}"))


def _write(path: str, text: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {len(text)} chars to {path}", file=sys.stderr)


def _emit(text: str, path: str | None) -> None:
    """Write to `path` if given, otherwise print to stdout."""
    if path:
        _write(path, text)
    else:
        print(text)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_path", help="Path to an audio or video file")
    parser.add_argument("-o", "--output", help="Write result to this file instead of stdout")
    parser.add_argument(
        "--clean", action="store_true", help="Run LLM cleanup (fillers, punctuation)"
    )
    parser.add_argument(
        "--transform",
        choices=["keypoints", "formal", "short", "long"],
        help="Apply a transformation to the cleaned text (implies --clean)",
    )
    parser.add_argument("--llm-model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    def report_progress(segment):
        print(f"[{segment.start:6.1f}s] {segment.text.strip()}", file=sys.stderr)

    result = transcribe(args.audio_path, on_segment=report_progress)

    if not args.clean and not args.transform:
        _emit(result.text, args.output)
        return

    cleaned_text = clean(result.text, model=args.llm_model)

    if args.output:
        _write(_sibling_path(args.output, "raw"), result.text)

    if args.transform:
        transformed_text = transform(cleaned_text, args.transform, model=args.llm_model)
        if args.output:
            _write(_sibling_path(args.output, "clean"), cleaned_text)
            _write(args.output, transformed_text)
        else:
            print(transformed_text)
    else:
        _emit(cleaned_text, args.output)


if __name__ == "__main__":
    main()
