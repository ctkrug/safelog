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


def test_main_accepts_mode_flag(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"email a@b.com\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--mode", "mask"]) == 0
    os.close(read_fd)
    assert out.getvalue() == "email ***\n"


def test_disable_flag_leaves_named_detector_untouched(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"contact a@b.com from 10.0.0.1\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--disable", "email"]) == 0
    os.close(read_fd)
    result = out.getvalue()
    assert "a@b.com" in result
    assert "[REDACTED:ip]" in result


def test_disable_flag_is_repeatable(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"contact a@b.com from 10.0.0.1\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--disable", "email", "--disable", "ip"]) == 0
    os.close(read_fd)
    assert out.getvalue() == "contact a@b.com from 10.0.0.1\n"


def test_list_detectors_prints_every_disable_capable_name(monkeypatch):
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--list-detectors"]) == 0
    names = out.getvalue().splitlines()
    assert "email" in names
    assert "private-key" in names
    assert names == sorted(names)


def test_missing_config_file_falls_back_to_defaults(monkeypatch):
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"email a@b.com\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--config", "/nonexistent/safelog.toml"]) == 0
    os.close(read_fd)
    assert "[REDACTED:email]" in out.getvalue()


def test_config_file_custom_pattern_is_redacted(monkeypatch, tmp_path):
    config_path = tmp_path / "safelog.toml"
    config_path.write_text('[patterns]\ninternal-id = "INTERNAL-[0-9]{6}"\n')
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"ref INTERNAL-123456 filed\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--config", str(config_path)]) == 0
    os.close(read_fd)
    assert out.getvalue() == "ref [REDACTED:internal-id] filed\n"


def test_config_file_disabled_list_is_merged_with_disable_flag(monkeypatch, tmp_path):
    config_path = tmp_path / "safelog.toml"
    config_path.write_text('[detectors]\ndisabled = ["ip"]\n')
    read_fd, write_fd = os.pipe()
    os.write(write_fd, b"contact a@b.com from 10.0.0.1\n")
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main(["--config", str(config_path), "--disable", "email"]) == 0
    os.close(read_fd)
    assert out.getvalue() == "contact a@b.com from 10.0.0.1\n"
