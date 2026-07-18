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
    token_hash = models.CharField(max_length=64, unique=True, db_index=True, default="")
    token_prefix = models.CharField(max_length=20, default="")
    description = models.TextField(blank=True)
    scope = models.CharField(
        max_length=20,
        default="read_write",
        choices=[("read_only", "Read Only"), ("read_write", "Read Write")],
    )
    restricted_folder = models.ForeignKey(
        "folders.Folder", on_delete=models.SET_NULL, null=True, blank=True,
    )
    expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.email} - {self.description[:30]} ({self.scope})"
