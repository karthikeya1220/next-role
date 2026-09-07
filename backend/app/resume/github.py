"""GitHub profile enricher.

Fetches public GitHub data for a username and formats it as structured text
for the resume scorer.  No auth token required for basic public data.
"""

import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}


def fetch_github_profile(username: str) -> Optional[dict]:
    """Fetch public profile + top repos for *username*."""
    try:
        with httpx.Client(timeout=15) as client:
            user_resp = client.get(f"{GITHUB_API}/users/{username}", headers=HEADERS)
            if user_resp.status_code == 404:
                logger.warning("GitHub user not found: %s", username)
                return None
            user_resp.raise_for_status()
            user = user_resp.json()

            repos_resp = client.get(
                f"{GITHUB_API}/users/{username}/repos",
                headers=HEADERS,
                params={"sort": "updated", "per_page": 10, "type": "owner"},
            )
            repos_resp.raise_for_status()
            repos = repos_resp.json()

        top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]

        return {
            "username": username,
            "name": user.get("name"),
            "bio": user.get("bio"),
            "public_repos": user.get("public_repos", 0),
            "followers": user.get("followers", 0),
            "account_age_years": _account_age(user.get("created_at", "")),
            "top_repos": [
                {
                    "name": r["name"],
                    "description": r.get("description") or "",
                    "stars": r.get("stargazers_count", 0),
                    "language": r.get("language") or "unknown",
                    "topics": r.get("topics", []),
                }
                for r in top_repos
            ],
        }
    except Exception as exc:
        logger.error("GitHub fetch failed for %s: %s", username, exc)
        return None


def _account_age(created_at: str) -> float:
    if not created_at:
        return 0
    from datetime import datetime, timezone
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return round((now - created).days / 365.25, 1)
    except ValueError:
        return 0


def format_github_for_scoring(profile: dict) -> str:
    """Return a plain-text summary of the GitHub profile for LLM consumption."""
    if not profile:
        return ""
    lines = [
        f"GitHub: @{profile['username']}",
        f"Public repos: {profile['public_repos']} | Followers: {profile['followers']} | Account age: {profile['account_age_years']}y",
    ]
    if profile.get("bio"):
        lines.append(f"Bio: {profile['bio']}")
    if profile.get("top_repos"):
        lines.append("\nTop repositories:")
        for r in profile["top_repos"]:
            topics = ", ".join(r["topics"][:4]) if r["topics"] else ""
            lines.append(
                f"  • {r['name']} ({r['language']}, ★{r['stars']})"
                + (f" — {r['description'][:80]}" if r["description"] else "")
                + (f" [{topics}]" if topics else "")
            )
    return "\n".join(lines)
