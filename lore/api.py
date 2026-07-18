import hashlib

from django.utils import timezone
from ninja import NinjaAPI
from ninja.errors import HttpError
from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from apps.accounts.models import AgentToken, User

api = NinjaAPI(
    title="Lore API",
    description="Collaborative file vault, skill registry, and artifact workspace for AI agents and humans.",
    version="0.1.0",
)


class LoreAuth(HttpBearer):
    """
    Dual-path bearer authentication.

    Tokens prefixed with ``lore_agent_`` are looked up by SHA-256 hash
    against the AgentToken table.  All other tokens are decoded as
    SimpleJWT AccessTokens for human users.
    """

    def authenticate(self, request, token):
        # --- Agent token path (prefix-based) ---
        if token.startswith("lore_agent_"):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            try:
                agent_token = AgentToken.objects.select_related("user").get(
                    token_hash=token_hash,
                )
            except AgentToken.DoesNotExist:
                return None

            # Reject expired tokens
            if agent_token.expires_at and agent_token.expires_at < timezone.now():
                return None

            # Scope enforcement: read_only tokens cannot perform mutations
            if (
                agent_token.scope == "read_only"
                and request.method not in ("GET", "HEAD", "OPTIONS")
            ):
                raise HttpError(
                    403, "Token scope 'read_only' does not permit this operation.",
                )

            request.agent_token = agent_token
            request.user = agent_token.user
            return agent_token.user

        # --- Human JWT path ---
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get("user_id")
            if user_id:
                user = User.objects.get(id=user_id)
                request.agent_token = None
                request.user = user
                return user
        except (TokenError, User.DoesNotExist):
            pass

        return None




# Global auth instance reused by routers
lore_auth = LoreAuth()

from apps.accounts.api import router as accounts_router  # noqa: E402
from apps.files.api import router as files_router  # noqa: E402
from apps.folders.api import router as folders_router  # noqa: E402

api.add_router("/auth", accounts_router)
api.add_router("/files", files_router, auth=lore_auth)
api.add_router("/folders", folders_router, auth=lore_auth)


@api.get("/hello", auth=lore_auth)
def hello(request):
    return {"message": "Welcome to Lore API"}


