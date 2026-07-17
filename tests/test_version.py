import pytest

from safelog import __version__
from safelog.cli import main


def test_version_flag_prints_version_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    assert __version__ in capsys.readouterr().out


def test_help_flag_documents_every_flag(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0
    help_text = capsys.readouterr().out
    for flag in ("--mode", "--disable", "--list-detectors", "--config", "--entropy-threshold", "--version"):
        assert flag in help_text
