from safelog.entropy import DEFAULT_THRESHOLD, find_high_entropy_tokens, shannon_entropy

RANDOM_SECRET = "aB3dE9fGh2JkLmN8pQrS5tUvWxYz012A"  # 32 random-looking base62 chars
UUID = "550e8400-e29b-41d4-a716-446655440000"
FILE_PATH = "usr/local/lib/python3.12/site-packages/pkg"
COMMON_SENTENCE = "the connection was closed by the remote host unexpectedly"


def test_shannon_entropy_of_empty_string_is_zero():
    assert shannon_entropy("") == 0.0


def test_shannon_entropy_of_repeated_char_is_zero():
    assert shannon_entropy("aaaaaaaa") == 0.0


def test_shannon_entropy_of_two_equally_likely_symbols_is_one_bit():
    assert shannon_entropy("abababab") == 1.0


def test_random_looking_32_char_token_is_flagged():
    matches = list(find_high_entropy_tokens(f"token: {RANDOM_SECRET} end"))
    assert [m.group(0) for m in matches] == [RANDOM_SECRET]


def test_short_random_token_below_min_length_is_not_flagged():
    short = RANDOM_SECRET[:20]
    assert list(find_high_entropy_tokens(f"token={short}")) == []


def test_uuid_is_not_flagged_at_default_threshold():
    assert list(find_high_entropy_tokens(f"request_id={UUID}", DEFAULT_THRESHOLD)) == []


def test_file_path_is_not_flagged_at_default_threshold():
    assert list(find_high_entropy_tokens(f"loading module from {FILE_PATH}", DEFAULT_THRESHOLD)) == []


def test_common_english_sentence_is_not_flagged():
    assert list(find_high_entropy_tokens(COMMON_SENTENCE, DEFAULT_THRESHOLD)) == []


def test_threshold_is_tunable():
    borderline = "sk_a8f5f167f44f4964e6c998dee827110c"  # hex-ish, entropy ~3.9
    assert list(find_high_entropy_tokens(borderline, threshold=3.5)) != []
    assert list(find_high_entropy_tokens(borderline, threshold=4.5)) == []
