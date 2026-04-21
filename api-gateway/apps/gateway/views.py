from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import httpx
from django.conf import settings
from django.db import DatabaseError, connections
from django.http import HttpResponse, JsonResponse
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .services import build_upstream_url, get_route_config, list_active_routes


def _request_id_from_request(request) -> str:
    return getattr(request, "request_id", "")


def _json_response(payload: Any, status: int = 200) -> JsonResponse:
    return JsonResponse(payload, status=status, safe=not isinstance(payload, list))


def _parse_upstream_payload(response: httpx.Response):
    content_type = response.headers.get("Content-Type", "")
    if "application/json" in content_type:
        try:
            return response.json(), content_type
        except ValueError:
            return {"raw": response.text}, "application/json"
    # Non-JSON payloads should be normalized to text for safe JSON wrapping in
    # error responses (upstream 4xx/5xx), while successful passthrough keeps
    # binary support through HttpResponse below.
    text_payload = response.text
    if text_payload:
        return text_payload, content_type
    return response.content.decode("utf-8", errors="replace"), content_type


class GatewayHealthView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        payload = {
            "status": "ok",
            "service": "api-gateway",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "request_id": _request_id_from_request(request),
        }
        return _json_response(payload)


class GatewayReadinessView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        db_ready = False
        error_message = None
        try:
            connections["default"].cursor().execute("SELECT 1")
            db_ready = True
        except DatabaseError as exc:
            error_message = str(exc)

        status_code = 200 if db_ready else 503
        payload = {
            "status": "ready" if db_ready else "not_ready",
            "checks": {
                "database": "ok" if db_ready else "failed",
            },
            "request_id": _request_id_from_request(request),
        }
        if error_message:
            payload["checks"]["database_error"] = error_message
        return _json_response(payload, status=status_code)


class GatewayRoutesView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        routes = list_active_routes()
        payload = {
            "routes": [
                {
                    "route_prefix": route.route_prefix,
                    "upstream_base_url": route.upstream_base_url,
                    "is_active": route.is_active,
                }
                for route in routes
            ],
            "request_id": _request_id_from_request(request),
        }
        return _json_response(payload)


class ProxyServiceView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]

    def get(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def post(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def put(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def patch(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def delete(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def options(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def head(self, request, service: str, subpath: str = ""):
        return self._proxy(request, service, subpath)

    def _proxy(self, request, service: str, subpath: str):
        route = get_route_config(service)
        if not route:
            return _json_response(
                {
                    "error": {
                        "code": "route_not_found",
                        "message": "No active route is configured for this service.",
                        "details": {"service": service},
                    },
                    "request_id": _request_id_from_request(request),
                },
                status=404,
            )

        upstream_url = build_upstream_url(route.upstream_base_url, subpath or "")
        headers = self._build_forward_headers(request)
        body = request.body if request.method not in {"GET", "HEAD"} else None

        try:
            upstream_params = []
            for key, values in request.GET.lists():
                for value in values:
                    upstream_params.append((key, value))

            upstream_response = httpx.request(
                method=request.method,
                url=upstream_url,
                headers=headers,
                params=upstream_params,
                content=body,
                timeout=settings.GATEWAY_UPSTREAM_TIMEOUT_SECONDS,
            )
        except httpx.RequestError as exc:
            return _json_response(
                {
                    "error": {
                        "code": "upstream_unavailable",
                        "message": "Unable to reach upstream service.",
                        "details": {"service": service, "reason": str(exc)},
                    },
                    "request_id": _request_id_from_request(request),
                },
                status=502,
            )

        if upstream_response.status_code >= 400:
            upstream_payload, _ = _parse_upstream_payload(upstream_response)
            return _json_response(
                {
                    "error": {
                        "code": "upstream_http_error",
                        "message": "Upstream service returned an error.",
                        "details": {
                            "service": service,
                            "upstream_status": upstream_response.status_code,
                            "upstream_response": upstream_payload,
                        },
                    },
                    "request_id": _request_id_from_request(request),
                },
                status=upstream_response.status_code,
            )

        upstream_payload, content_type = _parse_upstream_payload(upstream_response)
        if isinstance(upstream_payload, (dict, list)):
            return _json_response(upstream_payload, status=upstream_response.status_code)

        response = HttpResponse(
            upstream_payload,
            status=upstream_response.status_code,
            content_type=content_type or "application/octet-stream",
        )
        for header_name in ("Content-Disposition", "Location"):
            header_value = upstream_response.headers.get(header_name)
            if header_value:
                response[header_name] = header_value
        return response

    @staticmethod
    def _build_forward_headers(request) -> dict[str, str]:
        allowed_headers = {
            "authorization": "Authorization",
            "content-type": "Content-Type",
            "accept": "Accept",
            "x-request-id": "X-Request-ID",
            "x-user-id": "X-User-ID",
        }
        forwarded_headers = {}
        for header_name, header_value in request.headers.items():
            key = allowed_headers.get(header_name.lower())
            if key:
                forwarded_headers[key] = header_value

        forwarded_headers["X-Request-ID"] = _request_id_from_request(request)
        return forwarded_headers
