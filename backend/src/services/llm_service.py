from __future__ import annotations

from typing import AsyncGenerator, Iterable, List

from ..schemas.chat import ChatOptions, Message


async def stream_chat(
    message: str,
    history: List[Message] | None = None,
    options: ChatOptions | None = None,
) -> AsyncGenerator[str, None]:
    """Stub streaming generator.

    Replace with Azure OpenAI streaming implementation. For now, yields
    a simple simulated response in chunks to unblock wiring.
    """

    text = f"Echo: {message}"
    for chunk in _chunk(text, size=8):
        yield chunk


def _chunk(s: str, size: int) -> Iterable[str]:
    for i in range(0, len(s), size):
        yield s[i : i + size]
