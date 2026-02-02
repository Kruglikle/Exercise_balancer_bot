from config import LLM_PROVIDER, OLLAMA_ENDPOINT, OLLAMA_MODEL, QWEN_API_KEY
from local_generator import generate_exercises_local
from ollama_client import OllamaError, generate_exercises_ollama
from qwen_client import QwenAPIError, generate_exercises as generate_exercises_qwen


class LLMError(Exception):
    """Общая ошибка генерации."""


def _has_real_qwen_key() -> bool:
    if not QWEN_API_KEY:
        return False
    lowered = QWEN_API_KEY.strip().lower()
    if not lowered:
        return False
    # Частые плейсхолдеры
    if "paste" in lowered or "your" in lowered or "xxx" in lowered:
        return False
    return True


async def generate_exercises(prompt: str, count: int, vocab_words: list[str]) -> str:
    """
    Унифицированный генератор:
    - qwen (DashScope) при наличии ключа
    - ollama (локально)
    - local (шаблоны), если ключа нет или выбран local
    """
    provider = LLM_PROVIDER
    if not provider:
        provider = "qwen" if _has_real_qwen_key() else "local"

    if provider == "qwen":
        try:
            return await generate_exercises_qwen(prompt, QWEN_API_KEY)
        except QwenAPIError as exc:
            # Если провайдер явно задан — ошибка
            if LLM_PROVIDER:
                raise LLMError(str(exc)) from exc
            # Иначе fallback
            return generate_exercises_local(count, vocab_words)

    if provider == "ollama":
        try:
            return await generate_exercises_ollama(prompt, OLLAMA_MODEL, OLLAMA_ENDPOINT)
        except OllamaError as exc:
            if LLM_PROVIDER:
                raise LLMError(str(exc)) from exc
            return generate_exercises_local(count, vocab_words)

    if provider == "local":
        return generate_exercises_local(count, vocab_words)

    raise LLMError(f"Неизвестный LLM_PROVIDER: {provider}")
