import io

from safelog.cli import main


def test_main_redacts_stdin_to_stdout(monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO("email a@b.com\n"))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main() == 0
    assert "[REDACTED:email]" in out.getvalue()
