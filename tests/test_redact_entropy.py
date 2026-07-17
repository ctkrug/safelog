from safelog.redact import Redactor, redact_entropy

RANDOM_SECRET = "aB3dE9fGh2JkLmN8pQrS5tUvWxYz012A"


def test_redact_entropy_replaces_high_entropy_token():
    out = redact_entropy(f"key: {RANDOM_SECRET}\n")
    assert out == "key: [REDACTED:high-entropy]\n"


def test_redact_entropy_leaves_line_without_candidates_untouched():
    line = "2026-07-17T12:00:01Z INFO  starting worker pool=4\n"
    assert redact_entropy(line) == line


def test_redactor_flags_generic_secret_no_regex_would_catch():
    redactor = Redactor()
    out = redactor.process_line(f"generic_api_key: {RANDOM_SECRET}\n")
    assert out == "generic_api_key: [REDACTED:high-entropy]\n"


def test_redactor_disable_entropy_leaves_secret_untouched():
    redactor = Redactor(detect_entropy=False)
    out = redactor.process_line(f"generic_api_key: {RANDOM_SECRET}\n")
    assert RANDOM_SECRET in out


def test_regex_match_and_adjacent_high_entropy_text_both_redact_cleanly():
    line = f"stripe key sk_test_NOTREALZZZ and also {RANDOM_SECRET} nearby\n"
    redactor = Redactor()
    out = redactor.process_line(line)
    assert out == "stripe key sk_test_[REDACTED:stripe-key] and also [REDACTED:high-entropy] nearby\n"


def test_entropy_threshold_is_configurable_on_redactor():
    borderline = "sk_a8f5f167f44f4964e6c998dee827110c"
    permissive = Redactor(entropy_threshold=3.5)
    strict = Redactor(entropy_threshold=4.5)
    assert "[REDACTED:high-entropy]" in permissive.process_line(f"{borderline}\n")
    assert borderline in strict.process_line(f"{borderline}\n")
