"""Salary benchmarking.

Two modes:
1. Local JSON data file (salary_data.json at repo root) — fast, offline.
2. LLM estimate via OpenRouter — fallback when no local data exists.

The local file format follows ai-job-search/salary_data.json:
{
  "metadata": { "currency": "INR", "year": 2026 },
  "companies": [
    { "name": "Stripe", "roles": [
        { "title": "SDE", "min": 2500000, "max": 4000000, "currency": "INR" }
    ]}
  ]
}
"""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

from app.llm_client import FAST_MODEL, chat_json

logger = logging.getLogger(__name__)

_DATA_FILE = Path(__file__).resolve().parents[4] / "salary_data.json"


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text.lower())
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def lookup_from_file(company: str, role_title: str) -> Optional[dict]:
    """Search the local salary_data.json for a matching entry."""
    if not _DATA_FILE.exists():
        return None
    try:
        data = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None

    norm_company = _normalize(company)
    norm_role = _normalize(role_title)

    for entry in data.get("companies", []):
        if _normalize(entry.get("name", "")) != norm_company:
            continue
        for role in entry.get("roles", []):
            if _normalize(role.get("title", "")) in norm_role or norm_role in _normalize(role.get("title", "")):
                currency = role.get("currency", data.get("metadata", {}).get("currency", "USD"))
                return {
                    "source": "local_data",
                    "company": entry["name"],
                    "role_title": role["title"],
                    "min": role.get("min"),
                    "max": role.get("max"),
                    "median": role.get("median"),
                    "currency": currency,
                    "year": data.get("metadata", {}).get("year"),
                }
    return None


_LLM_SYSTEM = """You are a compensation data analyst. Provide realistic salary estimates
based on your training data (market rates as of 2025–2026). Be conservative and accurate.
Respond with JSON only. If you cannot estimate reliably, set all numeric fields to null."""

_LLM_PROMPT = """Estimate the salary range for this role:

Company: {company}
Role: {role_title}
Location: {location}
Experience level: {experience}

Respond with:
{{
  "min_annual": <number or null>,
  "max_annual": <number or null>,
  "median_annual": <number or null>,
  "currency": "<3-letter code>",
  "confidence": "high" | "medium" | "low",
  "notes": "...",
  "percentiles": {{
    "p25": <number or null>,
    "p50": <number or null>,
    "p75": <number or null>
  }}
}}"""

_LLM_SCHEMA = {
    "type": "object",
    "properties": {
        "min_annual": {"type": ["number", "null"]},
        "max_annual": {"type": ["number", "null"]},
        "median_annual": {"type": ["number", "null"]},
        "currency": {"type": "string"},
        "confidence": {"type": "string"},
        "notes": {"type": "string"},
        "percentiles": {
            "type": "object",
            "properties": {
                "p25": {"type": ["number", "null"]},
                "p50": {"type": ["number", "null"]},
                "p75": {"type": ["number", "null"]},
            },
        },
    },
    "required": ["min_annual", "max_annual", "median_annual", "currency", "confidence", "notes"],
}


def lookup_from_llm(
    company: str,
    role_title: str,
    location: str = "India",
    experience: str = "entry-level (0-2 years)",
    model: str = FAST_MODEL,
) -> dict:
    """Use OpenRouter to estimate a salary range."""
    prompt = _LLM_PROMPT.format(
        company=company, role_title=role_title,
        location=location, experience=experience,
    )
    result = chat_json(
        [{"role": "system", "content": _LLM_SYSTEM},
         {"role": "user", "content": prompt}],
        _LLM_SCHEMA,
        model=model,
        temperature=0.1,
    )
    result["source"] = "llm_estimate"
    result["company"] = company
    result["role_title"] = role_title
    return result


def benchmark(
    company: str,
    role_title: str,
    location: str = "India",
    experience: str = "entry-level (0-2 years)",
) -> dict:
    """Return salary data from local file, falling back to LLM estimate."""
    local = lookup_from_file(company, role_title)
    if local:
        return local
    return lookup_from_llm(company, role_title, location, experience)
