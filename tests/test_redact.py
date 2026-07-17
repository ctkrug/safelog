from safelog.redact import redact_line


def test_passthrough_of_plain_text():
    line = "2026-07-17T12:00:01Z INFO  starting worker pool=4\n"
    assert redact_line(line) == line


def test_redacts_aws_secret_key_but_keeps_env_var_name():
    line = "ERROR AWS_SECRET_ACCESS_KEY=abcd1234EFGH5678ijkl9012MNOP\n"
    out = redact_line(line)
    assert "AWS_SECRET_ACCESS_KEY=[REDACTED:aws-secret]" in out
    assert "abcd1234EFGH5678ijkl9012MNOP" not in out


def test_redacts_stripe_key_but_keeps_prefix():
    line = "stripe key sk_test_NOTREALZZZ rejected\n"
    out = redact_line(line)
    assert "sk_test_[REDACTED:stripe-key]" in out
    assert "NOTREALZZZ" not in out


def test_redacts_email():
    line = "contact jane.doe@example.com about quota\n"
    out = redact_line(line)
    assert "[REDACTED:email]" in out
    assert "jane.doe@example.com" not in out


def test_redacts_ipv4():
    line = "client 10.0.4.212 connected\n"
    out = redact_line(line)
    assert "[REDACTED:ip]" in out
    assert "10.0.4.212" not in out


def test_redacts_github_token():
    line = "token ghp_" + "A" * 36 + " expired\n"
    out = redact_line(line)
    assert "[REDACTED:github-token]" in out


def test_redacts_jwt():
    line = "auth eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ used\n"
    out = redact_line(line)
    assert "[REDACTED:jwt]" in out


def test_redacts_gitlab_token():
    line = "token glpat-" + "A" * 20 + " expired\n"
    out = redact_line(line)
    assert "[REDACTED:gitlab-token]" in out
    assert "A" * 20 not in out
