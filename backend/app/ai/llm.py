"""Thin, swappable wrapper around the local LLM (Ollama).

Everything that needs the model calls `generate_json` — a single choke point.
To swap Ollama for something else later (e.g. OpenRouter), only this file changes.

We force JSON output so extraction/generation returns something we can parse,
and use a low temperature because these are extraction tasks, not creative ones.
"""
import json

import httpx

from app.config import settings

# Ollama defaults a model to a few thousand tokens of context whatever the model
# can actually do, and silently drops what does not fit. Every prompt we send is
# long on purpose — the whole knowledge base, a whole resume section, a whole
# document — so an unset window means the model quietly stops seeing the start
# of its own instructions. Set it once, here, for every call.
CONTEXT_TOKENS = 16384


def generate_json(
    system: str, prompt: str, timeout: float | None = 120.0, max_tokens: int = 1200
) -> dict:
    """Send a system+user prompt, get a parsed JSON object back.

    `max_tokens` is not optional in spirit: small models sometimes fall into a
    repetition loop and generate until something kills them. Capping the output
    turns a 10-minute hang into a fast, retryable failure.

    `timeout=None` waits indefinitely. Use it only for work the user has been
    told is slow and can watch progress on — document parsing — never for a
    call made inside a request the browser is holding open.
    """
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "format": "json",  # Ollama guarantees the response is valid JSON.
        "options": {
            "temperature": 0.1,
            "num_predict": max_tokens,
            "num_ctx": CONTEXT_TOKENS,
        },
    }
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=timeout)
    resp.raise_for_status()
    content = resp.json()["message"]["content"]
    return json.loads(content)


def generate_text(
    system: str, prompt: str, timeout: float | None = 120.0, max_tokens: int = 1200
) -> str:
    """Same call, without the JSON envelope — for output that *is* the answer.

    LaTeX is the case: wrapping a document full of backslashes in a JSON string
    means every one of them has to survive escaping, which is a needless way to
    lose a resume.
    """
    payload = {
        "model": settings.ollama_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": max_tokens,
            "num_ctx": CONTEXT_TOKENS,
        },
    }
    resp = httpx.post(f"{settings.ollama_url}/api/chat", json=payload, timeout=timeout)
    resp.raise_for_status()
    return resp.json()["message"]["content"]
