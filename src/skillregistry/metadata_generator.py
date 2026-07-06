"""LLM-based metadata generation for skills."""

from __future__ import annotations

import json
import re

from skillregistry.backends import create_llm_backend
from skillregistry.backends.base import LLMBackend
from skillregistry.backends.mock import MockLLMBackend
from skillregistry.models import PROMPT_VERSION, MetadataSource, ParsedSkill, SkillRecord

SYSTEM_PROMPT = """You are building a skill routing index for an LLM agent.
Given a skill document, produce metadata that helps route user queries to this skill.

Output ONLY valid JSON with these fields:
- trigger_questions: array of 5-8 realistic user queries that SHOULD route to this skill
- tags: array of 3-6 lowercase tags
- one_line_summary: string, max 120 chars

Rules:
- Questions must sound like real user prompts (imperative or question form)
- Include varied phrasing and synonyms
- Do NOT mention file paths or internal skill filenames
- Be specific to THIS skill's unique capability
- Output JSON only, no markdown fences"""

USER_TEMPLATE = """Skill name: {name}
Description: {description}

Skill body (truncated):
{body}
"""


def _extract_json(text: str) -> dict:
    text = text.strip()
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError(f"No JSON object in LLM output: {text[:200]}")
    return json.loads(text[start : end + 1])


def _normalize_metadata(raw: dict) -> dict:
    questions = raw.get("trigger_questions", [])
    if not isinstance(questions, list):
        questions = [str(questions)]
    questions = [str(q) for q in questions if q]

    tags = raw.get("tags", [])
    if not isinstance(tags, list):
        tags = [str(tags)] if tags else []
    tags = [str(t).lower() for t in tags]

    summary = raw.get("one_line_summary")
    if summary:
        summary = str(summary)[:120]

    return {
        "trigger_questions": questions,
        "tags": tags,
        "one_line_summary": summary,
    }


class MetadataGenerator:
    def __init__(self, llm: str | LLMBackend = "mock"):
        self.llm = create_llm_backend(llm)
        self.model_spec = llm if isinstance(llm, str) else "custom"

    def generate(self, skill: ParsedSkill, max_body_chars: int = 3000) -> dict:
        if isinstance(self.llm, MockLLMBackend):
            return _normalize_metadata(self.llm.generate_for_skill(skill))

        body = skill.body[:max_body_chars]
        user = USER_TEMPLATE.format(
            name=skill.name, description=skill.description, body=body
        )

        for attempt in range(2):
            raw_text = self.llm.complete(SYSTEM_PROMPT, user)
            try:
                return _normalize_metadata(_extract_json(raw_text))
            except (json.JSONDecodeError, ValueError):
                if attempt == 1:
                    raise

        raise RuntimeError("Failed to parse metadata from LLM")

    def enrich(
        self, skill: ParsedSkill, auto_metadata: bool = True
    ) -> SkillRecord:
        user_questions = list(skill.trigger_questions)
        metadata_source: MetadataSource = "auto"
        tags = list(skill.tags)
        categories = list(skill.categories)
        one_line_summary: str | None = None
        trigger_questions = list(user_questions)

        if user_questions:
            metadata_source = "user"
            if auto_metadata:
                generated = self.generate(skill)
                # Merge tags/summary from LLM but keep user questions
                tags = list({*tags, *generated.get("tags", [])})
                one_line_summary = generated.get("one_line_summary")
                if tags or one_line_summary:
                    metadata_source = "hybrid"
        elif auto_metadata:
            generated = self.generate(skill)
            trigger_questions = generated.get("trigger_questions", [])
            tags = generated.get("tags", tags)
            one_line_summary = generated.get("one_line_summary")
            metadata_source = "auto"
        else:
            metadata_source = "user"

        return SkillRecord(
            id=skill.id,
            name=skill.name,
            path=skill.path,
            description=skill.description,
            trigger_questions=trigger_questions,
            tags=tags,
            categories=categories,
            one_line_summary=one_line_summary,
            content_hash=skill.content_hash,
            metadata_source=metadata_source,
            prompt_version=PROMPT_VERSION,
            model=self.model_spec if auto_metadata else None,
        )
