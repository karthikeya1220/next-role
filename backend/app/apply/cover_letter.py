"""Cover letter generator — drafter → reviewer → final pipeline.

Ported from ai-job-search workflow. Uses OpenRouter:
  - FAST_MODEL for the initial draft
  - POWER_MODEL for the reviewer critique and final revision
"""

import logging
from dataclasses import dataclass
from app.llm_client import FAST_MODEL, POWER_MODEL, chat

logger = logging.getLogger(__name__)

_DRAFT_SYSTEM = """You are an expert cover letter writer.
Write a concise, forward-looking cover letter (max 350 words, 3 paragraphs).
Do NOT use hollow filler phrases like "I am excited to apply" or "I believe I would be a great fit".
Ground every claim in specific, verifiable accomplishments from the candidate's profile.
Output only the letter body — no subject line, no date, no address."""

_DRAFT_PROMPT = """Write a cover letter for this application.

## Job Description
{job_description}

## Candidate Accomplishments
{candidate_profile}

## Tone
{tone}

Rules:
- Open with the strongest relevant accomplishment, not with "I am applying…"
- Paragraph 1: most relevant achievement that directly addresses the role's top requirement
- Paragraph 2: second proof point + why this specific company/team
- Paragraph 3: brief forward-looking close (what you'd work on, not just "I look forward to hearing")
- Max 350 words
"""

_REVIEWER_SYSTEM = """You are a strict senior hiring manager reviewing a cover letter draft.
Identify the 3 most important improvements needed. Be specific and actionable.
Output JSON only."""

_REVIEWER_PROMPT = """Review this cover letter draft for the job below.

## Job Description
{job_description}

## Draft
{draft}

Respond with:
{{
  "critique": ["issue1", "issue2", "issue3"],
  "overall_quality": "excellent" | "good" | "needs_work",
  "approve": true | false
}}"""

_REVISE_SYSTEM = """You are a cover letter editor. Revise the draft based on the critique.
Preserve the best parts. Output only the revised letter body."""

_REVISE_PROMPT = """Revise this cover letter based on the critique below.

## Original Draft
{draft}

## Critique
{critique}

Output the improved letter only."""


@dataclass
class CoverLetterResult:
    draft: str
    critique: list[str]
    overall_quality: str
    final: str
    approved_at_draft: bool


def generate_cover_letter(
    job_description: str,
    candidate_profile: str,
    tone: str = "professional and direct",
    fast_model: str = FAST_MODEL,
    power_model: str = POWER_MODEL,
) -> CoverLetterResult:
    """Drafter → reviewer → (optional revision) pipeline.

    Returns a CoverLetterResult with the draft, critique, and final version.
    """
    # Step 1: Draft
    draft_prompt = _DRAFT_PROMPT.format(
        job_description=job_description,
        candidate_profile=candidate_profile,
        tone=tone,
    )
    draft = chat(
        [{"role": "system", "content": _DRAFT_SYSTEM},
         {"role": "user", "content": draft_prompt}],
        model=fast_model,
        temperature=0.7,
    )

    # Step 2: Review
    import json
    review_prompt = _REVIEWER_PROMPT.format(
        job_description=job_description, draft=draft
    )
    try:
        from app.llm_client import chat_json, _parse_json
        _REVIEW_SCHEMA = {
            "type": "object",
            "properties": {
                "critique": {"type": "array", "items": {"type": "string"}},
                "overall_quality": {"type": "string"},
                "approve": {"type": "boolean"},
            },
            "required": ["critique", "overall_quality", "approve"],
        }
        review = chat_json(
            [{"role": "system", "content": _REVIEWER_SYSTEM},
             {"role": "user", "content": review_prompt}],
            _REVIEW_SCHEMA,
            model=power_model,
            temperature=0.2,
        )
    except Exception as exc:
        logger.warning("Review step failed, skipping revision: %s", exc)
        return CoverLetterResult(
            draft=draft, critique=[], overall_quality="unknown",
            final=draft, approved_at_draft=True
        )

    critique = review.get("critique", [])
    approved = review.get("approve", False)
    quality = review.get("overall_quality", "unknown")

    if approved:
        return CoverLetterResult(
            draft=draft, critique=critique, overall_quality=quality,
            final=draft, approved_at_draft=True
        )

    # Step 3: Revise
    revise_prompt = _REVISE_PROMPT.format(
        draft=draft,
        critique="\n".join(f"- {c}" for c in critique),
    )
    final = chat(
        [{"role": "system", "content": _REVISE_SYSTEM},
         {"role": "user", "content": revise_prompt}],
        model=power_model,
        temperature=0.5,
    )

    return CoverLetterResult(
        draft=draft, critique=critique, overall_quality=quality,
        final=final, approved_at_draft=False
    )
