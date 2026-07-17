from safelog.config import EMPTY_CONFIG, load_config, parse_config


def test_parses_custom_pattern_and_matches_it():
    config = parse_config('[patterns]\ninternal-id = "INTERNAL-[0-9]{6}"\n')
    assert len(config.custom_detectors) == 1
    detector = config.custom_detectors[0]
    assert detector.name == "internal-id"
    match = detector.pattern.search("ref INTERNAL-123456 filed")
    assert match.group("secret") == "INTERNAL-123456"


def test_parses_disabled_detectors_list():
    config = parse_config('[detectors]\ndisabled = ["email", "ip"]\n')
    assert config.disabled_detectors == ["email", "ip"]


def test_empty_text_yields_empty_config():
    assert parse_config("") == EMPTY_CONFIG


def test_comments_and_blank_lines_are_ignored():
    text = "\n# a comment\n[patterns]\n# another comment\n\nid = \"X-[0-9]+\"\n"
    config = parse_config(text)
    assert len(config.custom_detectors) == 1
    assert config.custom_detectors[0].name == "id"


def test_malformed_lines_are_ignored_not_raised():
    config = parse_config("[patterns]\nthis is not valid = = \n")
    assert config == EMPTY_CONFIG


def test_load_config_returns_empty_when_file_missing():
    assert load_config("/nonexistent/path/safelog.toml") == EMPTY_CONFIG


def test_load_config_reads_a_real_file(tmp_path):
    config_path = tmp_path / "safelog.toml"
    config_path.write_text('[detectors]\ndisabled = ["ip"]\n')
    config = load_config(str(config_path))
    assert config.disabled_detectors == ["ip"]


def test_invalid_custom_regex_is_ignored_not_raised():
    config = parse_config('[patterns]\nbroken = "[unterminated"\n')
    assert config == EMPTY_CONFIG


def test_valid_patterns_still_load_alongside_an_invalid_one():
    text = '[patterns]\nbroken = "[unterminated"\ngood = "OK-[0-9]+"\n'
    config = parse_config(text)
    assert len(config.custom_detectors) == 1
    assert config.custom_detectors[0].name == "good"
