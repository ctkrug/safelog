from safelog.redact import Redactor

PEM_BLOCK = [
    "-----BEGIN RSA PRIVATE KEY-----\n",
    "MIIEowIBAAKCAQEAtest1234567890abcdefghijklmnopqrstuvwxyz\n",
    "moreKeyMaterialThatShouldNeverAppearInOutput==\n",
    "-----END RSA PRIVATE KEY-----\n",
]


def test_pem_block_collapses_to_single_redacted_line():
    redactor = Redactor()
    outputs = [redactor.process_line(line) for line in PEM_BLOCK]
    assert outputs[:3] == [None, None, None]
    assert outputs[3] == "[REDACTED:private-key]\n"


def test_pem_block_key_material_never_appears_in_output():
    redactor = Redactor()
    outputs = [redactor.process_line(line) for line in PEM_BLOCK]
    joined = "".join(o for o in outputs if o)
    assert "MIIEowIBAAKCAQEA" not in joined
    assert "moreKeyMaterialThatShouldNeverAppearInOutput" not in joined


def test_pem_block_split_across_many_individual_process_line_calls():
    redactor = Redactor()
    lines = PEM_BLOCK[0:1] + list(PEM_BLOCK[1]) + PEM_BLOCK[2:]
    outputs = [redactor.process_line(line) for line in lines]
    non_none = [o for o in outputs if o is not None]
    assert non_none == ["[REDACTED:private-key]\n"]


def test_lines_before_and_after_pem_block_are_redacted_normally():
    redactor = Redactor()
    before = redactor.process_line("contact jane@example.com\n")
    for line in PEM_BLOCK:
        redactor.process_line(line)
    after = redactor.process_line("client 10.0.0.1 connected\n")
    assert before == "contact [REDACTED:email]\n"
    assert after == "client [REDACTED:ip] connected\n"


def test_unterminated_pem_block_is_redacted_on_flush():
    redactor = Redactor()
    for line in PEM_BLOCK[:2]:
        assert redactor.process_line(line) is None
    assert redactor.flush() == "[REDACTED:private-key]\n"


def test_flush_is_a_noop_outside_a_pem_block():
    redactor = Redactor()
    redactor.process_line("plain line\n")
    assert redactor.flush() is None


def test_non_pem_lines_pass_through_the_normal_detectors():
    redactor = Redactor()
    out = redactor.process_line("2026-07-17T12:00:01Z INFO  starting worker\n")
    assert out == "2026-07-17T12:00:01Z INFO  starting worker\n"
