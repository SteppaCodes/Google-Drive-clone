import hashlib

from django.core.files.base import ContentFile
from django.test import TestCase

from apps.accounts.models import AgentToken, User
from apps.files.models import File as FileModel
from apps.files.models import FileVersion
from apps.folders.models import Folder
from mcp_server import (
    authenticate_token,
    create_server_for_token,
    execute_list_directory,
    execute_read_document,
    execute_search_documents,
    execute_write_document,
)


class MCPServerLogicTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="password123",
            terms_agreement=True
        )
        self.folder_allowed = Folder.objects.create(name="Allowed", owner=self.user)
        self.folder_blocked = Folder.objects.create(name="Blocked", owner=self.user)

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

    def test_authenticate_token(self):
        # Valid token
        token_obj = authenticate_token(self.rw_raw_token)
        self.assertIsNotNone(token_obj)
        self.assertEqual(token_obj.id, self.rw_agent_token.id)

        # Invalid prefix token
        self.assertIsNone(authenticate_token("invalid_token_prefix"))

        # Non-existent token
        self.assertIsNone(authenticate_token("lore_agent_notreal123"))

    def test_execute_list_directory_restricted(self):
        # Create folder and file inside Allowed folder
        subfolder = Folder.objects.create(name="Sub", owner=self.user, folder=self.folder_allowed)
        FileModel.objects.create(
            owner=self.user,
            name="file.txt",
            file=ContentFile(b"Content", name="file.txt"),
            folder=self.folder_allowed
        )

        # List Allowed folder root (default)
        result = execute_list_directory(self.rw_agent_token)
        self.assertIn("Directory contents for: Allowed", result)
        self.assertIn("Subdirectories:", result)
        self.assertIn("file.txt", result)

        # List Allowed subfolder (allowed scope)
        result_sub = execute_list_directory(self.rw_agent_token, folder_id=str(subfolder.id))
        self.assertIn("Directory contents for: Sub", result_sub)

        # Try to list Blocked folder (outside sandbox)
        result_blocked = execute_list_directory(self.rw_agent_token, folder_id=str(self.folder_blocked.id))
        self.assertIn("Error: Access denied", result_blocked)

    def test_execute_read_document_restricted(self):
        # File inside Allowed folder
        allowed_file = FileModel.objects.create(
            owner=self.user,
            name="allowed.txt",
            file=ContentFile(b"allowed document data", name="allowed.txt"),
            folder=self.folder_allowed
        )

        # File inside Blocked folder
        blocked_file = FileModel.objects.create(
            owner=self.user,
            name="blocked.txt",
            file=ContentFile(b"blocked document data", name="blocked.txt"),
            folder=self.folder_blocked
        )

        # Read allowed file (should succeed)
        content = execute_read_document(self.rw_agent_token, str(allowed_file.id))
        self.assertEqual(content, "allowed document data")

        # Read blocked file (should be blocked)
        content_blocked = execute_read_document(self.rw_agent_token, str(blocked_file.id))
        self.assertIn("Error: Access denied", content_blocked)

    def test_execute_write_document_versioning(self):
        # Write new file (should succeed)
        res = execute_write_document(
            self.rw_agent_token,
            name="new_mcp_doc.txt",
            content="mcp line 1\n",
            folder_id=str(self.folder_allowed.id)
        )
        self.assertIn("created successfully", res)

        file_obj = FileModel.objects.get(name="new_mcp_doc.txt", folder=self.folder_allowed)
        self.assertEqual(file_obj.file.read(), b"mcp line 1\n")
        file_obj.file.seek(0)

        # Overwrite file content (should trigger FileVersion creation)
        res_overwrite = execute_write_document(
            self.rw_agent_token,
            name="new_mcp_doc.txt",
            content="mcp line 1\nmcp line 2 modified\n",
            folder_id=str(self.folder_allowed.id)
        )
        self.assertIn("overwritten successfully", res_overwrite)

        # Verify FileVersion exists and has correct diff
        version = FileVersion.objects.get(file=file_obj)
        self.assertEqual(version.version_number, 1)
        self.assertIn("+mcp line 2 modified", version.diff_content)

    def test_execute_search_documents(self):
        # Create folder and file
        FileModel.objects.create(
            owner=self.user,
            name="search_target.txt",
            file=ContentFile(b"UniqueSearchPhraseInsideFile", name="search_target.txt"),
            folder=self.folder_allowed
        )

        # Search by filename
        result = execute_search_documents(self.rw_agent_token, "target")
        self.assertIn("search_target.txt", result)

        # Search by content
        result_content = execute_search_documents(self.rw_agent_token, "UniqueSearchPhrase")
        self.assertIn("search_target.txt", result_content)

    def test_create_server_for_token(self):
        server = create_server_for_token(self.rw_agent_token)
        self.assertIsNotNone(server)
