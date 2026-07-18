import ipaddress
import string

from hypothesis import assume, given
from hypothesis import strategies as st

from safelog.redact import redact_line

alnum_run = st.text(alphabet=string.ascii_letters + string.digits, min_size=0, max_size=8)
hex_run = st.text(alphabet="0123456789abcdefABCDEF", min_size=1, max_size=4)
ipv6_int = st.integers(min_value=0, max_value=2**128 - 1)


@given(alnum_run, hex_run)
def test_hex_tail_of_an_identifier_before_double_colon_is_never_flagged(rest, hexrun):
    # "s" guarantees a non-hex, alnum char always sits directly in front of
    # hexrun, mirroring the shape of "std::", "...cord::", etc. — the class
    # of false positive the leading lookbehind guard exists to reject.
    prefix = "s" + rest
    line = f"scope {prefix}{hexrun}:: end\n"
    assert f"{prefix}{hexrun}::" in redact_line(line)


@given(ipv6_int)
def test_any_valid_ipv6_address_between_delimiters_is_redacted(as_int):
    address = str(ipaddress.IPv6Address(as_int))
    # "::" (all-zeros) is the deliberate exception: a bare double colon reads
    # as a route/placeholder, not a secret worth flagging (see
    # test_bare_double_colon_is_not_flagged_as_ipv6 in test_redact.py).
    assume(address != "::")
    line = f"peer [{address}]:443 connected\n"
    out = redact_line(line)
    assert "[REDACTED:ip]" in out
    assert address not in out
