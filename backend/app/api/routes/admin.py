from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.database import get_db
from app.core.security import require_role
from app.models.user import User, Organization
from app.models.document import Document
from app.models.conversation import Conversation, Message
from app.schemas.common import APIResponse
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin"])


class AnalyticsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    total_conversations: int
    total_messages: int
    messages_today: int
    avg_latency_ms: float | None
    thumbs_up_count: int
    thumbs_down_count: int
    tokens_used_today: int
    tokens_used_month: int
    daily_token_budget: int
    monthly_token_budget: int
    top_unanswered: list[str]


class OrgSettingsUpdate(BaseModel):
    default_llm_provider: str | None = None
    default_llm_model: str | None = None
    daily_token_budget: int | None = None
    monthly_token_budget: int | None = None


class UserRoleUpdate(BaseModel):
    role: str  # admin, member, viewer


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Get organization-level analytics."""
    org = await db.get(Organization, user.org_id)
    today = datetime.utcnow().date()

    total_docs = await db.scalar(
        select(func.count()).select_from(Document).where(Document.org_id == user.org_id)
    ) or 0

    total_chunks = await db.scalar(
        select(func.sum(Document.chunk_count)).where(Document.org_id == user.org_id)
    ) or 0

    total_convos = await db.scalar(
        select(func.count()).select_from(Conversation).where(Conversation.org_id == user.org_id)
    ) or 0

    total_msgs = await db.scalar(
        select(func.count()).select_from(Message)
        .join(Conversation)
        .where(Conversation.org_id == user.org_id)
    ) or 0

    msgs_today = await db.scalar(
        select(func.count()).select_from(Message)
        .join(Conversation)
        .where(
            Conversation.org_id == user.org_id,
            func.date(Message.created_at) == today,
        )
    ) or 0

    avg_latency = await db.scalar(
        select(func.avg(Message.latency_ms))
        .join(Conversation)
        .where(Conversation.org_id == user.org_id, Message.latency_ms.isnot(None))
    )

    thumbs_up = await db.scalar(
        select(func.count()).select_from(Message)
        .join(Conversation)
        .where(Conversation.org_id == user.org_id, Message.feedback == "thumbs_up")
    ) or 0

    thumbs_down = await db.scalar(
        select(func.count()).select_from(Message)
        .join(Conversation)
        .where(Conversation.org_id == user.org_id, Message.feedback == "thumbs_down")
    ) or 0

    # Find messages where assistant said "I don't have enough information"
    low_conf_result = await db.execute(
        select(Message.content)
        .join(Conversation)
        .where(
            Conversation.org_id == user.org_id,
            Message.role == "assistant",
            Message.confidence == "low",
        )
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    unanswered_msgs = low_conf_result.scalars().all()

    return AnalyticsResponse(
        total_documents=total_docs,
        total_chunks=total_chunks,
        total_conversations=total_convos,
        total_messages=total_msgs,
        messages_today=msgs_today,
        avg_latency_ms=round(avg_latency, 1) if avg_latency else None,
        thumbs_up_count=thumbs_up,
        thumbs_down_count=thumbs_down,
        tokens_used_today=org.tokens_used_today if org else 0,
        tokens_used_month=org.tokens_used_month if org else 0,
        daily_token_budget=org.daily_token_budget if org else 0,
        monthly_token_budget=org.monthly_token_budget if org else 0,
        top_unanswered=unanswered_msgs[:5],
    )


@router.put("/settings", response_model=APIResponse)
async def update_org_settings(
    body: OrgSettingsUpdate,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update organization settings (LLM provider, budgets, etc.)."""
    org = await db.get(Organization, user.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    if body.default_llm_provider is not None:
        if body.default_llm_provider not in ("openai", "anthropic", "google"):
            raise HTTPException(status_code=400, detail="Invalid LLM provider")
        org.default_llm_provider = body.default_llm_provider

    if body.default_llm_model is not None:
        org.default_llm_model = body.default_llm_model

    if body.daily_token_budget is not None:
        org.daily_token_budget = body.daily_token_budget

    if body.monthly_token_budget is not None:
        org.monthly_token_budget = body.monthly_token_budget

    return APIResponse(message="Settings updated successfully")


@router.get("/users", response_model=list[dict])
async def list_users(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """List all users in the organization."""
    result = await db.execute(
        select(User).where(User.org_id == user.org_id).order_by(User.created_at)
    )
    users = result.scalars().all()
    return [
        {
            "id": str(u.id),
            "email": u.email,
            "full_name": u.full_name,
            "role": u.role,
            "is_active": u.is_active,
            "created_at": u.created_at.isoformat(),
        }
        for u in users
    ]


@router.put("/users/{user_id}/role", response_model=APIResponse)
async def update_user_role(
    user_id: str,
    body: UserRoleUpdate,
    admin: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Update a user's role."""
    if body.role not in ("admin", "member", "viewer"):
        raise HTTPException(status_code=400, detail="Invalid role")

    result = await db.execute(
        select(User).where(User.id == user_id, User.org_id == admin.org_id)
    )
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")

    target.role = body.role
    return APIResponse(message=f"User role updated to '{body.role}'")


@router.post("/reset-token-usage", response_model=APIResponse)
async def reset_daily_tokens(
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Reset daily token usage counter."""
    org = await db.get(Organization, user.org_id)
    if org:
        org.tokens_used_today = 0
    return APIResponse(message="Daily token usage reset")
