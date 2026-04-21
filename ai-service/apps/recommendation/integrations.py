from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


def _safe_json_request(
    url: str,
    method: str = "GET",
    payload: dict | None = None,
    token: str = "",
    timeout_seconds: float | None = None,
):
    body = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url=url, method=method, headers=headers, data=body)
    timeout = timeout_seconds
    if timeout is None:
        timeout = float(getattr(settings, "AI_UPSTREAM_TIMEOUT_SECONDS", 3.0))
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.getcode(), json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
        return None, None


class UserServiceClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def get_housing_preferences(self, user_id: int) -> dict | None:
        code, payload = _safe_json_request(f"{self.base_url}/users/{user_id}/preferences/housing", token=self.token)
        if code != 200 or not isinstance(payload, dict):
            return None
        return payload

    def get_profile(self, user_id: int) -> dict | None:
        code, payload = _safe_json_request(f"{self.base_url}/users/{user_id}/profile", token=self.token)
        if code != 200 or not isinstance(payload, dict):
            return None
        return payload


class HousingDataClient:
    def __init__(self, housing_base_url: str, search_base_url: str, token: str = ""):
        self.housing_base_url = housing_base_url.rstrip("/")
        self.search_base_url = search_base_url.rstrip("/")
        self.token = token

    def get_indexed_units(self) -> list[dict]:
        code, payload = _safe_json_request(f"{self.search_base_url}/search/housing?page=1&page_size=100", token=self.token)
        if code == 200 and isinstance(payload, dict):
            results = payload.get("results", [])
            if isinstance(results, list) and results:
                return results
        # fallback to housing service listings
        code, payload = _safe_json_request(f"{self.housing_base_url}/housing/units", token=self.token)
        if code == 200 and isinstance(payload, list):
            return payload
        return []


class NotificationClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def send_recommendation_ready(self, user_id: int, recommendation_count: int):
        if not self.token:
            return
        _safe_json_request(
            f"{self.base_url}/notifications/send",
            method="POST",
            payload={
                "user_id": user_id,
                "event_key": "ai.recommendations.ready",
                "context": {"user_id": user_id, "recommendation_count": recommendation_count},
            },
            token=self.token,
            timeout_seconds=float(getattr(settings, "AI_NOTIFICATION_TIMEOUT_SECONDS", 1.5)),
        )
