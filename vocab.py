#!/usr/bin/env python3
"""Stage 5 CLI: manage the personal vocabulary used to correct name/term
spelling during LLM cleanup.

Usage:
    python vocab.py add "שם או מונח"
    python vocab.py remove "שם או מונח"
    python vocab.py list
"""

import argparse

from hebtranscriber.storage import add_term, list_terms, remove_term


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="Add a term")
    add_parser.add_argument("term")

    remove_parser = subparsers.add_parser("remove", help="Remove a term")
    remove_parser.add_argument("term")

    subparsers.add_parser("list", help="List all terms")

    args = parser.parse_args()

    if args.command == "add":
        add_term(args.term)
    elif args.command == "remove":
        remove_term(args.term)
    elif args.command == "list":
        for term in list_terms():
            print(term)


if __name__ == "__main__":
    main()
