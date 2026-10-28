import unittest

from app import create_app, db


class ApiTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app({
            "TESTING": True,
            "SECRET_KEY": "test-only-secret-that-is-long-enough-32-bytes",
            "JWT_SECRET_KEY": "test-only-jwt-secret-that-is-long-enough-32-bytes",
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        })
        self.client = self.app.test_client()

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.engine.dispose()

    def register(self, email, name="Test User"):
        response = self.client.post("/api/auth/register", json={
            "name": name,
            "email": email,
            "password": "correct-horse-123",
        })
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()

    def auth_headers(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_health_and_login_flow(self):
        self.assertEqual(self.client.get("/api/health").get_json(), {"status": "ok"})
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

        account = self.register("login@example.com")
        response = self.client.post("/api/auth/login", json={
            "email": "LOGIN@example.com",
            "password": "correct-horse-123",
        })
        self.assertEqual(response.status_code, 200)
        token = response.get_json()["access_token"]
        profile = self.client.get("/api/auth/me", headers=self.auth_headers(token))
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.get_json()["user"]["id"], account["user"]["id"])
        bad_login = self.client.post("/api/auth/login", json={"email": "login@example.com", "password": "wrong"})
        self.assertEqual(bad_login.status_code, 401)

    def test_transactions_budget_dashboard_and_owner_isolation(self):
        alice = self.register("alice@example.com")
        bob = self.register("bob@example.com", "Other User")
        alice_headers = self.auth_headers(alice["access_token"])
        bob_headers = self.auth_headers(bob["access_token"])
        transaction = {
            "title": "Groceries", "amount": "42.50", "kind": "expense",
            "category": "Food & drink", "spent_on": "2026-10-20", "note": "weekly",
        }
        created = self.client.post("/api/transactions", json=transaction, headers=alice_headers)
        self.assertEqual(created.status_code, 201, created.get_json())
        transaction_id = created.get_json()["transaction"]["id"]

        self.assertEqual(self.client.patch(f"/api/transactions/{transaction_id}", json=transaction, headers=bob_headers).status_code, 404)
        self.assertEqual(self.client.delete(f"/api/transactions/{transaction_id}", headers=bob_headers).status_code, 404)

        budget = self.client.put("/api/budget", json={"month": "2026-10", "amount": 500}, headers=alice_headers)
        self.assertEqual(budget.status_code, 200)
        dashboard = self.client.get("/api/dashboard?month=2026-10", headers=alice_headers)
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(dashboard.get_json()["spent"], 42.5)
        self.assertEqual(dashboard.get_json()["budget"], 500.0)

        updated = dict(transaction, title="Updated groceries", amount="50")
        self.assertEqual(self.client.patch(f"/api/transactions/{transaction_id}", json=updated, headers=alice_headers).status_code, 200)
        self.assertEqual(self.client.delete(f"/api/transactions/{transaction_id}", headers=alice_headers).status_code, 200)

    def test_validation_and_csv_export(self):
        invalid_registration = self.client.post("/api/auth/register", json={"name": "X", "email": "bad", "password": "short"})
        self.assertEqual(invalid_registration.status_code, 400)
        account = self.register("csv@example.com")
        headers = self.auth_headers(account["access_token"])
        invalid = self.client.post("/api/transactions", json={"title": "Bad", "amount": -1}, headers=headers)
        self.assertEqual(invalid.status_code, 400)
        self.client.post("/api/transactions", json={
            "title": "=1+1", "amount": 1, "kind": "expense", "category": "Other",
            "spent_on": "2026-10-20", "note": "",
        }, headers=headers)
        exported = self.client.get("/api/export.csv", headers=headers)
        self.assertEqual(exported.status_code, 200)
        self.assertIn(b"'=1+1", exported.data)

    def test_cors_allows_vercel_origin(self):
        origin = "https://expense-tracker-two-omega-62.vercel.app"
        response = self.client.options("/api/auth/login", headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        })
        self.assertEqual(response.headers.get("Access-Control-Allow-Origin"), origin)


if __name__ == "__main__":
    unittest.main()
