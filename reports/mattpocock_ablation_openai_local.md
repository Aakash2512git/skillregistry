# Ablation Results

# Skill Registry Eval Report

Queries: 30
Index mode: description
MRR: 0.700
Latency p50: 7.2 ms

## Recall@k
- Recall@1: 0.700 (70.0%)
- Recall@3: 0.700 (70.0%)
- Recall@5: 0.700 (70.0%)

## Failures

- Query: `Implement the work described in this spec using test-driven development` | expected: ['implement'] | got: ['to-spec']
- Query: `Which skill should I use for my current situation?` | expected: ['ask-matt'] | got: ['teach']
- Query: `Grill me on this plan and also update CONTEXT.md as we go` | expected: ['grill-with-docs'] | got: ['grill-me']
- Query: `Help me define ubiquitous language for this domain` | expected: ['domain-modeling'] | got: ['ubiquitous-language']
- Query: `Record an architectural decision and update the glossary` | expected: ['domain-modeling'] | got: ['ubiquitous-language']
- Query: `Scan my codebase for modules that need deepening` | expected: ['improve-codebase-architecture'] | got: ['codebase-design']
- Query: `Triage these GitHub issues and categorize them` | expected: ['triage'] | got: ['request-refactor-plan']
- Query: `Hand off this conversation to another agent` | expected: ['handoff'] | got: ['claude-handoff']
- Query: `Stress-test my plan before I commit to building it` | expected: ['grill-me'] | got: ['loop-me']

# Skill Registry Eval Report

Queries: 30
Index mode: full
MRR: 0.800
Latency p50: 7.1 ms

## Recall@k
- Recall@1: 0.800 (80.0%)
- Recall@3: 0.800 (80.0%)
- Recall@5: 0.800 (80.0%)

## Failures

- Query: `Grill me on this plan and also update CONTEXT.md as we go` | expected: ['grill-with-docs'] | got: ['grilling']
- Query: `Help me define ubiquitous language for this domain` | expected: ['domain-modeling'] | got: ['ubiquitous-language']
- Query: `Scan my codebase for modules that need deepening` | expected: ['improve-codebase-architecture'] | got: ['codebase-design']
- Query: `Hand off this conversation to another agent` | expected: ['handoff'] | got: ['claude-handoff']
- Query: `Red-green-refactor loop for fixing this bug` | expected: ['tdd'] | got: ['diagnosing-bugs']
- Query: `Stress-test my plan before I commit to building it` | expected: ['grill-me'] | got: ['grilling']
