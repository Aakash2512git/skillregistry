"""Deterministic mock LLM for tests."""

from __future__ import annotations

import json

from skillregistry.backends.base import LLMBackend
from skillregistry.models import ParsedSkill

# Per-skill canned metadata keyed by skill name
_MOCK_METADATA: dict[str, dict] = {
    "create-hook": {
        "trigger_questions": [
            "How do I run a script when the agent session starts?",
            "Block dangerous shell commands before they run",
            "Set up beforeShellExecution hook in hooks.json",
            "Inject context before each user prompt",
            "Automate behavior around agent tool use events",
        ],
        "tags": ["hooks", "cursor", "automation", "session"],
        "one_line_summary": "Set up Cursor hooks for agent lifecycle and tool events.",
    },
    "create-rule": {
        "trigger_questions": [
            "How do I add persistent AI guidance for my project?",
            "Write a .cursor/rules file for coding standards",
            "Create AGENTS.md for team conventions",
            "Set up project-level rules for the agent",
            "Define always-on context for Cursor agent",
        ],
        "tags": ["rules", "cursor", "standards", "guidance"],
        "one_line_summary": "Author Cursor rules and AGENTS.md for persistent guidance.",
    },
    "create-skill": {
        "trigger_questions": [
            "How do I write a new Agent Skill?",
            "What goes in SKILL.md frontmatter?",
            "Create a skill for my custom workflow",
            "Author SKILL.md structure and layout",
            "Add a new skill to .cursor/skills",
        ],
        "tags": ["skills", "cursor", "authoring"],
        "one_line_summary": "Author Cursor Agent Skills with proper SKILL.md structure.",
    },
    "pdf-processing": {
        "trigger_questions": [
            "Extract tables from a PDF document",
            "Fill out PDF form fields programmatically",
            "Merge multiple PDF files into one",
            "Parse text from a scanned PDF",
            "Work with PDF documents and forms",
        ],
        "tags": ["pdf", "documents", "forms"],
        "one_line_summary": "Process PDFs — extract, fill forms, and merge documents.",
    },
    "deploy-kubernetes": {
        "trigger_questions": [
            "Deploy my app to a Kubernetes cluster",
            "Create a Helm chart for deployment",
            "Set up kubectl deployment and service",
            "Configure ConfigMaps and Secrets in k8s",
            "Roll out application to production cluster",
        ],
        "tags": ["kubernetes", "devops", "helm", "deploy"],
        "one_line_summary": "Deploy and manage apps on Kubernetes with kubectl and Helm.",
    },
}


def _default_metadata(skill: ParsedSkill) -> dict:
    return {
        "trigger_questions": [
            f"How do I use {skill.name}?",
            f"Help me with {skill.description[:60]}",
            f"Guide for {skill.name} workflow",
        ],
        "tags": skill.tags or ["general"],
        "one_line_summary": skill.description[:120],
    }


class MockLLMBackend(LLMBackend):
    def complete(self, system: str, user: str) -> str:
        # Extract skill name from user prompt
        for name, meta in _MOCK_METADATA.items():
            if f"Skill name: {name}" in user:
                return json.dumps(meta)
        return json.dumps(
            {
                "trigger_questions": ["How do I complete this task?"],
                "tags": ["general"],
                "one_line_summary": "General skill assistance.",
            }
        )

    def generate_for_skill(self, skill: ParsedSkill) -> dict:
        return _MOCK_METADATA.get(skill.name, _default_metadata(skill))
