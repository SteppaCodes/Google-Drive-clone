import json

from django.test import TestCase
from ninja.testing import TestClient

from apps.accounts.models import User
from apps.folders.models import Folder
from lore.api import api


class FolderAPITests(TestCase):
    """
    Tests for the Folders Ninja API router mounted at /api/folders/.
    Uses Ninja's TestClient which bypasses the DRF authentication layer
    and exercises the LoreAuth bearer path directly.
    """

    def setUp(self):
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="testpassword123",
        )
        # Obtain a JWT token via the /api/auth/login endpoint
        self.client = TestClient(api)
        response = self.client.post(
            "/auth/login",
            json={"email": "john@example.com", "password": "testpassword123"},
        )
        self.assertEqual(response.status_code, 200, msg=f"Login failed: {response.json()}")
        # Login returns { status, message, data: { access_token, refresh_token, ... } }
        self.token = response.json()["data"]["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    # --- Create ---

    def test_create_root_folder(self):
        response = self.client.post(
            "/folders/",
            json={"name": "Root Folder"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 201, msg=response.json())
        data = response.json()
        self.assertEqual(data["name"], "Root Folder")
        self.assertIsNone(data["parent_folder_id"])

    def test_create_subfolder(self):
        parent = Folder.objects.create(name="Parent", owner=self.user)
        response = self.client.post(
            "/folders/",
            json={"name": "Subfolder", "parent_folder_id": str(parent.id)},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 201, msg=response.json())
        data = response.json()
        self.assertEqual(data["name"], "Subfolder")
        self.assertEqual(data["parent_folder_id"], str(parent.id))

    def test_create_folder_unauthenticated(self):
        response = self.client.post("/folders/", json={"name": "Ghost"})
        self.assertEqual(response.status_code, 401)

    # --- List ---

    def test_list_root_folders(self):
        for i in range(5):
            Folder.objects.create(name=f"Folder {i}", owner=self.user)
        response = self.client.get("/folders/", headers=self.headers)
        self.assertEqual(response.status_code, 200, msg=response.json())
        data = response.json()
        self.assertEqual(len(data), 5)

    def test_list_root_folders_query_filter(self):
        Folder.objects.create(name="Alpha", owner=self.user)
        Folder.objects.create(name="Beta", owner=self.user)
        response = self.client.get("/folders/?query=alph", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["name"], "Alpha")

    def test_list_subfolders_by_parent(self):
        parent = Folder.objects.create(name="Parent", owner=self.user)
        Folder.objects.create(name="Child A", owner=self.user, folder=parent)
        Folder.objects.create(name="Child B", owner=self.user, folder=parent)
        url = f"/folders/?parent_folder_id={parent.id}"
        response = self.client.get(url, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 2)

    # --- Get detail & contents ---

    def test_get_folder(self):
        folder = Folder.objects.create(name="My Folder", owner=self.user)
        response = self.client.get(f"/folders/{folder.id}", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "My Folder")

    def test_get_folder_contents(self):
        folder = Folder.objects.create(name="Docs", owner=self.user)
        Folder.objects.create(name="Sub", owner=self.user, folder=folder)
        response = self.client.get(f"/folders/{folder.id}/contents", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("folder", data)
        self.assertIn("subfolders", data)
        self.assertIn("file_ids", data)
        self.assertEqual(len(data["subfolders"]), 1)

    def test_get_folder_not_found(self):
        import uuid
        response = self.client.get(f"/folders/{uuid.uuid4()}", headers=self.headers)
        self.assertEqual(response.status_code, 404)

    # --- Update ---

    def test_rename_folder(self):
        folder = Folder.objects.create(name="Old Name", owner=self.user)
        response = self.client.patch(
            f"/folders/{folder.id}",
            json={"name": "New Name"},
            headers=self.headers,
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["name"], "New Name")

    # --- Delete ---

    def test_delete_folder(self):
        folder = Folder.objects.create(name="Temp", owner=self.user)
        response = self.client.delete(f"/folders/{folder.id}", headers=self.headers)
        self.assertEqual(response.status_code, 204)
        self.assertFalse(Folder.objects.filter(id=folder.id).exists())

    def test_cannot_access_other_users_folder(self):
        """BOLA: another user's folder must return 404 (not 403) to avoid leaking existence."""
        other = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="pass123",
        )
        folder = Folder.objects.create(name="Private", owner=other)
        response = self.client.get(f"/folders/{folder.id}", headers=self.headers)
        self.assertEqual(response.status_code, 404)
