"""BambooHR job-board connector.

BambooHR hosts public career pages at https://{slug}.bamboohr.com/careers.
The underlying API exposes a clean JSON feed:

    GET https://api.bamboohr.com/api/gateway.php/{slug}/v1/applicant_tracking/jobs

This returns lightweight listing entries (id, title, location, employmentStatus).
Full descriptions require a second request per job, so we apply the same
relevance pre-filter used by the SmartRecruiters connector before paying that
cost.

No authentication is required for public boards. No HTML scraping.
"""
from datetime import UTC, datetime

import httpx

from app.connectors.base import TIMEOUT, RawJob, strip_html
from app.ingestion.relevance import DEFAULT_REGION, is_relevant

LIST_URL = "https://api.bamboohr.com/api/gateway.php/{slug}/v1/applicant_tracking/jobs"
DETAIL_URL = "https://api.bamboohr.com/api/gateway.php/{slug}/v1/applicant_tracking/jobs/{job_id}"
# BambooHR asks for an Accept header; without it some boards return XML.
HEADERS = {"Accept": "application/json"}
MAX_DETAIL_FETCHES = 60  # safety valve for very large boards


def fetch(token: str, company: str, region: str = DEFAULT_REGION) -> list[RawJob]:
    """Fetch all relevant jobs for a BambooHR-hosted board.

    `token` is the BambooHR company subdomain slug (e.g. ``"deel"`` for
    ``deel.bamboohr.com``).
    """
    listings = _list_jobs(token)

    jobs: list[RawJob] = []
    for item in listings:
        location = _location_string(item)
        remote = _is_remote(item)
        title = item.get("title") or item.get("jobOpeningName") or ""

        if not is_relevant(location, remote, title, region):
            continue
        if len(jobs) >= MAX_DETAIL_FETCHES:
            break

        job_id = str(item.get("id", ""))
        jobs.append(
            RawJob(
                source="bamboohr",
                external_id=job_id,
                company=company,
                title=title,
                location=location,
                remote=remote,
                description=_description(token, job_id),
                apply_url=item.get("url") or f"https://{token}.bamboohr.com/careers/{job_id}",
                posted_at=_parse_date(item.get("datePosted") or item.get("createdAt")),
            )
        )
    return jobs


def _list_jobs(slug: str) -> list[dict]:
    """Fetch the lightweight job listing for a BambooHR board."""
    try:
        resp = httpx.get(
            LIST_URL.format(slug=slug),
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
        # API may return a top-level list or a dict with a "result" key.
        if isinstance(data, list):
            return data
        return data.get("result") or data.get("jobs") or []
    except Exception:  # noqa: BLE001 - board unavailable → empty list
        return []


def _description(slug: str, job_id: str) -> str:
    """Fetch and flatten the full description for one BambooHR posting."""
    if not job_id:
        return ""
    try:
        resp = httpx.get(
            DETAIL_URL.format(slug=slug, job_id=job_id),
            headers=HEADERS,
            timeout=TIMEOUT,
            follow_redirects=True,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception:  # noqa: BLE001 - a missing description is not fatal
        return ""

    parts = []
    for key in ("description", "jobDescription", "qualifications", "requirements"):
        raw = data.get(key) or ""
        if raw:
            parts.append(strip_html(raw))
    return "\n\n".join(p.strip() for p in parts if p.strip())


def _location_string(item: dict) -> str:
    """Normalise BambooHR's location field into a plain string."""
    loc = item.get("location")
    if isinstance(loc, str):
        return loc
    if isinstance(loc, dict):
        parts = [loc.get("city"), loc.get("state"), loc.get("country")]
        return ", ".join(p for p in parts if p)
    return ""


def _is_remote(item: dict) -> bool:
    """Best-effort remote detection from BambooHR listing metadata."""
    if "remote" in str(item.get("employmentType") or "").lower():
        return True
    loc = _location_string(item)
    return "remote" in loc.lower()


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)
    except (ValueError, TypeError):
        return None
