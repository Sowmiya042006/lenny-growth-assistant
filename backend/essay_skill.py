ESSAY_TARGET_WORDS = 1250


def build_essay_prompt(
    topic: str,
    evidence: list[dict],
) -> str:
    evidence_blocks = []

    for index, passage in enumerate(evidence, start=1):
        evidence_blocks.append(
            "\n".join(
                [
                    f"[{index}]",
                    f"Transcript: {passage['transcript_id']}",
                    passage["text"],
                ]
            )
        )

    evidence_text = "\n\n".join(evidence_blocks)

    return f"""
You are executing the "Ship 30 for 30" essay skill.

Write a polished product-and-growth essay about:

{topic}

Requirements:
- Write approximately {ESSAY_TARGET_WORDS} words.
- Use Markdown.
- Include a compelling title.
- Start with a concise introduction.
- Use clear section headings.
- Explain practical lessons and actionable recommendations.
- Include a short conclusion.
- Ground factual claims only in the supplied transcript evidence.
- Add transcript citations such as [1] or [1, 2].
- Do not invent quotations, people, companies, or statistics.
- If the evidence is insufficient, clearly say so.
- Do not include HTML, JavaScript, or external resources.

Transcript evidence:

{evidence_text}
""".strip()