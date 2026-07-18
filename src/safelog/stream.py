"""Bounded, streaming line reader.

Reads raw bytes off a file descriptor with :func:`os.read`, which returns as
soon as *any* data is available rather than waiting to fill a fixed-size
buffer. That is what keeps ``tail -f | safelog`` responsive: a line is
yielded the moment its trailing newline arrives, not after the pipe closes.

A single line with no newline is bounded to ``max_line_bytes`` so a
pathologically long line (or a stream with no newlines at all) can't grow
memory usage without limit — it is yielded in fixed-size chunks instead.
"""

import codecs
import os
from collections.abc import Iterator

DEFAULT_CHUNK_SIZE = 65536
DEFAULT_MAX_LINE_BYTES = 1_000_000


def iter_stream_lines(
    fileno: int,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    max_line_bytes: int = DEFAULT_MAX_LINE_BYTES,
) -> Iterator[str]:
    """Yield decoded text from ``fileno``, one newline-terminated line at a
    time, falling back to bounded chunks for lines longer than
    ``max_line_bytes`` and flushing a final partial line at EOF.
    """
    decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
    buffer = ""
    while True:
        raw = os.read(fileno, chunk_size)
        if not raw:
            buffer += decoder.decode(b"", final=True)
            if buffer:
                yield buffer
            return
        buffer += decoder.decode(raw)
        while True:
            newline_at = buffer.find("\n")
            if newline_at != -1:
                yield buffer[: newline_at + 1]
                buffer = buffer[newline_at + 1 :]
            elif len(buffer) >= max_line_bytes:
                yield buffer[:max_line_bytes]
                buffer = buffer[max_line_bytes:]
            else:
                break
