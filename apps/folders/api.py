from uuid import UUID

from django.shortcuts import get_object_or_404
from ninja import Router

from apps.common.security import scope_folders_queryset
from lore.api import lore_auth

from .models import Folder
from .schemas import FolderCreateSchema, FolderResponseSchema, FolderUpdateSchema

router = Router(tags=["Folders"])


# --- Folder List & Create ---

@router.get("/", response=list[FolderResponseSchema])
def list_folders(request, parent_folder_id: UUID | None = None, query: str = ""):
    """
    List all root-level folders for the authenticated user/agent.

    Pass ``parent_folder_id`` to list the subfolders of a specific folder.
    Pass ``query`` to filter by name (case-insensitive).
    """
    qs = Folder.objects.select_related("owner")
    qs = scope_folders_queryset(qs, request)

    if parent_folder_id is not None:
        qs = qs.filter(folder_id=parent_folder_id)
    else:
        qs = qs.filter(folder__isnull=True)  # Root-level folders only

    if query:
        qs = qs.filter(name__icontains=query)

    return [FolderResponseSchema.from_model(f) for f in qs]


@router.post("/", response={201: FolderResponseSchema, 400: dict, 403: dict})
def create_folder(request, data: FolderCreateSchema):
    """
    Create a new folder.

    Optionally nest it inside another folder by supplying ``parent_folder_id``.
    Agents with a restricted_folder scope may only create subfolders within
    their permitted boundary.
    """
    agent_token = getattr(request, "agent_token", None)

    if data.parent_folder_id:
        # Validate parent exists and is in scope
        qs = Folder.objects.all()
        qs = scope_folders_queryset(qs, request)
        parent = get_object_or_404(qs, id=data.parent_folder_id)
    else:
        # Root-level creation — blocked for scope-restricted agents
        if agent_token and agent_token.restricted_folder:
            return 403, {
                "message": "Scope-restricted agents cannot create root-level folders."
            }
        parent = None

    folder = Folder.objects.create(
        name=data.name,
        owner=request.user,
        folder=parent,
    )
    return 201, FolderResponseSchema.from_model(folder)


# --- Folder Detail ---

@router.get("/{folder_id}", response={200: FolderResponseSchema, 404: dict})
def get_folder(request, folder_id: UUID):
    """Retrieve a single folder's metadata."""
    qs = Folder.objects.select_related("owner")
    qs = scope_folders_queryset(qs, request)
    folder = get_object_or_404(qs, id=folder_id)
    return 200, FolderResponseSchema.from_model(folder)


@router.get("/{folder_id}/contents", response={200: dict, 404: dict})
def get_folder_contents(request, folder_id: UUID, query: str = ""):
    """
    Retrieve the contents of a folder: its metadata, subfolders, and files.

    Files are returned as a list of IDs — fetch their full details from
    ``GET /api/files/?folder_id=<folder_id>`` which applies the same scoping.
    """
    qs = Folder.objects.select_related("owner")
    qs = scope_folders_queryset(qs, request)
    folder = get_object_or_404(qs, id=folder_id)

    # Subfolders
    subfolders_qs = Folder.objects.select_related("owner").filter(folder=folder)
    subfolders_qs = scope_folders_queryset(subfolders_qs, request)
    if query:
        subfolders_qs = subfolders_qs.filter(name__icontains=query)

    # Files in this folder (scoped via folder ownership, full data via /files endpoint)
    from apps.common.security import scope_files_queryset
    from apps.files.models import File as FileModel
    files_qs = FileModel.objects.filter(folder=folder)
    files_qs = scope_files_queryset(files_qs, request)
    if query:
        files_qs = files_qs.filter(name__icontains=query)

    return 200, {
        "folder": FolderResponseSchema.from_model(folder),
        "subfolders": [FolderResponseSchema.from_model(f) for f in subfolders_qs],
        "file_count": files_qs.count(),
        "file_ids": [str(f.id) for f in files_qs],
    }


# --- Folder Update & Delete ---

@router.patch("/{folder_id}", response={200: FolderResponseSchema, 403: dict, 404: dict})
def update_folder(request, folder_id: UUID, data: FolderUpdateSchema):
    """Rename a folder."""
    qs = Folder.objects.select_related("owner")
    qs = scope_folders_queryset(qs, request)
    folder = get_object_or_404(qs, id=folder_id)

    folder.name = data.name
    folder.save(update_fields=["name", "updated_at"])
    return 200, FolderResponseSchema.from_model(folder)


@router.delete("/{folder_id}", response={204: None, 403: dict, 404: dict})
def delete_folder(request, folder_id: UUID):
    """
    Delete a folder and all its contents recursively.

    Agents with read_only scope will be rejected by LoreAuth before
    this function is reached.
    """
    qs = Folder.objects.select_related("owner")
    qs = scope_folders_queryset(qs, request)
    folder = get_object_or_404(qs, id=folder_id)

    folder.delete()
    return 204, None
