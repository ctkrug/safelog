import math
import random

from hypothesis import given
from hypothesis import strategies as st

from safelog.entropy import find_high_entropy_tokens, shannon_entropy

text = st.text(min_size=0, max_size=200)
nonempty_text = st.text(min_size=1, max_size=200)


@given(text)
def test_entropy_is_never_negative(s):
    assert shannon_entropy(s) >= 0.0


@given(st.characters(), st.integers(min_value=1, max_value=50))
def test_entropy_of_any_repeated_single_char_is_zero(char, n):
    assert shannon_entropy(char * n) == 0.0


@given(nonempty_text)
def test_entropy_is_bounded_by_log2_of_distinct_chars(s):
    max_possible = math.log2(len(set(s)))
    assert shannon_entropy(s) <= max_possible + 1e-9


@given(nonempty_text)
def test_entropy_is_invariant_under_shuffling(s):
    # Shannon entropy is a function of the character *frequency* distribution
    # only, so scrambling the order of an already-generated string must never
    # change its score.
    chars = list(s)
    random.Random(0).shuffle(chars)
    shuffled = "".join(chars)
    assert shannon_entropy(s) == shannon_entropy(shuffled)


@given(text, st.floats(min_value=0, max_value=8, allow_nan=False), st.integers(min_value=1, max_value=64))
def test_every_flagged_token_actually_clears_the_bar(line, threshold, min_length):
    for match in find_high_entropy_tokens(line, threshold=threshold, min_length=min_length):
        token = match.group(0)
        assert len(token) >= min_length
        assert shannon_entropy(token) >= threshold
