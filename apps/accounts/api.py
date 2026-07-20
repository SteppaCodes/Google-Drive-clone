import hashlib
import secrets
from datetime import timedelta
from uuid import UUID

from django.contrib.auth import authenticate
from django.utils import timezone
from ninja import Router
from ninja.errors import HttpError

from .auth import lore_auth

from .models import AgentToken, Invite, User, Principal
from .schemas import (
    AgentTokenCreateResponseSchema,
    AgentTokenCreateSchema,
    AgentTokenResponseSchema,
    InviteClaimSchema,
    InviteCreateSchema,
    InviteListSchema,
    InvitePreviewSchema,
    InviteResponseSchema,
    LoginSchema,
    RegisterSchema,
)

router = Router(tags=["Authentication"])

# ---------------------------------------------------------------------------
# Invite-only default duration (days)
# ---------------------------------------------------------------------------
INVITE_EXPIRY_DAYS = 7


# ---------------------------------------------------------------------------
# Workspace Initialization (first-user-is-admin)
# ---------------------------------------------------------------------------


@router.post("/register", response={201: dict, 403: dict})
def register(request, data: RegisterSchema):
    """
    Register the workspace admin.

    This endpoint only works once — when no users exist in the database.
    The first user to register becomes the workspace admin.  All subsequent
    human users must be provisioned through invites issued by the admin.
    """
    if User.objects.exists():
        return 403, {
            "message": (
                "This workspace is invite-only. "
                "Contact your workspace admin for an invite link."
            ),
        }

    if User.objects.filter(email=data.email).exists():
        return 403, {"message": "User with this email already exists"}

    user = User.objects.create_user(
        email=data.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
        is_workspace_admin=True,
    )
    # Create Principal for user
    Principal.objects.create(
        kind=Principal.Kind.USER,
        display_name=user.full_name,
        user=user,
    )
    tokens = user.tokens()
    return 201, {
        "message": (
            f"Workspace initialized. Welcome, {user.first_name}. "
            f"You are the workspace admin."
        ),
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
        },
    }


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Invite Management (workspace admin only)
# ---------------------------------------------------------------------------


def _require_admin(request):
    """Raise 403 if the requesting user is not a workspace admin."""
    if not getattr(request.user, "is_workspace_admin", False):
        raise HttpError(403, "Only the workspace admin can manage invites.")


@router.post(
    "/invites",
    auth=lore_auth,
    response={201: InviteResponseSchema, 400: dict, 403: dict},
)
def create_invite(request, data: InviteCreateSchema):
    """Issue an invite link for a new collaborator (admin only)."""
    _require_admin(request)

    if User.objects.filter(email=data.email).exists():
        return 400, {"message": "A user with this email already exists."}

    # Delete any prior unclaimed invite for the same email (re-invite)
    Invite.objects.filter(email=data.email, claimed=False).delete()

    token = Invite.generate_token()
    invite = Invite.objects.create(
        email=data.email,
        name=data.name,
        token=token,
        created_by=request.user,
        expires_at=timezone.now() + timedelta(days=INVITE_EXPIRY_DAYS),
    )
    return 201, invite


@router.get(
    "/invites",
    auth=lore_auth,
    response=list[InviteListSchema],
)
def list_invites(request):
    """List all invites (admin only)."""
    _require_admin(request)
    invites = Invite.objects.all().order_by("-created_at")
    result = []
    for inv in invites:
        result.append(
            InviteListSchema(
                id=inv.id,
                email=inv.email,
                name=inv.name,
                token_prefix=inv.token[:8],
                expires_at=inv.expires_at,
                claimed=inv.claimed,
                claimed_at=inv.claimed_at,
                created_at=inv.created_at,
            )
        )
    return result


@router.delete(
    "/invites/{invite_id}",
    auth=lore_auth,
    response={204: None, 404: dict},
)
def revoke_invite(request, invite_id: UUID):
    """Revoke an unclaimed invite (admin only)."""
    _require_admin(request)
    try:
        invite = Invite.objects.get(id=invite_id, claimed=False)
        invite.delete()
        return 204, None
    except Invite.DoesNotExist:
        return 404, {"message": "Invite not found or already claimed."}


# ---------------------------------------------------------------------------
# Invite Validation & Claim (unauthenticated)
# ---------------------------------------------------------------------------


@router.get(
    "/invites/{token}/preview",
    response={200: InvitePreviewSchema, 400: dict, 404: dict},
)
def preview_invite(request, token: str):
    """
    Validate an invite token and return a public preview.

    Used by the frontend to pre-fill the claim form before the user
    submits their name and password.
    """
    try:
        invite = Invite.objects.get(token=token)
    except Invite.DoesNotExist:
        return 404, {"message": "Invite not found."}

    if invite.claimed:
        return 400, {"message": "This invite has already been used."}

    if invite.expires_at < timezone.now():
        return 400, {"message": "This invite has expired."}

    return 200, InvitePreviewSchema(
        email=invite.email,
        name=invite.name,
        expires_at=invite.expires_at,
    )


@router.post(
    "/invites/{token}/claim",
    response={201: dict, 400: dict, 404: dict},
)
def claim_invite(request, token: str, data: InviteClaimSchema):
    """
    Claim an invite and create a new user account.

    The invitee provides their name and password.  On success, the
    invite is marked as claimed and a JWT token pair is returned.
    """
    try:
        invite = Invite.objects.get(token=token)
    except Invite.DoesNotExist:
        return 404, {"message": "Invite not found."}

    if invite.claimed:
        return 400, {"message": "This invite has already been used."}

    if invite.expires_at < timezone.now():
        return 400, {"message": "This invite has expired."}

    if User.objects.filter(email=invite.email).exists():
        return 400, {"message": "A user with this email already exists."}

    user = User.objects.create_user(
        email=invite.email,
        first_name=data.first_name,
        last_name=data.last_name,
        password=data.password,
    )

    # Create Principal for user
    Principal.objects.create(
        kind=Principal.Kind.USER,
        display_name=user.full_name,
        user=user,
    )

    invite.claimed = True
    invite.claimed_at = timezone.now()
    invite.save(update_fields=["claimed", "claimed_at"])

    tokens = user.tokens()
    return 201, {
        "message": f"Welcome to the workspace, {user.first_name}.",
        "data": {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "access_token": tokens["access"],
            "refresh_token": tokens["refresh"],
        },
    }


# ---------------------------------------------------------------------------
# Scoped Agent Token Endpoints (unchanged)
# ---------------------------------------------------------------------------


@router.post("/tokens", auth=lore_auth, response={201: AgentTokenCreateResponseSchema})
def create_agent_token(request, data: AgentTokenCreateSchema):
    raw_token = "lore_agent_" + secrets.token_hex(24)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    token_prefix = raw_token[:20]

    expires_at = None
    if data.expires_in_days:
        expires_at = timezone.now() + timedelta(days=data.expires_in_days)

    # Create Principal for agent token
    principal = Principal.objects.create(
        kind=Principal.Kind.AGENT_TOKEN,
        display_name=f"Agent: {data.description[:30]}",
    )

    agent_token = AgentToken.objects.create(
        user=request.user,
        principal=principal,
        token_hash=token_hash,
        token_prefix=token_prefix,
        description=data.description,
        scope=data.scope,
        restricted_collection_id=data.restricted_collection_id,
        expires_at=expires_at,
    )

    # Build a response object that includes the raw token (shown once only).
    # AgentTokenCreateResponseSchema expects a `token` field — we attach it
    # transiently since the model no longer stores the raw value.
    agent_token.token = raw_token  # Attribute set for serialization only
    return 201, agent_token


@router.get("/tokens", auth=lore_auth, response=list[AgentTokenResponseSchema])
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
