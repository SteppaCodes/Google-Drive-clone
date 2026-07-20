from django.db.models import QuerySet

from apps.collections.models import Collection


def get_allowed_collections_for_request(request) -> list:
    """
    Returns a list of Collection objects the request (user or agent) is authorized to access.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return []

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_collection:
        # Agent is restricted to a specific collection and all its descendants recursively
        return agent_token.restricted_collection.get_descendants(include_self=True)

    # Otherwise, return all collections owned by the user's principal
    principal = getattr(user, 'principal', None)
    if principal:
        return list(Collection.objects.filter(owner=principal))
    return []


def scope_collections_queryset(queryset: QuerySet, request) -> QuerySet:
    """
    Applies security scoping to a Collection queryset.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return queryset.none()

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_collection:
        allowed_collections = get_allowed_collections_for_request(request)
        allowed_ids = [c.id for c in allowed_collections]
        return queryset.filter(id__in=allowed_ids)

    principal = getattr(user, 'principal', None)
    if principal:
        return queryset.filter(owner=principal)
    return queryset.none()


def scope_artifacts_queryset(queryset: QuerySet, request) -> QuerySet:
    """
    Applies security scoping to an Artifact queryset.
    Artifacts are scoped through their collection ownership.
    """
    user = request.user
    if not user or not user.is_authenticated:
        return queryset.none()

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_collection:
        allowed_collections = get_allowed_collections_for_request(request)
        allowed_ids = [c.id for c in allowed_collections]
        return queryset.filter(collection_id__in=allowed_ids)

    principal = getattr(user, 'principal', None)
    if principal:
        return queryset.filter(owner=principal)
    return queryset.none()


# --- Backward-compatible aliases for legacy apps.files code ---

def get_allowed_folders_for_request(request) -> list:
    """Alias for get_allowed_collections_for_request."""
    return get_allowed_collections_for_request(request)


def scope_folders_queryset(queryset: QuerySet, request) -> QuerySet:
    """Alias for scope_collections_queryset."""
    return scope_collections_queryset(queryset, request)


def scope_files_queryset(queryset: QuerySet, request) -> QuerySet:
    """
    Applies security scoping to a File queryset (legacy).
    """
    user = request.user
    if not user or not user.is_authenticated:
        return queryset.none()

    agent_token = getattr(request, 'agent_token', None)
    if agent_token and agent_token.restricted_collection:
        allowed_collections = get_allowed_collections_for_request(request)
        allowed_ids = [c.id for c in allowed_collections]
        return queryset.filter(folder_id__in=allowed_ids)

    return queryset.filter(owner=user)

