import io
import os

from safelog.cli import main


class _FdStdin:
    def __init__(self, fileno):
        self._fileno = fileno

    def fileno(self):
        return self._fileno


def test_cli_collapses_pem_block_to_single_redacted_line(monkeypatch):
    read_fd, write_fd = os.pipe()
    block = (
        "before the key\n"
        "-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEAtest1234567890abcdefghijklmnopqrstuvwxyz\n"
        "-----END RSA PRIVATE KEY-----\n"
        "after the key\n"
    )
    os.write(write_fd, block.encode())
    os.close(write_fd)
    monkeypatch.setattr("sys.stdin", _FdStdin(read_fd))
    out = io.StringIO()
    monkeypatch.setattr("sys.stdout", out)
    assert main([]) == 0
    os.close(read_fd)
    result = out.getvalue()
    assert result == "before the key\n[REDACTED:private-key]\nafter the key\n"
