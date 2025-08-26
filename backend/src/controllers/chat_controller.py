from __future__ import annotations

import time
import uuid
from typing import AsyncGenerator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas.chat import ChatRequest
from ..services import llm_service
from ..utils.errors import ConfigError, UpstreamError
from ..utils.logging import get_logger


router = APIRouter()


@router.post("/api/chat/stream", response_class=StreamingResponse)
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    logger = get_logger("controllers.chat")
    request_id = str(uuid.uuid4())
    t0 = time.perf_counter()

    async def _wrapped() -> AsyncGenerator[str, None]:
        tokens = 0
        try:
            async for chunk in llm_service.stream_chat(
                message=payload.message,
                history=payload.history,
                options=payload.options,
            ):
                tokens += len(chunk)
                yield chunk
            duration = (time.perf_counter() - t0) * 1000
            logger.info(
                "chat stream complete",
                extra={
                    "request_id": request_id,
                    "duration_ms": round(duration, 2),
                    "tokens_streamed": tokens,
                },
            )
        except ConfigError as e:
            duration = (time.perf_counter() - t0) * 1000
            logger.error(
                "configuration error while streaming",
                exc_info=True,
                extra={"request_id": request_id, "duration_ms": round(duration, 2)},
            )
            yield f"[config error] {e}"
        except UpstreamError as e:
            duration = (time.perf_counter() - t0) * 1000
            logger.warning(
                "upstream error while streaming",
                exc_info=True,
                extra={"request_id": request_id, "duration_ms": round(duration, 2)},
            )
            yield f"[upstream error] {e}"
        except Exception as e:  # pragma: no cover
            duration = (time.perf_counter() - t0) * 1000
            logger.exception(
                "unexpected error while streaming",
                extra={"request_id": request_id, "duration_ms": round(duration, 2)},
            )
            yield "[unexpected error] Something went wrong. Please try again."

    headers = {"X-Request-ID": request_id, "Cache-Control": "no-store"}
    return StreamingResponse(_wrapped(), media_type="text/plain; charset=utf-8", headers=headers)
