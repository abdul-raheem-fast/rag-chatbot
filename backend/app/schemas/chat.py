from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

__all__ = [
    "ChatRequest", "ChatResponse", "CitationItem", "MessageResponse",
    "ConversationResponse", "FeedbackRequest",
]


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: UUID | None = None  # None = new conversation


class CitationItem(BaseModel):
    index: int
    doc_id: str
    doc_name: str
    page_number: int | None = None
    snippet: str
    source_url: str | None = None
    score: float


class ChatResponse(BaseModel):
    conversation_id: UUID
    message_id: UUID
    content: str
    citations: list[CitationItem]
    confidence: str  # high, medium, low
    tokens_used: int
    latency_ms: int


class MessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    citations: list[CitationItem] | None = None
    confidence: str | None = None
    feedback: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationResponse(BaseModel):
    id: UUID
    title: str | None
    created_at: datetime
    messages: list[MessageResponse] = []

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    message_id: UUID
    feedback: str = Field(pattern="^(thumbs_up|thumbs_down)$")
