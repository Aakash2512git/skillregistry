"""Skill retrieval."""

from __future__ import annotations

from skillregistry.embedder import Embedder, create_embedder
from skillregistry.index import SkillIndex
from skillregistry.models import IndexMode, SkillMatch, SkillRecord


class Retriever:
    def __init__(
        self,
        records: list[SkillRecord],
        index: SkillIndex,
        embedder: str | Embedder = "mock",
        index_mode: IndexMode = "full",
    ):
        self.records = records
        self.index = index
        self.embedder = (
            embedder if isinstance(embedder, Embedder) else create_embedder(embedder)
        )
        self.index_mode = index_mode

    def retrieve(self, query: str, top_k: int = 5) -> list[SkillMatch]:
        hits = self.index.search(query, self.embedder, top_k=top_k)
        results: list[SkillMatch] = []
        for idx, score in hits:
            record = self.records[idx]
            results.append(
                SkillMatch(
                    id=record.id,
                    name=record.name,
                    score=score,
                    description=record.description,
                    path=record.path,
                )
            )
        return results
