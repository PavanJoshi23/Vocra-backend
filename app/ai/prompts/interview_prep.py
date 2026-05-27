PROMPT_VERSION = "v2"

_TEMPLATE = """\
You are an interview coach. List the topics a candidate must prepare for the following role.

Role: {role}
Company: {company}
Required skills: {jd_skills}
Candidate strengths: {resume_strengths}
Gaps to address: {missing_skills}

Output a plain list of 8 to 12 topics to study. One topic per line. No numbering, no bullet symbols, no explanations, no extra text."""


def build_prompt(ctx: dict) -> str:
    return _TEMPLATE.format(
        role=ctx["role"],
        company=ctx["company"],
        jd_skills=", ".join(ctx["jd_skills"][:10]),
        resume_strengths=", ".join(ctx["resume_strengths"][:5]),
        missing_skills=", ".join(ctx["missing_skills"]),
    )


def parse_response(raw: str) -> list[str]:
    topics = []
    for line in raw.strip().splitlines():
        line = line.strip().lstrip("-•*·→>0123456789.) \t")
        if line and len(line) > 2:
            topics.append(line)
    return topics[:15]
