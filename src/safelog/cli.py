"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import argparse
import sys

from .config import load_config
from .detectors import ALL_DETECTOR_NAMES, DETECTORS
from .entropy import DEFAULT_THRESHOLD as DEFAULT_ENTROPY_THRESHOLD
from .redact import DEFAULT_MODE, ENTROPY_LABEL, MODES, PEM_LABEL, Redactor
from .stream import iter_stream_lines

DEFAULT_CONFIG_PATH = "safelog.toml"


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
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        metavar="PATH",
        help="config file for custom patterns/detector toggles (default: %(default)s)",
    )
    parser.add_argument(
        "--entropy-threshold",
        type=float,
        default=DEFAULT_ENTROPY_THRESHOLD,
        metavar="FLOAT",
        help="Shannon-entropy bits/char required to flag a token as a secret (default: %(default)s)",
    )
    return parser


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    config = load_config(args.config)
    listable_names = sorted(
        {*ALL_DETECTOR_NAMES, PEM_LABEL, ENTROPY_LABEL, *(d.name for d in config.custom_detectors)}
    )

    if args.list_detectors:
        for name in listable_names:
            print(name)
        return 0

    disabled = set(args.disable) | set(config.disabled_detectors)
    detectors = [d for d in DETECTORS if d.name not in disabled]
    detectors += [d for d in config.custom_detectors if d.name not in disabled]
    detect_pem = PEM_LABEL not in disabled
    detect_entropy = ENTROPY_LABEL not in disabled

    redactor = Redactor(
        detectors=detectors,
        mode=args.mode,
        detect_pem=detect_pem,
        detect_entropy=detect_entropy,
        entropy_threshold=args.entropy_threshold,
    )
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
