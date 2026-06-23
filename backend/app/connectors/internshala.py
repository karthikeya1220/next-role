"""Internshala job & internship connector.

Internshala does not expose a public JSON API, but their AJAX listing endpoint
returns a structured, paginated HTML fragment that has been stable for years:

    GET https://internshala.com/internships/ajax_get_listing/
    GET https://internshala.com/jobs/ajax_get_listing/

Each listing card is a `div.individual_internship` element with:
  - ``internshipid`` attribute  — stable numeric ID, used as ``external_id``
  - ``employment_type`` attribute — ``"internship"`` or ``"job"``
  - ``data-href`` attribute — URL path to the detail page

This connector intentionally avoids scraping by CSS class wherever a data-
attribute gives us the same value, because class names are cosmetic and will
change; data attributes are semantic and won't.

Why scrape at all?
  Internshala is the largest Indian platform specifically for 0–2 year
  experience roles. Every other connector targets company ATSes directly;
  this is the one aggregator that genuinely cannot be skipped for the Indian
  fresher market. The scraper is tightly isolated: if Internshala changes
  their HTML, only this connector fails.
"""
import re
import time
from datetime import UTC, datetime, timedelta

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import TIMEOUT, RawJob
from app.ingestion.relevance import DEFAULT_REGION, is_relevant

BASE_URL = "https://internshala.com"
INTERNSHIP_AJAX = BASE_URL + "/internships/ajax_get_listing/"
JOB_AJAX = BASE_URL + "/jobs/ajax_get_listing/"

# Maximum cards to return per listing type (internships + jobs combined).
# Internshala returns 50 per page; we allow up to 3 pages to avoid hammering.
MAX_PAGES = 3
PAGE_SIZE = 50

# Polite inter-page delay (seconds) so we don't look like a crawler.
PAGE_DELAY = 1.5

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "X-Requested-With": "XMLHttpRequest",
    "Referer": BASE_URL + "/internships/",
}


def fetch(token: str, company: str, region: str = DEFAULT_REGION) -> list[RawJob]:
    """Fetch fresher-friendly listings from Internshala.

    ``token`` is ignored — Internshala is a search aggregator, not a per-company
    board.  The ingestion layer uses ``token="internshala"`` as a sentinel so the
    database row stays consistent with the other connectors.
    """
    with httpx.Client(
        follow_redirects=True,
        timeout=TIMEOUT,
        headers=_HEADERS,
    ) as session:
        # A real browser visit sets the session cookie (PHPSESSID, CSRF token)
        # which the AJAX endpoint checks.  One warm-up GET is enough.
        try:
            session.get(BASE_URL + "/internships/")
        except Exception:  # noqa: BLE001
            pass

        jobs: list[RawJob] = []
        _fetch_pages(session, INTERNSHIP_AJAX, "internshala", "Internshala", region, jobs)
        _fetch_pages(session, JOB_AJAX, "internshala", "Internshala", region, jobs)
        return jobs


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _fetch_pages(
    session: httpx.Client,
    url: str,
    source: str,
    company: str,
    region: str,
    out: list[RawJob],
) -> None:
    """Paginate through one listing type and append matching RawJobs to ``out``."""
    for page in range(1, MAX_PAGES + 1):
        try:
            # Internshala paginates with a ``start`` offset, 1-indexed by page.
            resp = session.get(
                url,
                params={"search-internship": "1", "start": (page - 1) * PAGE_SIZE + 1},
            )
            resp.raise_for_status()
        except Exception:  # noqa: BLE001 - any failure ends pagination cleanly
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select(".individual_internship")
        if not cards:
            break  # No more results

        for card in cards:
            job = _parse_card(card, source, company)
            if job and is_relevant(job.location, job.remote, job.title, region):
                out.append(job)

        if len(cards) < PAGE_SIZE:
            break  # Last page
        if page < MAX_PAGES:
            time.sleep(PAGE_DELAY)


def _parse_card(card, source: str, company: str) -> RawJob | None:
    """Extract a RawJob from one ``.individual_internship`` div."""
    # The numeric ID is in the ``internshipid`` HTML attribute — stable,
    # semantic, won't change when CSS classes are renamed.
    job_id = card.get("internshipid", "")
    if not job_id:
        return None

    # URL path is in data-href; prefix the base domain.
    href = card.get("data-href", "")
    apply_url = BASE_URL + href if href else BASE_URL + f"/internship/detail/{job_id}"

    title_el = card.select_one(".job-internship-name a") or card.select_one("h2 a")
    title = title_el.get_text(strip=True) if title_el else ""

    company_el = card.select_one("p.company-name") or card.select_one(".company-name")
    company_name = company_el.get_text(strip=True) if company_el else company

    # Location: "Work From Home" cards have no city element.
    loc_el = card.select_one(".locations span")
    location_text = loc_el.get_text(strip=True) if loc_el else ""
    is_wfh = "work from home" in card.get_text().lower() or "remote" in card.get_text().lower()
    remote = is_wfh or "remote" in location_text.lower()
    location = "Remote" if is_wfh and not location_text else location_text

    # Description is the plain-text requirements/about section already in the card.
    desc_el = card.select_one(".about_job .text")
    description = desc_el.get_text(separator="\n", strip=True) if desc_el else ""

    # Stipend / salary — include it in the description so the LLM can score it.
    stipend_el = card.select_one(".stipend")
    if stipend_el:
        stipend = stipend_el.get_text(strip=True)
        if stipend and description:
            description = f"Stipend/Salary: {stipend}\n\n{description}"

    posted_at = _parse_posted(card)

    return RawJob(
        source=source,
        external_id=str(job_id),
        company=company_name,
        title=title,
        location=location,
        remote=remote,
        description=description,
        apply_url=apply_url,
        posted_at=posted_at,
    )


_AGO_RE = re.compile(r"(\d+)\s+(day|hour|week|month)s?\s+ago", re.IGNORECASE)


def _parse_posted(card) -> datetime | None:
    """Parse relative timestamps like '5 days ago' into UTC datetimes."""
    el = card.select_one(".status-info span")
    if not el:
        return None
    text = el.get_text(strip=True)
    m = _AGO_RE.search(text)
    if not m:
        return None
    n, unit = int(m.group(1)), m.group(2).lower()
    deltas = {"hour": timedelta(hours=n), "day": timedelta(days=n),
              "week": timedelta(weeks=n), "month": timedelta(days=n * 30)}
    delta = deltas.get(unit)
    return (datetime.now(tz=UTC) - delta) if delta else None
