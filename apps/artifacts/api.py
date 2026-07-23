import json
import time
from datetime import datetime
from queue import Empty
from uuid import UUID

from django.core.files.base import ContentFile
from django.http import FileResponse, HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from ninja import File, Router, UploadedFile

from apps.accounts.auth import lore_auth
from apps.collections.models import Collection
from apps.common.realtime import publish_artifact_event, subscribe_events, unsubscribe_events
from apps.common.security import (
    get_allowed_collections_for_request,
    scope_artifacts_queryset,
    scope_collections_queryset,
)

from .chunking import chunk_text_content
from .models import (
    Artifact,
    ArtifactComment,
    ArtifactPermission,
    ArtifactRelationship,
    ArtifactType,
    ArtifactVersion,
    DecisionArtifact,
    DocumentArtifact,
    LifecycleState,
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
from .wiki_links import extract_and_sync_wiki_links

router = Router(tags=["Artifacts & Graph"])

def _initial_lifecycle_state(requested: str, request) -> str:
    """
    Determines initial lifecycle state based on actor capability:
    1. Human Users: Can assign any valid lifecycle state (Draft, Review, Approved, Published).
    2. Trusted Agents (can_auto_approve=True): Can assign any valid state.
    3. Untrusted / Background Agents (can_auto_approve=False): Clamped to Draft or Review.
    """
    agent_token = getattr(request, "agent_token", None)
    if agent_token is None or getattr(agent_token, "can_auto_approve", False):
        valid_states = {
            LifecycleState.DRAFT,
            LifecycleState.REVIEW,
            LifecycleState.APPROVED,
            LifecycleState.PUBLISHED,
            LifecycleState.ARCHIVED,
        }
        if requested in valid_states:
            return requested
        return LifecycleState.DRAFT

    if requested in {LifecycleState.DRAFT, LifecycleState.REVIEW}:
        return requested
    return LifecycleState.DRAFT


# --- Server-Sent Events (SSE) Real-Time Stream ---

@router.get("/stream/events")
def event_stream(request):
    """
    Server-Sent Events (SSE) stream delivering real-time artifact updates,
    state changes, and diff patch notifications to Web UI clients and AI Agents.

    Events are filtered by the subscribing principal: a client only receives
    events for artifacts owned by its own Principal, preventing cross-tenant
    leakage of titles, diffs, and lifecycle state.
    """
    principal = getattr(request, "principal", None)
    if principal is None:
        return HttpResponse(
            '{"message": "Authentication required for the event stream."}',
            status=401, content_type="application/json",
        )
    principal_id = str(principal.id)

    def event_generator():
        q = subscribe_events()
        try:
            yield "event: connected\ndata: {\"status\": \"connected\"}\n\n"
            while True:
                try:
                    event_data = q.get(timeout=25)
                    # Only deliver events the subscriber is authorized to see.
                    if event_data.get("owner_id") != principal_id:
                        continue
                    yield f"event: {event_data['event']}\ndata: {json.dumps(event_data)}\n\n"
                except Empty:
                    # Ping keepalive every 25 seconds
                    yield "event: ping\ndata: {\"ping\": true}\n\n"
        finally:
            unsubscribe_events(q)

    response = StreamingHttpResponse(event_generator(), content_type="text/event-stream")
    response["Cache-Control"] = "no-cache"
    response["X-Accel-Buffering"] = "no"
    return response


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
        inherit_permissions=(collection is not None),
        lifecycle_state=_initial_lifecycle_state(data.lifecycle_state or "draft", request),
    )

    text_to_scan = ""
    if data.type == "skill":
        text_to_scan = data.skill_md_content or ""
        SkillArtifact.objects.create(
            artifact=artifact,
            skill_md_content=text_to_scan,
        )
    elif data.type == "decision":
        text_to_scan = (data.decision_text or "") + "\n" + (data.rationale or "")
        DecisionArtifact.objects.create(
            artifact=artifact,
            decision_text=data.decision_text or "",
            rationale=data.rationale or "",
        )
    elif data.type == "memory":
        text_to_scan = data.memory_content or ""
        MemoryArtifact.objects.create(
            artifact=artifact,
            content=text_to_scan,
            scope=data.memory_scope or "",
        )

    # Create initial version snapshot via unified service
    from apps.artifacts.services import create_initial_version, update_artifact_version, revert_artifact_to_version
    create_initial_version(artifact, text_to_scan, principal)

    # Publish real-time event
    publish_artifact_event(
        event_type="artifact.created",
        artifact_id=str(artifact.id),
        payload={"title": artifact.title, "type": artifact.type, "state": artifact.lifecycle_state},
        owner_id=str(artifact.owner_id),
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
        diff_patch = compute_diff(old_content, new_content)
        version = ArtifactVersion.objects.create(
            artifact=existing_artifact,
            version_number=version_num,
            file_instance=ContentFile(old_content, name=f"v{version_num}_{file.name}"),
            diff_content=diff_patch,
            created_by=principal,
            commit_message=f"Update document to version {version_num}",
        )

        existing_artifact.current_version = version
        existing_artifact.lifecycle_state = _initial_lifecycle_state(lifecycle_state, request)
        existing_artifact.save()

        # Overwrite file
        doc.file.save(file.name, file, save=False)
        doc.save()

        try:
            text_str = new_content.decode("utf-8")
            extract_and_sync_wiki_links(existing_artifact, text_str, principal)
            chunk_text_content(existing_artifact, version, text_str)
        except Exception:
            pass

        # Publish real-time update event
        publish_artifact_event(
            event_type="artifact.updated",
            artifact_id=str(existing_artifact.id),
            payload={"version_number": version_num, "diff": diff_patch, "state": existing_artifact.lifecycle_state},
            owner_id=str(existing_artifact.owner_id),
        )

        return 201, ArtifactResponseSchema.from_model(existing_artifact)

    # Create new artifact
    artifact = Artifact.objects.create(
        type="document",
        title=file.name,
        owner=principal,
        created_by=principal,
        collection=collection,
        inherit_permissions=(collection is not None),
        lifecycle_state=_initial_lifecycle_state(lifecycle_state, request),
    )

    doc = DocumentArtifact.objects.create(
        artifact=artifact,
        file=file,
        format=file.name.split(".")[-1] if "." in file.name else "markdown",
    )

    version = ArtifactVersion.objects.create(
        artifact=artifact,
        version_number=1,
        file_instance=ContentFile(new_content, name=f"v1_{file.name}"),
        diff_content="",
        created_by=principal,
        commit_message="Initial document upload",
    )
    artifact.current_version = version
    artifact.save(update_fields=["current_version"])

    try:
        text_str = new_content.decode("utf-8")
        extract_and_sync_wiki_links(artifact, text_str, principal)
        chunk_text_content(artifact, version, text_str)
    except Exception:
        pass

    # Publish real-time creation event
    publish_artifact_event(
        event_type="artifact.created",
        artifact_id=str(artifact.id),
        payload={"title": artifact.title, "type": "document", "state": artifact.lifecycle_state},
        owner_id=str(artifact.owner_id),
    )

    return 201, ArtifactResponseSchema.from_model(artifact)


# --- Artifact Retrieval & Mutation ---

@router.get("/", response=list[ArtifactResponseSchema])
def list_artifacts(request, collection_id: UUID | None = None, type: str | None = None, query: str = ""):
    """List and filter artifacts within the caller's scoped workspace."""
    qs = Artifact.objects.filter(deleted_at__isnull=True).select_related(
        "owner", "created_by", "current_version", "skill", "decision", "document", "memory"
    )
    qs = scope_artifacts_queryset(qs, request)

    if collection_id:
        qs = qs.filter(collection_id=collection_id)
    elif not type:
        qs = qs.filter(collection__isnull=True)

    if type:
        qs = qs.filter(type=type)

    if query:
        qs = qs.filter(title__icontains=query)

    return [ArtifactResponseSchema.from_model(a) for a in qs]


# --- Governance Approval & Rejection Endpoints ---

def _require_human_reviewer(request):
    """
    Governance gate: only human principals may approve/reject.

    Agent tokens (autonomous actors) cannot transition their own proposals
    into a trusted state — that is the human-in-the-loop guarantee. Returns
    an error dict when the actor is an agent, else None.
    """
    if getattr(request, "agent_token", None) is not None:
        return {"message": "Only human reviewers can approve or reject artifacts."}
    return None


@router.post("/{artifact_id}/approve", response={200: ArtifactResponseSchema, 403: dict, 404: dict})
def approve_artifact(request, artifact_id: UUID):
    """
    Approve an artifact proposal. Transitions lifecycle state to `approved`
    and emits a real-time event to wake up waiting background agents.

    Restricted to human reviewers — agent tokens cannot self-approve.
    """
    denied = _require_human_reviewer(request)
    if denied:
        return 403, denied

    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    previous_state = artifact.lifecycle_state
    artifact.lifecycle_state = LifecycleState.APPROVED
    artifact.save(update_fields=["lifecycle_state", "updated_at"])

    # Publish real-time state change event
    publish_artifact_event(
        event_type="artifact.state_changed",
        artifact_id=str(artifact.id),
        payload={"new_state": artifact.lifecycle_state, "previous_state": previous_state, "actor": str(request.user)},
        owner_id=str(artifact.owner_id),
    )

    return 200, ArtifactResponseSchema.from_model(artifact)


@router.post("/{artifact_id}/reject", response={200: ArtifactResponseSchema, 403: dict, 404: dict})
def reject_artifact(request, artifact_id: UUID):
    """
    Reject or deny an artifact proposal. Transitions lifecycle state to `rejected`
    and emits a real-time event.

    Restricted to human reviewers — agent tokens cannot self-reject.
    """
    denied = _require_human_reviewer(request)
    if denied:
        return 403, denied

    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    previous_state = artifact.lifecycle_state
    artifact.lifecycle_state = LifecycleState.REJECTED
    artifact.save(update_fields=["lifecycle_state", "updated_at"])

    # Publish real-time state change event
    publish_artifact_event(
        event_type="artifact.state_changed",
        artifact_id=str(artifact.id),
        payload={"new_state": artifact.lifecycle_state, "previous_state": previous_state, "actor": str(request.user)},
        owner_id=str(artifact.owner_id),
    )

    return 200, ArtifactResponseSchema.from_model(artifact)


# --- Token-Efficient Delta Patch Endpoint ---

@router.get("/{artifact_id}/delta", response={200: dict, 404: dict})
def get_artifact_delta(request, artifact_id: UUID, since_version: int = 1):
    """
    Retrieve lightweight diff patches between `since_version` and current version,
    preventing LLM agents from wasting tokens re-reading unchanged documents.
    """
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    versions = artifact.versions.filter(version_number__gt=since_version).order_by("version_number")
    patches = []
    for v in versions:
        patches.append({
            "version_number": v.version_number,
            "commit_message": v.commit_message,
            "diff_content": v.diff_content,
            "created_at": v.created_at.isoformat(),
        })

    current_ver = artifact.current_version.version_number if artifact.current_version else 1
    return 200, {
        "artifact_id": str(artifact.id),
        "title": artifact.title,
        "current_version": current_ver,
        "since_version": since_version,
        "delta_count": len(patches),
        "patches": patches,
    }


# --- Dynamic Skill Registry ---

@router.get("/skills/list", response=list[ArtifactResponseSchema])
def list_skills(request):
    """
    Dynamic Skill Registry: List all available skills across all collections
    accessible to the caller.
    """
    qs = Artifact.objects.filter(deleted_at__isnull=True, type="skill").select_related(
        "owner", "created_by", "current_version", "skill"
    )
    qs = scope_artifacts_queryset(qs, request)
    return [ArtifactResponseSchema.from_model(a) for a in qs]


@router.get("/skills/{title}", response={200: dict, 404: dict})
def fetch_skill(request, title: str):
    """
    Fetch a skill by title for dynamic agent prompt hydration.
    Atomically increments usage_count on the SkillArtifact.
    """
    qs = Artifact.objects.filter(deleted_at__isnull=True, type="skill", title__iexact=title)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs)

    if hasattr(artifact, "skill"):
        skill = artifact.skill
        skill.usage_count += 1
        skill.save(update_fields=["usage_count"])
        md_content = skill.skill_md_content
    else:
        md_content = ""

    return 200, {
        "id": str(artifact.id),
        "title": artifact.title,
        "collection_id": str(artifact.collection_id) if artifact.collection_id else None,
        "usage_count": artifact.skill.usage_count if hasattr(artifact, "skill") else 0,
        "content": md_content,
        "lifecycle_state": artifact.lifecycle_state,
        "updated_at": artifact.updated_at.isoformat(),
    }


# --- Vector & Chunk RAG Search ---

@router.get("/chunks/search", response=list[dict])
def search_chunks(request, query: str = "", limit: int = 10):
    """
    Search across granular ArtifactChunk text blocks for targeted RAG context.
    Returns matching snippets with chunk index, version number, and artifact provenance.
    """
    if not query:
        return []

    from .models import ArtifactChunk

    allowed_artifacts = scope_artifacts_queryset(Artifact.objects.filter(deleted_at__isnull=True), request)
    chunks = ArtifactChunk.objects.filter(
        artifact__in=allowed_artifacts,
        text__icontains=query,
    ).select_related("artifact", "version")[:limit]

    results = []
    for chunk in chunks:
        results.append({
            "chunk_id": str(chunk.id),
            "artifact_id": str(chunk.artifact.id),
            "artifact_title": chunk.artifact.title,
            "artifact_type": chunk.artifact.type,
            "version_number": chunk.version.version_number,
            "chunk_index": chunk.chunk_index,
            "text": chunk.text,
        })
    return results


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
    new_text_content = None
    if artifact.type == "skill" and hasattr(artifact, "skill"):
        if data.skill_md_content is not None:
            new_text_content = data.skill_md_content
    elif artifact.type == "decision" and hasattr(artifact, "decision"):
        decision = artifact.decision
        if data.decision_text is not None:
            new_text_content = data.decision_text
        if data.rationale is not None:
            decision.rationale = data.rationale
        if data.decision_status is not None:
            decision.status = data.decision_status
        decision.save()
    elif artifact.type == "memory" and hasattr(artifact, "memory"):
        mem = artifact.memory
        if data.memory_content is not None:
            new_text_content = data.memory_content
        if data.memory_scope is not None:
            mem.scope = data.memory_scope
        mem.save()

    if new_text_content is not None:
        version = update_artifact_version(
            artifact,
            new_text_content,
            principal,
            commit_message="Updated content",
        )
        version_num = version.version_number
    else:
        version_num = artifact.current_version.version_number if artifact.current_version else 1

    # Publish real-time update event
    publish_artifact_event(
        event_type="artifact.updated",
        artifact_id=str(artifact.id),
        payload={"title": artifact.title, "state": artifact.lifecycle_state, "version_number": version_num},
        owner_id=str(artifact.owner_id),
    )

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
    Revert an artifact of any subtype to a historical version.
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

    new_version = revert_artifact_to_version(
        artifact=artifact,
        target_version=target_version,
        created_by=principal,
        commit_message=commit_message,
    )

    publish_artifact_event(
        event_type="artifact.updated",
        artifact_id=str(artifact.id),
        payload={"version_number": new_version.version_number, "state": artifact.lifecycle_state},
        owner_id=str(artifact.owner_id),
    )

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

    # Publish relationship created event
    publish_artifact_event(
        event_type="artifact.relationship_created",
        artifact_id=str(from_art.id),
        payload={"to_artifact_id": str(to_art.id), "relation_type": data.relation_type},
    )

    return 201, RelationshipResponseSchema.from_model(rel)


@router.get("/{artifact_id}/relationships", response=dict)
def get_relationships(request, artifact_id: UUID):
    """Retrieve all relationships (incoming and outgoing) for this artifact."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)
    artifact = get_object_or_404(qs, id=artifact_id)

    outgoing = artifact.outgoing_relationships.select_related("from_artifact", "to_artifact", "created_by").all()
    incoming = artifact.incoming_relationships.select_related("from_artifact", "to_artifact", "created_by").all()

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
