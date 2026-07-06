"""Tests for metadata generator."""

from pathlib import Path

from skillregistry.metadata_generator import MetadataGenerator
from skillregistry.scanner import parse_skill_file

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


def test_mock_metadata_generation():
    skill = parse_skill_file(FIXTURES / "create-hook" / "SKILL.md")
    gen = MetadataGenerator(llm="mock")
    meta = gen.generate(skill)
    assert len(meta["trigger_questions"]) >= 3
    assert "hooks" in meta["tags"] or "cursor" in meta["tags"]
    assert meta["one_line_summary"]


def test_enrich_auto_metadata():
    skill = parse_skill_file(FIXTURES / "pdf-processing" / "SKILL.md")
    gen = MetadataGenerator(llm="mock")
    record = gen.enrich(skill, auto_metadata=True)
    assert record.metadata_source == "auto"
    assert len(record.trigger_questions) >= 3
    assert record.one_line_summary
