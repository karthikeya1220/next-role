"""Resume evaluator — rubric-based LLM scoring.

Ported from hiring-agent/evaluator.py. Rewired to use app.llm_client (OpenRouter).
"""

import json
import logging
from typing import Any

from app.llm_client import FAST_MODEL, chat_json
from app.resume.models import build_evaluation_model
from app.resume.roles import Role

logger = logging.getLogger(__name__)


class ResumeEvaluator:
    """Score a resume text against a role rubric using OpenRouter."""

    def __init__(self, role: Role, model: str = FAST_MODEL):
        self.role = role
        self.model = model
        self.evaluation_model = build_evaluation_model(role)

    def evaluate(self, resume_text: str) -> Any:
        """Return an EvaluationData Pydantic model for *resume_text*.

        Raises on unrecoverable LLM errors.
        """
        from jinja2 import Environment

        env = Environment()
        system_msg = env.from_string(self.role.system_message_source).render()
        prompt = env.from_string(self.role.criteria_source).render(
            text_content=resume_text
        )

        schema = self.evaluation_model.model_json_schema()
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ]

        try:
            data = chat_json(messages, schema, model=self.model, temperature=0.3)
            return self.evaluation_model(**data)
        except Exception as exc:
            logger.error("Evaluation failed: %s", exc)
            raise


def score_resume(resume_text: str, role: Role, model: str = FAST_MODEL) -> dict:
    """Convenience wrapper — returns a serialisable score dict.

    Keys: categories (dict of category_key -> {score, max, evidence}),
          bonus_points, deductions, key_strengths, areas_for_improvement,
          total_score, max_score.
    """
    evaluator = ResumeEvaluator(role, model=model)
    result = evaluator.evaluate(resume_text)
    data = result.model_dump()

    # Compute totals
    scores = data.get("scores", {})
    total = sum(v.get("score", 0) for v in scores.values())
    total += data.get("bonus_points", {}).get("total", 0)
    total -= data.get("deductions", {}).get("total", 0)
    max_score = sum(v.get("max", 0) for v in scores.values()) + role.bonus_max

    return {
        **data,
        "total_score": round(total, 1),
        "max_score": max_score,
        "role_name": role.name,
        "position_title": role.position_title,
    }
