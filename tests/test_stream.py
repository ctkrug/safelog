import os
import threading

from safelog.stream import iter_stream_lines


def _pipe():
    read_fd, write_fd = os.pipe()
    return read_fd, write_fd


def test_yields_lines_as_they_arrive_without_waiting_for_eof():
    read_fd, write_fd = _pipe()
    gen = iter_stream_lines(read_fd)
    os.write(write_fd, b"line1\n")
    assert next(gen) == "line1\n"
    os.write(write_fd, b"line2\n")
    assert next(gen) == "line2\n"
    os.close(write_fd)
    os.close(read_fd)


def test_flushes_final_partial_line_without_trailing_newline():
    read_fd, write_fd = _pipe()
    os.write(write_fd, b"no newline here")
    os.close(write_fd)
    lines = list(iter_stream_lines(read_fd))
    os.close(read_fd)
    assert lines == ["no newline here"]


def test_empty_stream_yields_nothing():
    read_fd, write_fd = _pipe()
    os.close(write_fd)
    lines = list(iter_stream_lines(read_fd))
    os.close(read_fd)
    assert lines == []


def test_long_unterminated_line_is_bounded_into_chunks():
    read_fd, write_fd = _pipe()
    payload = b"a" * (2_500_000)

    def writer():
        os.write(write_fd, payload)
        os.close(write_fd)

    thread = threading.Thread(target=writer)
    thread.start()
    chunks = list(iter_stream_lines(read_fd, max_line_bytes=1_000_000))
    thread.join()
    os.close(read_fd)
    assert len(chunks) > 1
    assert all(len(chunk) <= 1_000_000 for chunk in chunks)
    assert "".join(chunks) == payload.decode()


def test_short_lines_are_not_split_by_max_line_bytes():
    read_fd, write_fd = _pipe()
    os.write(write_fd, b"short line\n")
    os.close(write_fd)
    lines = list(iter_stream_lines(read_fd, max_line_bytes=5))
    os.close(read_fd)
    assert lines == ["short line\n"]
