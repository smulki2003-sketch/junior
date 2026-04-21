from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from django.conf import settings


def _safe_json_request(url: str, method: str = "GET", payload: dict | None = None, token: str = ""):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url=url, method=method, headers=headers, data=body)
    try:
        with urlopen(request, timeout=5.0) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None, None


def _build_service_access_token() -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    payload = {
        "sub": "0",
        "email": "payment-service@internal.local",
        "roles": ["service"],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_SERVICE_JWT_SECRET, algorithm=settings.AUTH_SERVICE_JWT_ALGORITHM)


class BookingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token or _build_service_access_token()

    def update_booking_status(self, booking_id: int, booking_status: str):
        return _safe_json_request(
            f"{self.base_url}/bookings/{booking_id}/status",
            method="PATCH",
            payload={"status": booking_status},
            token=self.service_token,
        )


class NotificationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token or _build_service_access_token()

    def send_payment_notification(self, user_id: int, event_key: str, context: dict):
        _safe_json_request(
            f"{self.base_url}/notifications/send",
            method="POST",
            payload={"user_id": user_id, "event_key": event_key, "context": context},
            token=self.service_token,
        )
