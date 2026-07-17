"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import argparse
import sys

from .detectors import ALL_DETECTOR_NAMES, DETECTORS
from .redact import DEFAULT_MODE, MODES, PEM_LABEL, Redactor
from .stream import iter_stream_lines

LISTABLE_DETECTOR_NAMES = sorted({*ALL_DETECTOR_NAMES, PEM_LABEL})


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
    parser.add_argument(
        "--disable",
        action="append",
        default=[],
        metavar="NAME",
        help="disable a detector by name (repeatable); see --list-detectors",
    )
    parser.add_argument(
        "--list-detectors",
        action="store_true",
        help="print every detector name usable with --disable, then exit",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.list_detectors:
        for name in LISTABLE_DETECTOR_NAMES:
            print(name)
        return 0

    disabled = set(args.disable)
    detectors = [d for d in DETECTORS if d.name not in disabled]
    detect_pem = PEM_LABEL not in disabled

    redactor = Redactor(detectors=detectors, mode=args.mode, detect_pem=detect_pem)
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
