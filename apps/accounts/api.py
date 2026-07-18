import hashlib
import secrets
from datetime import timedelta
from typing import List
from uuid import UUID

from django.contrib.auth import authenticate
from django.utils import timezone
from ninja import Router

from .models import User, AgentToken
from .schemas import (
    RegisterSchema,
    LoginSchema,
    AgentTokenCreateSchema,
    AgentTokenCreateResponseSchema,
    AgentTokenResponseSchema,
)
from lore.api import lore_auth

router = Router(tags=["Authentication"])


@router.post("/register", response={201: dict, 400: dict})
def register(request, data: RegisterSchema):
    if User.objects.filter(email=data.email).exists():
        return 400, {"message": "User with this email already exists"}

    user = User.objects.create_user(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
        terms_agreement=data.terms_agreement,
    )
    return 201, {
        "status": "success",
        "message": f"Hi {user.first_name}, thank you for signing up.",
        "data": {
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
    }


@router.post("/login", response={200: dict, 401: dict})
def login(request, data: LoginSchema):
    user = authenticate(email=data.email, password=data.password)
    if not user:
        return 401, {"message": "Invalid email or password"}

    tokens = user.tokens()
    return 200, {
        "status": "success",
        "message": "Login successful",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
        },
    }


# --- Scoped Agent Token Endpoints ---


@router.post("/tokens", auth=lore_auth, response={201: AgentTokenCreateResponseSchema})
def create_agent_token(request, data: AgentTokenCreateSchema):
    raw_token = "lore_agent_" + secrets.token_hex(24)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_prefix = raw_token[:20]

    expires_at = None
    if data.expires_in_days:
        expires_at = timezone.now() + timedelta(days=data.expires_in_days)

    agent_token = AgentToken.objects.create(
        user=request.user,
        token_hash=token_hash,
        token_prefix=token_prefix,
        description=data.description,
        scope=data.scope,
        restricted_folder_id=data.restricted_folder_id,
        expires_at=expires_at,
    )

    # Build a response object that includes the raw token (shown once only).
    # AgentTokenCreateResponseSchema expects a `token` field — we attach it
    # transiently since the model no longer stores the raw value.
    agent_token.token = raw_token  # noqa: attribute set for serialization only
    return 201, agent_token


@router.get("/tokens", auth=lore_auth, response=List[AgentTokenResponseSchema])
def list_agent_tokens(request):
    return AgentToken.objects.filter(user=request.user)


@router.delete("/tokens/{token_id}", auth=lore_auth, response={204: None, 404: dict})
def delete_agent_token(request, token_id: UUID):
    try:
        agent_token = AgentToken.objects.get(id=token_id, user=request.user)
        agent_token.delete()
        return 204, None
    except AgentToken.DoesNotExist:
        return 404, {"message": "Agent token not found"}
