#!/usr/bin/env python3
"""Stage 5 CLI: browse and search local dictation session history.

Usage:
    python history.py recent [--limit N]
    python history.py search "query"
    python history.py stats
"""

import argparse
import datetime
import sys

from hebtranscriber.storage import Session, recent_sessions, search, stats


def _print_sessions(sessions: list[Session]) -> None:
    if not sessions:
        print("No sessions found.", file=sys.stderr)
        return
    for s in sessions:
        when = datetime.datetime.fromtimestamp(s.created_at, tz=datetime.UTC)
        when = when.astimezone().strftime("%Y-%m-%d %H:%M")
        print(f"[{s.id}] {when} ({s.duration_s:.0f}s, {s.words_per_minute:.0f} wpm)")
        print(f"    {s.clean_text}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    recent_parser = subparsers.add_parser("recent", help="Show recent sessions")
    recent_parser.add_argument("--limit", type=int, default=10)

    search_parser = subparsers.add_parser("search", help="Full-text search past sessions")
    search_parser.add_argument("query")

    subparsers.add_parser("stats", help="Show aggregate statistics")

    args = parser.parse_args()

    if args.command == "recent":
        _print_sessions(recent_sessions(limit=args.limit))
    elif args.command == "search":
        _print_sessions(search(args.query))
    elif args.command == "stats":
        for key, value in stats().items():
            print(f"{key}: {value}")


if __name__ == "__main__":
    main()
