from django.contrib.contenttypes.models import ContentType
from rest_framework.permissions import SAFE_METHODS, BasePermission

from apps.common.models import SharedItem


class IsOwner(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return request.user and obj.owner == request.user


class IsOwnerOrShared(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user and obj.owner == request.user:
            return True

        # Non-owners can only read if the item has been shared with them
        if request.method in SAFE_METHODS:
            content_type = ContentType.objects.get_for_model(obj)
            return SharedItem.objects.filter(
                content_type=content_type,
                object_id=obj.id,
                users=request.user
            ).exists()

        return False
