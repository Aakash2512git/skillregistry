"""OpenAI LLM backend."""

from __future__ import annotations

import os

from skillregistry.backends.base import LLMBackend


class OpenAILLMBackend(LLMBackend):
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    def complete(self, system: str, user: str) -> str:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise ImportError(
                "OpenAI backend requires: pip install skillregistry[openai]"
            ) from e

        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
