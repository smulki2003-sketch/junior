from __future__ import annotations

import json
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


class AdminServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def overview(self):
        return _safe_json_request(f"{self.base_url}/admin/dashboard/overview", token=self.service_token)

    def users(self, limit: int = 500, include_staff: bool = False):
        include_staff_value = "true" if include_staff else "false"
        return _safe_json_request(
            f"{self.base_url}/admin/users?limit={limit}&include_staff={include_staff_value}&include_profiles=false&include_booking_counts=false",
            token=self.service_token,
        )

    def bookings(self, limit: int = 500):
        return _safe_json_request(f"{self.base_url}/admin/bookings?limit={limit}&include_user_details=false", token=self.service_token)

    def payments(self, limit: int = 500):
        return _safe_json_request(f"{self.base_url}/admin/payments?limit={limit}&include_user_details=false", token=self.service_token)

    def complaints(self):
        return _safe_json_request(f"{self.base_url}/admin/complaints", token=self.service_token)


class BookingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def user_bookings(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/bookings/users/{user_id}", token=self.service_token)


class PaymentServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def payment(self, payment_id: int):
        return _safe_json_request(f"{self.base_url}/payments/{payment_id}", token=self.service_token)


class HousingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def list_units(self, moderation_status: str | None = None):
        suffix = ""
        if moderation_status:
            suffix = f"?moderation_status={moderation_status}"
        return _safe_json_request(f"{self.base_url}/housing/units{suffix}", token=self.service_token)


class NotificationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def user_notifications(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/notifications/users/{user_id}", token=self.service_token)


class AIRecommendationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def recommendations(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/ai/recommendations/housing/{user_id}", token=self.service_token)


class RoommateServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def matches(self, user_id: int):
        return _safe_json_request(f"{self.base_url}/ai/roommates/matches/{user_id}", token=self.service_token)


class ModerationServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def complaints(self):
        return _safe_json_request(f"{self.base_url}/moderation/complaints", token=self.service_token)
