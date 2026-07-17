"""Safelog: a zero-dependency streaming secret redaction filter."""

from .redact import redact_line

__version__ = "0.1.0"
__all__ = ["redact_line", "__version__"]
