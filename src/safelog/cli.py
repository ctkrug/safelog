"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import sys

from .redact import redact_line


def main(argv=None) -> int:
    for line in sys.stdin:
        sys.stdout.write(redact_line(line))
        sys.stdout.flush()
    return 0
