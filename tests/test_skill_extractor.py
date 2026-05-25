import time

import pytest

from app.services.skill_extractor import ExtractedSkill, extract_skills

SAMPLE_JD = """
We are looking for a Senior Software Engineer with 5+ years of experience.

Required skills:
- Python (FastAPI, SQLAlchemy)
- JavaScript and TypeScript (React, Node.js)
- Docker and Kubernetes for container orchestration
- AWS (EC2, S3, Lambda)
- PostgreSQL and Redis
- Experience with REST API design and microservices architecture
- CI/CD pipelines using GitHub Actions
- Strong understanding of machine learning concepts

Nice to have:
- Go or Rust experience
- TensorFlow or PyTorch
- Kafka for event streaming
"""

SAMPLE_RESUME = """
Software Engineer with 6 years of experience building scalable web applications.
Proficient in Python, JavaScript, and TypeScript.
Built REST APIs using FastAPI and Django.
Deployed applications with Docker and Kubernetes on AWS.
Experience with PostgreSQL, Redis, and Elasticsearch.
Strong background in CI/CD and DevOps practices.
"""


def test_extract_skills_returns_list_of_extracted_skill():
    results = extract_skills(SAMPLE_JD)
    assert isinstance(results, list)
    assert len(results) > 0
    for item in results:
        assert isinstance(item, ExtractedSkill)
        assert item.skill_name
        assert item.skill_type in {"languages", "frameworks", "tools", "concepts", "experience", None}
        assert 0.0 <= item.importance_score <= 1.0


def test_extract_skills_finds_explicitly_mentioned_tech():
    results = extract_skills(SAMPLE_JD)
    found = {s.skill_name.lower() for s in results}
    for expected in ["python", "javascript", "typescript", "docker", "aws", "postgresql", "redis"]:
        assert expected in found, f"expected skill not found: {expected}"


def test_extract_skills_no_llm_calls(monkeypatch):
    """Service must be deterministic — no HTTP calls."""
    import urllib.request
    original = urllib.request.urlopen

    def fail_if_called(*args, **kwargs):
        raise AssertionError("HTTP call made inside extract_skills — no LLM allowed")

    monkeypatch.setattr(urllib.request, "urlopen", fail_if_called)
    results = extract_skills(SAMPLE_JD)
    assert len(results) > 0


def test_extract_skills_performance():
    """Must complete in under 2 seconds on a 2000-word document."""
    long_text = SAMPLE_JD * 10  # ~2000 words
    start = time.monotonic()
    results = extract_skills(long_text)
    elapsed = time.monotonic() - start
    assert elapsed < 2.0, f"took {elapsed:.2f}s, exceeds 2s limit"
    assert len(results) > 0


def test_extract_skills_empty_text():
    results = extract_skills("")
    assert results == []


def test_extract_skills_extracts_years_of_experience():
    text = "We need 5+ years of Python experience and 3 years of React."
    results = extract_skills(text)
    experience_items = [s for s in results if s.skill_type == "experience"]
    assert len(experience_items) >= 1


def test_extract_skills_deduplicates():
    """Repeated mentions should not produce duplicate skill entries."""
    text = "Python Python Python Python Python"
    results = extract_skills(text)
    python_skills = [s for s in results if s.skill_name.lower() == "python"]
    assert len(python_skills) == 1


def test_extract_skills_resume_text():
    results = extract_skills(SAMPLE_RESUME)
    found = {s.skill_name.lower() for s in results}
    for expected in ["python", "javascript", "docker", "aws", "postgresql", "redis"]:
        assert expected in found, f"expected skill not found in resume: {expected}"
