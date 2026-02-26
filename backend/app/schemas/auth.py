from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

__all__ = [
    "UserCreate", "UserLogin", "UserResponse", "TokenResponse",
    "OrgCreate", "OrgResponse",
]


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    org_name: str | None = None  # if creating a new org


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    org_id: UUID
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class OrgCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class OrgResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    daily_token_budget: int
    monthly_token_budget: int
    tokens_used_today: int
    tokens_used_month: int
    default_llm_provider: str
    default_llm_model: str
    created_at: datetime

    model_config = {"from_attributes": True}
