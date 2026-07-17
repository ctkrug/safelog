"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import argparse
import sys

from .redact import MODES, DEFAULT_MODE, Redactor
from .stream import iter_stream_lines


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="safelog",
        description="Redact secrets from a piped stream of logs or terminal output.",
    )
    parser.add_argument(
        "--mode",
        choices=MODES,
        default=DEFAULT_MODE,
        help="how detected secrets are replaced (default: %(default)s)",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    redactor = Redactor(mode=args.mode)
    for line in iter_stream_lines(sys.stdin.fileno()):
        out = redactor.process_line(line)
        if out is not None:
            sys.stdout.write(out)
            sys.stdout.flush()
    trailing = redactor.flush()
    if trailing is not None:
        sys.stdout.write(trailing)
        sys.stdout.flush()
    return 0
