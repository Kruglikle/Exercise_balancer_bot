import asyncio
from typing import Optional

import aiohttp


class OllamaError(Exception):
    """Ошибки работы с Ollama."""


async def generate_exercises_ollama(
    prompt: str, model: str, endpoint: str, max_retries: int = 2
) -> str:
    """Вызывает локальный Ollama API и возвращает сгенерированный текст."""
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(endpoint, json=payload, timeout=60) as resp:
                    if resp.status >= 500:
                        await asyncio.sleep(1 + attempt)
                        continue
                    if resp.status >= 400:
                        text = await resp.text()
                        raise OllamaError(f"Ошибка Ollama {resp.status}: {text}")
                    data = await resp.json()
                    text = _extract_text(data)
                    if not text:
                        raise OllamaError("Пустой ответ от Ollama.")
                    return text
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt >= max_retries - 1:
                    raise OllamaError(f"Сетевая ошибка Ollama: {exc}") from exc
                await asyncio.sleep(1 + attempt)

    raise OllamaError("Не удалось получить ответ от Ollama.")


def _extract_text(data: dict) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    return data.get("response")
