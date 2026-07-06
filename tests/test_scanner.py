"""Tests for scanner."""

from pathlib import Path

import pytest

from skillregistry.scanner import discover_skills, parse_skill_file, scan_paths

FIXTURES = Path(__file__).parent / "fixtures" / "skills"


def test_discover_skills():
    paths = discover_skills(FIXTURES)
    assert len(paths) == 5
    assert all(p.name == "SKILL.md" for p in paths)


def test_parse_skill_file():
    skill_path = FIXTURES / "create-hook" / "SKILL.md"
    skill = parse_skill_file(skill_path)
    assert skill.name == "create-hook"
    assert skill.description
    assert skill.content_hash
    assert "sessionStart" in skill.body


def test_scan_paths_dedupes():
    skills = scan_paths([FIXTURES, FIXTURES])
    assert len(skills) == 5


def test_parse_missing_frontmatter(tmp_path):
    bad = tmp_path / "SKILL.md"
    bad.write_text("# No frontmatter\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        parse_skill_file(bad)
