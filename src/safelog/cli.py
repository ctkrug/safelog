"""Command-line entrypoint: redact stdin, write to stdout, line by line."""

import sys

from .redact import Redactor
from .stream import iter_stream_lines


def main(argv=None) -> int:
    redactor = Redactor()
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
