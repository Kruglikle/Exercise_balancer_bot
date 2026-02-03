import asyncio
from typing import Optional

import aiohttp

from config import (
    OPENROUTER_ENDPOINT,
    OPENROUTER_MODEL,
    OPENROUTER_REFERER,
    OPENROUTER_TITLE,
)


class OpenRouterError(Exception):
    """Errors when calling OpenRouter API."""


async def generate_exercises_openrouter(prompt: str, api_key: str, max_retries: int = 3) -> str:
    """Call OpenRouter API and return generated text."""
    if not api_key:
        raise OpenRouterError("OPENROUTER_API_KEY is not set in the environment.")
    if not OPENROUTER_MODEL:
        raise OpenRouterError("OPENROUTER_MODEL is not set in the environment.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if OPENROUTER_REFERER:
        headers["HTTP-Referer"] = OPENROUTER_REFERER
    if OPENROUTER_TITLE:
        headers["X-Title"] = OPENROUTER_TITLE

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
    }

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(
                    OPENROUTER_ENDPOINT, headers=headers, json=payload, timeout=60
                ) as resp:
                    if resp.status == 429:
                        await asyncio.sleep(2**attempt)
                        continue
                    if resp.status >= 500:
                        await asyncio.sleep(2**attempt)
                        continue
                    if resp.status >= 400:
                        text = await resp.text()
                        raise OpenRouterError(f"OpenRouter API error {resp.status}: {text}")

                    data = await resp.json()
                    error = data.get("error") if isinstance(data, dict) else None
                    if error:
                        if isinstance(error, dict):
                            message = error.get("message") or str(error)
                        else:
                            message = str(error)
                        raise OpenRouterError(f"OpenRouter error: {message}")
                    content = _extract_text(data)
                    if not content:
                        raise OpenRouterError("Empty response from OpenRouter.")
                    return content
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt >= max_retries - 1:
                    raise OpenRouterError(f"Network error calling OpenRouter: {exc}") from exc
                await asyncio.sleep(2**attempt)

    raise OpenRouterError("Failed to get response from OpenRouter after retries.")


def _extract_text(data: dict) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    choice0 = choices[0]
    if isinstance(choice0, dict):
        message = choice0.get("message")
        if isinstance(message, dict):
            content = message.get("content")
            if content:
                return content
        if "text" in choice0:
            return choice0.get("text")
    return None
