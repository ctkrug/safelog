import subprocess
import sys
import threading

import safelog.cli as cli


def test_early_downstream_close_exits_without_traceback():
    """`safelog | head`-style early close must not dump a BrokenPipeError.

    safelog is built to sit inline in a live pipe, so a downstream consumer
    that stops reading (a pager the user quit, `head -c1`, an agent that got
    what it needed) must terminate it cleanly rather than with a Python
    traceback the way an unhandled SIGPIPE would.
    """
    proc = subprocess.Popen(
        [sys.executable, "-m", "safelog"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    def feed():
        try:
            proc.stdin.write(b"AWS_SECRET_ACCESS_KEY=ABCDEFGHIJKLMNOP0000\n" * 200_000)
            proc.stdin.close()
        except (BrokenPipeError, OSError):
            pass  # process exited first; nothing left to feed

    feeder = threading.Thread(target=feed, daemon=True)
    feeder.start()

    # Consume one line, then close the read end so the next write hits a dead pipe.
    proc.stdout.readline()
    proc.stdout.close()
    stderr = proc.stderr.read()
    proc.wait(timeout=15)
    feeder.join(timeout=5)

    assert b"Traceback" not in stderr
    assert b"BrokenPipeError" not in stderr


class _DummyStdout:
    def fileno(self):
        return 1


def test_broken_pipe_returns_signalled_exit_code(monkeypatch):
    """A BrokenPipeError from the write loop yields exit 141 (128+SIGPIPE)."""

    def raise_broken_pipe(_redactor):
        raise BrokenPipeError

    dup2_calls = []
    monkeypatch.setattr(cli, "_stream_redacted", raise_broken_pipe)
    monkeypatch.setattr(cli.os, "open", lambda *args, **kwargs: 999)
    monkeypatch.setattr(cli.os, "dup2", lambda *args: dup2_calls.append(args))
    monkeypatch.setattr(cli.sys, "stdout", _DummyStdout())

    assert cli.main([]) == 141
    assert dup2_calls  # stdout was redirected away from the dead pipe
