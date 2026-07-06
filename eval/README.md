# Evaluation Dataset

Add one JSON object per line to `queries.jsonl`:

```json
{"query": "How do I block shell commands?", "expected_ids": ["create-hook"], "difficulty": "easy"}
```

## Fields

| Field | Required | Description |
|-------|----------|-------------|
| `query` | yes | User query to route |
| `expected_ids` | yes | Skill id or name that should rank highly |
| `difficulty` | no | `easy`, `medium`, or `hard` |

## Run eval

```bash
skillregistry eval --paths tests/fixtures/skills -d eval/queries.jsonl --embedder mock --llm mock

# Ablation: description-only vs full (with trigger questions)
skillregistry eval --paths tests/fixtures/skills -d eval/queries.jsonl --ablate --embedder mock
```

## Metrics

- **Recall@k** — fraction of queries where expected skill appears in top-k
- **MRR** — mean reciprocal rank of first correct hit
- **Latency p50** — median retrieval time in ms

## Extending

1. Add skills to `tests/fixtures/skills/`
2. Add queries that paraphrase real user language (not copy-paste descriptions)
3. Include hard negatives (similar skills) to stress-test routing
