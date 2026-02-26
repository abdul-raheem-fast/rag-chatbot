import json
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.redis import get_redis
from app.models.user import User, Organization
from app.models.conversation import Conversation, Message
from app.schemas.chat import (
    ChatRequest, ChatResponse, ConversationResponse,
    MessageResponse, FeedbackRequest,
)
from app.schemas.common import APIResponse
from app.rag.engine import rag_chat, rag_chat_stream
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Send a message and get a RAG-powered response with citations."""
    org = await db.get(Organization, user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Check token budget
    if org.tokens_used_today >= org.daily_token_budget:
        raise HTTPException(status_code=429, detail="Daily token budget exceeded")

    response = await rag_chat(
        db=db,
        user_query=body.message,
        org_id=str(user.org_id),
        user_id=str(user.id),
        conversation_id=body.conversation_id,
        org_name=org.name,
        provider=org.default_llm_provider,
        model=org.default_llm_model,
    )

    # Update token usage
    org.tokens_used_today += response.tokens_used
    org.tokens_used_month += response.tokens_used

    return response


@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Streaming chat endpoint using Server-Sent Events."""
    org = await db.get(Organization, user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if org.tokens_used_today >= org.daily_token_budget:
        raise HTTPException(status_code=429, detail="Daily token budget exceeded")

    return StreamingResponse(
        rag_chat_stream(
            user_query=body.message,
            org_id=str(user.org_id),
            org_name=org.name,
            provider=org.default_llm_provider,
            model=org.default_llm_model,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/conversations", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .limit(50)
    )
    convos = result.scalars().all()
    return [ConversationResponse.model_validate(c) for c in convos]


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user.id,
        )
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return ConversationResponse.model_validate(conv)


@router.post("/feedback", response_model=APIResponse)
async def submit_feedback(
    body: FeedbackRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit thumbs up/down feedback on a message."""
    result = await db.execute(select(Message).where(Message.id == body.message_id))
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    msg.feedback = body.feedback
    logger.info("Feedback received", message_id=str(body.message_id), feedback=body.feedback)
    return APIResponse(message=f"Feedback '{body.feedback}' recorded")
