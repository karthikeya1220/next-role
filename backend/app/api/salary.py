"""GET /salary — market salary benchmarking."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.salary.lookup import benchmark

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/salary", tags=["salary"])


class SalaryResponse(BaseModel):
    company: str
    role_title: str
    min_annual: Optional[float]
    max_annual: Optional[float]
    median_annual: Optional[float]
    currency: str
    confidence: Optional[str] = None
    notes: Optional[str] = None
    source: str
    percentiles: Optional[dict] = None


@router.get("", response_model=SalaryResponse)
def salary_benchmark(
    company: str = Query(..., description="Company name"),
    role: str = Query(..., description="Role/job title"),
    location: str = Query("India", description="Country or city"),
    experience: str = Query("entry-level (0-2 years)",
                            description="Experience level description"),
):
    """Look up market salary for a role at a company."""
    if not company.strip() or not role.strip():
        raise HTTPException(status_code=400,
                            detail="company and role are required.")
    try:
        result = benchmark(
            company=company.strip(),
            role_title=role.strip(),
            location=location,
            experience=experience,
        )
        return SalaryResponse(**result)
    except Exception as exc:
        logger.error("Salary lookup failed: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc))
