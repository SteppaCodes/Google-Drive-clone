import secrets
import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _
from rest_framework_simplejwt.tokens import RefreshToken

from .managers import CustomUserManager


class User(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    email = models.EmailField(_('Email Address'), unique=True)
    avatar= models.ImageField(upload_to='avatars/', null=True, blank=True)
    is_agent = models.BooleanField(default=False)
    is_workspace_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    terms_agreement = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects =CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.full_name

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh':str(refresh),
            'access': str(refresh.access_token)
        }


class Principal(models.Model):
    """
    Unified identity for all actors in Lore.

    Every entity that can own, create, modify, or be granted permissions
    to an artifact resolves to a single Principal row.  This eliminates
    polymorphic FKs throughout the schema — ``Artifact.owner``,
    ``ArtifactRelationship.created_by``, ``ArtifactPermission.principal``
    all point here.

    Principals are created directly in the registration, invite-claim,
    and agent-token-create views — not via signals.
    """

    class Kind(models.TextChoices):
        USER = "user", "User"
        AGENT_TOKEN = "agent_token", "Agent Token"

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    kind = models.CharField(max_length=20, choices=Kind.choices)
    display_name = models.CharField(max_length=255)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, null=True, blank=True,
        related_name="principal",
    )
    # agent_token FK is set below AgentToken definition to avoid
    # forward-reference issues within the same file.
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.display_name} ({self.kind})"


class AgentToken(models.Model):
    """
    Scoped API key for AI agent access.

    The raw token is returned exactly once at creation time. Only its
    SHA-256 hash is persisted; the hash is used for all subsequent
    lookups.  ``token_prefix`` stores the first 14 characters of the
    raw token for display identification (e.g., "lore_agent_ab12").
    """

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="agent_tokens")
    principal = models.OneToOneField(
        Principal, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="agent_token",
    )
    token_hash = models.CharField(max_length=64, unique=True, db_index=True, default="")
    token_prefix = models.CharField(max_length=20, default="")
    description = models.TextField(blank=True)
    scope = models.CharField(
        max_length=20,
        default="read_write",
        choices=[("read_only", "Read Only"), ("read_write", "Read Write")],
    )
    restricted_collection = models.ForeignKey(
        "collections.Collection", on_delete=models.SET_NULL, null=True, blank=True,
    )
    can_auto_approve = models.BooleanField(
        default=False,
        help_text=_("Allows pre-reviewed pipeline agents to create artifacts directly in approved or published states."),
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.description[:30]} ({self.scope})"


class Invite(models.Model):
    """
    Single-use invite token for provisioning human collaborators.

    The workspace admin generates an invite for a specific email.
    The invitee clicks the link, claims their account (name + password),
    and the invite is marked as consumed.  Unclaimed invites expire
    after the configured duration (default: 7 days).
    """

    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150, blank=True)  # optional display name hint
    token = models.CharField(max_length=64, unique=True, db_index=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_invites",
    )
    claimed = models.BooleanField(default=False)
    claimed_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        status = "claimed" if self.claimed else "pending"
        return f"Invite({self.email}, {status})"

    @staticmethod
    def generate_token():
        """Generate a cryptographically secure URL-safe invite token."""
        return secrets.token_urlsafe(32)

