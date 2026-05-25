import json

PROMPT_VERSION = "v1"

_TEMPLATE = """\
You are a resume writing coach. Improve the wording of this resume bullet for the given job context.

Job title: {job_title}
Company: {company}
Job context keywords: {jd_keywords}

Resume bullet to improve:
"{bullet_text}"

Rules:
- Only rephrase and clarify what is already stated.
- Do NOT invent new skills, projects, or experiences.
- Do NOT add years of experience not mentioned.
- Do NOT fabricate metrics or achievements.
- Return ONLY valid JSON, no markdown, no prose.

{{"original": "{bullet_text}", "suggestion": "...", "changes": ["..."]}}"""

_FALLBACK = {
    "original": "",
    "suggestion": "",
    "changes": [],
}


def build_improve_prompt(bullet_text: str, job_title: str, company: str, jd_keywords: list[str]) -> str:
    return _TEMPLATE.format(
        job_title=job_title,
        company=company,
        jd_keywords=", ".join(jd_keywords[:10]),
        bullet_text=bullet_text.replace('"', '\\"'),
    )


def parse_improve_response(raw: str, original_bullet: str) -> dict:
    try:
        data = json.loads(raw.strip())
        return {
            "original": original_bullet,
            "suggestion": data.get("suggestion", ""),
            "changes": data.get("changes", []),
        }
    except (json.JSONDecodeError, AttributeError):
        return {"original": original_bullet, "suggestion": "", "changes": []}
