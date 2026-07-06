"""Evaluation harness for skill retrieval quality."""

from __future__ import annotations

import json
import statistics
import time
from dataclasses import dataclass, field
from pathlib import Path

from skillregistry.models import EvalQuery, IndexMode
from skillregistry.registry import SkillRegistry


@dataclass
class EvalResult:
    recall_at_k: dict[int, float] = field(default_factory=dict)
    mrr: float = 0.0
    latency_p50_ms: float = 0.0
    failures: list[dict] = field(default_factory=list)
    total_queries: int = 0
    index_mode: str = "full"

    def format_report(self) -> str:
        lines = [
            f"# Skill Registry Eval Report",
            f"",
            f"Queries: {self.total_queries}",
            f"Index mode: {self.index_mode}",
            f"MRR: {self.mrr:.3f}",
            f"Latency p50: {self.latency_p50_ms:.1f} ms",
            f"",
            "## Recall@k",
        ]
        for k, v in sorted(self.recall_at_k.items()):
            lines.append(f"- Recall@{k}: {v:.3f} ({v * 100:.1f}%)")

        if self.failures:
            lines.extend(["", "## Failures", ""])
            for f in self.failures:
                lines.append(
                    f"- Query: `{f['query']}` | expected: {f['expected']} | "
                    f"got: {f['got']}"
                )
        return "\n".join(lines)


def load_eval_dataset(path: str | Path) -> list[EvalQuery]:
    queries: list[EvalQuery] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        queries.append(EvalQuery.model_validate(json.loads(line)))
    return queries


def run_eval(
    registry: SkillRegistry,
    dataset: list[EvalQuery],
    top_k_values: list[int] | None = None,
    index_mode: IndexMode | None = None,
) -> EvalResult:
    if top_k_values is None:
        top_k_values = [1, 3, 5]

    max_k = max(top_k_values)
    mode = index_mode or registry.index_mode

    # Rebuild index in requested mode if different
    if mode != registry.index_mode:
        registry.index_mode = mode
        registry.build_index()

    hits_at_k = {k: 0 for k in top_k_values}
    reciprocal_ranks: list[float] = []
    latencies: list[float] = []
    failures: list[dict] = []

    for item in dataset:
        start = time.perf_counter()
        matches = registry.retrieve(item.query, top_k=max_k)
        latencies.append((time.perf_counter() - start) * 1000)

        retrieved_ids = [m.id for m in matches]
        retrieved_names = [m.name for m in matches]
        expected = set(item.expected_ids)

        # Match by id or name
        def _hit(ids: list[str]) -> bool:
            for e in expected:
                if e in ids:
                    return True
                for rid in ids:
                    if rid == e:
                        return True
            return False

        for k in top_k_values:
            top_ids = retrieved_ids[:k] + retrieved_names[:k]
            if _hit(top_ids):
                hits_at_k[k] += 1

        rr = 0.0
        for rank, (rid, rname) in enumerate(
            zip(retrieved_ids, retrieved_names), start=1
        ):
            if any(e in (rid, rname) for e in expected):
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        if not _hit(retrieved_ids[: max(top_k_values)]):
            failures.append(
                {
                    "query": item.query,
                    "expected": list(expected),
                    "got": retrieved_names[:3],
                    "difficulty": item.difficulty,
                }
            )

    n = len(dataset) or 1
    return EvalResult(
        recall_at_k={k: hits_at_k[k] / n for k in top_k_values},
        mrr=sum(reciprocal_ranks) / n,
        latency_p50_ms=statistics.median(latencies) if latencies else 0.0,
        failures=failures,
        total_queries=len(dataset),
        index_mode=mode,
    )


def run_ablation(
    paths: list[str],
    dataset_path: str,
    embedder: str = "mock",
    llm: str = "mock",
    top_k_values: list[int] | None = None,
) -> dict[str, EvalResult]:
    """Compare description-only vs full index modes."""
    results: dict[str, EvalResult] = {}
    dataset = load_eval_dataset(dataset_path)

    for mode in ("description", "full"):
        registry = SkillRegistry.from_paths(
            paths, llm=llm, embedder=embedder, index_mode=mode
        )
        registry.register()
        results[mode] = run_eval(
            registry, dataset, top_k_values=top_k_values, index_mode=mode
        )
    return results
