"""Regex-based secret detectors.

Each pattern captures the sensitive span in a ``secret`` named group so the
surrounding context (an env var name, a key prefix) stays visible in the
redacted output — only the group itself gets replaced.
"""

import re
from typing import NamedTuple, Pattern


class Detector(NamedTuple):
    name: str
    pattern: Pattern


DETECTORS = [
    Detector(
        "aws-secret",
        re.compile(r"AWS_SECRET_ACCESS_KEY=(?P<secret>[A-Za-z0-9/+=]{16,})"),
    ),
    Detector(
        "aws-key-id",
        re.compile(r"(?P<secret>AKIA[0-9A-Z]{16})"),
    ),
    Detector(
        "stripe-key",
        re.compile(r"sk_(?:live|test)_(?P<secret>[A-Za-z0-9]{10,})"),
    ),
    Detector(
        "github-token",
        re.compile(r"(?P<secret>gh[pousr]_[A-Za-z0-9]{36,255})"),
    ),
    Detector(
        "slack-token",
        re.compile(r"(?P<secret>xox[baprs]-[A-Za-z0-9-]{10,})"),
    ),
    Detector(
        "gitlab-token",
        re.compile(r"(?P<secret>glpat-[A-Za-z0-9_-]{20,})"),
    ),
    Detector(
        "jwt",
        re.compile(r"(?P<secret>eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+)"),
    ),
    Detector(
        "email",
        # Local/domain parts are bounded (RFC 5321 caps the local part at 64
        # octets; real domains never approach 255) so a long run of word
        # characters with no "@" can't force O(n) backtracking at every
        # starting offset — unbounded `+` there is a quadratic-time DoS on
        # an oversized line.
        re.compile(r"(?P<secret>[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,255}\.[A-Za-z]{2,24})"),
    ),
    Detector(
        "ip",
        re.compile(
            r"(?P<secret>\b(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)\b)"
        ),
    ),
    Detector(
        "ip",
        re.compile(
            r"(?P<secret>"
            r"(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}"
            r"|(?:[A-Fa-f0-9]{1,4}:)+:(?:[A-Fa-f0-9]{1,4}(?::[A-Fa-f0-9]{1,4})*)?"
            r"|:(?::[A-Fa-f0-9]{1,4})+"
            r")"
        ),
    ),
]

ALL_DETECTOR_NAMES = sorted({detector.name for detector in DETECTORS})
