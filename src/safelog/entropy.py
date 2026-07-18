"""Shannon-entropy fallback detector for token-like secrets regex can't name.

Runs after the regex detectors, over whatever text they left behind, so it
only ever sees spans the regexes didn't already redact.
"""

import math
import re
from collections import Counter

TOKEN_RE = re.compile(r"[A-Za-z0-9+_=-]+")
MIN_TOKEN_LENGTH = 32
DEFAULT_THRESHOLD = 4.3


def shannon_entropy(data: str) -> float:
    """Return the Shannon entropy of ``data`` in bits per character."""
    if not data:
        return 0.0
    length = len(data)
    counts = Counter(data)
    return -sum((n / length) * math.log2(n / length) for n in counts.values())


def find_high_entropy_tokens(
    line: str,
    threshold: float = DEFAULT_THRESHOLD,
    min_length: int = MIN_TOKEN_LENGTH,
):
    """Yield regex ``Match`` objects for token-like substrings scoring above ``threshold``.

    Candidates are contiguous runs of token-ish characters (letters, digits,
    ``+_=-``) at least ``min_length`` long — long enough to exclude ordinary
    words, and excluding path separators and dots keeps file paths from
    forming one long candidate out of several short, low-entropy segments.
    """
    for match in TOKEN_RE.finditer(line):
        token = match.group(0)
        if len(token) < min_length:
            continue
        if shannon_entropy(token) >= threshold:
            yield match
