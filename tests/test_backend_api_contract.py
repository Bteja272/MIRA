import unittest

from fastapi.testclient import (
    TestClient,
)

from app.main import app
from app.schemas.query import (
    QueryRequest,
)


class BackendAPIContractTests(
    unittest.TestCase
):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(
            app
        )

    def test_root_contract(self):
        response = self.client.get(
            "/"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertIn(
            "version",
            payload,
        )

        self.assertEqual(
            payload["documentation"],
            "/docs",
        )

    def test_health_contract(self):
        response = self.client.get(
            "/health"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        payload = response.json()

        self.assertEqual(
            payload["status"],
            "ok",
        )

        self.assertIn(
            "application",
            payload,
        )

    def test_openapi_contains_backend_routes(self):
        response = self.client.get(
            "/openapi.json"
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        paths = response.json()[
            "paths"
        ]

        required_paths = {
            "/auth/register",
            "/auth/login",
            "/auth/me",
            "/ingest",
            "/query",
            "/documents",
            "/documents/{document_id}",
            "/documents/{document_id}/extract",
            "/documents/{document_id}/extraction",
        }

        self.assertTrue(
            required_paths.issubset(
                paths.keys()
            )
        )

    def test_openapi_declares_extraction_tag(self):
        response = self.client.get(
            "/openapi.json"
        )

        tags = {
            tag["name"]
            for tag in (
                response.json()
                .get("tags", [])
            )
        }

        self.assertIn(
            "extractions",
            tags,
        )

    def test_cors_allows_vite_origin(self):
        response = self.client.options(
            "/health",
            headers={
                "Origin": (
                    "http://localhost:5173"
                ),
                "Access-Control-Request-Method": (
                    "GET"
                ),
            },
        )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.headers.get(
                "access-control-allow-origin"
            ),
            "http://localhost:5173",
        )

    def test_security_headers_are_present(self):
        response = self.client.get(
            "/health"
        )

        self.assertEqual(
            response.headers.get(
                "cache-control"
            ),
            "no-store",
        )

        self.assertEqual(
            response.headers.get(
                "x-content-type-options"
            ),
            "nosniff",
        )

        self.assertEqual(
            response.headers.get(
                "x-frame-options"
            ),
            "DENY",
        )

    def test_query_request_normalizes_ids(self):
        request = QueryRequest(
            query="  Explain the report.  ",
            document_id=" doc-1 ",
            document_ids=[
                "doc-1",
                " doc-2 ",
                "",
            ],
        )

        self.assertEqual(
            request.query,
            "Explain the report.",
        )

        self.assertEqual(
            request.document_ids,
            [
                "doc-1",
                "doc-2",
            ],
        )


if __name__ == "__main__":
    unittest.main()