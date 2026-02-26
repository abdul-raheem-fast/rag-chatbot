"""
LLM Gateway using LiteLLM for provider-agnostic LLM calls.
Supports OpenAI, Anthropic (Claude), and Google (Gemini).
"""
import litellm
from typing import AsyncGenerator
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

PROVIDER_MODEL_MAP = {
    "openai": settings.openai_model,
    "anthropic": settings.anthropic_model,
    "google": settings.google_model,
}

litellm.drop_params = True


def _get_model_string(provider: str | None = None, model: str | None = None) -> str:
    provider = provider or settings.default_llm_provider
    if model:
        return model if "/" in model else f"{provider}/{model}"

    default_model = PROVIDER_MODEL_MAP.get(provider, settings.openai_model)
    if provider == "openai":
        return default_model
    return f"{provider}/{default_model}"


async def llm_completion(
    messages: list[dict],
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> dict:
    """Non-streaming LLM call. Returns {"content": str, "tokens": int}."""
    model_str = _get_model_string(provider, model)
    logger.info("LLM completion", model=model_str, messages_count=len(messages))

    response = await litellm.acompletion(
        model=model_str,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    content = response.choices[0].message.content
    tokens = response.usage.total_tokens if response.usage else 0
    return {"content": content, "tokens": tokens}


async def llm_stream(
    messages: list[dict],
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.1,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    """Streaming LLM call. Yields content chunks."""
    model_str = _get_model_string(provider, model)
    logger.info("LLM stream", model=model_str)

    response = await litellm.acompletion(
        model=model_str,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,
    )

    async for chunk in response:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content
