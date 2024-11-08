from rest_framework.permissions import BasePermission


class ISOwner(BasePermission):
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        user = request.user

        if obj.owner == user:
            return True
        else:
            return False