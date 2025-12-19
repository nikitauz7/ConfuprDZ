from __future__ import annotations

class ConfigLangError(Exception):
    """Base error for the translator."""


class ConfigLangSyntaxError(ConfigLangError):
    """Raised when the input text cannot be parsed."""

    def __init__(self, message: str, *, line: int | None = None, column: int | None = None):
        self.line = line
        self.column = column
        super().__init__(message)


class ConfigLangEvalError(ConfigLangError):
    """Raised when constant expression evaluation fails."""
