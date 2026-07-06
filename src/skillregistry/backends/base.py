"""LLM backends for metadata generation."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMBackend(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str:
        """Return raw LLM text response."""
