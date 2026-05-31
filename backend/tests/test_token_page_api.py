from __future__ import annotations

import unittest

from fastapi.testclient import TestClient

from backend.app.main import app


class TokenPageApiTestCase(unittest.TestCase):
    TOKENS = ("fet", "eth", "pepe")

    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_health(self) -> None:
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_page_endpoint(self) -> None:
        for token in self.TOKENS:
            with self.subTest(token=token):
                response = self.client.get(f"/api/v1/tokens/{token}/page")
                self.assertEqual(response.status_code, 200)
                payload = response.json()
                self.assertEqual(payload["code"], "OK")
                self.assertEqual(payload["data"]["summary"]["token_symbol"], token.upper())
                self.assertEqual(payload["meta"]["token_symbol"], token.upper())
                self.assertIn("top_addresses", payload["data"])
                self.assertIn("address_profiles", payload["data"])

    def test_summary_contains_ai_summary(self) -> None:
        for token in self.TOKENS:
            with self.subTest(token=token):
                response = self.client.get(f"/api/v1/tokens/{token}/summary")
                self.assertEqual(response.status_code, 200)
                summary = response.json()["data"]
                self.assertIn("research_summary", summary)
                self.assertIn("risk_highlight", summary)
                self.assertIn("ai_summary", summary)
                self.assertIn("+08:00", summary["as_of_date"])

    def test_top_addresses_sorting(self) -> None:
        response = self.client.get(
            "/api/v1/tokens/fet/top-addresses",
            params={"limit": 3, "sort_by": "position_value_usd", "order": "desc"},
        )
        self.assertEqual(response.status_code, 200)
        items = response.json()["data"]["items"]
        self.assertEqual(len(items), 3)
        self.assertGreaterEqual(items[0]["position_value_usd"], items[1]["position_value_usd"])

    def test_page_freshness_contains_ai_summary_time(self) -> None:
        for token in self.TOKENS:
            with self.subTest(token=token):
                response = self.client.get(f"/api/v1/tokens/{token}/page")
                self.assertEqual(response.status_code, 200)
                freshness = response.json()["data"]["freshness"]
                self.assertIn("ai_summary_generated_at", freshness)
                self.assertIn("price_cache_generated_at", freshness)
                self.assertIn("price_cache_last_updated_at", freshness)

    def test_invalid_token_returns_400(self) -> None:
        response = self.client.get("/api/v1/tokens/abc/page")
        self.assertEqual(response.status_code, 400)
        detail = response.json()["detail"]
        self.assertEqual(detail["code"], "TOKEN_NOT_SUPPORTED")


if __name__ == "__main__":
    unittest.main()
