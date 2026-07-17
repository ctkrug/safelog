import io
import os

from safelog.cli import main

RANDOM_SECRET = b"aB3dE9fGh2JkLmN8pQrS5tUvWxYz012A"


class _FdStdin:
    """A minimal stand-in for sys.stdin backed by a real file descriptor."""

    def __init__(self, fileno):
        self._fileno = fileno

    def fileno(self):
        return self._fileno


def _run(monkeypatch, argv, stdin_bytes):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, stdin_bytes)
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(argv) == 0
    os.close(read_fd)
    return out.getvalue()


def test_high_entropy_secret_is_flagged_by_default(monkeypatch):
    result = _run(monkeypatch, [], b"token: " + RANDOM_SECRET + b"\n")
    assert result == "token: [REDACTED:high-entropy]\n"


def test_disable_high_entropy_leaves_secret_untouched(monkeypatch):
    result = _run(monkeypatch, ["--disable", "high-entropy"], b"token: " + RANDOM_SECRET + b"\n")
    assert RANDOM_SECRET.decode() in result


def test_entropy_threshold_flag_lowers_sensitivity(monkeypatch):
    borderline = b"sk_a8f5f167f44f4964e6c998dee827110c"
    flagged = _run(monkeypatch, ["--entropy-threshold", "3.5"], borderline + b"\n")
    passed = _run(monkeypatch, ["--entropy-threshold", "4.5"], borderline + b"\n")
    assert "[REDACTED:high-entropy]" in flagged
    assert borderline.decode() in passed


def test_list_detectors_includes_high_entropy(monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--list-detectors"]) == 0
    assert "high-entropy" in out.getvalue().splitlines()
