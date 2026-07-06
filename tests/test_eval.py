"""Tests for eval harness."""

from pathlib import Path

from skillregistry.eval import load_eval_dataset, run_ablation, run_eval
from skillregistry.registry import SkillRegistry

FIXTURES = Path(__file__).parent / "fixtures" / "skills"
EVAL_DATA = Path(__file__).parent.parent / "eval" / "queries.jsonl"


def test_load_eval_dataset():
    queries = load_eval_dataset(EVAL_DATA)
    assert len(queries) >= 20
    assert queries[0].expected_ids


def test_run_eval():
    registry = SkillRegistry.from_paths(
        [str(FIXTURES)], llm="mock", embedder="mock", index_mode="full"
    )
    registry.register()
    queries = load_eval_dataset(EVAL_DATA)
    result = run_eval(registry, queries, top_k_values=[1, 3, 5])
    assert result.total_queries == len(queries)
    assert result.recall_at_k[3] >= 0.5
    assert result.mrr > 0


def test_ablation_full_beats_description():
    results = run_ablation(
        [str(FIXTURES)],
        str(EVAL_DATA),
        embedder="mock",
        llm="mock",
        top_k_values=[3],
    )
    assert "description" in results
    assert "full" in results
    # Full index with trigger questions should match or beat description-only
    assert results["full"].recall_at_k[3] >= results["description"].recall_at_k[3]
