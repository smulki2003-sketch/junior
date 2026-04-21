from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


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


class NotificationClient:
    def __init__(self, base_url: str, token: str = ""):
        self.base_url = base_url.rstrip("/")
        self.token = token

    def send_matches_ready(self, user_id: int, candidate_count: int):
        if not self.token:
            return
        _safe_json_request(
            f"{self.base_url}/notifications/send",
            method="POST",
            payload={
                "user_id": user_id,
                "event_key": "ai.roommate.matches.ready",
                "context": {"user_id": user_id, "candidate_count": candidate_count},
            },
            token=self.token,
        )
