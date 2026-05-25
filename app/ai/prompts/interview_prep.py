import json

PROMPT_VERSION = "v1"

_TEMPLATE = """\
You are an interview coach. Given the context below, generate interview preparation material.

Role: {role}
Company: {company}
Top JD skills: {jd_skills}
Resume strengths: {resume_strengths}
Skills to improve: {missing_skills}

Return ONLY valid JSON with exactly these keys. No markdown, no prose.
Do NOT invent skills, projects, or experiences not listed above.
Do NOT fabricate company-specific information.

{{
  "technical_topics": [{{"topic": "...", "priority": "high|medium|low", "why": "..."}}],
  "behavioral_questions": ["..."],
  "coding_topics": ["..."],
  "study_roadmap": [{{"week": 1, "focus": "...", "resources": ["..."]}}]
}}"""

_FALLBACK: dict = {
    "technical_topics": [],
    "behavioral_questions": [],
    "coding_topics": [],
    "study_roadmap": [],
}


def build_prompt(ctx: dict) -> str:
    """Build the interview prep prompt from preprocessed context."""
    return _TEMPLATE.format(
        role=ctx["role"],
        company=ctx["company"],
        jd_skills=", ".join(ctx["jd_skills"][:10]),
        resume_strengths=", ".join(ctx["resume_strengths"][:5]),
        missing_skills=", ".join(ctx["missing_skills"]),
    )


def parse_response(raw: str) -> dict:
    """Parse Ollama's JSON response; return fallback dict on failure."""
    try:
        data = json.loads(raw.strip())
        return {
            "technical_topics": data.get("technical_topics", []),
            "behavioral_questions": data.get("behavioral_questions", []),
            "coding_topics": data.get("coding_topics", []),
            "study_roadmap": data.get("study_roadmap", []),
        }
    except (json.JSONDecodeError, AttributeError):
        return dict(_FALLBACK)
