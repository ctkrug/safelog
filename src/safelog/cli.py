"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import sys

from .redact import redact_line
from .stream import iter_stream_lines


def main(argv=None) -> int:
    for line in iter_stream_lines(sys.stdin.fileno()):
        sys.stdout.write(redact_line(line))
        sys.stdout.flush()
    return 0
