"""Workable job-board connector.

Workable exposes a public, unauthenticated widget API for every hosted board:

    GET https://apply.workable.com/api/v1/widget/accounts/{slug}

This returns the full job list in one shot with location fields (city, state,
country) at the top level, a ``telecommuting`` flag for remote, and a
``shortcode`` that is stable across re-runs (ideal for deduplication).

No browser automation, no HTML scraping. Styling changes on apply.workable.com
have no effect here.
"""
from datetime import UTC, datetime

import httpx

from app.connectors.base import TIMEOUT, RawJob, strip_html
from app.ingestion.relevance import DEFAULT_REGION, is_relevant

WIDGET_URL = "https://apply.workable.com/api/v1/widget/accounts/{slug}"
DETAIL_URL = "https://apply.workable.com/api/v3/accounts/{slug}/jobs/{shortcode}"
MAX_DETAIL_FETCHES = 60  # safety valve for very large boards


def fetch(token: str, company: str, region: str = DEFAULT_REGION) -> list[RawJob]:
    """Fetch all relevant jobs for a Workable-hosted board.

    ``token`` is the Workable account slug (e.g. ``"skroutz"`` for
    ``apply.workable.com/skroutz``).
    """
    listings = _list_jobs(token)

    jobs: list[RawJob] = []
    for item in listings:
        location = _location_string(item)
        remote = bool(item.get("telecommuting"))
        title = item.get("title", "")

        if not is_relevant(location, remote, title, region):
            continue
        if len(jobs) >= MAX_DETAIL_FETCHES:
            break

        shortcode = item.get("shortcode", "")
        jobs.append(
            RawJob(
                source="workable",
                external_id=shortcode,
                company=company,
                title=title,
                location=location,
                remote=remote,
                description=_description(token, shortcode),
                apply_url=item.get("application_url") or item.get("url") or (
                    f"https://apply.workable.com/{token}/j/{shortcode}/"
                ),
                posted_at=_parse_date(item.get("created_at")),
            )
        )
    return jobs


def _list_jobs(slug: str) -> list[dict]:
    """Fetch the full public job listing for a Workable board via the widget API."""
    try:
        resp = httpx.get(
            WIDGET_URL.format(slug=slug),
            timeout=TIMEOUT,
            follow_redirects=True,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        return data.get("jobs") or []
    except Exception:  # noqa: BLE001 - board unavailable → empty list
        return []


def _description(slug: str, shortcode: str) -> str:
    """Fetch and flatten the full description for one Workable posting."""
    if not shortcode:
        return ""
    try:
        resp = httpx.get(
            DETAIL_URL.format(slug=slug, shortcode=shortcode),
            timeout=TIMEOUT,
            follow_redirects=True,
            headers={"Accept": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:  # noqa: BLE001 - a missing description is not fatal
        return ""

    parts = []
    for key in ("description", "requirements", "benefits"):
        raw = data.get(key) or ""
        if raw:
            parts.append(strip_html(raw))
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _location_string(item: dict) -> str:
    """Build a plain location string from Workable's flat city/state/country fields."""
    parts = [item.get("city"), item.get("state"), item.get("country")]
    return ", ".join(p for p in parts if p)


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, TypeError):
        return None
