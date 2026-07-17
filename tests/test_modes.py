from safelog.redact import Redactor, redact_line


def test_mask_mode_replaces_secret_with_fixed_mask_and_no_label():
    line = "contact jane.doe@example.com about quota\n"
    out = redact_line(line, mode="mask")
    assert "***" in out
    assert "REDACTED" not in out
    assert "jane.doe@example.com" not in out


def test_hash_mode_is_stable_for_the_same_secret():
    line = "contact jane.doe@example.com about quota\n"
    first = redact_line(line, mode="hash")
    second = redact_line(line, mode="hash")
    assert first == second
    assert "jane.doe@example.com" not in first


def test_hash_mode_differs_for_different_secrets():
    out_a = redact_line("contact a@example.com\n", mode="hash")
    out_b = redact_line("contact b@example.com\n", mode="hash")
    assert out_a != out_b


def test_label_mode_is_the_default():
    line = "contact jane.doe@example.com about quota\n"
    assert redact_line(line) == redact_line(line, mode="label")
    assert "[REDACTED:email]" in redact_line(line)


def test_pem_block_collapse_honors_mask_mode():
    redactor = Redactor(mode="mask")
    redactor.process_line("-----BEGIN RSA PRIVATE KEY-----\n")
    redactor.process_line("keymaterial\n")
    out = redactor.process_line("-----END RSA PRIVATE KEY-----\n")
    assert out == "***\n"
