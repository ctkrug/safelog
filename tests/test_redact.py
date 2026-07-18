import re
import time

from safelog.detectors import Detector
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


def test_identifier_ending_in_stripe_prefix_is_not_flagged():
    # "sk_live_"/"sk_test_" are literal substrings with no boundary check,
    # so a variable name like "desk_live_actionXYZ123" opens a match right
    # where the literal happens to appear inside it.
    line = "desk_live_actionXYZ123 rest\n"
    assert redact_line(line) == line


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


def test_identifier_ending_in_github_prefix_is_not_flagged():
    # "ghp_"/"gho_"/"ghu_"/"ghs_"/"ghr_" are unanchored, so a word ending in
    # one of those 4-char sequences opens a match mid-identifier.
    line = "thighp_used" + "A" * 40 + " context\n"
    assert redact_line(line) == line


def test_redacts_jwt():
    line = "auth eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dQw4w9WgXcQ used\n"
    out = redact_line(line)
    assert "[REDACTED:jwt]" in out


def test_dotted_property_chain_containing_eyj_is_not_flagged_as_jwt():
    # "keyJSON" contains the JWT literal prefix "eyJ" as a substring; a
    # dotted call/property chain after it ("obj.keyJSON.parse.value") has
    # the same two-dot shape as a real JWT and must not be mistaken for one.
    line = "const keyJSON = obj.keyJSON.parse.value;\n"
    assert redact_line(line) == line


def test_redacts_gitlab_token():
    line = "token glpat-" + "A" * 20 + " expired\n"
    out = redact_line(line)
    assert "[REDACTED:gitlab-token]" in out
    assert "A" * 20 not in out


def test_identifier_ending_in_gitlab_prefix_is_not_flagged():
    # "glpat-" is a literal substring with no boundary check.
    line = "not_a_glpat-realtokenabcdefghij1234 here\n"
    assert redact_line(line) == line


def test_identifier_ending_in_slack_prefix_is_not_flagged():
    # "xox[baprs]-" is unanchored, so a word containing that 5-char
    # sequence opens a match mid-identifier.
    line = "a boxoxb-officechair here\n"
    assert redact_line(line) == line


def test_identifier_ending_in_aws_key_id_prefix_is_not_flagged():
    # "AKIA" has no boundary check either — a single leading letter that
    # happens to be uppercase merges into what looks like a valid key id.
    line = "PAKIA1234567890123456 rest\n"
    assert redact_line(line) == line


def test_redacts_ipv6():
    line = "client 2001:db8::1 connected\n"
    out = redact_line(line)
    assert "[REDACTED:ip]" in out
    assert "2001:db8::1" not in out


def test_bare_double_colon_is_not_flagged_as_ipv6():
    line = "default route ::\n"
    assert redact_line(line) == line


def test_cpp_scope_resolution_is_not_flagged_as_ipv6():
    # "std::vector", "core::fmt::Display" and "ActiveRecord::Base" all end a
    # hex-letter identifier ("d", "e", "d") right before "::" — a naive
    # compressed-form IPv6 match swallows just that trailing letter.
    for line in (
        "template<typename T> std::vector<T> make()\n",
        "use core::fmt::Display as Fmt;\n",
        "class Post < ActiveRecord::Base\n",
    ):
        assert redact_line(line) == line


def test_scope_resolution_before_non_word_char_is_not_flagged():
    # Regression for the leading guard specifically: when the char after
    # "::" isn't alphanumeric (a brace, a newline), only a lookbehind on the
    # char *before* the match — not the trailing lookahead — rejects the
    # "d::" fragment inside "std::".
    line = "namespace std:: {\n"
    assert redact_line(line) == line


def test_double_colon_followed_by_identifier_is_not_flagged():
    # Regression for the trailing guard specifically: "::1abc" alone fits
    # the compressed-form branch (1abc is a valid 4-char hex group), so
    # without a lookahead rejecting a following alnum char, the "xyz" tail
    # of an ordinary identifier like "::1abcxyz" gets silently dropped.
    line = "id ::1abcxyz done\n"
    assert redact_line(line) == line


def test_redacts_ipv6_inside_url_brackets():
    line = "connecting to http://[::1]:8080/health\n"
    out = redact_line(line)
    assert "[REDACTED:ip]" in out
    assert "::1" not in out


def test_redacts_bare_loopback_ipv6_after_whitespace():
    line = "peer address ::1 accepted\n"
    out = redact_line(line)
    assert "[REDACTED:ip]" in out
    assert " ::1 " not in out


def test_long_at_free_line_does_not_trigger_quadratic_backtracking():
    # A long run of word characters with no "@" anywhere forces the email
    # detector's local-part backtracking on every starting offset; an
    # unbounded quantifier there turns this into O(n^2) and can hang the
    # process on a single oversized line (e.g. a base64 blob or hex dump).
    line = "A" * 200_000 + "\n"
    start = time.monotonic()
    redact_line(line)
    assert time.monotonic() - start < 2.0


def test_only_the_captured_span_is_replaced_not_every_copy_of_its_text():
    # The replacement used to substitute the secret *by value* across the
    # whole match, so leading context that happened to read the same as the
    # secret was redacted too. Only the captured span may be replaced.
    detectors = [Detector("dup", re.compile(r"tok (?P<secret>[a-z]+)"))]
    assert redact_line("tok tok", detectors) == "tok [REDACTED:dup]"
