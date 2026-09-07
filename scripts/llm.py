"""Minimal LLM client for optional AI enhancements in the weekly digest.

Reads environment variables:
    LLM_PROVIDER   deepseek (default) | openai | openrouter | anthropic
    LLM_API_KEY    required
    LLM_MODEL      default deepseek-chat
Optional:
    LLM_BASE_URL   override the chat completions endpoint
"""

from __future__ import annotations

import json
import os
import urllib.request


def llm_complete(
    prompt: str,
    system: str | None = None,
    max_tokens: int = 2500,
    temperature: float = 0.3,
) -> str | None:
    api_key = os.getenv("LLM_API_KEY", "").strip()
    if not api_key:
        return None

    provider = os.getenv("LLM_PROVIDER", "deepseek").strip().lower()
    model = os.getenv("LLM_MODEL", "deepseek-chat").strip()

    if provider == "deepseek":
        url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/chat/completions")
    elif provider == "anthropic":
        # Keep the code simple: Anthropic can be used through OpenRouter or
        # through a native adapter later; for now route via OpenAI-compatible
        # base URL if provided, otherwise fail with a clear message.
        url = os.getenv("LLM_BASE_URL", "")
        if not url:
            raise RuntimeError("Anthropic provider requires LLM_BASE_URL (OpenAI-compatible endpoint).")
    else:
        url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1/chat/completions")

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "weekly-ai-sync/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected LLM response: {data}") from exc


def available() -> bool:
    return bool(os.getenv("LLM_API_KEY", "").strip())