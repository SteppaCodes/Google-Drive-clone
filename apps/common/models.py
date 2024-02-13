from django.db import models
import uuid
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils.translation import gettext_lazy as _

from apps.accounts.models import User


class BaseModel(models.Model):
    """Base model for all other models."""

    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class StarredItem(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4)
    file_or_folder = GenericForeignKey("content_type", "object_id")

    def __str__(self):
        return self.file_or_folder


class SharedItem(BaseModel):
    users = models.ManyToManyField(User, related_name="collab_items",verbose_name=_("all users that have a access to the file or folder"))
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField(default=uuid.uuid4)
    owner = models.ForeignKey(
        User, related_name="shared_items", on_delete=models.CASCADE
    )
    file_or_folder = GenericForeignKey("content_type", "object_id")


