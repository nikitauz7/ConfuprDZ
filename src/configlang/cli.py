from __future__ import annotations

import argparse
import json
import sys

from .errors import ConfigLangError
from .parser import parse
from .evaluator import translate


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="configlang",
        description="Translate educational config language (Variant 2) from stdin to JSON on stdout.",
    )
    p.add_argument(
        "-p",
        "--pretty",
        action="store_true",
        help="Pretty-print JSON (indent=2).",
    )
    p.add_argument(
        "--ensure-ascii",
        action="store_true",
        help="Escape non-ASCII characters in JSON output (default: keep UTF-8).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    src = sys.stdin.read()
    try:
        assignments = parse(src)
        obj = translate(assignments)
        json.dump(
            obj,
            sys.stdout,
            ensure_ascii=args.ensure_ascii,
            indent=2 if args.pretty else None,
            sort_keys=True,
        )
        if args.pretty:
            sys.stdout.write("\n")
        return 0
    except ConfigLangError as e:
        print(str(e), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
