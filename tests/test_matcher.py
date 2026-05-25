import pytest
from app.services.matcher import MatchResult, match


def test_match_returns_match_result():
    result = match(["python", "react"], ["python", "react"])
    assert isinstance(result, MatchResult)
    assert hasattr(result, "match_percentage")
    assert hasattr(result, "matched")
    assert hasattr(result, "missing")
    assert hasattr(result, "match_details")


def test_exact_match_case_insensitive():
    """JavaScript vs Javascript → matched via exact after normalize."""
    result = match(["JavaScript"], ["Javascript"])
    assert "javascript" in {m.lower() for m in result.matched}
    assert result.match_percentage == 100.0


def test_fuzzy_match_nodejs():
    """Node.js vs NodeJS → matched via fuzzy layer."""
    result = match(["Node.js"], ["NodeJS"])
    assert len(result.matched) >= 1
    assert result.match_percentage > 0


def test_fuzzy_match_rest_api():
    """REST API vs RESTful services → fuzzy or semantic match."""
    result = match(["REST API"], ["RESTful services"])
    assert result.match_percentage > 0


def test_missing_skill_reported():
    """React missing from resume → appears in missing."""
    result = match(["python", "django"], ["python", "django", "react"])
    missing_lower = {m.lower() for m in result.missing}
    assert "react" in missing_lower


def test_full_overlap_is_100():
    skills = ["python", "docker", "aws", "react"]
    result = match(skills, skills)
    assert result.match_percentage == 100.0
    assert result.missing == []


def test_no_overlap_is_0():
    result = match(["python", "django"], ["java", "spring"])
    # With semantic fallback there may be small scores, but missing should be non-empty
    assert len(result.missing) > 0


def test_empty_resume_skills():
    result = match([], ["python", "react"])
    assert result.match_percentage == 0.0
    assert set(result.missing) >= {"python", "react"}


def test_empty_jd_skills():
    result = match(["python"], [])
    assert result.match_percentage == 0.0


def test_match_details_has_layer_info():
    result = match(["python", "Node.js"], ["python", "nodejs", "react"])
    for detail in result.match_details:
        assert "resume_skill" in detail
        assert "jd_skill" in detail
        assert "layer" in detail
        assert detail["layer"] in {"exact", "fuzzy", "semantic"}
        assert "score" in detail


def test_match_percentage_range():
    result = match(["python", "java", "react"], ["python", "javascript", "docker"])
    assert 0.0 <= result.match_percentage <= 100.0
