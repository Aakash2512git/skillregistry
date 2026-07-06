"""Discover and parse Cursor-style SKILL.md files."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml

from skillregistry.models import ParsedSkill

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n(.*)", re.DOTALL)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _expand_path(path: str | Path) -> Path:
    return Path(path).expanduser().resolve()


def _normalize_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value)]


def parse_skill_file(path: Path) -> ParsedSkill:
    """Parse a single SKILL.md file."""
    raw = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(raw)
    if not match:
        raise ValueError(f"Missing YAML frontmatter in {path}")

    frontmatter = yaml.safe_load(match.group(1)) or {}
    body = match.group(2).strip()

    name = frontmatter.get("name")
    description = frontmatter.get("description")
    if not name or not description:
        raise ValueError(f"SKILL.md must have name and description: {path}")

    skill_id = str(frontmatter.get("id", name))
    return ParsedSkill(
        id=skill_id,
        name=str(name),
        path=str(path.resolve()),
        description=str(description),
        body=body,
        content_hash=_content_hash(raw),
        trigger_questions=_normalize_list(frontmatter.get("trigger_questions")),
        tags=_normalize_list(frontmatter.get("tags")),
        categories=_normalize_list(frontmatter.get("categories")),
    )


def discover_skills(root: Path) -> list[Path]:
    """Find all SKILL.md files under a root directory."""
    root = _expand_path(root)
    if not root.exists():
        return []
    if root.is_file() and root.name == "SKILL.md":
        return [root]
    return sorted(root.rglob("SKILL.md"))


def scan_paths(paths: list[str | Path]) -> list[ParsedSkill]:
    """Scan multiple directories for skills."""
    seen: set[str] = set()
    skills: list[ParsedSkill] = []

    for path_str in paths:
        root = _expand_path(path_str)
        for skill_path in discover_skills(root):
            resolved = str(skill_path.resolve())
            if resolved in seen:
                continue
            seen.add(resolved)
            skills.append(parse_skill_file(skill_path))

    return skills
