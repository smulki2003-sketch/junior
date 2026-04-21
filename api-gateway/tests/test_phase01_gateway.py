from unittest.mock import patch

import httpx
from django.core.cache import cache
from django.test import TestCase

from apps.gateway.models import GatewayRateLimitPolicy, GatewayRouteRegistry


class GatewaySmokeTests(TestCase):
    def setUp(self):
        cache.clear()

    def test_health_endpoint(self):
        response = self.client.get("/gateway/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertIn("X-Request-ID", response.headers)

    def test_ready_endpoint(self):
        response = self.client.get("/gateway/ready")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ready")

    def test_routes_endpoint_lists_active_routes(self):
        response = self.client.get("/gateway/routes")
        self.assertEqual(response.status_code, 200)
        prefixes = {item["route_prefix"] for item in response.json()["routes"]}
        for expected in {
            "auth",
            "users",
            "housing",
            "search",
            "bookings",
            "payments",
            "notifications",
            "ai",
            "moderation",
            "admin",
            "reports",
        }:
            self.assertIn(expected, prefixes)

    @patch("apps.gateway.views.httpx.request")
    def test_proxy_forwards_auth_header_and_request_id(self, mock_request):
        captured = {}

        def fake_request(**kwargs):
            captured.update(kwargs)
            return httpx.Response(
                200,
                json={"ok": True},
                headers={"Content-Type": "application/json"},
            )

        mock_request.side_effect = fake_request
        response = self.client.get(
            "/api/v1/auth/session",
            {"foo": "bar"},
            HTTP_AUTHORIZATION="Bearer test-token",
            HTTP_X_USER_ID="42",
            HTTP_X_REQUEST_ID="custom-request-id",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"ok": True})
        self.assertEqual(captured["headers"]["Authorization"], "Bearer test-token")
        self.assertEqual(captured["headers"]["X-User-ID"], "42")
        self.assertEqual(captured["headers"]["X-Request-ID"], "custom-request-id")
        self.assertIn(("foo", "bar"), captured["params"])

    @patch("apps.gateway.views.httpx.request")
    def test_proxy_normalizes_upstream_error(self, mock_request):
        mock_request.return_value = httpx.Response(
            404,
            json={"detail": "not found"},
            headers={"Content-Type": "application/json"},
        )
        response = self.client.get("/api/v1/auth/missing")
        self.assertEqual(response.status_code, 404)
        payload = response.json()
        self.assertEqual(payload["error"]["code"], "upstream_http_error")
        self.assertEqual(payload["error"]["details"]["upstream_status"], 404)

    @patch("apps.gateway.views.httpx.request")
    def test_proxy_handles_unavailable_upstream(self, mock_request):
        mock_request.side_effect = httpx.RequestError("connection failed")
        response = self.client.get("/api/v1/auth/login")
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()["error"]["code"], "upstream_unavailable")

    @patch("apps.gateway.views.httpx.request")
    def test_rate_limit_by_ip(self, mock_request):
        mock_request.return_value = httpx.Response(
            200,
            json={"ok": True},
            headers={"Content-Type": "application/json"},
        )
        GatewayRateLimitPolicy.objects.update_or_create(
            scope=GatewayRateLimitPolicy.SCOPE_IP,
            defaults={"limit_per_minute": 1, "burst_limit": 0, "is_active": True},
        )
        first = self.client.get("/api/v1/auth/ping")
        second = self.client.get("/api/v1/auth/ping")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 429)

    @patch("apps.gateway.views.httpx.request")
    def test_route_registry_used_for_proxy_target(self, mock_request):
        GatewayRouteRegistry.objects.update_or_create(
            route_prefix="auth",
            defaults={
                "upstream_base_url": "http://localhost:9999/custom-auth",
                "is_active": True,
            },
        )

        captured = {}

        def fake_request(**kwargs):
            captured.update(kwargs)
            return httpx.Response(200, json={"ok": True}, headers={"Content-Type": "application/json"})

        mock_request.side_effect = fake_request
        response = self.client.get("/api/v1/auth/login")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(captured["url"], "http://localhost:9999/custom-auth/login")
