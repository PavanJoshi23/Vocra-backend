import pytest
from app.parsers.skill_dictionary import SKILL_DICT, SKILL_SET, get_category


def test_skill_dict_has_required_categories():
    categories = set(SKILL_DICT.keys())
    assert "languages" in categories
    assert "frameworks" in categories
    assert "tools" in categories
    assert "concepts" in categories


def test_skill_dict_covers_languages():
    langs = {s.lower() for s in SKILL_DICT["languages"]}
    for expected in ["python", "java", "javascript", "typescript", "go", "rust"]:
        assert expected in langs, f"missing language: {expected}"


def test_skill_dict_covers_frameworks():
    fw = {s.lower() for s in SKILL_DICT["frameworks"]}
    for expected in ["react", "fastapi", "django", "spring"]:
        assert expected in fw, f"missing framework: {expected}"


def test_skill_dict_covers_tools():
    tools = {s.lower() for s in SKILL_DICT["tools"]}
    for expected in ["docker", "git", "aws", "gcp"]:
        assert expected in tools, f"missing tool: {expected}"


def test_skill_dict_covers_concepts():
    concepts = {s.lower() for s in SKILL_DICT["concepts"]}
    for expected in ["rest api", "microservices", "ci/cd"]:
        assert expected in concepts, f"missing concept: {expected}"


def test_skill_set_contains_at_least_200_items():
    assert len(SKILL_SET) >= 200


def test_skill_set_items_are_lowercase():
    for skill in SKILL_SET:
        assert skill == skill.lower(), f"skill not lowercase: {skill}"


def test_get_category_returns_correct_category():
    assert get_category("python") == "languages"
    assert get_category("react") == "frameworks"
    assert get_category("docker") == "tools"
    assert get_category("ci/cd") == "concepts"


def test_get_category_returns_none_for_unknown():
    assert get_category("not_a_real_skill_xyz") is None
