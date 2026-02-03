from config import (
    LLM_PROVIDER,
    OLLAMA_ENDPOINT,
    OLLAMA_MODEL,
    OPENROUTER_API_KEY,
    QWEN_API_KEY,
)
from local_generator import generate_exercises_local
from ollama_client import OllamaError, generate_exercises_ollama
from openrouter_client import OpenRouterError, generate_exercises_openrouter
from qwen_client import QwenAPIError, generate_exercises as generate_exercises_qwen


class LLMError(Exception):
    """Unified generation error."""


def _has_real_openrouter_key() -> bool:
    if not OPENROUTER_API_KEY:
        return False
    lowered = OPENROUTER_API_KEY.strip().lower()
    if not lowered:
        return False
    if "paste" in lowered or "your" in lowered or "xxx" in lowered:
        return False
    return True


def _has_real_qwen_key() -> bool:
    if not QWEN_API_KEY:
        return False
    lowered = QWEN_API_KEY.strip().lower()
    if not lowered:
        return False
    # Common placeholders
    if "paste" in lowered or "your" in lowered or "xxx" in lowered:
        return False
    return True


def _resolve_provider() -> str:
    if LLM_PROVIDER:
        return LLM_PROVIDER
    if _has_real_openrouter_key():
        return "openrouter"
    if _has_real_qwen_key():
        return "qwen"
    return "local"


async def generate_exercises(prompt: str, count: int, vocab_words: list[str]) -> str:
    """
    Unified generator:
    - openrouter (Qwen via OpenRouter) when key is present
    - qwen (DashScope) when key is present
    - ollama (local)
    - local templates if no provider is configured
    """
    provider = _resolve_provider()

    if provider == "openrouter":
        try:
            return await generate_exercises_openrouter(prompt, OPENROUTER_API_KEY)
        except OpenRouterError as exc:
            raise LLMError(str(exc)) from exc

    if provider == "qwen":
        try:
            return await generate_exercises_qwen(prompt, QWEN_API_KEY)
        except QwenAPIError as exc:
            if LLM_PROVIDER:
                raise LLMError(str(exc)) from exc
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

    raise LLMError(f"Unknown LLM_PROVIDER: {provider}")
