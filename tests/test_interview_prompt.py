import json
from app.ai.prompts.interview_prep import build_prompt, PROMPT_VERSION


def _context():
    return {
        "role": "Senior Python Engineer",
        "company": "Acme Corp",
        "jd_skills": ["python", "docker", "aws", "fastapi", "postgresql", "redis", "celery", "git", "ci/cd", "rest api"],
        "resume_strengths": ["python", "docker", "fastapi", "git", "rest api"],
        "missing_skills": ["aws", "postgresql", "redis", "celery", "ci/cd"],
    }


def test_build_prompt_returns_string():
    prompt = build_prompt(_context())
    assert isinstance(prompt, str)
    assert len(prompt) > 0


def test_prompt_contains_role_and_company():
    ctx = _context()
    prompt = build_prompt(ctx)
    assert ctx["role"] in prompt
    assert ctx["company"] in prompt


def test_prompt_contains_jd_skills():
    ctx = _context()
    prompt = build_prompt(ctx)
    for skill in ctx["jd_skills"][:5]:
        assert skill in prompt


def test_prompt_contains_missing_skills():
    ctx = _context()
    prompt = build_prompt(ctx)
    for skill in ctx["missing_skills"]:
        assert skill in prompt


def test_prompt_under_500_tokens():
    """Rough token estimate: 1 token ≈ 4 characters."""
    prompt = build_prompt(_context())
    estimated_tokens = len(prompt) / 4
    assert estimated_tokens < 500, f"Prompt too long: ~{estimated_tokens:.0f} tokens"


def test_prompt_requests_json_output():
    prompt = build_prompt(_context())
    assert "JSON" in prompt or "json" in prompt


def test_prompt_includes_safety_constraints():
    prompt = build_prompt(_context())
    # Should instruct the model not to invent information
    assert "invent" in prompt.lower() or "fabricate" in prompt.lower() or "only" in prompt.lower()


def test_prompt_version_is_string():
    assert isinstance(PROMPT_VERSION, str)
    assert len(PROMPT_VERSION) > 0


def test_expected_output_keys_mentioned_in_prompt():
    prompt = build_prompt(_context())
    for key in ["technical_topics", "behavioral_questions", "coding_topics", "study_roadmap"]:
        assert key in prompt


def test_parse_valid_ollama_response():
    from app.ai.prompts.interview_prep import parse_response
    valid_json = json.dumps({
        "technical_topics": [{"topic": "FastAPI", "priority": "high", "why": "core skill"}],
        "behavioral_questions": ["Tell me about a time you debugged a hard issue."],
        "coding_topics": ["async/await patterns"],
        "study_roadmap": [{"week": 1, "focus": "AWS basics", "resources": ["docs.aws.amazon.com"]}],
    })
    result = parse_response(valid_json)
    assert result["technical_topics"][0]["topic"] == "FastAPI"
    assert len(result["behavioral_questions"]) == 1


def test_parse_malformed_response_returns_fallback():
    from app.ai.prompts.interview_prep import parse_response
    result = parse_response("This is not JSON at all")
    assert "technical_topics" in result
    assert "behavioral_questions" in result
    assert "coding_topics" in result
    assert "study_roadmap" in result
    assert result["technical_topics"] == []
