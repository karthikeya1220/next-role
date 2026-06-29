"""Filter settings: what the candidate will actually apply to.

Re-scoring is exposed here rather than run automatically on save, so the user
sees explicitly that changing a filter recomputes the list — and because it is
pure arithmetic over cached extractions, it finishes in seconds.
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Preferences
from app.db.session import get_db
from app.ingestion.enrich import rescore_all
from app.schemas import PreferencesIn, PreferencesOut

router = APIRouter(prefix="/preferences", tags=["preferences"])


def _get_or_create(db: Session) -> Preferences:
    prefs = db.scalar(select(Preferences).limit(1))
    if prefs is None:
        prefs = Preferences()
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    return prefs


@router.get("", response_model=PreferencesOut)
def get_preferences(db: Session = Depends(get_db)) -> Preferences:
    return _get_or_create(db)


@router.put("", response_model=PreferencesOut)
def update_preferences(data: PreferencesIn, db: Session = Depends(get_db)) -> Preferences:
    prefs = _get_or_create(db)
    prefs.region = data.region
    prefs.max_years = data.max_years
    prefs.allowed_seniority = data.allowed_seniority
    prefs.role_families = data.role_families
    prefs.preferred_locations = data.preferred_locations
    prefs.remote_ok = data.remote_ok
    db.commit()
    db.refresh(prefs)
    return prefs


@router.post("/rescore")
def rescore(db: Session = Depends(get_db)) -> dict:
    """Re-apply filters and recompute every score. No LLM calls."""
    return rescore_all(db)
