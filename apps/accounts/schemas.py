from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class RegisterSchema(BaseModel):
    first_name: str = Field(..., max_length=50)
    last_name: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)
    terms_agreement: bool


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    refresh: str
    access: str


class AgentTokenCreateSchema(BaseModel):
    description: str = Field(..., max_length=500)
    scope: str = Field("read_write", max_length=20)
    restricted_folder_id: UUID | None = None
    expires_in_days: int | None = Field(90, ge=1, le=365)


class AgentTokenCreateResponseSchema(BaseModel):
    """Returned exactly once at creation time — contains the raw token."""

    id: UUID
    token: str
    description: str
    scope: str
    restricted_folder_id: UUID | None = None
    expires_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class AgentTokenResponseSchema(BaseModel):
    """Returned on list/detail — raw token is NOT exposed, only the prefix."""

    id: UUID
    token_prefix: str
    description: str
    scope: str
    restricted_folder_id: UUID | None = None
    expires_at: datetime | None = None
    created_at: datetime

    class Config:
        from_attributes = True
