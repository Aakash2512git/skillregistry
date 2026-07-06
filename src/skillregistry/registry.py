"""Skill registry — register, index, retrieve."""

from __future__ import annotations

import json
from pathlib import Path

from skillregistry.embedder import create_embedder
from skillregistry.index import SkillIndex
from skillregistry.loader import load_document
from skillregistry.metadata_generator import MetadataGenerator
from skillregistry.models import IndexMode, RegistryConfig, SkillDocument, SkillMatch, SkillRecord
from skillregistry.retriever import Retriever
from skillregistry.scanner import scan_paths


class SkillRegistry:
    def __init__(
        self,
        paths: list[str | Path] | None = None,
        llm: str = "mock",
        auto_metadata: bool = True,
        embedder: str = "mock",
        index_mode: IndexMode = "full",
    ):
        self.paths = [str(p) for p in (paths or [])]
        self.llm = llm
        self.auto_metadata = auto_metadata
        self.embedder_spec = embedder
        self.index_mode = index_mode
        self.records: list[SkillRecord] = []
        self._index = SkillIndex()
        self._retriever: Retriever | None = None

    @classmethod
    def from_paths(
        cls,
        paths: list[str | Path],
        llm: str = "mock",
        auto_metadata: bool = True,
        embedder: str = "mock",
        index_mode: IndexMode = "full",
    ) -> SkillRegistry:
        return cls(
            paths=paths,
            llm=llm,
            auto_metadata=auto_metadata,
            embedder=embedder,
            index_mode=index_mode,
        )

    @classmethod
    def from_directory(cls, directory: str | Path) -> SkillRegistry:
        directory = Path(directory)
        config_path = directory / "registry.json"
        data = json.loads(config_path.read_text(encoding="utf-8"))
        config = RegistryConfig.model_validate(data)

        registry = cls(
            embedder=config.embedder,
            index_mode=config.index_mode,
        )
        registry.records = config.records
        registry._index.load(directory)
        registry._build_retriever()
        return registry

    def register(self, changed_only: bool = False) -> int:
        """Scan paths, generate metadata, build index. Returns count of new/updated skills."""
        if not self.paths:
            raise ValueError("No paths configured. Use from_paths() or set paths.")

        parsed = scan_paths(self.paths)
        generator = MetadataGenerator(llm=self.llm)

        existing = {r.id: r for r in self.records}
        updated: list[SkillRecord] = []
        changed_count = 0

        for skill in parsed:
            prev = existing.get(skill.id)
            if changed_only and prev and prev.content_hash == skill.content_hash:
                updated.append(prev)
                continue

            record = generator.enrich(skill, auto_metadata=self.auto_metadata)
            updated.append(record)
            if not prev or prev.content_hash != skill.content_hash:
                changed_count += 1

        self.records = updated
        self.build_index()
        return changed_count

    def build_index(self, embedder: str | None = None) -> None:
        spec = embedder or self.embedder_spec
        self.embedder_spec = spec
        self._index.build(
            self.records, embedder=spec, index_mode=self.index_mode
        )
        self._build_retriever()

    def _build_retriever(self) -> None:
        self._retriever = Retriever(
            records=self.records,
            index=self._index,
            embedder=self.embedder_spec,
            index_mode=self.index_mode,
        )

    def retrieve(self, query: str, top_k: int = 5) -> list[SkillMatch]:
        if self._retriever is None:
            raise RuntimeError("Registry not built. Call register() or load().")
        return self._retriever.retrieve(query, top_k=top_k)

    def load_skill(self, skill_id: str) -> SkillDocument:
        for record in self.records:
            if record.id == skill_id or record.name == skill_id:
                return load_document(record)
        raise KeyError(f"Skill not found: {skill_id}")

    def get_record(self, skill_id: str) -> SkillRecord:
        for record in self.records:
            if record.id == skill_id or record.name == skill_id:
                return record
        raise KeyError(f"Skill not found: {skill_id}")

    def save(self, directory: str | Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)

        config = RegistryConfig(
            embedder=self.embedder_spec,
            index_mode=self.index_mode,
            records=self.records,
        )
        (directory / "registry.json").write_text(
            config.model_dump_json(indent=2), encoding="utf-8"
        )
        self._index.save(directory)

    def __len__(self) -> int:
        return len(self.records)
