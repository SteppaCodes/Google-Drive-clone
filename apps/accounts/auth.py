import hashlib

from django.utils import timezone
from ninja.errors import HttpError
from ninja.security import HttpBearer
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from .models import AgentToken, User


class LoreAuth(HttpBearer):
    """
    Dual-path bearer authentication.

    Tokens prefixed with ``lore_agent_`` are looked up by SHA-256 hash
    against the AgentToken table.  All other tokens are decoded as
    SimpleJWT AccessTokens for human users.

    Sets ``request.principal`` for unified identity resolution.
    """

    def authenticate(self, request, token):
        # --- Agent token path (prefix-based) ---
        if token.startswith("lore_agent_"):
            token_hash = hashlib.sha256(token.encode()).hexdigest()
            try:
                agent_token = AgentToken.objects.select_related(
                    "user", "principal",
                ).get(token_hash=token_hash)
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
            request.principal = agent_token.principal
            return agent_token.user

        # --- Human JWT path ---
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get("user_id")
            if user_id:
                user = User.objects.select_related("principal").get(id=user_id)
                request.agent_token = None
                request.user = user
                request.principal = getattr(user, "principal", None)
                return user
        except (TokenError, User.DoesNotExist):
            pass

        return None


lore_auth = LoreAuth()
