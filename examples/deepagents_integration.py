#!/usr/bin/env python3
"""Integrate skillregistry with LangChain Deep Agents.

Use skillregistry for semantic skill routing on large SKILL.md libraries,
and Deep Agents for planning, filesystem, sub-agents, and context management.

Prerequisites:
    pip install "skillregistry[local,openai]" deepagents langchain-openai

    # deepagents requires Python 3.11+

Build a skill index once:
    export OPENAI_API_KEY=sk-...

    skillregistry register tests/fixtures/skills -o .skill-index \\
        --llm openai:gpt-4o-mini --embedder local

Run:
    python examples/deepagents_integration.py \\
        --index .skill-index \\
        --query "Help me write tests first for this API endpoint"
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

SKILL_SYSTEM_PROMPT = """You have a skill library via retrieve_skills and load_skill.

Workflow for every new user task:
1. Call retrieve_skills with a short search query.
2. Call load_skill for the best match before giving detailed guidance.
3. Follow the loaded SKILL.md instructions precisely.
4. If the task spans multiple domains, retrieve and load additional skills.

Do not guess skill content — always load_skill first.

You also have Deep Agents built-in tools (planning, filesystem, sub-agents).
Use those when the loaded skill calls for multi-step work or file operations."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a Deep Agent with skillregistry retrieval tools."
    )
    parser.add_argument(
        "--index",
        type=Path,
        default=Path(".skill-index"),
        help="Path to a pre-built skillregistry index directory",
    )
    parser.add_argument(
        "--query",
        required=True,
        help="User task to send to the agent",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("DEEPAGENTS_MODEL", "openai:gpt-4o-mini"),
        help="Model for create_deep_agent (default: openai:gpt-4o-mini)",
    )
    return parser.parse_args()


def build_skill_tools(registry):
    from langchain_core.tools import tool

    @tool
    def retrieve_skills(query: str, top_k: int = 3) -> str:
        """Search the skill library for skills relevant to the user's task.

        Call at the start of every new task with a short natural-language query.
        """
        matches = registry.retrieve(query, top_k=top_k)
        if not matches:
            return "No matching skills found."
        lines = [
            f"- id={m.id} name={m.name} score={m.score:.3f}: {m.description}"
            for m in matches
        ]
        return "Matching skills:\n" + "\n".join(lines)

    @tool
    def load_skill(skill_id: str) -> str:
        """Load full SKILL.md instructions for a skill by id or name.

        Always call after retrieve_skills before following a skill playbook.
        """
        doc = registry.load_skill(skill_id)
        return f"# Skill: {doc.record.name}\n\n{doc.body}"

    return retrieve_skills, load_skill


def main() -> int:
    args = parse_args()

    if not args.index.exists():
        print(
            f"Index not found: {args.index}\n"
            "Build one first, e.g.:\n"
            "  skillregistry register tests/fixtures/skills -o .skill-index "
            "--llm mock --embedder mock",
            file=sys.stderr,
        )
        return 1

    if not os.environ.get("OPENAI_API_KEY"):
        print("Warning: OPENAI_API_KEY is not set.", file=sys.stderr)

    try:
        from deepagents import create_deep_agent
    except ImportError:
        print(
            "deepagents is not installed. Install with:\n"
            "  pip install deepagents langchain-openai",
            file=sys.stderr,
        )
        return 1

    from skillregistry import SkillRegistry

    registry = SkillRegistry.from_directory(args.index)
    retrieve_skills, load_skill = build_skill_tools(registry)

    agent = create_deep_agent(
        model=args.model,
        tools=[retrieve_skills, load_skill],
        system_prompt=SKILL_SYSTEM_PROMPT,
        # Use skillregistry tools instead of built-in skills=[] for large libraries.
    )

    print(f"Index: {args.index} ({len(registry)} skills)")
    print(f"Query: {args.query}\n")

    result = agent.invoke({"messages": [{"role": "user", "content": args.query}]})
    messages = result.get("messages", [])
    if not messages:
        print("No response from agent.")
        return 1

    print(messages[-1].content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
