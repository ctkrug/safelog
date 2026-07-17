"""Line-level secret redaction."""

import re

from .detectors import DETECTORS

PEM_BEGIN_RE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
PEM_END_RE = re.compile(r"-----END [A-Z0-9 ]*PRIVATE KEY-----")
PEM_LABEL = "private-key"


def redact_line(line: str, detectors=DETECTORS) -> str:
    """Return ``line`` with every detected secret span replaced in place."""
    for detector in detectors:
        line = detector.pattern.sub(_replacer(detector.name), line)
    return line


def _replacer(name: str):
    def replace(match) -> str:
        return match.group(0).replace(match.group("secret"), f"[REDACTED:{name}]")

    return replace


class Redactor:
    """Stateful, line-at-a-time redactor.

    Wraps the stateless per-line regex detectors with a small state machine
    for PEM private-key blocks, which span multiple lines and must collapse
    to a single placeholder rather than leaking the key material line by
    line. State survives across calls, so a block split across an arbitrary
    number of ``process_line`` calls is still handled correctly.
    """

    def __init__(self, detectors=DETECTORS):
        self.detectors = detectors
        self._in_pem_block = False

    def process_line(self, line: str):
        """Return the redacted line, or ``None`` while buffering a PEM block."""
        if self._in_pem_block:
            if PEM_END_RE.search(line):
                self._in_pem_block = False
                return f"[REDACTED:{PEM_LABEL}]\n"
            return None
        if PEM_BEGIN_RE.search(line) and not PEM_END_RE.search(line):
            self._in_pem_block = True
            return None
        return redact_line(line, self.detectors)

    def flush(self):
        """Return output for any buffered-but-never-closed PEM block."""
        if self._in_pem_block:
            self._in_pem_block = False
            return f"[REDACTED:{PEM_LABEL}]\n"
        return None
