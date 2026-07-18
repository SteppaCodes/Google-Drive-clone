from django.db.models import QuerySet
from apps.folders.models import Folder
from apps.files.models import File

def get_allowed_folders_for_request(request) -> list:
    """
    Returns a list of Folder objects the request (user or agent) is authorized to access.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return []

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_folder:
        # Agent is restricted to a specific folder and all its descendants recursively
        return agent_token.restricted_folder.get_descendants(include_self=True)
    
    # Otherwise, return all folders owned by the user
    return list(Folder.objects.filter(owner=user))

def scope_folders_queryset(queryset: QuerySet, request) -> QuerySet:
    """
    Applies security scoping to a Folder queryset.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return queryset.none()

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_folder:
        allowed_folders = get_allowed_folders_for_request(request)
        allowed_ids = [f.id for f in allowed_folders]
        return queryset.filter(id__in=allowed_ids)
    
    return queryset.filter(owner=user)

def scope_files_queryset(queryset: QuerySet, request) -> QuerySet:
    """
    Applies security scoping to a File queryset.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return queryset.none()

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_folder:
        allowed_folders = get_allowed_folders_for_request(request)
        allowed_ids = [f.id for f in allowed_folders]
        return queryset.filter(folder_id__in=allowed_ids)
    
    return queryset.filter(owner=user)
