from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.recommendation.models import HousingRecommendationResult, RecommendationFeedback


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


class AIHousingRecommendationTests(TestCase):
    @patch("apps.recommendation.integrations.NotificationClient.send_recommendation_ready", return_value=None)
    @patch(
        "apps.recommendation.integrations.HousingDataClient.get_indexed_units",
        return_value=[
            {
                "unit_id": 1001,
                "price": "300.00",
                "location": "Damascus",
                "unit_type": "studio",
                "amenities_json": ["wifi", "laundry"],
            },
            {
                "unit_id": 1002,
                "price": "650.00",
                "location": "Aleppo",
                "unit_type": "shared",
                "amenities_json": ["parking"],
            },
            {
                "unit_id": 1003,
                "price": "450.00",
                "location": "Damascus",
                "unit_type": "studio",
                "amenities_json": ["wifi"],
            },
        ],
    )
    @patch(
        "apps.recommendation.integrations.UserServiceClient.get_housing_preferences",
        return_value={
            "min_budget": "200.00",
            "max_budget": "500.00",
            "preferred_locations": ["Damascus"],
            "preferred_types": ["studio"],
            "preferred_services": ["wifi"],
        },
    )
    def test_refresh_and_rank_deterministic(
        self,
        _preferences_mock,
        _housing_mock,
        _notification_mock,
    ):
        token = build_access_token(20, ["student"])
        response = self.client.post(
            "/ai/recommendations/housing/20/refresh",
            data={"top_n": 3},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["generated_count"], 2)
        self.assertEqual(response.json()["results"][0]["unit_id"], 1001)

        list_response = self.client.get(
            "/ai/recommendations/housing/20",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 2)
        self.assertEqual(list_response.json()[0]["unit_id"], 1001)

    def test_feedback_capture(self):
        token = build_access_token(30, ["student"])
        response = self.client.post(
            "/ai/recommendations/housing/30/feedback",
            data={"unit_id": 5001, "feedback_type": "like"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(RecommendationFeedback.objects.filter(user_id=30, unit_id=5001).exists())

    def test_explain_endpoint(self):
        HousingRecommendationResult.objects.create(
            user_id=40,
            unit_id=7001,
            similarity_score=0.91,
            rank=1,
            reasoning_json={"top_dimensions": [{"dimension": "location:damascus", "contribution": 1.0}]},
        )
        token = build_access_token(40, ["student"])
        response = self.client.get(
            "/ai/recommendations/housing/40/explain/7001",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unit_id"], 7001)
