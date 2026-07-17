"""Line-level secret redaction."""

import hashlib
import re

from .detectors import DETECTORS

PEM_BEGIN_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
PEM_END_RE = re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----")
PEM_LABEL = "private-key"

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


class Redactor:
    """Stateful, line-at-a-time redactor.

    Wraps the stateless per-line regex detectors with a small state machine
    for PEM private-key blocks, which span multiple lines and must collapse
    to a single placeholder rather than leaking the key material line by
    line. State survives across calls, so a block split across an arbitrary
    number of ``process_line`` calls is still handled correctly.
    """

    def __init__(self, detectors=DETECTORS, mode: str = DEFAULT_MODE, detect_pem: bool = True):
        self.detectors = detectors
        self.mode = mode
        self.detect_pem = detect_pem
        self._in_pem_block = False
        self._pem_buffer = []

    def process_line(self, line: str):
        """Return the redacted line, or ``None`` while buffering a PEM block."""
        if not self.detect_pem:
            return redact_line(line, self.detectors, self.mode)
        if self._in_pem_block:
            self._pem_buffer.append(line)
            if PEM_END_RE.search(line):
                return self._collapse_pem()
            return None
        if PEM_BEGIN_RE.search(line) and not PEM_END_RE.search(line):
            self._in_pem_block = True
            self._pem_buffer = [line]
            return None
        return redact_line(line, self.detectors, self.mode)

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
