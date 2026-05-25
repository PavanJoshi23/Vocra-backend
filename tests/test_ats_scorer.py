import pytest
from app.services.ats_scorer import ScoreBreakdown, compute_ats_score


def test_compute_ats_score_returns_score_breakdown():
    result = compute_ats_score(
        resume_text="Python developer with 5 years experience. Bachelor degree.",
        jd_text="Looking for Python developer with 3+ years. Bachelor degree required.",
    )
    assert isinstance(result, ScoreBreakdown)
    assert hasattr(result, "total")
    assert hasattr(result, "skills")
    assert hasattr(result, "experience")
    assert hasattr(result, "keyword_coverage")
    assert hasattr(result, "education")


def test_total_score_range():
    result = compute_ats_score(
        resume_text="Python developer with 5 years experience.",
        jd_text="Looking for Python developer.",
    )
    assert 0 <= result.total <= 100
    assert isinstance(result.total, int)


def test_score_is_deterministic():
    resume = "Python developer with 5 years of experience building FastAPI apps."
    jd = "Looking for a Python backend engineer with FastAPI experience, 3+ years."
    r1 = compute_ats_score(resume, jd)
    r2 = compute_ats_score(resume, jd)
    assert r1.total == r2.total
    assert r1.skills == r2.skills


def test_perfect_match_scores_high():
    text = (
        "Python developer with 5 years experience. "
        "Expertise in FastAPI, Docker, AWS, PostgreSQL. "
        "REST API, microservices, CI/CD. "
        "Bachelor of Science in Computer Science."
    )
    result = compute_ats_score(resume_text=text, jd_text=text)
    assert result.total >= 80


def test_no_match_scores_low():
    resume = "Java Spring Boot developer with 3 years experience."
    jd = "Looking for Python FastAPI engineer with React experience."
    result = compute_ats_score(resume_text=resume, jd_text=jd)
    assert result.total < 50


def test_breakdown_weights_sum_to_100():
    result = compute_ats_score(
        resume_text="Python developer with 5 years experience. Bachelor degree.",
        jd_text="Python developer, 3+ years, Bachelor degree.",
    )
    weighted = (
        result.skills * 0.40
        + result.experience * 0.30
        + result.keyword_coverage * 0.20
        + result.education * 0.10
    )
    assert abs(weighted - result.total) <= 1  # allow 1 point rounding error


def test_no_llm_in_scorer(monkeypatch):
    import urllib.request

    def fail(*args, **kwargs):
        raise AssertionError("HTTP call made in ats_scorer — no LLM allowed")

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    result = compute_ats_score("Python developer.", "Python engineer needed.")
    assert 0 <= result.total <= 100


def test_empty_texts_return_zero():
    result = compute_ats_score("", "")
    assert result.total == 0


def test_per_category_scores_in_range():
    result = compute_ats_score(
        resume_text="Python developer with 5 years of experience. MS Computer Science.",
        jd_text="Python engineer, 3+ years experience, MS degree preferred.",
    )
    for score in [result.skills, result.experience, result.keyword_coverage, result.education]:
        assert 0 <= score <= 100
