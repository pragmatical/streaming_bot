from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


Role = Literal["system", "user", "assistant"]


class Message(BaseModel):
    role: Role
    content: str


class ChatOptions(BaseModel):
    max_tokens: Optional[int] = Field(default=512, ge=1)
    temperature: Optional[float] = Field(default=0.2, ge=0, le=2)
    top_p: Optional[float] = Field(default=1.0, ge=0, le=1)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    history: List[Message] = Field(default_factory=list)
    options: ChatOptions = Field(default_factory=ChatOptions)
