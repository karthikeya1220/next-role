"""Fit evaluator — assess how well a candidate matches a job description.

Ported from ai-job-search workflow logic. Uses OpenRouter (POWER_MODEL) for
nuanced evaluation of skills, experience, and culture fit.
"""

import logging
from typing import Optional

from app.llm_client import POWER_MODEL, chat_json

logger = logging.getLogger(__name__)

_SYSTEM = """You are an expert career advisor assessing job application fit.
Evaluate objectively on skills, experience level, and role requirements.
Never reference the candidate's name, gender, or demographic information.
Respond with valid JSON only."""

_PROMPT_TEMPLATE = """Evaluate this candidate's fit for the following job.

## Job Description
{job_description}

## Candidate Profile
{candidate_profile}

Respond with this JSON structure:
{{
  "overall_fit": "strong" | "moderate" | "weak",
  "fit_score": <0-100>,
  "skills_match": {{
    "matched": ["skill1", "skill2"],
    "missing_required": ["skill3"],
    "missing_preferred": ["skill4"]
  }},
  "experience_match": {{
    "meets_requirements": true | false,
    "notes": "..."
  }},
  "culture_fit": {{
    "indicators": ["..."],
    "concerns": ["..."]
  }},
  "recommendation": "apply" | "consider" | "skip",
  "recommendation_reason": "...",
  "tailoring_tips": ["tip1", "tip2", "tip3"]
}}"""

_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_fit": {"type": "string", "enum": ["strong", "moderate", "weak"]},
        "fit_score": {"type": "number"},
        "skills_match": {
            "type": "object",
            "properties": {
                "matched": {"type": "array", "items": {"type": "string"}},
                "missing_required": {"type": "array", "items": {"type": "string"}},
                "missing_preferred": {"type": "array", "items": {"type": "string"}},
            },
        },
        "experience_match": {
            "type": "object",
            "properties": {
                "meets_requirements": {"type": "boolean"},
                "notes": {"type": "string"},
            },
        },
        "culture_fit": {
            "type": "object",
            "properties": {
                "indicators": {"type": "array", "items": {"type": "string"}},
                "concerns": {"type": "array", "items": {"type": "string"}},
            },
        },
        "recommendation": {"type": "string", "enum": ["apply", "consider", "skip"]},
        "recommendation_reason": {"type": "string"},
        "tailoring_tips": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["overall_fit", "fit_score", "skills_match", "experience_match",
                 "culture_fit", "recommendation", "recommendation_reason", "tailoring_tips"],
    "additionalProperties": False,
}


def evaluate_fit(job_description: str, candidate_profile: str,
                 model: str = POWER_MODEL) -> dict:
    """Return a structured fit evaluation dict."""
    prompt = _PROMPT_TEMPLATE.format(
        job_description=job_description,
        candidate_profile=candidate_profile,
    )
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user", "content": prompt},
    ]
    return chat_json(messages, _SCHEMA, model=model, temperature=0.2)
