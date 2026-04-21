from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.test import TestCase

from apps.search.models import HousingSearchIndex, SavedFilter, SearchQueryLog


def build_access_token(user_id: int, roles: list[str] | None = None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": f"user{user_id}@example.com",
        "roles": roles or ["student"],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_SERVICE_JWT_SECRET, algorithm=settings.AUTH_SERVICE_JWT_ALGORITHM)


class SearchServiceIntegrationTests(TestCase):
    def setUp(self):
        HousingSearchIndex.objects.create(
            unit_id=101,
            title="Campus Studio",
            description="Quiet studio near library",
            price="450.00",
            location="Damascus",
            unit_type="studio",
            amenities_json=["wifi", "laundry"],
            is_available=True,
        )
        HousingSearchIndex.objects.create(
            unit_id=102,
            title="Shared Flat Downtown",
            description="Spacious flat",
            price="320.00",
            location="Aleppo",
            unit_type="shared",
            amenities_json=["wifi"],
            is_available=True,
        )
        HousingSearchIndex.objects.create(
            unit_id=103,
            title="Reserved Apartment",
            description="Temporarily unavailable",
            price="700.00",
            location="Damascus",
            unit_type="apartment",
            amenities_json=["parking"],
            is_available=False,
        )

    def test_search_filters_sorting_pagination_and_query_logging(self):
        response = self.client.get(
            "/search/housing?location=damascus&min_price=400&sort=price&page=1&page_size=10"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["pagination"]["total_results"], 1)
        self.assertEqual(payload["results"][0]["unit_id"], 101)
        self.assertEqual(SearchQueryLog.objects.count(), 1)

    def test_suggestions_returns_location_and_keywords(self):
        response = self.client.get("/search/housing/suggestions?q=wifi")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["query"], "wifi")
        self.assertIn("wifi", [item.lower() for item in payload["keywords"]])

    def test_index_sync_requires_admin_or_service_role(self):
        user_token = build_access_token(1, ["student"])
        denied_response = self.client.post(
            "/search/index/sync",
            data={
                "records": [
                    {
                        "unit_id": 201,
                        "title": "New Listing",
                        "description": "desc",
                        "price": "500.00",
                        "location": "Homs",
                        "unit_type": "studio",
                        "amenities_json": ["wifi"],
                        "is_available": True,
                    }
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {user_token}",
        )
        self.assertEqual(denied_response.status_code, 403)

        admin_token = build_access_token(2, ["admin"])
        allowed_response = self.client.post(
            "/search/index/sync",
            data={
                "records": [
                    {
                        "unit_id": 201,
                        "title": "New Listing",
                        "description": "desc",
                        "price": "500.00",
                        "location": "Homs",
                        "unit_type": "studio",
                        "amenities_json": ["wifi"],
                        "is_available": True,
                    }
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(allowed_response.status_code, 200)
        self.assertTrue(HousingSearchIndex.objects.filter(unit_id=201).exists())

    def test_saved_filters_owner_access_and_delete(self):
        owner_token = build_access_token(10, ["student"])
        create_response = self.client.post(
            "/search/saved-filters",
            data={
                "user_id": 10,
                "name": "Budget Damascus",
                "filters": {"min_price": "300.00", "max_price": "600.00", "location": "Damascus"},
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(create_response.status_code, 201)
        filter_id = create_response.json()["id"]

        list_response = self.client.get(
            "/search/saved-filters/10",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        other_user_token = build_access_token(11, ["student"])
        forbidden_list_response = self.client.get(
            "/search/saved-filters/10",
            HTTP_AUTHORIZATION=f"Bearer {other_user_token}",
        )
        self.assertEqual(forbidden_list_response.status_code, 403)

        delete_response = self.client.delete(
            f"/search/saved-filters/{filter_id}",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(delete_response.status_code, 204)
        self.assertFalse(SavedFilter.objects.filter(id=filter_id).exists())

