"""Line-level secret redaction."""

import hashlib
import re

from .detectors import DETECTORS
from .entropy import DEFAULT_THRESHOLD as DEFAULT_ENTROPY_THRESHOLD
from .entropy import find_high_entropy_tokens

PEM_BEGIN_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
PEM_END_RE = re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----")
PEM_LABEL = "private-key"
ENTROPY_LABEL = "high-entropy"

MODES = ("label", "mask", "hash")
DEFAULT_MODE = "label"


def format_replacement(mode: str, name: str, secret: str) -> str:
    """Render the placeholder that replaces a detected secret's span."""
    if mode == "mask":
        return "***"
    if mode == "hash":
        digest = hashlib.sha256(secret.encode()).hexdigest()[:8]
        return f"[REDACTED:{digest}]"
    return f"[REDACTED:{name}]"


def redact_line(line: str, detectors=DETECTORS, mode: str = DEFAULT_MODE) -> str:
    """Return ``line`` with every detected secret span replaced in place."""
    for detector in detectors:
        line = detector.pattern.sub(_replacer(detector.name, mode), line)
    return line


def _replacer(name: str, mode: str):
    def replace(match) -> str:
        secret = match.group("secret")
        return match.group(0).replace(secret, format_replacement(mode, name, secret))

    return replace


def redact_entropy(
    line: str,
    mode: str = DEFAULT_MODE,
    threshold: float = DEFAULT_ENTROPY_THRESHOLD,
) -> str:
    """Replace high-entropy token-like substrings the regex detectors missed.

    Runs on ``line`` *after* regex substitution, so already-redacted spans
    are short placeholders (``[REDACTED:x]``, ``***``, a hash) — never long
    enough to be mistaken for another secret.
    """
    matches = list(find_high_entropy_tokens(line, threshold))
    if not matches:
        return line
    pieces = []
    cursor = 0
    for match in matches:
        pieces.append(line[cursor : match.start()])
        pieces.append(format_replacement(mode, ENTROPY_LABEL, match.group(0)))
        cursor = match.end()
    pieces.append(line[cursor:])
    return "".join(pieces)


class Redactor:
    """Stateful, line-at-a-time redactor.

    Wraps the stateless per-line regex detectors with a small state machine
    for PEM private-key blocks, which span multiple lines and must collapse
    to a single placeholder rather than leaking the key material line by
    line. State survives across calls, so a block split across an arbitrary
    number of ``process_line`` calls is still handled correctly.
    """

    def __init__(
        self,
        detectors=DETECTORS,
        mode: str = DEFAULT_MODE,
        detect_pem: bool = True,
        detect_entropy: bool = True,
        entropy_threshold: float = DEFAULT_ENTROPY_THRESHOLD,
    ):
        self.detectors = detectors
        self.mode = mode
        self.detect_pem = detect_pem
        self.detect_entropy = detect_entropy
        self.entropy_threshold = entropy_threshold
        self._in_pem_block = False
        self._pem_buffer = []

    def process_line(self, line: str):
        """Return the redacted line, or ``None`` while buffering a PEM block."""
        if not self.detect_pem:
            return self._finish(redact_line(line, self.detectors, self.mode))
        if self._in_pem_block:
            self._pem_buffer.append(line)
            if PEM_END_RE.search(line):
                return self._collapse_pem()
            return None
        begin_match = PEM_BEGIN_RE.search(line)
        if begin_match:
            end_match = PEM_END_RE.search(line, begin_match.end())
            if end_match:
                return self._finish(self._collapse_inline_pem(line, begin_match, end_match))
            self._in_pem_block = True
            self._pem_buffer = [line]
            return None
        return self._finish(redact_line(line, self.detectors, self.mode))

    def _collapse_inline_pem(self, line: str, begin_match, end_match) -> str:
        prefix = redact_line(line[: begin_match.start()], self.detectors, self.mode)
        suffix = redact_line(line[end_match.end() :], self.detectors, self.mode)
        secret = line[begin_match.start() : end_match.end()]
        return prefix + format_replacement(self.mode, PEM_LABEL, secret) + suffix

    def _finish(self, text: str) -> str:
        if self.detect_entropy:
            return redact_entropy(text, self.mode, self.entropy_threshold)
        return text

    def flush(self):
        """Return output for any buffered-but-never-closed PEM block."""
        if self._in_pem_block:
            return self._collapse_pem()
        return None

    def _collapse_pem(self) -> str:
        self._in_pem_block = False
        secret = "".join(self._pem_buffer)
        self._pem_buffer = []
        return format_replacement(self.mode, PEM_LABEL, secret) + "\n"
