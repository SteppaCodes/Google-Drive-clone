import re
from typing import TYPE_CHECKING
from django.db import transaction

if TYPE_CHECKING:
    from apps.artifacts.models import Artifact
    from apps.accounts.models import Principal


WIKI_LINK_REGEX = re.compile(r"\[\[(.*?)\]\]")


def extract_and_sync_wiki_links(artifact: "Artifact", text_content: str, created_by: "Principal") -> list[str]:
    """
    Scans text_content for [[Artifact Title]] syntax.
    Finds existing artifacts matching those titles within the workspace,
    and creates 'references' relationships from artifact -> target_artifact.
    Returns the list of resolved title strings.
    """
    if not text_content:
        return []

    titles = list(set(WIKI_LINK_REGEX.findall(text_content)))
    if not titles:
        return []

    from apps.artifacts.models import Artifact, ArtifactRelationship

    # Find target artifacts by title within the same owner workspace (excluding self)
    target_artifacts = Artifact.objects.filter(
        owner=artifact.owner,
        title__in=titles,
        deleted_at__isnull=True,
    ).exclude(id=artifact.id)

    resolved_titles = []
    with transaction.atomic():
        for target in target_artifacts:
            ArtifactRelationship.objects.get_or_create(
                from_artifact=artifact,
                to_artifact=target,
                relation_type="references",
                defaults={"created_by": created_by},
            )
            resolved_titles.append(target.title)

    return resolved_titles
