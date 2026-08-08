#!/usr/bin/env python3
"""Stage 1 CLI: transcribe a Hebrew audio/video file to text.

Usage: python transcribe.py path/to/file.mp3 -o output.txt
"""

import argparse
import sys

from hebtranscriber.asr import transcribe


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio_path", help="Path to an audio or video file")
    parser.add_argument("-o", "--output", help="Write transcript to this file instead of stdout")
    args = parser.parse_args()

    def report_progress(segment):
        print(f"[{segment.start:6.1f}s] {segment.text.strip()}", file=sys.stderr)

    result = transcribe(args.audio_path, on_segment=report_progress)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result.text)
        print(f"\nWrote {len(result.text)} chars to {args.output}", file=sys.stderr)
    else:
        print(result.text)


if __name__ == "__main__":
    main()
