"""POST /cover-letter — generate a tailored cover letter for a job."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.apply.cover_letter import generate_cover_letter
from app.apply.fit_evaluator import evaluate_fit

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cover-letter", tags=["apply"])


class CoverLetterRequest(BaseModel):
    job_description: str
    candidate_profile: str
    tone: str = "professional and direct"
    run_fit_check: bool = True


class CoverLetterResponse(BaseModel):
    final: str
    draft: str
    critique: list[str]
    overall_quality: str
    approved_at_draft: bool
    fit: Optional[dict] = None


@router.post("", response_model=CoverLetterResponse)
def generate(req: CoverLetterRequest):
    """Generate a cover letter through the drafter → reviewer → revise pipeline."""
    if len(req.job_description) < 50:
        raise HTTPException(status_code=400,
                            detail="job_description too short (min 50 chars).")
    if len(req.candidate_profile) < 50:
        raise HTTPException(status_code=400,
                            detail="candidate_profile too short (min 50 chars).")

    # Optional fit check before writing
    fit = None
    if req.run_fit_check:
        try:
            fit = evaluate_fit(req.job_description, req.candidate_profile)
        except Exception as exc:
            logger.warning("Fit check failed (non-fatal): %s", exc)

    try:
        result = generate_cover_letter(
            job_description=req.job_description,
            candidate_profile=req.candidate_profile,
            tone=req.tone,
        )
    except Exception as exc:
        logger.error("Cover letter generation failed: %s", exc)
        raise HTTPException(status_code=500,
                            detail=f"Cover letter generation failed: {exc}")

    return CoverLetterResponse(
        final=result.final,
        draft=result.draft,
        critique=result.critique,
        overall_quality=result.overall_quality,
        approved_at_draft=result.approved_at_draft,
        fit=fit,
    )


class FitRequest(BaseModel):
    job_description: str
    candidate_profile: str


@router.post("/fit", tags=["apply"])
def fit_check(req: FitRequest):
    """Standalone fit evaluation without generating a letter."""
    try:
        return evaluate_fit(req.job_description, req.candidate_profile)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
