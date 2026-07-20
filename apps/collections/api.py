from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from apps.common.security import scope_collections_queryset
from apps.accounts.auth import lore_auth

from .models import Collection
from .schemas import CollectionCreateSchema, CollectionResponseSchema, CollectionUpdateSchema

router = Router(tags=["Collections"])


# --- Collection List & Create ---

@router.get("/", response=list[CollectionResponseSchema])
def list_collections(request, parent_id: UUID | None = None, query: str = ""):
    """
    List all root-level collections for the authenticated user/agent.

    Pass ``parent_id`` to list the children of a specific collection.
    Pass ``query`` to filter by name (case-insensitive).
    """
    qs = Collection.objects.select_related("owner")
    qs = scope_collections_queryset(qs, request)

    if parent_id is not None:
        qs = qs.filter(parent_id=parent_id)
    else:
        qs = qs.filter(parent__isnull=True)  # Root-level collections only

    if query:
        qs = qs.filter(name__icontains=query)

    return [CollectionResponseSchema.from_model(c) for c in qs]


@router.post("/", response={201: CollectionResponseSchema, 400: dict, 403: dict})
def create_collection(request, data: CollectionCreateSchema):
    """
    Create a new collection.

    Optionally nest it inside another collection by supplying ``parent_id``.
    Agents with a restricted_collection scope may only create children within
    their permitted boundary.
    """
    agent_token = getattr(request, "agent_token", None)
    principal = getattr(request.user, "principal", None)

    if not principal:
        return 400, {"message": "No principal found for user. Please re-register."}

    if data.parent_id:
        # Validate parent exists and is in scope
        qs = Collection.objects.all()
        qs = scope_collections_queryset(qs, request)
        parent = get_object_or_404(qs, id=data.parent_id)
    else:
        # Root-level creation — blocked for scope-restricted agents
        if agent_token and agent_token.restricted_collection:
            return 403, {
                "message": "Scope-restricted agents cannot create root-level collections."
            }
        parent = None

    collection = Collection.objects.create(
        name=data.name,
        owner=principal,
        parent=parent,
    )
    return 201, CollectionResponseSchema.from_model(collection)


# --- Collection Detail ---

@router.get("/{collection_id}", response={200: CollectionResponseSchema, 404: dict})
def get_collection(request, collection_id: UUID):
    """Retrieve a single collection's metadata."""
    qs = Collection.objects.select_related("owner")
    qs = scope_collections_queryset(qs, request)
    collection = get_object_or_404(qs, id=collection_id)
    return 200, CollectionResponseSchema.from_model(collection)


@router.get("/{collection_id}/contents", response={200: dict, 404: dict})
def get_collection_contents(request, collection_id: UUID, query: str = ""):
    """
    Retrieve the contents of a collection: its metadata, child collections,
    and artifact IDs.
    """
    qs = Collection.objects.select_related("owner")
    qs = scope_collections_queryset(qs, request)
    collection = get_object_or_404(qs, id=collection_id)

    # Child collections
    children_qs = Collection.objects.select_related("owner").filter(parent=collection)
    children_qs = scope_collections_queryset(children_qs, request)
    if query:
        children_qs = children_qs.filter(name__icontains=query)

    # Artifacts in this collection
    from apps.artifacts.models import Artifact
    artifacts_qs = Artifact.objects.filter(collection=collection, deleted_at__isnull=True)
    if query:
        artifacts_qs = artifacts_qs.filter(title__icontains=query)

    return 200, {
        "collection": CollectionResponseSchema.from_model(collection),
        "children": [CollectionResponseSchema.from_model(c) for c in children_qs],
        "artifact_count": artifacts_qs.count(),
        "artifact_ids": [str(a.id) for a in artifacts_qs],
    }


# --- Collection Update & Delete ---

@router.patch("/{collection_id}", response={200: CollectionResponseSchema, 403: dict, 404: dict})
def update_collection(request, collection_id: UUID, data: CollectionUpdateSchema):
    """Rename a collection."""
    qs = Collection.objects.select_related("owner")
    qs = scope_collections_queryset(qs, request)
    collection = get_object_or_404(qs, id=collection_id)

    collection.name = data.name
    collection.save(update_fields=["name", "updated_at"])
    return 200, CollectionResponseSchema.from_model(collection)


@router.delete("/{collection_id}", response={204: None, 403: dict, 404: dict})
def delete_collection(request, collection_id: UUID):
    """
    Delete a collection and all its contents recursively.

    Agents with read_only scope will be rejected by LoreAuth before
    this function is reached.
    """
    qs = Collection.objects.select_related("owner")
    qs = scope_collections_queryset(qs, request)
    collection = get_object_or_404(qs, id=collection_id)

    collection.delete()
    return 204, None
