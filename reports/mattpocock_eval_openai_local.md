# Skill Registry Eval Report

Queries: 30
Index mode: full
MRR: 0.767
Latency p50: 7.2 ms

## Recall@k
- Recall@1: 0.767 (76.7%)
- Recall@3: 0.767 (76.7%)
- Recall@5: 0.767 (76.7%)

## Failures

- Query: `Implement the work described in this spec using test-driven development` | expected: ['implement'] | got: ['to-spec']
- Query: `Grill me on this plan and also update CONTEXT.md as we go` | expected: ['grill-with-docs'] | got: ['grilling']
- Query: `Help me define ubiquitous language for this domain` | expected: ['domain-modeling'] | got: ['ubiquitous-language']
- Query: `Triage these GitHub issues and categorize them` | expected: ['triage'] | got: ['setup-matt-pocock-skills']
- Query: `Hand off this conversation to another agent` | expected: ['handoff'] | got: ['claude-handoff']
- Query: `Red-green-refactor loop for fixing this bug` | expected: ['tdd'] | got: ['diagnosing-bugs']
- Query: `Stress-test my plan before I commit to building it` | expected: ['grill-me'] | got: ['grilling']