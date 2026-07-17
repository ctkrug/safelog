"""Config file support for custom detectors and detector toggles.

Deliberately not a general TOML parser — safelog stays stdlib-only
across Python 3.9+ (the ``tomllib`` module only ships from 3.11), so
this implements just the subset of TOML the config file needs:

    [patterns]
    internal-id = "INTERNAL-[0-9]{6}"

    [detectors]
    disabled = ["email", "ip"]
"""

import re
from typing import List, NamedTuple

from .detectors import Detector

_SECTION_RE = re.compile(r"^\[(?P<name>[A-Za-z0-9_-]+)\]$")
_STRING_KV_RE = re.compile(r'^(?P<key>[A-Za-z0-9_-]+)\s*=\s*"(?P<value>(?:[^"\\]|\\.)*)"$')
_LIST_KV_RE = re.compile(r"^(?P<key>[A-Za-z0-9_-]+)\s*=\s*\[(?P<items>.*)\]$")
_STRING_ITEM_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


class Config(NamedTuple):
    custom_detectors: List[Detector]
    disabled_detectors: List[str]


EMPTY_CONFIG = Config(custom_detectors=[], disabled_detectors=[])


def parse_config(text: str) -> Config:
    """Parse config file text into a :class:`Config`.

    Unrecognized or malformed lines are ignored rather than raising, so a
    hand-edited config with an unsupported TOML feature degrades to "that
    line has no effect" instead of crashing the CLI.
    """
    section = None
    custom_detectors = []
    disabled_detectors = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            continue
        section_match = _SECTION_RE.match(line)
        if section_match:
            section = section_match.group("name")
            continue
        if section == "patterns":
            kv = _STRING_KV_RE.match(line)
            if kv:
                try:
                    pattern = re.compile(f"(?P<secret>{kv.group('value')})")
                except re.error:
                    continue
                custom_detectors.append(Detector(kv.group("key"), pattern))
        elif section == "detectors":
            kv = _LIST_KV_RE.match(line)
            if kv and kv.group("key") == "disabled":
                disabled_detectors = _STRING_ITEM_RE.findall(kv.group("items"))
    return Config(custom_detectors=custom_detectors, disabled_detectors=disabled_detectors)


def load_config(path: str) -> Config:
    """Load config from ``path``, falling back to defaults if it's absent."""
    try:
        with open(path, encoding="utf-8") as config_file:
            text = config_file.read()
    except FileNotFoundError:
        return EMPTY_CONFIG
    return parse_config(text)
