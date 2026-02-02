import asyncio
from typing import Optional

import aiohttp

from config import QWEN_ENDPOINT, QWEN_MODEL


class QwenAPIError(Exception):
    """Ошибки работы с Qwen API."""


async def generate_exercises(prompt: str, api_key: str, max_retries: int = 3) -> str:
    """
    Вызывает DashScope (Qwen) и возвращает сгенерированный текст.
    """
    if not api_key:
        raise QwenAPIError("Не задан QWEN_API_KEY в переменных окружения.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": QWEN_MODEL,
        "input": {"prompt": prompt},
        "parameters": {
            "result_format": "message",
            "temperature": 0.7,
        },
    }

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_retries):
            try:
                async with session.post(QWEN_ENDPOINT, headers=headers, json=payload, timeout=60) as resp:
                    if resp.status == 429:
                        # Rate limit — ждём и повторяем
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if resp.status >= 500:
                        await asyncio.sleep(2 ** attempt)
                        continue
                    if resp.status >= 400:
                        text = await resp.text()
                        raise QwenAPIError(f"Ошибка API {resp.status}: {text}")

                    data = await resp.json()
                    content = _extract_text(data)
                    if not content:
                        raise QwenAPIError("Пустой ответ от Qwen API.")
                    return content
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt >= max_retries - 1:
                    raise QwenAPIError(f"Сетевая ошибка при вызове Qwen: {exc}") from exc
                await asyncio.sleep(2 ** attempt)

    raise QwenAPIError("Не удалось получить ответ от Qwen после повторных попыток.")


def _extract_text(data: dict) -> Optional[str]:
    """
    Пытаемся извлечь текст из разных форматов ответа DashScope.
    """
    if not isinstance(data, dict):
        return None

    output = data.get("output") or {}
    if isinstance(output, dict):
        # Формат с output.text
        if "text" in output:
            return output.get("text")
        # Формат с choices/message
        choices = output.get("choices") or []
        if choices and isinstance(choices, list):
            choice0 = choices[0]
            if isinstance(choice0, dict):
                message = choice0.get("message", {})
                if isinstance(message, dict):
                    return message.get("content")
    return None
