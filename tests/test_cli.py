import io
import os

from safelog.cli import main


class _FdStdin:
    """A minimal stand-in for sys.stdin backed by a real file descriptor."""

    def __init__(self, fileno):
        self._fileno = fileno

    def fileno(self):
        return self._fileno


def test_main_redacts_stdin_to_stdout(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"email a@b.com\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main([]) == 0
    os.close(read_fd)
    assert "[REDACTED:email]" in out.getvalue()
