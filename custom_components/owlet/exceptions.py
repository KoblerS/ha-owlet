"""Exceptions for the Owlet integration."""

from __future__ import annotations


class OwletError(Exception):
    """Base error."""


class OwletAuthenticationError(OwletError):
    """Raised when authentication fails for a recoverable/credential reason."""


class OwletCredentialsError(OwletAuthenticationError):
    """Raised when the supplied username/password are rejected."""


class OwletConnectionError(OwletError):
    """Raised when the Owlet/Ayla API cannot be reached."""


class OwletDevicesError(OwletError):
    """Raised when no supported devices are found on the account."""
