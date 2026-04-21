from __future__ import annotations


class ServiceEventAdapter:
    """Bridge integration for internal service event payloads."""

    def adapt_event_payload(self, event_type: str, payload: dict) -> dict:
        event_key = event_type.replace("_", ".")
        user_id = int(payload.get("user_id", 0))
        if user_id <= 0:
            raise ValueError("Service event payload requires a positive user_id.")
        return {
            "user_id": user_id,
            "event_key": event_key,
            "title": "",
            "body": "",
            "context": payload,
        }

