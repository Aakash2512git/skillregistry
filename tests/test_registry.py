"""Tests for registry."""

from pathlib import Path

import pytest

from skillregistry.registry import SkillRegistry

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


def test_register_and_save_load(tmp_path):
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock"
    )
    count = registry.register()
    assert count == 5
    assert len(registry) == 5

    out = tmp_path / "index"
    registry.save(out)

    loaded = SkillRegistry.from_directory(out)
    assert len(loaded) == 5
    assert loaded.records[0].trigger_questions


def test_changed_only_skips_unchanged(tmp_path):
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock"
    )
    registry.register()
    out = tmp_path / "index"
    registry.save(out)

    registry2 = SkillRegistry.from_directory(out)
    registry2.paths = [str(FIXTURES)]
    count = registry2.register(changed_only=True)
    assert count == 0


def test_load_skill():
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock"
    )
    registry.register()
    doc = registry.load_skill("create-hook")
    assert "sessionStart" in doc.body


def test_get_record_not_found():
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock"
    )
    registry.register()
    with pytest.raises(KeyError):
        registry.get_record("nonexistent")
