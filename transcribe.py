#!/usr/bin/env python3
"""Stage 1+2+5 CLI: transcribe a Hebrew audio/video file, optionally cleaning it up
and exporting it.

Usage:
    python transcribe.py path/to/file.mp3 -o output.txt
    python transcribe.py path/to/file.mp3 -o output.txt --clean
    python transcribe.py path/to/file.mp3 -o output.txt --transform keypoints
    python transcribe.py path/to/file.mp3 -o output.txt --export srt
"""

import argparse
import sys
from pathlib import Path

from hebtranscriber.asr import transcribe
from hebtranscriber.cleaning import DEFAULT_MODEL, clean, transform
from hebtranscriber.storage import export_markdown, export_srt, list_terms


def _sibling_path(output: str, suffix: str) -> str:
    path = Path(output)
    return str(path.with_suffix(f".{suffix}{path.suffix}"))


def _with_extension(output: str, ext: str) -> str:
    return str(Path(output).with_suffix(f".{ext}"))


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
    parser.add_argument(
        "--export",
        choices=["md", "srt"],
        help="Also write a sibling .md or .srt file (requires -o); srt uses raw "
        "timestamps, so it reflects the untransformed transcript",
    )
    args = parser.parse_args()
    if args.export and not args.output:
        parser.error("--export requires -o")

    def report_progress(segment):
        print(f"[{segment.start:6.1f}s] {segment.text.strip()}", file=sys.stderr)

    result = transcribe(args.audio_path, on_segment=report_progress)
    final_text = result.text

    if args.clean or args.transform:
        vocabulary = list_terms()
        cleaned_text = clean(result.text, model=args.llm_model, vocabulary=vocabulary)
        final_text = cleaned_text
        if args.output:
            _write(_sibling_path(args.output, "raw"), result.text)
        if args.transform:
            final_text = transform(cleaned_text, args.transform, model=args.llm_model)
            if args.output:
                _write(_sibling_path(args.output, "clean"), cleaned_text)

    _emit(final_text, args.output)

    if args.export == "md":
        path = _with_extension(args.output, "md")
        export_markdown(final_text, path, title=Path(args.audio_path).stem)
        print(f"Wrote Markdown export to {path}", file=sys.stderr)
    elif args.export == "srt":
        path = _with_extension(args.output, "srt")
        export_srt(result.segments, path)
        print(f"Wrote SRT export to {path}", file=sys.stderr)


if __name__ == "__main__":
    main()
