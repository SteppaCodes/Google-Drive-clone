from django.test import TestCase

from apps.accounts.models import Principal, User
from apps.artifacts.chunking import chunk_text_content
from apps.artifacts.models import Artifact, ArtifactChunk, ArtifactVersion, SkillArtifact


class ChunkingTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email="chunktest@lore.com", password="password123", first_name="Chunk", last_name="Test")
        self.principal = Principal.objects.create(kind="user", user=self.user)

        self.artifact = Artifact.objects.create(
            type="skill",
            title="Large System Skill",
            owner=self.principal,
            created_by=self.principal,
            inherit_permissions=False,
        )
        SkillArtifact.objects.create(artifact=self.artifact, skill_md_content="Skill content")
        self.version = ArtifactVersion.objects.create(
            artifact=self.artifact,
            version_number=1,
            created_by=self.principal,
            commit_message="Initial",
        )

    def test_chunk_text_content(self):
        sample_text = "Word " * 200  # 1000 characters
        num_chunks = chunk_text_content(self.artifact, self.version, sample_text)

        self.assertGreater(num_chunks, 1)
        self.assertEqual(ArtifactChunk.objects.filter(version=self.version).count(), num_chunks)
        self.assertEqual(self.artifact.embedding_status, "indexed")
