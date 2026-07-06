"""Tests for retriever."""

from pathlib import Path

from skillregistry.registry import SkillRegistry

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


def _registry() -> SkillRegistry:
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock", index_mode="full"
    )
    registry.register()
    return registry


def test_retrieve_hook_query():
    registry = _registry()
    matches = registry.retrieve("block shell commands before they run", top_k=3)
    assert matches
    assert matches[0].name == "create-hook"


def test_retrieve_pdf_query():
    registry = _registry()
    matches = registry.retrieve("extract tables from PDF document", top_k=3)
    names = [m.name for m in matches]
    assert "pdf-processing" in names


def test_retrieve_kubernetes_query():
    registry = _registry()
    matches = registry.retrieve("deploy application to kubernetes cluster helm", top_k=3)
    names = [m.name for m in matches]
    assert "deploy-kubernetes" in names


def test_description_mode_still_retrieves():
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock", index_mode="description"
    )
    registry.register()
    matches = registry.retrieve("create cursor hooks for session start", top_k=3)
    names = [m.name for m in matches]
    assert "create-hook" in names
