from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid

from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from django.http import JsonResponse

from .models import GatewayRateLimitPolicy, GatewayRequestLog


logger = logging.getLogger("gateway.request")


def get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def get_user_identifier(request) -> str | None:
    user_id_header = request.headers.get("X-User-ID")
    if user_id_header:
        return f"user:{user_id_header}"

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
        if token:
            digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
            return f"token:{digest}"
    return None


class RequestContextMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request._gateway_start_time = time.perf_counter()
        request._gateway_client_ip = get_client_ip(request)
        request._gateway_user_identifier = get_user_identifier(request)

        response = self.get_response(request)

        duration_ms = int((time.perf_counter() - request._gateway_start_time) * 1000)
        response["X-Request-ID"] = request.request_id

        log_payload = {
            "request_id": request.request_id,
            "method": request.method,
            "path": request.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": request._gateway_client_ip,
            "user_identifier": request._gateway_user_identifier,
        }
        logger.info(json.dumps(log_payload, separators=(",", ":")))

        if not request.path.startswith("/admin/"):
            try:
                GatewayRequestLog.objects.create(
                    request_id=request.request_id,
                    method=request.method,
                    path=request.path[:255],
                    status_code=response.status_code,
                    duration_ms=max(duration_ms, 0),
                    client_ip=request._gateway_client_ip,
                    user_identifier=request._gateway_user_identifier,
                )
            except DatabaseError:
                # During migrations/startup we intentionally avoid failing requests.
                pass

        return response


class RateLimitMiddleware:
    SKIP_PATH_PREFIXES = ("/gateway/health", "/gateway/ready", "/admin/")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._should_skip(request.path):
            return self.get_response(request)

        request_id = getattr(request, "request_id", None)
        ip_identifier = request._gateway_client_ip or "unknown-ip"
        user_identifier = request._gateway_user_identifier

        ip_check = self._check_limit("ip", ip_identifier, request_id)
        if ip_check is not None:
            return ip_check

        if user_identifier:
            user_check = self._check_limit("user", user_identifier, request_id)
            if user_check is not None:
                return user_check

        return self.get_response(request)

    @classmethod
    def _should_skip(cls, path: str) -> bool:
        return any(path.startswith(prefix) for prefix in cls.SKIP_PATH_PREFIXES)

    @staticmethod
    def _resolve_policy(scope: str) -> tuple[int, int]:
        defaults = settings.GATEWAY_DEFAULT_RATE_LIMITS[scope]
        try:
            policy = GatewayRateLimitPolicy.objects.filter(scope=scope, is_active=True).first()
            if policy:
                return policy.limit_per_minute, policy.burst_limit
        except DatabaseError:
            pass
        return defaults["limit_per_minute"], defaults["burst_limit"]

    def _check_limit(self, scope: str, identifier: str, request_id: str | None):
        minute_bucket = int(time.time() // 60)
        cache_key = f"gateway:rate:{scope}:{identifier}:{minute_bucket}"
        created = cache.add(cache_key, 1, timeout=120)
        if created:
            current_count = 1
        else:
            try:
                current_count = cache.incr(cache_key)
            except ValueError:
                cache.set(cache_key, 1, timeout=120)
                current_count = 1

        limit_per_minute, burst_limit = self._resolve_policy(scope)
        if current_count <= limit_per_minute + burst_limit:
            return None

        payload = {
            "error": {
                "code": "rate_limited",
                "message": f"Rate limit exceeded for {scope}.",
                "details": {
                    "scope": scope,
                    "limit_per_minute": limit_per_minute,
                    "burst_limit": burst_limit,
                },
            },
            "request_id": request_id,
        }
        response = JsonResponse(payload, status=429)
        response["Retry-After"] = "60"
        return response
