import subprocess
import sys
import threading


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
