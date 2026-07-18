from pathlib import Path

GITLEAKS_CONFIG = Path(__file__).resolve().parent.parent / ".gitleaks.toml"


def test_gitleaks_config_exists():
    assert GITLEAKS_CONFIG.is_file()


def test_gitleaks_config_extends_the_default_ruleset():
    text = GITLEAKS_CONFIG.read_text()
    assert "useDefault = true" in text


def test_gitleaks_config_allowlists_the_fixture_paths():
    text = GITLEAKS_CONFIG.read_text()
    for path in ("tests/", "fixtures/", "scripts/benchmark"):
        assert path in text, f"{path!r} missing from the .gitleaks.toml allowlist"
