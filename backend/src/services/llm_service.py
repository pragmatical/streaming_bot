from __future__ import annotations

from typing import AsyncGenerator, Iterable, List

from openai import AsyncAzureOpenAI

from ..config.settings import settings
from ..schemas.chat import ChatOptions, Message
from .kernel_service import KernelService


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
    """Stream chat via Semantic Kernel; fallback to direct OpenAI if needed."""

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
            gen_cfg = {}
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
    except Exception:
        # Fall back to direct OpenAI below
        pass

    # Fallback: direct OpenAI SDK
    if not settings.azure_openai_api_key or not settings.azure_openai_endpoint:
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
