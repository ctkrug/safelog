"""Line-level secret redaction."""

from .detectors import DETECTORS


def redact_line(line: str) -> str:
    """Return ``line`` with every detected secret span replaced in place."""
    for detector in DETECTORS:
        line = detector.pattern.sub(_replacer(detector.name), line)
    return line


def _replacer(name: str):
    def replace(match) -> str:
        return match.group(0).replace(match.group("secret"), f"[REDACTED:{name}]")

    return replace
