"""Unified LLM client backed by OpenRouter.

A single OPENROUTER_API_KEY gives access to hundreds of models through
one OpenAI-compatible endpoint.  Every feature in CareerOS (resume scorer,
cover-letter writer, fit evaluator) calls this module instead of the three
separate providers the original projects used.

Environment variables (all optional — sensible defaults are baked in):
    OPENROUTER_API_KEY   Required. Get one at https://openrouter.ai/keys
    LLM_FAST_MODEL       Default: google/gemini-flash-1.5
    LLM_POWER_MODEL      Default: anthropic/claude-sonnet-4-5
"""

import json
import logging
import os
import random
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1"

# Fast + cheap — bulk work: scoring 100 jobs, parsing PDF sections.
FAST_MODEL = os.getenv("LLM_FAST_MODEL", "google/gemini-flash-1.5")

# Higher quality — creative writing: cover-letter reviewer pass, fit eval.
POWER_MODEL = os.getenv("LLM_POWER_MODEL", "anthropic/claude-sonnet-4-5")

_MAX_RETRIES = 5
_BASE_DELAY = 10.0  # seconds
_MAX_DELAY = 120.0


def _get_api_key() -> str:
    key = os.getenv("OPENROUTER_API_KEY", "")
    if not key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is not set. "
            "Add it to your .env file — get a key at https://openrouter.ai/keys"
        )
    return key


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_api_key()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/karthikeya1220/next-role",
        "X-Title": "CareerOS",
    }


def chat(
    messages: list[dict],
    *,
    model: str = FAST_MODEL,
    temperature: float = 0.3,
    top_p: float = 0.9,
    response_format: dict | None = None,
    timeout: float = 300.0,
) -> str:
    """Send a chat request to OpenRouter and return the assistant reply text."""
    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "stream": False,
    }
    if response_format:
        body["response_format"] = response_format

    for attempt in range(_MAX_RETRIES):
        try:
            resp = httpx.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers=_headers(),
                json=body,
                timeout=timeout,
            )
        except httpx.TimeoutException:
            delay = min(_BASE_DELAY * (2**attempt), _MAX_DELAY)
            sleep = round(delay * random.uniform(0.8, 1.2), 2)
            logger.warning("OpenRouter timeout (attempt %d/%d). Retrying in %ss…", attempt + 1, _MAX_RETRIES, sleep)
            time.sleep(sleep)
            continue

        if resp.status_code == 429 and attempt < _MAX_RETRIES - 1:
            retry_after = resp.headers.get("Retry-After")
            exp_delay = min(_BASE_DELAY * (2**attempt), _MAX_DELAY)
            delay = float(retry_after) if retry_after else exp_delay
            sleep = round(delay * random.uniform(0.8, 1.2), 2)
            logger.warning("Rate-limited (attempt %d/%d). Retrying in %ss…", attempt + 1, _MAX_RETRIES, sleep)
            time.sleep(sleep)
            continue

        if resp.status_code in {500, 502, 503, 504} and attempt < _MAX_RETRIES - 1:
            exp_delay = min(_BASE_DELAY * (2**attempt), _MAX_DELAY)
            sleep = round(exp_delay * random.uniform(0.8, 1.2), 2)
            logger.warning("Transient server error %d (attempt %d/%d). Retrying in %ss…",
                           resp.status_code, attempt + 1, _MAX_RETRIES, sleep)
            time.sleep(sleep)
            continue

        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ValueError(f"Unexpected OpenRouter response shape: {data}") from exc

    raise RuntimeError(f"OpenRouter request failed after {_MAX_RETRIES} attempts.")


def chat_json(
    messages: list[dict],
    schema: dict,
    *,
    model: str = FAST_MODEL,
    temperature: float = 0.1,
) -> dict:
    """Like chat(), but requests structured JSON output matching *schema*."""
    response_format = {
        "type": "json_schema",
        "json_schema": {"name": "response", "strict": True, "schema": schema},
    }
    raw = chat(messages, model=model, temperature=temperature,
               response_format=response_format)
    return _parse_json(raw)


def _parse_json(text: str) -> dict:
    """Extract and parse JSON from a string, stripping markdown fences and <think> tags."""
    if "<think>" in text:
        start = text.find("<think>")
        end = text.find("</think>")
        if start != -1 and end != -1:
            text = text[:start] + text[end + 8:]

    text = text.strip()
    for prefix in ("```json", "```"):
        if text.startswith(prefix):
            text = text[len(prefix):]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1:
        text = text[start: end + 1]

    return json.loads(text)
