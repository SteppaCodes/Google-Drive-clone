from django.test import TestCase, Client
from apps.accounts.models import User, AgentToken

class AccountsNinjaAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_data = {
            "first_name": "Agent",
            "last_name": "Tester",
            "email": "agent.tester@example.com",
            "password": "strongpassword123",
            "terms_agreement": True,
        }
        self.login_data = {
            "email": "agent.tester@example.com",
            "password": "strongpassword123",
        }

    def test_auth_and_token_flow(self):
        # 1. Register User
        res = self.client.post(
            "/api/auth/register",
            data=self.register_data,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.json()["status"], "success")

        # 2. Login User to get JWT
        res = self.client.post(
            "/api/auth/login",
            data=self.login_data,
            content_type="application/json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["status"], "success")
        
        jwt_access_token = res.json()["data"]["access_token"]
        headers = {"HTTP_AUTHORIZATION": f"Bearer {jwt_access_token}"}

        # 3. Create Agent Token
        token_data = {
            "description": "Local test agent key",
            "scope": "read_write",
        }
        res = self.client.post(
            "/api/auth/tokens",
            data=token_data,
            content_type="application/json",
            **headers,
        )
        self.assertEqual(res.status_code, 201)
        
        token_id = res.json()["id"]
        agent_token_key = res.json()["token"]
        self.assertTrue(agent_token_key.startswith("lore_agent_"))

        # 4. List Agent Tokens
        res = self.client.get("/api/auth/tokens", **headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["id"], token_id)

        # 5. Authenticate with Agent Token key on Hello Endpoint
        agent_headers = {"HTTP_AUTHORIZATION": f"Bearer {agent_token_key}"}
        res = self.client.get("/api/hello", **agent_headers)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"message": "Welcome to Lore API"})

        # 6. Revoke Agent Token
        res = self.client.delete(f"/api/auth/tokens/{token_id}", **headers)
        self.assertEqual(res.status_code, 204)

        # 7. Verify Revoked Agent Token fails authentication
        res = self.client.get("/api/hello", **agent_headers)
        self.assertEqual(res.status_code, 401)
