"""Weighted ATS scoring.

Weights (from spec):
  Skills match       = 40%
  Experience match   = 30%  (years of exp, seniority keywords)
  Keyword coverage   = 20%  (% of JD keywords found in resume)
  Education match    = 10%  (degree keywords)

All scoring is deterministic — no LLM calls.
"""

import re
from dataclasses import dataclass

from app.services.matcher import match
from app.services.skill_extractor import extract_skills

_YEARS_RE = re.compile(r"(\d+)\+?\s+years?", re.IGNORECASE)
_SENIORITY_SENIOR = re.compile(r"\b(senior|lead|principal|staff|architect)\b", re.IGNORECASE)
_SENIORITY_JUNIOR = re.compile(r"\b(junior|entry[\s-]?level|intern)\b", re.IGNORECASE)
_EDUCATION_DEGREE = re.compile(
    r"\b(bachelor|b\.?s\.?|b\.?e\.?|b\.?tech|master|m\.?s\.?|m\.?e\.?|phd|ph\.?d|mba|associate)\b",
    re.IGNORECASE,
)
_EDUCATION_CS = re.compile(
    r"\b(computer science|software engineering|information technology|electrical engineering|mathematics|physics|engineering)\b",
    re.IGNORECASE,
)


@dataclass
class ScoreBreakdown:
    total: int
    skills: int
    experience: int
    keyword_coverage: int
    education: int


def _score_skills(resume_text: str, jd_text: str) -> int:
    resume_skills = [s.skill_name for s in extract_skills(resume_text) if s.skill_type != "experience"]
    jd_skills = [s.skill_name for s in extract_skills(jd_text) if s.skill_type != "experience"]

    if not jd_skills:
        return 0
    if not resume_skills:
        return 0

    result = match(resume_skills, jd_skills)
    return min(100, int(result.match_percentage))


def _score_experience(resume_text: str, jd_text: str) -> int:
    resume_years_found = _YEARS_RE.findall(resume_text)
    jd_years_found = _YEARS_RE.findall(jd_text)

    score = 50  # base if no explicit years mentioned

    if jd_years_found:
        jd_min_years = min(int(y) for y in jd_years_found)
        if resume_years_found:
            resume_max_years = max(int(y) for y in resume_years_found)
            if resume_max_years >= jd_min_years:
                score = 100
            elif resume_max_years >= jd_min_years - 1:
                score = 75
            else:
                score = max(0, int(resume_max_years / jd_min_years * 100))
        else:
            score = 30  # JD requires years but resume doesn't mention any

    # Seniority keyword bonus/penalty
    jd_wants_senior = bool(_SENIORITY_SENIOR.search(jd_text))
    jd_wants_junior = bool(_SENIORITY_JUNIOR.search(jd_text))
    resume_is_senior = bool(_SENIORITY_SENIOR.search(resume_text))
    resume_is_junior = bool(_SENIORITY_JUNIOR.search(resume_text))

    if jd_wants_senior and resume_is_senior:
        score = min(100, score + 10)
    elif jd_wants_junior and resume_is_junior:
        score = min(100, score + 10)
    elif jd_wants_senior and resume_is_junior:
        score = max(0, score - 20)

    return min(100, max(0, score))


def _score_keyword_coverage(resume_text: str, jd_text: str) -> int:
    """% of JD keywords (all extracted skills) found in resume text."""
    jd_skills = extract_skills(jd_text)
    if not jd_skills:
        return 0

    resume_lower = resume_text.lower()
    found = sum(
        1 for s in jd_skills
        if re.search(r"\b" + re.escape(s.skill_name.lower()) + r"\b", resume_lower)
    )
    return min(100, int(found / len(jd_skills) * 100))


def _score_education(resume_text: str, jd_text: str) -> int:
    jd_wants_degree = bool(_EDUCATION_DEGREE.search(jd_text))
    if not jd_wants_degree:
        return 80  # no education requirement → default good score

    resume_has_degree = bool(_EDUCATION_DEGREE.search(resume_text))
    if not resume_has_degree:
        return 20

    resume_has_cs = bool(_EDUCATION_CS.search(resume_text))
    jd_wants_cs = bool(_EDUCATION_CS.search(jd_text))

    if jd_wants_cs and resume_has_cs:
        return 100
    if resume_has_degree:
        return 70
    return 50


def compute_ats_score(resume_text: str, jd_text: str) -> ScoreBreakdown:
    if not resume_text.strip() or not jd_text.strip():
        return ScoreBreakdown(total=0, skills=0, experience=0, keyword_coverage=0, education=0)

    skills = _score_skills(resume_text, jd_text)
    experience = _score_experience(resume_text, jd_text)
    keyword_coverage = _score_keyword_coverage(resume_text, jd_text)
    education = _score_education(resume_text, jd_text)

    total = int(
        skills * 0.40
        + experience * 0.30
        + keyword_coverage * 0.20
        + education * 0.10
    )
    total = min(100, max(0, total))

    return ScoreBreakdown(
        total=total,
        skills=skills,
        experience=experience,
        keyword_coverage=keyword_coverage,
        education=education,
    )
