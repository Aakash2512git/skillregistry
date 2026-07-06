"""Vector index for skill retrieval."""

from __future__ import annotations

import pickle
from pathlib import Path

import numpy as np

from skillregistry.embedder import Embedder, create_embedder
from skillregistry.models import IndexMode, SkillRecord


class SkillIndex:
    """In-memory vector index with optional FAISS backend."""

    def __init__(self):
        self._embeddings: np.ndarray | None = None
        self._faiss_index = None
        self._embedder_name: str = "mock"
        self._index_mode: IndexMode = "full"

    @property
    def is_built(self) -> bool:
        return self._embeddings is not None or self._faiss_index is not None

    def build(
        self,
        records: list[SkillRecord],
        embedder: str | Embedder = "mock",
        index_mode: IndexMode = "full",
    ) -> None:
        emb = embedder if isinstance(embedder, Embedder) else create_embedder(embedder)
        texts = [r.to_index_text(index_mode) for r in records]
        embeddings = emb.encode(texts)

        self._embedder_name = emb.name
        self._index_mode = index_mode
        self._embeddings = embeddings

        try:
            import faiss

            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            self._faiss_index = index
        except ImportError:
            self._faiss_index = None

    def search(
        self, query: str, embedder: Embedder, top_k: int = 5
    ) -> list[tuple[int, float]]:
        if not self.is_built:
            raise RuntimeError("Index not built")

        q_emb = embedder.encode([query])
        k = min(top_k, len(q_emb))

        if self._faiss_index is not None:
            scores, indices = self._faiss_index.search(q_emb, k)
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx < 0:
                    continue
                results.append((int(idx), float(score)))
            return results

        # Fallback: numpy cosine (embeddings already normalized)
        sims = (self._embeddings @ q_emb.T).flatten()
        top_indices = np.argsort(-sims)[:k]
        return [(int(i), float(sims[i])) for i in top_indices]

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        data = {
            "embedder_name": self._embedder_name,
            "index_mode": self._index_mode,
            "embeddings": self._embeddings,
        }
        with open(directory / "index.pkl", "wb") as f:
            pickle.dump(data, f)

        if self._faiss_index is not None:
            import faiss

            faiss.write_index(self._faiss_index, str(directory / "index.faiss"))

    def load(self, directory: str | Path) -> None:
        directory = Path(directory)
        with open(directory / "index.pkl", "rb") as f:
            data = pickle.load(f)

        self._embedder_name = data["embedder_name"]
        self._index_mode = data["index_mode"]
        self._embeddings = data["embeddings"]
        self._faiss_index = None

        faiss_path = directory / "index.faiss"
        if faiss_path.exists():
            import faiss

            self._faiss_index = faiss.read_index(str(faiss_path))
