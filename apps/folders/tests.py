from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.folders.models import Folder


class FolderAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            password="testpassword123",
            terms_agreement=True
        )
        self.client.force_authenticate(user=self.user)

    def test_create_root_folder(self):
        url = reverse("list-create-folder")
        data = {"name": "Root Folder"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["name"], "Root Folder")
        self.assertIsNone(response.data["data"]["folder"])

    def test_create_subfolder(self):
        parent = Folder.objects.create(name="Parent", owner=self.user)
        url = reverse("list-create-folder")
        data = {"name": "Subfolder", "folder": str(parent.id)}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["folder"], parent.id)

    def test_list_folders_paginated(self):
        for i in range(15):
            Folder.objects.create(name=f"Folder {i}", owner=self.user)

        url = reverse("list-create-folder")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("pagination", response.data)
        self.assertEqual(len(response.data["data"]), 10)
