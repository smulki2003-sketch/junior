from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def _safe_json_request(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    token: str = "",
    timeout_seconds: float = 5.0,
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


class HousingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def fetch_unit(self, unit_id: int):
        return _safe_json_request(
            f"{self.base_url}/housing/units/{unit_id}",
            method="GET",
            token=self.service_token,
        )

    def reject_listing(self, unit_id: int, reason: str):
        return _safe_json_request(
            f"{self.base_url}/housing/units/{unit_id}",
            method="PATCH",
            payload={"moderation_status": "rejected", "description": f"[moderation] {reason}"},
            token=self.service_token,
        )


class BookingServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def fetch_booking(self, booking_id: int):
        return _safe_json_request(
            f"{self.base_url}/bookings/{booking_id}",
            method="GET",
            token=self.service_token,
        )

    def cancel_booking(self, booking_id: int):
        return _safe_json_request(
            f"{self.base_url}/bookings/{booking_id}/status",
            method="PATCH",
            payload={"status": "cancelled"},
            token=self.service_token,
        )


class AdminServiceClient:
    def __init__(self, base_url: str, service_token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.service_token = service_token

    def suspend_user(self, user_id: int, reason: str):
        return _safe_json_request(
            f"{self.base_url}/admin/users/{user_id}/status",
            method="PATCH",
            payload={"status": "suspended", "reason": reason},
            token=self.service_token,
        )


class EnforcementGateway:
    def __init__(
        self,
        admin_client: AdminServiceClient,
        housing_client: HousingServiceClient,
        booking_client: BookingServiceClient,
    ):
        self.admin_client = admin_client
        self.housing_client = housing_client
        self.booking_client = booking_client

    def apply_action(self, action_type: str, target_type: str, target_id: int, reason: str):
        if action_type == "warn":
            return {"ok": True, "action": "warn", "target_type": target_type, "target_id": target_id}
        if action_type == "suspend" and target_type == "user":
            code, payload = self.admin_client.suspend_user(target_id, reason)
            return {"ok": code in {200, 202}, "status_code": code, "payload": payload}
        if action_type == "reject_listing" and target_type == "housing":
            code, payload = self.housing_client.reject_listing(target_id, reason)
            return {"ok": code in {200, 202}, "status_code": code, "payload": payload}
        if action_type == "suspend" and target_type == "booking":
            code, payload = self.booking_client.cancel_booking(target_id)
            return {"ok": code in {200, 202}, "status_code": code, "payload": payload}
        return {"ok": False, "error": "unsupported_action_target_pair"}

