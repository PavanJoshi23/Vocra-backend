"""Three-layer ATS skill matcher: exact → fuzzy → semantic (TF-IDF cosine).

No LLM calls in this module. Ollama embeddings are explicitly excluded from
the hot path per architectural decision.
"""

from dataclasses import dataclass, field

from rapidfuzz import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_FUZZY_THRESHOLD = 85
_SEMANTIC_THRESHOLD = 0.18


@dataclass
class MatchResult:
    matched: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    match_percentage: float = 0.0
    match_details: list[dict] = field(default_factory=list)


def _normalize(skill: str) -> str:
    return skill.lower().strip()


def _semantic_score(a: str, b: str) -> float:
    try:
        vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        tfidf = vec.fit_transform([a, b])
        return float(cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0])
    except Exception:
        return 0.0


def match(resume_skills: list[str], jd_skills: list[str]) -> MatchResult:
    if not jd_skills:
        return MatchResult()
    if not resume_skills:
        return MatchResult(
            missing=list(jd_skills),
            match_percentage=0.0,
        )

    resume_norm = {_normalize(s): s for s in resume_skills}
    matched: list[str] = []
    missing: list[str] = []
    details: list[dict] = []

    for jd_skill in jd_skills:
        jd_norm = _normalize(jd_skill)
        best_layer = None
        best_score = 0.0
        best_resume_skill = None

        # Layer 1: exact match
        if jd_norm in resume_norm:
            best_layer = "exact"
            best_score = 1.0
            best_resume_skill = resume_norm[jd_norm]
        else:
            # Layer 2: fuzzy match
            for r_norm, r_orig in resume_norm.items():
                score = fuzz.token_sort_ratio(jd_norm, r_norm) / 100.0
                if score >= _FUZZY_THRESHOLD / 100.0 and score > best_score:
                    best_score = score
                    best_layer = "fuzzy"
                    best_resume_skill = r_orig

            # Layer 3: semantic (TF-IDF cosine) — only if layers 1+2 missed
            if best_layer is None:
                for r_norm, r_orig in resume_norm.items():
                    score = _semantic_score(jd_norm, r_norm)
                    if score >= _SEMANTIC_THRESHOLD and score > best_score:
                        best_score = score
                        best_layer = "semantic"
                        best_resume_skill = r_orig

        if best_layer is not None:
            matched.append(jd_skill)
            details.append({
                "resume_skill": best_resume_skill,
                "jd_skill": jd_skill,
                "layer": best_layer,
                "score": round(best_score, 3),
            })
        else:
            missing.append(jd_skill)

    pct = round(len(matched) / len(jd_skills) * 100.0, 1) if jd_skills else 0.0
    return MatchResult(
        matched=matched,
        missing=missing,
        match_percentage=pct,
        match_details=details,
    )
