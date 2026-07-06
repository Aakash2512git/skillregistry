"""Data models for skill registry."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

PROMPT_VERSION = "v1"
MetadataSource = Literal["user", "auto", "hybrid"]
IndexMode = Literal["description", "full"]


class ParsedSkill(BaseModel):
    """Raw parsed SKILL.md before metadata enrichment."""

    id: str
    name: str
    path: str
    description: str
    body: str
    content_hash: str
    trigger_questions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)


class SkillRecord(BaseModel):
    """Enriched skill stored in the registry."""

    id: str
    name: str
    path: str
    description: str
    trigger_questions: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    one_line_summary: str | None = None
    content_hash: str
    metadata_source: MetadataSource = "auto"
    prompt_version: str = PROMPT_VERSION
    model: str | None = None

    def to_index_text(self, mode: IndexMode = "full") -> str:
        """Build text for embedding."""
        if mode == "description":
            return f"{self.name}. {self.description}"

        parts = [f"{self.name}. {self.description}"]
        if self.one_line_summary:
            parts.append(self.one_line_summary)
        if self.trigger_questions:
            parts.append("Questions: " + "; ".join(self.trigger_questions))
        if self.tags:
            parts.append("Tags: " + ", ".join(self.tags))
        if self.categories:
            parts.append("Categories: " + ", ".join(self.categories))
        return ". ".join(parts)


class SkillMatch(BaseModel):
    """Retrieval result."""

    id: str
    name: str
    score: float
    description: str
    path: str


class SkillDocument(BaseModel):
    """Full skill content loaded on demand."""

    record: SkillRecord
    body: str


class RegistryConfig(BaseModel):
    """Persisted registry metadata."""

    version: str = "0.1.0"
    embedder: str = "mock"
    index_mode: IndexMode = "full"
    records: list[SkillRecord] = Field(default_factory=list)


class EvalQuery(BaseModel):
    """Single benchmark query."""

    query: str
    expected_ids: list[str]
    difficulty: str = "medium"
