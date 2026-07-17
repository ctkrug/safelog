import runpy
import sys

import pytest


def test_python_m_safelog_runs_the_cli(monkeypatch):
    """`python -m safelog --version` runs cli.main() and exits 0."""
    monkeypatch.setattr(sys, "argv", ["safelog", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_module("safelog", run_name="__main__")
    assert exc_info.value.code == 0
