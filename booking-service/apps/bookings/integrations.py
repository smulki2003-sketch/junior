from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from django.conf import settings


def _safe_json_request(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    timeout_seconds: float = 5.0,
    extra_headers: dict | None = None,
):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if extra_headers:
        headers.update(extra_headers)
    request = Request(url=url, method=method, headers=headers, data=body)
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None, None


def _build_service_access_token() -> str:
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=5)
    payload = {
        "sub": "0",
        "email": "booking-service@internal.local",
        "roles": ["service"],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_SERVICE_JWT_SECRET, algorithm=settings.AUTH_SERVICE_JWT_ALGORITHM)


class HousingServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def is_unit_available(self, unit_id: int, start_date: date, end_date: date) -> bool:
        code, payload = _safe_json_request(f"{self.base_url}/housing/units/{unit_id}")
        if code != 200 or not isinstance(payload, dict):
            return False

        moderation_status = payload.get("moderation_status")
        if moderation_status != "approved":
            return False

        if payload.get("is_available") is False:
            return False

        availability_slots = payload.get("availability_slots", [])
        if not isinstance(availability_slots, list) or not availability_slots:
            return True

        # If housing service provides slots, we treat at least one overlapping "available" slot as valid.
        for slot in availability_slots:
            if not isinstance(slot, dict):
                continue
            slot_start = slot.get("start_date")
            slot_end = slot.get("end_date")
            if not slot_start or not slot_end:
                continue
            if slot.get("status") != "available":
                continue
            if str(start_date) >= str(slot_start) and str(end_date) <= str(slot_end):
                return True
        return False

    def adjust_unit_occupancy(self, unit_id: int, delta: int) -> bool:
        code, payload = _safe_json_request(
            f"{self.base_url}/housing/units/{unit_id}/occupancy",
            method="POST",
            payload={"delta": int(delta)},
        )
        if code != 200 or not isinstance(payload, dict):
            return False
        return True


class PaymentServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def create_payment_intent(
        self,
        booking_id: int,
        user_id: int,
        payer_bank_name: str,
        payer_account_number: str,
        amount: Decimal,
    ):
        token = _build_service_access_token()
        code, payload = _safe_json_request(
            f"{self.base_url}/payments/intents",
            method="POST",
            payload={
                "booking_id": booking_id,
                "user_id": user_id,
                "payer_bank_name": payer_bank_name,
                "payer_account_number": payer_account_number,
                "amount": str(amount),
            },
            extra_headers={"Authorization": f"Bearer {token}"},
        )
        if code not in {200, 201} or not isinstance(payload, dict):
            return None
        return payload.get("payment_intent_id")


class NotificationServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def publish_booking_event(self, event_type: str, payload: dict):
        token = _build_service_access_token()
        _safe_json_request(
            f"{self.base_url}/notifications/events",
            method="POST",
            payload={"event_type": event_type, "payload": payload},
            extra_headers={"Authorization": f"Bearer {token}"},
        )
