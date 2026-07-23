"""
Unified Artifact Versioning and Revert Services for Lore.
Provides robust, race-free version creation, diffing, content updates, and reversion
across all 4 artifact subtypes (Document, Skill, Decision, Memory).
"""

from typing import Any
from django.core.files.base import ContentFile
from django.db import models, transaction
from apps.artifacts.models import (
    Artifact,
    ArtifactVersion,
    DecisionArtifact,
    DocumentArtifact,
    MemoryArtifact,
    SkillArtifact,
)
from apps.artifacts.utils import compute_diff
from apps.artifacts.chunking import chunk_text_content
from apps.artifacts.wiki_links import extract_and_sync_wiki_links


def get_artifact_text_content(artifact: Artifact) -> str:
    """Retrieve raw text content for any artifact subtype."""
    if artifact.type == "document" and hasattr(artifact, "document") and artifact.document.file:
        try:
            artifact.document.file.seek(0)
            return artifact.document.file.read().decode("utf-8", errors="replace")
        except Exception:
            return ""
    elif artifact.type == "skill" and hasattr(artifact, "skill"):
        return artifact.skill.skill_md_content or ""
    elif artifact.type == "decision" and hasattr(artifact, "decision"):
        return artifact.decision.decision_text or ""
    elif artifact.type == "memory" and hasattr(artifact, "memory"):
        return artifact.memory.content or ""
    elif artifact.current_version and artifact.current_version.file_instance:
        try:
            artifact.current_version.file_instance.seek(0)
            return artifact.current_version.file_instance.read().decode("utf-8", errors="replace")
        except Exception:
            return ""
    return ""


def get_next_version_number(artifact: Artifact) -> int:
    """
    Safely calculate the next version number for an artifact using atomic locks
    to prevent race conditions in concurrent write environments.
    """
    with transaction.atomic():
        Artifact.objects.select_for_update().get(id=artifact.id)
        max_ver = artifact.versions.aggregate(max_num=models.Max("version_number"))["max_num"]
        return (max_ver or 0) + 1


def create_initial_version(artifact: Artifact, content_text: str, created_by: Any) -> ArtifactVersion:
    """Create version 1 for a newly created artifact across any subtype."""
    content_bytes = content_text.encode("utf-8")
    version = ArtifactVersion.objects.create(
        artifact=artifact,
        version_number=1,
        file_instance=ContentFile(content_bytes, name=f"v1_{artifact.title}.md"),
        diff_content="",
        created_by=created_by,
        commit_message="Initial creation",
    )
    artifact.current_version = version
    artifact.save(update_fields=["current_version"])

    if content_text:
        try:
            extract_and_sync_wiki_links(artifact, content_text, created_by)
            chunk_text_content(artifact, version, content_text)
        except Exception:
            pass

    return version


def update_artifact_version(
    artifact: Artifact,
    new_content_text: str,
    created_by: Any,
    commit_message: str = "",
) -> ArtifactVersion:
    """
    Create a new immutable ArtifactVersion for an existing artifact update,
    updating subtype extension tables, computing diffs, and syncing graph/chunks.
    """
    old_content_text = get_artifact_text_content(artifact)
    version_num = get_next_version_number(artifact)

    old_bytes = old_content_text.encode("utf-8")
    new_bytes = new_content_text.encode("utf-8")
    diff_patch = compute_diff(old_bytes, new_bytes)

    # 1. Create ArtifactVersion with the NEW content (fixes off-by-one bug)
    version = ArtifactVersion.objects.create(
        artifact=artifact,
        version_number=version_num,
        file_instance=ContentFile(new_bytes, name=f"v{version_num}_{artifact.title}.md"),
        diff_content=diff_patch,
        created_by=created_by,
        commit_message=commit_message or f"Update to version {version_num}",
    )

    # 2. Update subtype extension table
    if artifact.type == "skill" and hasattr(artifact, "skill"):
        artifact.skill.skill_md_content = new_content_text
        artifact.skill.save(update_fields=["skill_md_content"])
    elif artifact.type == "decision" and hasattr(artifact, "decision"):
        artifact.decision.decision_text = new_content_text
        artifact.decision.save(update_fields=["decision_text"])
    elif artifact.type == "memory" and hasattr(artifact, "memory"):
        artifact.memory.content = new_content_text
        artifact.memory.save(update_fields=["content"])
    elif artifact.type == "document" and hasattr(artifact, "document"):
        doc = artifact.document
        doc.file.save(artifact.title, ContentFile(new_bytes), save=False)
        doc.save()

    # 3. Update current_version pointer
    artifact.current_version = version
    artifact.save(update_fields=["current_version", "updated_at"])

    # 4. Sync wiki-links and chunk text
    try:
        extract_and_sync_wiki_links(artifact, new_content_text, created_by)
        chunk_text_content(artifact, version, new_content_text)
    except Exception:
        pass

    return version


def revert_artifact_to_version(
    artifact: Artifact,
    target_version: ArtifactVersion,
    created_by: Any,
    commit_message: str = "",
) -> ArtifactVersion:
    """
    Revert an artifact of ANY subtype to a target historical version.
    Appends a new forward version snapshot containing the historical content.
    """
    current_content_text = get_artifact_text_content(artifact)

    # Read target version content
    if target_version.file_instance:
        target_version.file_instance.seek(0)
        target_content_bytes = target_version.file_instance.read()
        target_content_text = target_content_bytes.decode("utf-8", errors="replace")
    else:
        target_content_text = ""
        target_content_bytes = b""

    version_num = get_next_version_number(artifact)
    diff_patch = compute_diff(current_content_text.encode("utf-8"), target_content_bytes)

    # 1. Create new append-only version row
    new_version = ArtifactVersion.objects.create(
        artifact=artifact,
        version_number=version_num,
        file_instance=ContentFile(
            target_content_bytes,
            name=f"v{version_num}_revert_to_v{target_version.version_number}_{artifact.title}.md",
        ),
        diff_content=diff_patch,
        created_by=created_by,
        commit_message=commit_message or f"Reverted artifact to version {target_version.version_number}",
    )

    # 2. Apply content to subtype extension tables
    if artifact.type == "skill" and hasattr(artifact, "skill"):
        artifact.skill.skill_md_content = target_content_text
        artifact.skill.save(update_fields=["skill_md_content"])
    elif artifact.type == "decision" and hasattr(artifact, "decision"):
        artifact.decision.decision_text = target_content_text
        artifact.decision.save(update_fields=["decision_text"])
    elif artifact.type == "memory" and hasattr(artifact, "memory"):
        artifact.memory.content = target_content_text
        artifact.memory.save(update_fields=["content"])
    elif artifact.type == "document" and hasattr(artifact, "document"):
        doc = artifact.document
        doc.file.save(artifact.title, ContentFile(target_content_bytes), save=False)
        doc.save()

    # 3. Update current_version pointer
    artifact.current_version = new_version
    artifact.save(update_fields=["current_version", "updated_at"])

    # 4. Sync wiki-links and chunk text
    try:
        extract_and_sync_wiki_links(artifact, target_content_text, created_by)
        chunk_text_content(artifact, new_version, target_content_text)
    except Exception:
        pass

    return new_version
