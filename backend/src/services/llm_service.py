from __future__ import annotations

from typing import AsyncGenerator, Iterable, List

from openai import AsyncAzureOpenAI

from ..config.settings import settings
from ..schemas.chat import ChatOptions, Message


def _to_openai_messages(history: List[Message] | None, user_message: str):
    msgs: list[dict] = []
    if history:
        for m in history:
            msgs.append({"role": m.role, "content": m.content})
    msgs.append({"role": "user", "content": user_message})
    return msgs


async def stream_chat(
    message: str,
    history: List[Message] | None = None,
    options: ChatOptions | None = None,
) -> AsyncGenerator[str, None]:
    """Stream Azure OpenAI chat completion tokens to the caller.

    Uses the OpenAI Python SDK configured for Azure.
    """

    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        # Fail fast with a helpful message for local dev
        yield "Configuration error: Missing Azure OpenAI settings (.env)."  # type: ignore[misc]
        return

    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )

    model = settings.azure_openai_deployment or ""
    if not model:
        yield "Configuration error: AZURE_OPENAI_DEPLOYMENT is not set."  # type: ignore[misc]
        return

    params = {
        "model": model,
        "messages": _to_openai_messages(history, message),
        "stream": True,
    }
    if options:
        if options.max_tokens is not None:
            params["max_tokens"] = options.max_tokens
        if options.temperature is not None:
            params["temperature"] = options.temperature
        if options.top_p is not None:
            params["top_p"] = options.top_p

    try:
        stream = await client.chat.completions.create(**params)  # type: ignore[arg-type]
        async for event in stream:  # type: ignore[assignment]
            for choice in getattr(event, "choices", []) or []:
                delta = getattr(choice, "delta", None)
                if delta and getattr(delta, "content", None):
                    yield delta.content
    except Exception as e:  # pragma: no cover
        yield f"[stream error] {e}"  # type: ignore[misc]
