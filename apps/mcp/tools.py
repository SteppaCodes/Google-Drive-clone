from typing import Any, Optional
from uuid import UUID

from django.core.files.base import ContentFile
from django.db import models

from apps.accounts.models import Principal
from apps.artifacts.models import (
    Artifact,
    ArtifactRelationship,
    ArtifactVersion,
    DecisionArtifact,
    DocumentArtifact,
    MemoryArtifact,
    SkillArtifact,
)
from apps.artifacts.utils import compute_diff
from apps.artifacts.wiki_links import extract_and_sync_wiki_links
from apps.collections.models import Collection
from apps.common.security import scope_artifacts_queryset, scope_collections_queryset


def mcp_search_artifacts(request, query: str = "", limit: int = 5, collection_id: Optional[str] = None) -> list[dict[str, Any]]:
    """Search for artifacts by title or content."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    if collection_id:
        qs = qs.filter(collection_id=collection_id)

    if query:
        qs = qs.filter(
            models.Q(title__icontains=query)
            | models.Q(skill__skill_md_content__icontains=query)
            | models.Q(decision__decision_text__icontains=query)
            | models.Q(memory__content__icontains=query)
        )

    results = []
    for art in qs.select_related("skill", "decision", "memory")[:limit]:
        content_snippet = ""
        if art.type == "skill" and hasattr(art, "skill"):
            content_snippet = art.skill.skill_md_content[:200]
        elif art.type == "decision" and hasattr(art, "decision"):
            content_snippet = art.decision.decision_text[:200]
        elif art.type == "memory" and hasattr(art, "memory"):
            content_snippet = art.memory.content[:200]

        results.append({
            "id": str(art.id),
            "title": art.title,
            "type": art.type,
            "collection_id": str(art.collection_id) if art.collection_id else None,
            "lifecycle_state": art.lifecycle_state,
            "snippet": content_snippet,
        })
    return results


def mcp_read_artifact(request, artifact_id: str) -> dict[str, Any]:
    """Retrieve full artifact metadata and content."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    try:
        art = qs.get(id=artifact_id)
    except Artifact.DoesNotExist:
        return {"error": f"Artifact {artifact_id} not found or access denied."}

    content = ""
    if art.type == "skill" and hasattr(art, "skill"):
        content = art.skill.skill_md_content
    elif art.type == "decision" and hasattr(art, "decision"):
        content = f"Decision: {art.decision.decision_text}\nRationale: {art.decision.rationale}"
    elif art.type == "memory" and hasattr(art, "memory"):
        content = art.memory.content
    elif art.type == "document" and hasattr(art, "document"):
        try:
            art.document.file.seek(0)
            content = art.document.file.read().decode("utf-8")
        except Exception:
            content = "[Binary document file]"

    return {
        "id": str(art.id),
        "title": art.title,
        "type": art.type,
        "collection_id": str(art.collection_id) if art.collection_id else None,
        "version_number": art.current_version.version_number if art.current_version else 1,
        "lifecycle_state": art.lifecycle_state,
        "content": content,
        "locked_by": str(art.locked_by) if art.locked_by else None,
        "updated_at": art.updated_at.isoformat(),
    }


def mcp_write_artifact(
    request,
    title: str,
    type: str,
    content: str,
    collection_id: Optional[str] = None,
    expected_version_number: Optional[int] = None,
) -> dict[str, Any]:
    """Create or update an artifact."""
    principal = getattr(request.user, "principal", None)
    if not principal:
        return {"error": "No principal identity found."}

    parent_collection = None
    if collection_id:
        col_qs = Collection.objects.all()
        col_qs = scope_collections_queryset(col_qs, request)
        try:
            parent_collection = col_qs.get(id=collection_id)
        except Collection.DoesNotExist:
            return {"error": f"Collection {collection_id} not found or access denied."}

    existing = Artifact.objects.filter(
        title=title,
        collection=parent_collection,
        deleted_at__isnull=True,
    ).first()

    if existing:
        current_ver = existing.current_version.version_number if existing.current_version else 1
        if expected_version_number is not None and expected_version_number != current_ver:
            return {"error": f"OCC conflict: Current version is {current_ver}, expected {expected_version_number}."}

        if existing.locked_by and existing.locked_by != principal:
            return {"error": f"Artifact is locked by {existing.locked_by}."}

        if existing.type == "skill" and hasattr(existing, "skill"):
            existing.skill.skill_md_content = content
            existing.skill.save()
        elif existing.type == "decision" and hasattr(existing, "decision"):
            existing.decision.decision_text = content
            existing.decision.save()
        elif existing.type == "memory" and hasattr(existing, "memory"):
            existing.memory.content = content
            existing.memory.save()

        extract_and_sync_wiki_links(existing, content, principal)
        return {
            "id": str(existing.id),
            "title": existing.title,
            "status": "updated",
            "version_number": current_ver,
        }

    artifact = Artifact.objects.create(
        type=type,
        title=title,
        owner=principal,
        created_by=principal,
        collection=parent_collection,
        lifecycle_state="draft",
    )

    if type == "skill":
        SkillArtifact.objects.create(artifact=artifact, skill_md_content=content)
    elif type == "decision":
        DecisionArtifact.objects.create(artifact=artifact, decision_text=content)
    elif type == "memory":
        MemoryArtifact.objects.create(artifact=artifact, content=content)

    extract_and_sync_wiki_links(artifact, content, principal)
    return {
        "id": str(artifact.id),
        "title": artifact.title,
        "status": "created",
        "version_number": 1,
    }


def mcp_revert_artifact(request, artifact_id: str, target_version_number: int, commit_message: str = "") -> dict[str, Any]:
    """Revert artifact to a previous version."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    try:
        art = qs.get(id=artifact_id)
    except Artifact.DoesNotExist:
        return {"error": f"Artifact {artifact_id} not found."}

    target_ver = art.versions.filter(version_number=target_version_number).first()
    if not target_ver:
        return {"error": f"Version {target_version_number} does not exist."}

    principal = getattr(request.user, "principal", None)
    if art.locked_by and art.locked_by != principal:
        return {"error": f"Artifact is locked by {art.locked_by}."}

    if art.type == "document" and hasattr(art, "document"):
        doc = art.document
        current_content = doc.file.read()
        doc.file.seek(0)
        target_content = target_ver.file_instance.read()
        target_ver.file_instance.seek(0)

        new_num = art.versions.count() + 1
        new_v = ArtifactVersion.objects.create(
            artifact=art,
            version_number=new_num,
            file_instance=ContentFile(target_content, name=f"v{new_num}_revert_{art.title}"),
            diff_content=compute_diff(current_content, target_content),
            created_by=principal,
            commit_message=commit_message or f"Reverted to version {target_version_number}",
        )
        doc.file.save(art.title, ContentFile(target_content), save=False)
        doc.save()
        art.current_version = new_v
        art.save()

    return {"status": "reverted", "artifact_id": str(art.id), "new_version_number": art.versions.count()}


def mcp_list_collection(request, collection_id: Optional[str] = None) -> dict[str, Any]:
    """List child collections and artifacts in a collection."""
    col_qs = Collection.objects.all()
    col_qs = scope_collections_queryset(col_qs, request)

    art_qs = Artifact.objects.filter(deleted_at__isnull=True)
    art_qs = scope_artifacts_queryset(art_qs, request)

    if collection_id:
        sub_cols = col_qs.filter(parent_id=collection_id)
        arts = art_qs.filter(collection_id=collection_id)
    else:
        sub_cols = col_qs.filter(parent__isnull=True)
        arts = art_qs.filter(collection__isnull=True)

    return {
        "collections": [{"id": str(c.id), "name": c.name} for c in sub_cols],
        "artifacts": [{"id": str(a.id), "title": a.title, "type": a.type} for a in arts],
    }


def mcp_create_relationship(request, from_artifact_id: str, to_artifact_id: str, relation_type: str) -> dict[str, Any]:
    """Create a directed edge between two artifacts."""
    qs = Artifact.objects.filter(deleted_at__isnull=True)
    qs = scope_artifacts_queryset(qs, request)

    try:
        from_art = qs.get(id=from_artifact_id)
        to_art = qs.get(id=to_artifact_id)
    except Artifact.DoesNotExist:
        return {"error": "One or both artifacts were not found or access denied."}

    principal = getattr(request.user, "principal", None)
    rel, _ = ArtifactRelationship.objects.get_or_create(
        from_artifact=from_art,
        to_artifact=to_art,
        relation_type=relation_type,
        defaults={"created_by": principal},
    )

    return {"status": "created", "relationship_id": str(rel.id), "relation_type": relation_type}


def mcp_list_skills(request) -> list[dict[str, Any]]:
    """List all skill artifacts accessible to caller."""
    qs = Artifact.objects.filter(deleted_at__isnull=True, type="skill")
    qs = scope_artifacts_queryset(qs, request)

    skills = []
    for art in qs.select_related("skill"):
        usage = art.skill.usage_count if hasattr(art, "skill") else 0
        skills.append({
            "id": str(art.id),
            "title": art.title,
            "usage_count": usage,
            "collection_id": str(art.collection_id) if art.collection_id else None,
        })
    return skills
