"""Pluggable text embedders."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod

import numpy as np


class Embedder(ABC):
    @abstractmethod
    def encode(self, texts: list[str]) -> np.ndarray:
        """Return normalized embeddings, shape (n, dim)."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class MockEmbedder(Embedder):
    """Feature-hashing embedder for tests (no ML deps)."""

    def __init__(self, dim: int = 512, num_hashes: int = 4):
        self.dim = dim
        self.num_hashes = num_hashes

    @property
    def name(self) -> str:
        return "mock"

    def _tokenize(self, text: str) -> list[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _vectorize(self, text: str) -> np.ndarray:
        import hashlib

        vec = np.zeros(self.dim, dtype=np.float32)
        tokens = self._tokenize(text)
        for token in tokens:
            for i in range(self.num_hashes):
                digest = hashlib.md5(f"{i}:{token}".encode()).hexdigest()
                idx = int(digest, 16) % self.dim
                sign = 1.0 if int(digest[:2], 16) % 2 == 0 else -1.0
                vec[idx] += sign
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec

    def encode(self, texts: list[str]) -> np.ndarray:
        return np.stack([self._vectorize(t) for t in texts])


class LocalEmbedder(Embedder):
    """Sentence-transformers embedder."""

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def name(self) -> str:
        return f"local:{self.model_name}"

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as e:
                raise ImportError(
                    "Local embedder requires: pip install skillregistry[local]"
                ) from e
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, texts: list[str]) -> np.ndarray:
        model = self._get_model()
        embeddings = model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        )
        return np.asarray(embeddings, dtype=np.float32)


def create_embedder(spec: str = "mock") -> Embedder:
    if spec == "mock":
        return MockEmbedder()
    if spec == "local":
        return LocalEmbedder()
    if spec.startswith("local:"):
        return LocalEmbedder(model_name=spec.split(":", 1)[1])
    raise ValueError(f"Unknown embedder: {spec}")
