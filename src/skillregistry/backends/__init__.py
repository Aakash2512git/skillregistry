"""LLM backend factory."""

from __future__ import annotations

from skillregistry.backends.base import LLMBackend
from skillregistry.backends.mock import MockLLMBackend
from skillregistry.backends.openai_backend import OpenAILLMBackend


def create_llm_backend(spec: str | LLMBackend) -> LLMBackend:
    if isinstance(spec, LLMBackend):
        return spec
    if spec == "mock":
        return MockLLMBackend()
    if spec.startswith("openai:"):
        model = spec.split(":", 1)[1]
        return OpenAILLMBackend(model=model)
    if spec.startswith("openai"):
        return OpenAILLMBackend()
    raise ValueError(f"Unknown LLM backend: {spec}")
