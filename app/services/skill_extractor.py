"""Deterministic skill extraction from resume/JD text.

Pipeline:
1. Lowercase + normalize
2. Exact match against SKILL_SET (O(1) per token)
3. spaCy NER for PRODUCT/ORG entities
4. TF-IDF top-N for importance scoring
5. Regex extraction of years-of-experience patterns
"""

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache

import spacy
from sklearn.feature_extraction.text import TfidfVectorizer

from app.parsers.skill_dictionary import SKILL_DICT, SKILL_SET, get_category

_YEARS_PATTERN = re.compile(r"(\d+)\+?\s+years?", re.IGNORECASE)
_MULTI_SPACE = re.compile(r"\s+")


@dataclass
class ExtractedSkill:
    skill_name: str
    skill_type: str | None
    importance_score: float = 0.5
    source: str = "dictionary"


@lru_cache(maxsize=1)
def _load_nlp() -> spacy.Language:
    return spacy.load("en_core_web_sm", disable=["parser", "lemmatizer"])


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return _MULTI_SPACE.sub(" ", text.lower()).strip()


def _extract_dictionary_skills(text_lower: str) -> list[tuple[str, str | None]]:
    found: list[tuple[str, str | None]] = []
    for skill in SKILL_SET:
        if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
            found.append((skill, get_category(skill)))
    return found


def _extract_ner_skills(text: str) -> list[str]:
    nlp = _load_nlp()
    doc = nlp(text[:10000])  # cap to avoid slow processing
    extras: list[str] = []
    for ent in doc.ents:
        if ent.label_ in {"PRODUCT", "ORG"}:
            name = ent.text.strip().lower()
            if 2 <= len(name) <= 60 and name not in SKILL_SET:
                extras.append(name)
    return extras


def _compute_importance(skills: list[str], text: str) -> dict[str, float]:
    if not skills or not text.strip():
        return {}
    corpus = [text]
    try:
        vec = TfidfVectorizer(vocabulary=skills, token_pattern=r"(?u)\b\S+\b")
        tfidf = vec.fit_transform(corpus)
        scores = tfidf.toarray()[0]
        max_score = scores.max() if scores.max() > 0 else 1.0
        return {skill: float(scores[i] / max_score) for i, skill in enumerate(skills)}
    except Exception:
        return {skill: 0.5 for skill in skills}


def extract_skills(text: str) -> list[ExtractedSkill]:
    if not text or not text.strip():
        return []

    text_lower = _normalize(text)

    # 1. Dictionary exact match
    dict_matches = _extract_dictionary_skills(text_lower)

    # 2. spaCy NER for unlisted tools
    ner_matches = _extract_ner_skills(text)

    # Build deduplicated skill list
    seen: dict[str, str | None] = {}
    for name, category in dict_matches:
        seen[name] = category
    for name in ner_matches:
        if name not in seen:
            seen[name] = None

    if not seen:
        return []

    # 3. TF-IDF importance scores
    skill_names = list(seen.keys())
    importance = _compute_importance(skill_names, text_lower)

    results: list[ExtractedSkill] = []
    for name, category in seen.items():
        results.append(ExtractedSkill(
            skill_name=name,
            skill_type=category,
            importance_score=importance.get(name, 0.5),
            source="dictionary" if category is not None else "ner",
        ))

    # 4. Years-of-experience extraction (separate type)
    exp_years = _YEARS_PATTERN.findall(text_lower)
    if exp_years:
        max_years = max(int(y) for y in exp_years)
        results.append(ExtractedSkill(
            skill_name=f"{max_years}+ years experience",
            skill_type="experience",
            importance_score=1.0,
            source="regex",
        ))

    results.sort(key=lambda s: s.importance_score, reverse=True)
    return results
