from datetime import datetime
from uuid import UUID

from django.core.files.base import ContentFile
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import File, Router, UploadedFile

from apps.collections.models import Collection
from apps.common.security import (
    get_allowed_collections_for_request,
    scope_artifacts_queryset,
    scope_collections_queryset,
)
from apps.accounts.auth import lore_auth

from .models import (
    Artifact,
    ArtifactComment,
    ArtifactPermission,
    ArtifactRelationship,
    ArtifactType,
    ArtifactVersion,
    DecisionArtifact,
    DocumentArtifact,
    MemoryArtifact,
    PermissionRole,
    RelationType,
    SkillArtifact,
)
from .schemas import (
    ArtifactCreateSchema,
    ArtifactResponseSchema,
    ArtifactUpdateSchema,
    ArtifactVersionResponseSchema,
    CommentResponseSchema,
    RelationshipCreateSchema,
    RelationshipResponseSchema,
)
from .utils import compute_diff

router = Router(tags=["Artifacts & Graph"])


# --- Artifact Creation & Upload ---

@router.post("/", response={201: ArtifactResponseSchema, 400: dict, 403: dict})
def create_artifact(request, data: ArtifactCreateSchema):
    """
    Create a new text-based artifact (skill, decision, memory).
    Documents must be uploaded via the `/api/artifacts/upload` endpoint.
    """
    agent_token = getattr(request, "agent_token", None)
    principal = getattr(request.user, "principal", None)

    if not principal:
        return 400, {"message": "No principal found for user context"}

    if data.type == "document":
        return 400, {"message": "Documents must be created via /api/artifacts/upload"}

    # Scope restriction check for agents
    if data.collection_id:
        allowed_cols = get_allowed_collections_for_request(request)
        allowed_ids = [c.id for c in allowed_cols]
        if agent_token and agent_token.restricted_collection and data.collection_id not in allowed_ids:
            return 403, {"message": "Access denied: Collection is outside sandboxed scope"}
        collection = get_object_or_404(Collection, id=data.collection_id)
    else:
        if agent_token and agent_token.restricted_collection:
            return 403, {"message": "Scope-restricted agents cannot create root-level artifacts."}
        collection = None

    artifact = Artifact.objects.create(
        type=data.type,
        title=data.title,
        owner=principal,
        created_by=principal,
        collection=collection,
        lifecycle_state=data.lifecycle_state or "draft",
    )

    if data.type == "skill":
        SkillArtifact.objects.create(
            artifact=artifact,
            skill_md_content=data.skill_md_content or "",
        )
    elif data.type == "decision":
        DecisionArtifact.objects.create(
            artifact=artifact,
            decision_text=data.decision_text or "",
            rationale=data.rationale or "",
        )
    elif data.type == "memory":
        MemoryArtifact.objects.create(
            artifact=artifact,
            content=data.memory_content or "",
            scope=data.memory_scope or "",
        )

    return 201, ArtifactResponseSchema.from_model(artifact)


@router.post("/upload", response={201: ArtifactResponseSchema, 400: dict, 403: dict})
def upload_document(
    request,
    file: UploadedFile = File(...),  # noqa: B008
    collection_id: UUID | None = None,
    lifecycle_state: str = "draft",
):
    """
    Upload a document artifact.
    If a document with the same name already exists in the target collection,
    an immutable new version is recorded and the document content is updated.
    """
    agent_token = getattr(request, "agent_token", None)
    principal = getattr(request.user, "principal", None)

    if not principal:
        return 400, {"message": "No principal found for user context"}

    if collection_id:
        allowed_cols = get_allowed_collections_for_request(request)
        allowed_ids = [c.id for c in allowed_cols]
        if agent_token and agent_token.restricted_collection and collection_id not in allowed_ids:
            return 403, {"message": "Access denied: Collection is outside sandboxed scope"}
        collection = get_object_or_404(Collection, id=collection_id)
    else:
        if agent_token and agent_token.restricted_collection:
            return 403, {"message": "Scope-restricted agents cannot create root-level artifacts."}
        collection = None

    # Read new content
    new_content = file.read()
    file.seek(0)

    # Check if a document with the same name already exists in this collection
    existing_artifact = Artifact.objects.filter(
        type="document",
        title=file.name,
        collection=collection,
        deleted_at__isnull=True,
    ).first()

    if existing_artifact:
        # Check locks
        if existing_artifact.locked_by and existing_artifact.locked_by != principal:
            return 403, {"message": f"Artifact is locked by {existing_artifact.locked_by}"}

        doc = existing_artifact.document
        old_content = doc.file.read()
        doc.file.seek(0)

        # Version increment
        version_num = existing_artifact.versions.count() + 1
        version = ArtifactVersion.objects.create(
            artifact=existing_artifact,
            version_number=version_num,
            file_instance=ContentFile(old_content, name=f"v{version_num}_{file.name}"),
            diff_content=compute_diff(old_content, new_content),
            created_by=principal,
            commit_message=f"Update document to version {version_num}",
        )

        existing_artifact.current_version = version
        existing_artifact.lifecycle_state = lifecycle_state
        existing_artifact.save()

        # Overwrite file
        doc.file.save(file.name, file, save=False)
        doc.save()

        return 201, ArtifactResponseSchema.from_model(existing_artifact)

    # Create new artifact
    artifact = Artifact.objects.create(
        type="document",
        title=file.name,
        owner=principal,
        created_by=principal,
        collection=collection,
        lifecycle_state=lifecycle_state,
    )

    DocumentArtifact.objects.create(
        artifact=artifact,
        file=file,
        format=file.name.split(".")[-1] if "." in file.name else "markdown",
    )

    return 201, ArtifactResponseSchema.from_model(artifact)


# --- Artifact Retrieval & Mutation ---

@router.get("/", response=list[ArtifactResponseSchema])
def list_artifacts(request, collection_id: UUID | None = None, type: str | None = None, query: str = ""):
    """List and filter artifacts within the caller's scoped workspace."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    if collection_id:
        qs = qs.filter(collection_id=collection_id)
    elif not type:
        # If no specific filtering, list root level
        qs = qs.filter(collection__isnull=True)

    if type:
        qs = qs.filter(type=type)

    if query:
        qs = qs.filter(title__icontains=query)

    return [ArtifactResponseSchema.from_model(a) for a in qs]


@router.get("/{artifact_id}", response={200: ArtifactResponseSchema, 404: dict})
def get_artifact(request, artifact_id: UUID):
    """Retrieve details for a specific artifact."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)
    return 200, ArtifactResponseSchema.from_model(artifact)


@router.patch("/{artifact_id}", response={200: ArtifactResponseSchema, 403: dict, 404: dict, 409: dict})
def update_artifact(request, artifact_id: UUID, data: ArtifactUpdateSchema):
    """Update metadata and contents of an existing artifact with optional OCC version check."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if artifact.locked_by and artifact.locked_by != principal:
        return 403, {"message": f"Artifact is locked by {artifact.locked_by}"}

    # Optimistic Concurrency Control (OCC) Check
    current_ver = artifact.current_version.version_number if artifact.current_version else 1
    if data.expected_version_number is not None and data.expected_version_number != current_ver:
        return 409, {
            "message": f"Artifact version mismatch: current version is {current_ver}, expected {data.expected_version_number}"
        }

    if data.title:
        artifact.title = data.title
    if data.lifecycle_state:
        artifact.lifecycle_state = data.lifecycle_state
    artifact.save()

    # Subtype-specific updates
    if artifact.type == "skill" and hasattr(artifact, "skill"):
        skill = artifact.skill
        if data.skill_md_content is not None:
            skill.skill_md_content = data.skill_md_content
        skill.save()
    elif artifact.type == "decision" and hasattr(artifact, "decision"):
        decision = artifact.decision
        if data.decision_text is not None:
            decision.decision_text = data.decision_text
        if data.rationale is not None:
            decision.rationale = data.rationale
        if data.decision_status is not None:
            decision.status = data.decision_status
        decision.save()
    elif artifact.type == "memory" and hasattr(artifact, "memory"):
        mem = artifact.memory
        if data.memory_content is not None:
            mem.content = data.memory_content
        if data.memory_scope is not None:
            mem.scope = data.memory_scope
        mem.save()

    return 200, ArtifactResponseSchema.from_model(artifact)


@router.delete("/{artifact_id}", response={204: None, 403: dict, 404: dict})
def delete_artifact(request, artifact_id: UUID):
    """Soft-delete an artifact."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if artifact.locked_by and artifact.locked_by != principal:
        return 403, {"message": f"Artifact is locked by {artifact.locked_by}"}

    artifact.deleted_at = timezone.now()
    artifact.save(update_fields=["deleted_at", "updated_at"])
    return 204, None


# --- Locking Mechanics ---

@router.post("/{artifact_id}/lock", response={200: ArtifactResponseSchema, 400: dict, 403: dict})
def lock_artifact(request, artifact_id: UUID):
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if not principal:
        return 400, {"message": "No principal found"}

    if artifact.locked_by:
        return 400, {"message": f"Artifact is already locked by {artifact.locked_by}"}

    artifact.locked_by = principal
    artifact.save()
    return 200, ArtifactResponseSchema.from_model(artifact)


@router.post("/{artifact_id}/unlock", response={200: ArtifactResponseSchema, 400: dict, 403: dict})
def unlock_artifact(request, artifact_id: UUID):
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if not principal:
        return 400, {"message": "No principal found"}

    if not artifact.locked_by:
        return 400, {"message": "Artifact is not locked"}

    if artifact.locked_by != principal and artifact.owner != principal:
        return 403, {"message": "You do not have permission to unlock this artifact"}

    artifact.locked_by = None
    artifact.save()
    return 200, ArtifactResponseSchema.from_model(artifact)


# --- Version History & Rollback ---

@router.get("/{artifact_id}/versions", response=list[ArtifactVersionResponseSchema])
def list_artifact_versions(request, artifact_id: UUID):
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    versions = artifact.versions.select_related("created_by").order_by("-version_number")
    return [ArtifactVersionResponseSchema.from_model(v) for v in versions]


@router.post("/{artifact_id}/revert", response={201: ArtifactResponseSchema, 400: dict, 403: dict, 404: dict})
def revert_artifact(request, artifact_id: UUID, target_version_number: int, commit_message: str = ""):
    """
    Revert an artifact to a historical version.
    This action creates a NEW append-only ArtifactVersion with the historical content
    and records a diff against the current state.
    """
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if artifact.locked_by and artifact.locked_by != principal:
        return 403, {"message": f"Artifact is locked by {artifact.locked_by}"}

    target_version = artifact.versions.filter(version_number=target_version_number).first()
    if not target_version:
        return 404, {"message": f"Version {target_version_number} not found for this artifact"}

    if artifact.type == "document" and hasattr(artifact, "document"):
        doc = artifact.document
        current_content = doc.file.read()
        doc.file.seek(0)

        target_content = target_version.file_instance.read()
        target_version.file_instance.seek(0)

        new_num = artifact.versions.count() + 1
        new_version = ArtifactVersion.objects.create(
            artifact=artifact,
            version_number=new_num,
            file_instance=ContentFile(target_content, name=f"v{new_num}_revert_to_v{target_version_number}_{artifact.title}"),
            diff_content=compute_diff(current_content, target_content),
            created_by=principal,
            commit_message=commit_message or f"Reverted artifact to version {target_version_number}",
        )

        doc.file.save(artifact.title, ContentFile(target_content), save=False)
        doc.save()

        artifact.current_version = new_version
        artifact.save()

    return 201, ArtifactResponseSchema.from_model(artifact)


@router.get("/{artifact_id}/download")
def download_document(request, artifact_id: UUID):
    qs = Artifact.objects.filter(deleted_at__isnull=True, type="document")
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    doc = artifact.document
    response = FileResponse(doc.file.open("rb"))
    response["Content-Disposition"] = f'attachment; filename="{artifact.title}"'
    return response


# --- Graph / Relationships ---

@router.post("/relationships", response={201: RelationshipResponseSchema, 400: dict, 403: dict})
def create_relationship(request, data: RelationshipCreateSchema):
    """Create a directed edge in the Artifact Graph."""
    principal = getattr(request.user, "principal", None)
    if not principal:
        return 400, {"message": "No principal found"}

    # Scoped check for both from and to artifacts
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    from_art = get_object_or_404(qs, id=data.from_artifact_id)
    to_art = get_object_or_404(qs, id=data.to_artifact_id)

    rel = ArtifactRelationship.objects.create(
        from_artifact=from_art,
        to_artifact=to_art,
        relation_type=data.relation_type,
        created_by=principal,
    )
    return 201, RelationshipResponseSchema.from_model(rel)


@router.get("/{artifact_id}/relationships", response=dict)
def get_relationships(request, artifact_id: UUID):
    """Retrieve all relationships (incoming and outgoing) for this artifact."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    outgoing = artifact.outgoing_relationships.all()
    incoming = artifact.incoming_relationships.all()

    return {
        "outgoing": [RelationshipResponseSchema.from_model(r) for r in outgoing],
        "incoming": [RelationshipResponseSchema.from_model(r) for r in incoming],
    }


# --- Comments ---

@router.get("/{artifact_id}/comments", response=list[CommentResponseSchema])
def list_comments(request, artifact_id: UUID):
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    comments = artifact.comments.select_related("author").order_by("-created_at")
    return [CommentResponseSchema.from_model(c) for c in comments]


@router.post("/{artifact_id}/comments", response={201: CommentResponseSchema, 400: dict})
def post_comment(request, artifact_id: UUID, body: str):
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    principal = getattr(request.user, "principal", None)
    if not principal:
        return 400, {"message": "No principal found"}

    comment = ArtifactComment.objects.create(
        artifact=artifact,
        author=principal,
        body=body,
    )
    return 201, CommentResponseSchema.from_model(comment)
