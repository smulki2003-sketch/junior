from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _safe_json_request(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    token: str = "",
    timeout_seconds: float = 6.0,
):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url=url, method=method, headers=headers, data=body)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None, None


class UserServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def fetch_profile(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/users/{user_id}/profile", token=self.service_token)


class AuthServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def update_user_roles(self, user_id: int, roles: list[str]):
        return _safe_json_request(
            f"{self.base_url}/auth/users/{user_id}/roles",
            method="PATCH",
            payload={"roles": roles},
            token=self.service_token,
        )

    def list_users(self, user_ids: list[int] | None = None, limit: int = 100):
        params = {"limit": str(limit)}
        if user_ids:
            params["user_ids"] = ",".join(str(user_id) for user_id in user_ids)
        query = urlencode(params)
        return _safe_json_request(f"{self.base_url}/auth/users?{query}", token=self.service_token)


class HousingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def list_pending(self):
        return _safe_json_request(f"{self.base_url}/housing/units?moderation_status=pending", token=self.service_token)

    def list_by_status(self, moderation_status: str):
        query = urlencode({"moderation_status": moderation_status})
        return _safe_json_request(f"{self.base_url}/housing/units?{query}", token=self.service_token)

    def update_approval(self, unit_id: int, approval: str, reason: str = ""):
        patch_payload = {"moderation_status": approval}
        if reason:
            patch_payload["description"] = f"[admin-moderation] {reason}"
        return _safe_json_request(
            f"{self.base_url}/housing/units/{unit_id}",
            method="PATCH",
            payload=patch_payload,
            token=self.service_token,
        )


class BookingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def fetch_booking(self, booking_id: int):
        return _safe_json_request(f"{self.base_url}/bookings/{booking_id}", token=self.service_token)

    def list_user_bookings(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/bookings/users/{user_id}", token=self.service_token)

    def list_bookings(self, booking_ids: list[int] | None = None, user_id: int | None = None, limit: int = 200):
        params = {"limit": str(limit)}
        if booking_ids:
            params["booking_ids"] = ",".join(str(booking_id) for booking_id in booking_ids)
        if isinstance(user_id, int):
            params["user_id"] = str(user_id)
        query = urlencode(params)
        return _safe_json_request(f"{self.base_url}/bookings?{query}", token=self.service_token)

    def override_status(self, booking_id: int, status: str):
        return _safe_json_request(
            f"{self.base_url}/bookings/{booking_id}/status",
            method="PATCH",
            payload={"status": status},
            token=self.service_token,
        )


class PaymentServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def fetch_payment(self, payment_id: int):
        return _safe_json_request(f"{self.base_url}/payments/{payment_id}", token=self.service_token)

    def list_payments(
        self,
        payment_ids: list[int] | None = None,
        user_id: int | None = None,
        booking_id: int | None = None,
        limit: int = 200,
    ):
        params = {"limit": str(limit)}
        if payment_ids:
            params["payment_ids"] = ",".join(str(payment_id) for payment_id in payment_ids)
        if isinstance(user_id, int):
            params["user_id"] = str(user_id)
        if isinstance(booking_id, int):
            params["booking_id"] = str(booking_id)
        query = urlencode(params)
        return _safe_json_request(f"{self.base_url}/payments?{query}", token=self.service_token)


class NotificationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def send_notification(self, user_id: int, event_key: str, context: dict):
        return _safe_json_request(
            f"{self.base_url}/notifications/send",
            method="POST",
            payload={"user_id": user_id, "event_key": event_key, "context": context},
            token=self.service_token,
        )


class ModerationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def list_complaints(self):
        return _safe_json_request(f"{self.base_url}/moderation/complaints", token=self.service_token)


class RoommateServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def questionnaire(self):
        return _safe_json_request(f"{self.base_url}/ai/roommates/questionnaire", token=self.service_token)
