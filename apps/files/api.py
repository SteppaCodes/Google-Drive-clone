import difflib
from typing import List, Optional
from uuid import UUID

from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from ninja import Router, File, UploadedFile
from ninja.errors import HttpError

from apps.accounts.models import User
from apps.common.security import scope_files_queryset, get_allowed_folders_for_request
from .models import File as FileModel, FileVersion, Comment
from .schemas import FileResponseSchema, FileVersionResponseSchema, CommentResponseSchema
from lore.api import lore_auth

router = Router(tags=["Files & Version History"])


def compute_diff(old_content: bytes, new_content: bytes) -> str:
    """Computes a unified text diff if possible, else returns binary placeholder."""
    try:
        old_text = old_content.decode("utf-8")
        new_text = new_content.decode("utf-8")
        old_lines = old_text.splitlines(keepends=True)
        new_lines = new_text.splitlines(keepends=True)
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile="original",
            tofile="updated",
        )
        return "".join(diff)
    except UnicodeDecodeError:
        return "[Binary file modification - no text diff available]"


# --- File Upload & Overwrite ---

@router.post("/upload", response={201: FileResponseSchema, 400: dict, 403: dict})
def upload_file(request, file: UploadedFile = File(...), folder_id: Optional[UUID] = None):
    # Verify agent folder boundary
    allowed_folders = get_allowed_folders_for_request(request)
    allowed_ids = [f.id for f in allowed_folders]
    
    agent_token = getattr(request, "agent_token", None)
    if agent_token and agent_token.restricted_folder:
        if not folder_id or folder_id not in allowed_ids:
            return 403, {"message": "Access denied: Target folder is outside sandboxed scope"}

    # Read new content
    new_content = file.read()
    file.seek(0)

    # Check if a file with the same name already exists in this folder (and owned by this user context)
    existing_file = FileModel.objects.filter(
        owner=request.user,
        name=file.name,
        folder_id=folder_id
    ).first()

    if existing_file:
        # Check locks
        if existing_file.locked_by and existing_file.locked_by != request.user:
            return 403, {"message": f"File is locked by {existing_file.locked_by.email}"}

        # Save historical version
        old_content = existing_file.file.read()
        existing_file.file.seek(0)

        version_number = existing_file.versions.count() + 1
        FileVersion.objects.create(
            file=existing_file,
            version_number=version_number,
            file_instance=ContentFile(old_content, name=f"v{version_number}_{existing_file.name}"),
            diff_content=compute_diff(old_content, new_content),
            created_by=request.user
        )

        # Overwrite content
        existing_file.file.save(file.name, file, save=False)
        existing_file.save()
        return 201, FileResponseSchema.from_model(existing_file)

    # Create new file
    new_file = FileModel.objects.create(
        owner=request.user,
        name=file.name,
        file=file,
        folder_id=folder_id
    )
    return 201, FileResponseSchema.from_model(new_file)


# --- File List & Download ---

@router.get("/", response=List[FileResponseSchema])
def list_files(request, folder_id: Optional[UUID] = None):
    qs = FileModel.objects.select_related("owner", "locked_by")
    qs = scope_files_queryset(qs, request)
    if folder_id:
        qs = qs.filter(folder_id=folder_id)
    return [FileResponseSchema.from_model(f) for f in qs]


@router.get("/{file_id}/download")
def download_file(request, file_id: UUID):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    # Open file context safe
    response = FileResponse(file_obj.file.open("rb"))
    response["Content-Disposition"] = f'attachment; filename="{file_obj.name}"'
    return response


# --- File Locking Mechanics ---

@router.post("/{file_id}/lock", response={200: FileResponseSchema, 400: dict, 403: dict})
def lock_file(request, file_id: UUID):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    if file_obj.locked_by:
        return 400, {"message": f"File is already locked by {file_obj.locked_by.email}"}

    file_obj.locked_by = request.user
    file_obj.save()
    return 200, FileResponseSchema.from_model(file_obj)


@router.post("/{file_id}/unlock", response={200: FileResponseSchema, 400: dict, 403: dict})
def unlock_file(request, file_id: UUID):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    if not file_obj.locked_by:
        return 400, {"message": "File is not locked"}

    # Only lock owner or file owner can unlock
    if file_obj.locked_by != request.user and file_obj.owner != request.user:
        return 403, {"message": "You do not have permission to unlock this file"}

    file_obj.locked_by = None
    file_obj.save()
    return 200, FileResponseSchema.from_model(file_obj)


# --- Version History & Diffs ---

@router.get("/{file_id}/versions", response=List[FileVersionResponseSchema], auth=lore_auth)
def list_file_versions(request, file_id: UUID):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    versions = file_obj.versions.select_related("created_by").order_by("-version_number")
    return [FileVersionResponseSchema.from_model(v) for v in versions]


# --- Comments endpoints ---

@router.get("/{file_id}/comments", response=List[CommentResponseSchema], auth=lore_auth)
def list_comments(request, file_id: UUID):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    comments = file_obj.comments.select_related("owner").order_by("-created_at")
    return [CommentResponseSchema.from_model(c) for c in comments]


@router.post("/{file_id}/comments", response={201: CommentResponseSchema}, auth=lore_auth)
def post_comment(request, file_id: UUID, comment_text: str):
    qs = FileModel.objects.all()
    qs = scope_files_queryset(qs, request)
    file_obj = get_object_or_404(qs, id=file_id)

    comment = Comment.objects.create(
        owner=request.user,
        file=file_obj,
        comment=comment_text
    )
    return 201, CommentResponseSchema.from_model(comment)
