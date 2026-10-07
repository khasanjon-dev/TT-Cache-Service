"""Transformer interface and a local stand-in for an external service."""

from typing import Protocol


class Transformer(Protocol):
    """Interface implemented by a transformer provider."""

    def transform(self, value: str) -> str:
        """Transform one input value."""


class SimulatedExternalTransformer:
    """Local stand-in that uppercases input instead of calling a remote service."""

    def transform(self, value: str) -> str:
        """Return an uppercase version of the input."""
        return value.upper()
