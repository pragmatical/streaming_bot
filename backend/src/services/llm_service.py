from __future__ import annotations

from typing import AsyncGenerator, List

from openai import AsyncAzureOpenAI

from ..config.settings import settings
from ..schemas.chat import ChatOptions, Message
from .kernel_service import KernelService
from ..utils.errors import ConfigError, UpstreamError
from ..utils.logging import get_logger


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
    """Stream chat via Semantic Kernel; fallback to direct OpenAI if needed.

    Raises:
        ConfigError: When required configuration for Azure OpenAI is missing.
        UpstreamError: When upstream provider fails and we cannot continue streaming.
    """
    logger = get_logger("services.llm")
    kernel_service = KernelService()
    kernel = kernel_service.get_kernel()

    # Try Semantic Kernel first
    try:
        chat_service = kernel.get_service(type="chat-completion")
        if chat_service:
            # Build SK chat history
            # SK Python provides chat_history in services. We'll assemble from our schema.
            # Add an initial system message if desired.
            history_msgs = [] if not history else history

            # Start with history
            # For streaming, use the service's streaming API
            from semantic_kernel.connectors.ai.open_ai import (  # type: ignore
                ChatHistory,
            )

            ch = ChatHistory()
            # Optional system prompt
            from .kernel_service import SYSTEM_PROMPT

            ch.add_system_message(SYSTEM_PROMPT)
            for m in history_msgs:
                if m.role == "user":
                    ch.add_user_message(m.content)
                elif m.role == "assistant":
                    ch.add_assistant_message(m.content)

            ch.add_user_message(message)

            # Options mapping
            gen_cfg = {
                "max_tokens": settings.generation_max_tokens,
                "temperature": settings.generation_temperature,
                "top_p": settings.generation_top_p,
            }
            if options:
                if options.max_tokens is not None:
                    gen_cfg["max_tokens"] = options.max_tokens
                if options.temperature is not None:
                    gen_cfg["temperature"] = options.temperature
                if options.top_p is not None:
                    gen_cfg["top_p"] = options.top_p

            # Stream via SK
            async for delta in chat_service.get_streaming_chat_message_contents_async(
                ch, **gen_cfg
            ):
                content = getattr(delta, "content", None)
                if content:
                    yield content
            return
    except Exception as e:
        # Fall back to direct OpenAI below
        logger.debug("SK streaming failed; falling back to OpenAI", exc_info=True)

    # Fallback: direct OpenAI SDK
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
        raise ConfigError("Missing Azure OpenAI settings (.env)")

    client = AsyncAzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )

    model = settings.azure_openai_deployment or ""
    if not model:
        raise ConfigError("AZURE_OPENAI_DEPLOYMENT is not set")

    params = {
        "model": model,
        "messages": _to_openai_messages(history, message),
        "stream": True,
    }
    # Defaults from settings
    params["max_tokens"] = settings.generation_max_tokens
    params["temperature"] = settings.generation_temperature
    params["top_p"] = settings.generation_top_p
    # Per-request overrides
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
        raise UpstreamError(str(e))
