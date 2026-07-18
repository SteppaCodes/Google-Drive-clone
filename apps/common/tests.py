from django.test import TestCase, Client
from apps.accounts.models import User

class NinjaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            password="testpassword",
            terms_agreement=True
        )

    def test_hello_endpoint_unauthenticated(self):
        response = self.client.get("/api/hello")
        self.assertEqual(response.status_code, 401)

    def test_hello_endpoint_authenticated(self):
        tokens = self.user.tokens()
        headers = {"HTTP_AUTHORIZATION": f"Bearer {tokens['access']}"}
        response = self.client.get("/api/hello", **headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to Lore API"})


