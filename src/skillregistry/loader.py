"""Load full skill documents."""

from __future__ import annotations

import re
from pathlib import Path

from skillregistry.models import SkillDocument, SkillRecord

_FRONTMATTER_RE = re.compile(r"^---\s*\n.*?\n---\s*\n(.*)", re.DOTALL)


def load_skill_body(path: str | Path) -> str:
    """Load markdown body from SKILL.md (strip frontmatter)."""
    raw = Path(path).read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(raw)
    if match:
        return match.group(1).strip()
    return raw.strip()


def load_document(record: SkillRecord) -> SkillDocument:
    """Load full skill content for a registry record."""
    body = load_skill_body(record.path)
    return SkillDocument(record=record, body=body)
