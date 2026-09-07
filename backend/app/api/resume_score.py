"""POST /resume-score — upload a PDF, get back an explainable score card.

Pipeline:
  1. Save the uploaded PDF to a temp file
  2. Extract text with PyMuPDF (app.resume.pdf)
  3. (Optional) enrich with GitHub data if a username is provided
  4. Run the LLM scorer (app.resume.evaluator)
  5. Return the structured score + raw resume JSON
"""

import logging
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.resume.pdf import extract_json_resume_from_pdf, extract_text_from_pdf
from app.resume.evaluator import score_resume
from app.resume.github import fetch_github_profile, format_github_for_scoring
from app.resume.roles import load_role, list_available_roles
from app.resume.transform import convert_json_resume_to_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/resume-score", tags=["resume-score"])


class ScoreRequest(BaseModel):
    role_name: str = "software_engineering_intern"
    github_username: Optional[str] = None


class ScoreResponse(BaseModel):
    total_score: float
    max_score: int
    position_title: str
    role_name: str
    categories: dict
    bonus_points: dict
    deductions: dict
    key_strengths: list[str]
    areas_for_improvement: list[str]
    candidate_name: Optional[str] = None
    github_enriched: bool = False


@router.get("/roles")
def list_roles():
    """Return available scoring roles."""
    return {"roles": list_available_roles()}


@router.post("", response_model=ScoreResponse)
async def score_resume_endpoint(
    file: UploadFile = File(..., description="Resume PDF"),
    role_name: str = Form("software_engineering_intern"),
    github_username: Optional[str] = Form(None),
):
    """Upload a resume PDF and receive an explainable score card."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Load role definition
    try:
        role = load_role(role_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # Save PDF to temp file
    content = await file.read()
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Extract JSON Resume
        json_resume = extract_json_resume_from_pdf(tmp_path)
        if json_resume is None:
            raise HTTPException(
                status_code=422,
                detail="Could not extract resume data from the PDF. "
                       "Ensure the file is a text-based (not scanned) PDF.",
            )

        # Build scoring text
        resume_text = convert_json_resume_to_text(json_resume)

        # GitHub enrichment
        github_enriched = False
        if github_username:
            profile = fetch_github_profile(github_username.strip())
            if profile:
                github_text = format_github_for_scoring(profile)
                resume_text = f"{resume_text}\n\n--- GitHub Profile ---\n{github_text}"
                github_enriched = True

        # Score
        result = score_resume(resume_text, role)

        # Candidate name from basics
        candidate_name = None
        if json_resume.basics and json_resume.basics.name:
            candidate_name = json_resume.basics.name

        return ScoreResponse(
            total_score=result["total_score"],
            max_score=result["max_score"],
            position_title=result["position_title"],
            role_name=result["role_name"],
            categories=result.get("scores", {}),
            bonus_points=result.get("bonus_points", {}),
            deductions=result.get("deductions", {}),
            key_strengths=result.get("key_strengths", []),
            areas_for_improvement=result.get("areas_for_improvement", []),
            candidate_name=candidate_name,
            github_enriched=github_enriched,
        )

    finally:
        os.unlink(tmp_path)
