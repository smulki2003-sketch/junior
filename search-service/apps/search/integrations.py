from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class HousingServiceClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0):
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    def fetch_units_for_indexing(self) -> list[dict]:
        request = Request(
            f"{self.base_url}/housing/units",
            method="GET",
            headers={"Accept": "application/json"},
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError):
            return []

        if not isinstance(payload, list):
            return []

        records: list[dict] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            unit_id = item.get("id")
            if not isinstance(unit_id, int):
                continue
            amenities_raw = item.get("amenities", [])
            amenities: list[str] = []
            if isinstance(amenities_raw, list):
                for amenity in amenities_raw:
                    if isinstance(amenity, dict):
                        name = str(amenity.get("name", "")).strip()
                    else:
                        name = str(amenity).strip()
                    if name:
                        amenities.append(name)

            records.append(
                {
                    "unit_id": unit_id,
                    "title": str(item.get("title", "")).strip(),
                    "description": str(item.get("description", "")).strip(),
                    "price": item.get("price", "0"),
                    "location": str(item.get("location", "")).strip(),
                    "unit_type": str(item.get("unit_type", "")).strip(),
                    "star_rating": item.get("star_rating", "3.0"),
                    "worker_count": item.get("worker_count", 1),
                    "max_occupancy": item.get("max_occupancy", 1),
                    "current_occupancy": item.get("current_occupancy", 0),
                    "amenities_json": amenities,
                    "is_available": bool(item.get("is_available", True)),
                }
            )

        return records
