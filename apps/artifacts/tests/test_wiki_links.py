from django.test import TestCase

from apps.accounts.models import Principal, User
from apps.artifacts.models import Artifact, ArtifactRelationship, SkillArtifact
from apps.artifacts.wiki_links import extract_and_sync_wiki_links


class WikiLinksTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="test@lore.com", password="password123", first_name="Wiki", last_name="Test")
        self.principal = Principal.objects.create(kind="user", user=self.user)

        self.target_art = Artifact.objects.create(
            type="skill",
            title="Django Ninja Patterns",
            owner=self.principal,
            created_by=self.principal,
            inherit_permissions=False,
        )
        SkillArtifact.objects.create(artifact=self.target_art, skill_md_content="Skill content")

    def test_extract_and_sync_wiki_links(self):
        source_art = Artifact.objects.create(
            type="skill",
            title="Backend Deployment",
            owner=self.principal,
            created_by=self.principal,
            inherit_permissions=False,
        )

        content = "Always follow [[Django Ninja Patterns]] when creating new API endpoints."
        resolved = extract_and_sync_wiki_links(source_art, content, self.principal)

        self.assertIn("Django Ninja Patterns", resolved)
        self.assertTrue(
            ArtifactRelationship.objects.filter(
                from_artifact=source_art,
                to_artifact=self.target_art,
                relation_type="references",
            ).exists()
        )
