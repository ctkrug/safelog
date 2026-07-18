"""Safelog: a zero-dependency streaming secret redaction filter."""

from .redact import redact_line

__version__ = "1.0.1"
__all__ = ["redact_line", "__version__"]
