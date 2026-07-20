from typing import TYPE_CHECKING
from django.db import transaction

if TYPE_CHECKING:
    from apps.artifacts.models import Artifact, ArtifactVersion


CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


def chunk_text_content(artifact: "Artifact", version: "ArtifactVersion", text_content: str) -> int:
    """
    Splits text_content into sequential overlapping chunks and stores
    ArtifactChunk rows for the given ArtifactVersion.
    Updates artifact.embedding_status to 'indexed'.
    Returns the number of created chunks.
    """
    if not text_content or not text_content.strip():
        artifact.embedding_status = "indexed"
        artifact.save(update_fields=["embedding_status"])
        return 0

    from apps.artifacts.models import ArtifactChunk

    text = text_content.strip()
    chunks = []
    start = 0

    while start < len(text):
        end = min(start + CHUNK_SIZE, len(text))
        chunk_str = text[start:end]
        chunks.append(chunk_str)

        if end == len(text):
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP

    with transaction.atomic():
        # Clean up any existing chunks for this specific version if re-running
        ArtifactChunk.objects.filter(version=version).delete()

        created_chunks = [
            ArtifactChunk(
                artifact=artifact,
                version=version,
                chunk_index=idx,
                text=chunk_text,
            )
            for idx, chunk_text in enumerate(chunks)
        ]
        ArtifactChunk.objects.bulk_create(created_chunks)

        artifact.embedding_status = "indexed"
        artifact.save(update_fields=["embedding_status"])

    return len(created_chunks)
