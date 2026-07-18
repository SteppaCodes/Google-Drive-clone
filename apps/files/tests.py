from datetime import timedelta
import hashlib
from django.core.files.base import ContentFile
from django.test import TestCase, Client
from django.utils import timezone
from apps.accounts.models import User, AgentToken
from apps.folders.models import Folder
from apps.files.models import File as FileModel, FileVersion, Comment

class FilesNinjaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="password123",
            terms_agreement=True
        )
        self.folder_allowed = Folder.objects.create(name="AllowedFolder", owner=self.user)
        self.folder_blocked = Folder.objects.create(name="BlockedFolder", owner=self.user)

        # Standard JWT Authentication
        self.user_tokens = self.user.tokens()
        self.user_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.user_tokens['access']}"}

        # Hardened Read-Write Agent Token restricted to AllowedFolder
        self.rw_raw_token = "lore_agent_rw1234567890abcdef"
        rw_hash = hashlib.sha256(self.rw_raw_token.encode()).hexdigest()
        self.rw_agent_token = AgentToken.objects.create(
            user=self.user,
            token_hash=rw_hash,
            token_prefix=self.rw_raw_token[:20],
            description="RW Agent Key",
            scope="read_write",
            restricted_folder=self.folder_allowed
        )
        self.rw_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.rw_raw_token}"}

        # Hardened Read-Only Agent Token restricted to AllowedFolder
        self.ro_raw_token = "lore_agent_ro1234567890abcdef"
        ro_hash = hashlib.sha256(self.ro_raw_token.encode()).hexdigest()
        self.ro_agent_token = AgentToken.objects.create(
            user=self.user,
            token_hash=ro_hash,
            token_prefix=self.ro_raw_token[:20],
            description="RO Agent Key",
            scope="read_only",
            restricted_folder=self.folder_allowed
        )
        self.ro_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.ro_raw_token}"}

    def test_file_upload_and_version_diffing(self):
        # 1. Upload new file using human user
        file_data = ContentFile(b"line 1\nline 2\n", name="test_doc.txt")
        res = self.client.post(
            "/api/files/upload",
            data={"file": file_data},
            **self.user_headers
        )
        self.assertEqual(res.status_code, 201)
        file_id = res.json()["id"]

        # 2. Overwrite the file with modified content (produces version diff)
        modified_file_data = ContentFile(b"line 1\nline 2 modified\nline 3\n", name="test_doc.txt")
        res = self.client.post(
            "/api/files/upload",
            data={"file": modified_file_data},
            **self.user_headers
        )
        self.assertEqual(res.status_code, 201)

        # 3. Retrieve version history and check diff
        res = self.client.get(f"/api/files/{file_id}/versions", **self.user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["version_number"], 1)
        self.assertIn("+line 2 modified", res.json()[0]["diff_content"])

    def test_file_locking_mechanics(self):
        # Create a file
        file_data = ContentFile(b"test lock content", name="lock_test.txt")
        res = self.client.post("/api/files/upload", data={"file": file_data}, **self.user_headers)
        file_id = res.json()["id"]

        # 1. Lock the file
        res = self.client.post(f"/api/files/{file_id}/lock", **self.user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["locked_by_email"], self.user.email)

        # 2. Try to lock again (should fail)
        res = self.client.post(f"/api/files/{file_id}/lock", **self.user_headers)
        self.assertEqual(res.status_code, 400)

        # 3. Overwrite locked file by owner (should succeed)
        overwrite_data = ContentFile(b"owner content edit", name="lock_test.txt")
        res = self.client.post("/api/files/upload", data={"file": overwrite_data}, **self.user_headers)
        self.assertEqual(res.status_code, 201)

        # 4. Unlock the file
        res = self.client.post(f"/api/files/{file_id}/unlock", **self.user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsNone(res.json()["locked_by_email"])

    def test_agent_sandbox_folder_restrictions(self):
        # 1. Upload to AllowedFolder (should succeed)
        file_data = ContentFile(b"agent content", name="agent_allowed.txt")
        res = self.client.post(
            f"/api/files/upload?folder_id={self.folder_allowed.id}",
            data={"file": file_data},
            **self.rw_headers
        )
        self.assertEqual(res.status_code, 201)
        file_id = res.json()["id"]

        # 2. Upload to BlockedFolder (should be blocked)
        blocked_file_data = ContentFile(b"agent blocked content", name="agent_blocked.txt")
        res = self.client.post(
            f"/api/files/upload?folder_id={self.folder_blocked.id}",
            data={"file": blocked_file_data},
            **self.rw_headers
        )
        self.assertEqual(res.status_code, 403)

        # 3. Try to access list of files — should filter out BlockedFolder contents
        # Create a file in BlockedFolder as human user
        file_in_blocked = ContentFile(b"blocked doc", name="blocked_doc.txt")
        self.client.post(
            f"/api/files/upload?folder_id={self.folder_blocked.id}",
            data={"file": file_in_blocked},
            **self.user_headers
        )

        res = self.client.get("/api/files/", **self.rw_headers)
        self.assertEqual(res.status_code, 200)
        # Should only list the one in AllowedFolder
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["id"], str(file_id))

    def test_read_only_agent_token_scope(self):
        # Create file as human user in allowed folder
        file_data = ContentFile(b"read only test", name="read_only_test.txt")
        res = self.client.post(
            f"/api/files/upload?folder_id={self.folder_allowed.id}",
            data={"file": file_data},
            **self.user_headers
        )
        file_id = res.json()["id"]

        # 1. Read-only agent tries to read files (should succeed)
        res = self.client.get(f"/api/files/", **self.ro_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)

        # 2. Read-only agent tries to upload/write (should be rejected with 403)
        new_file_data = ContentFile(b"ro write attempt", name="ro_attempt.txt")
        res = self.client.post(
            f"/api/files/upload?folder_id={self.folder_allowed.id}",
            data={"file": new_file_data},
            **self.ro_headers
        )
        self.assertEqual(res.status_code, 403)

        # 3. Read-only agent tries to lock file (should be rejected with 403)
        res = self.client.post(f"/api/files/{file_id}/lock", **self.ro_headers)
        self.assertEqual(res.status_code, 403)
