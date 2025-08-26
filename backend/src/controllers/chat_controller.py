from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from ..schemas.chat import ChatRequest
from ..services import llm_service


router = APIRouter()


@router.post("/api/chat/stream", response_class=StreamingResponse)
async def chat_stream(payload: ChatRequest) -> StreamingResponse:
    generator = llm_service.stream_chat(
        message=payload.message,
        history=payload.history,
        options=payload.options,
    )
    return StreamingResponse(generator, media_type="text/plain; charset=utf-8")
