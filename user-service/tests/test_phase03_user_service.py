from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.test import TestCase


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


class UserServiceIntegrationTests(TestCase):
    def test_owner_can_update_and_read_profile(self):
        token = build_access_token(10, ["student"])
        update_response = self.client.put(
            "/users/10/profile",
            data={
                "first_name": "Ayman",
                "last_name": "Ali",
                "phone": "12345678",
                "university": "Damascus University",
                "governorate": "Damascus",
                "bio": "Computer science student",
                "media": [{"media_type": "avatar", "url": "https://cdn.example.com/avatar.png"}],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["first_name"], "Ayman")

        get_response = self.client.get("/users/10/profile", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["university"], "Damascus University")
        self.assertEqual(len(get_response.json()["media"]), 1)

    def test_non_owner_cannot_access_other_profile(self):
        owner_token = build_access_token(20, ["student"])
        self.client.put(
            "/users/20/profile",
            data={
                "first_name": "Owner",
                "last_name": "User",
                "phone": "98765432",
                "university": "University of Aleppo",
                "governorate": "Aleppo",
                "bio": "Bio",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )

        other_token = build_access_token(21, ["student"])
        get_response = self.client.get("/users/20/profile", HTTP_AUTHORIZATION=f"Bearer {other_token}")
        self.assertEqual(get_response.status_code, 403)

    def test_admin_can_manage_other_user_profile(self):
        admin_token = build_access_token(1, ["admin"])
        update_response = self.client.put(
            "/users/30/profile",
            data={
                "first_name": "Managed",
                "last_name": "Student",
                "phone": "123123123",
                "university": "Damascus University",
                "governorate": "Damascus",
                "bio": "Managed by admin",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["university"], "Damascus University")

    def test_housing_preferences_validate_budget_range(self):
        token = build_access_token(40)
        invalid_response = self.client.put(
            "/users/40/preferences/housing",
            data={
                "min_budget": "500.00",
                "max_budget": "300.00",
                "preferred_locations": ["Damascus"],
                "preferred_types": ["studio"],
                "preferred_services": ["wifi"],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(invalid_response.status_code, 400)

        valid_response = self.client.put(
            "/users/40/preferences/housing",
            data={
                "min_budget": "300.00",
                "max_budget": "800.00",
                "preferred_locations": ["Damascus"],
                "preferred_types": ["studio"],
                "preferred_services": ["wifi", "laundry"],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(valid_response.status_code, 200)

    def test_lifestyle_scores_must_be_between_one_and_five(self):
        token = build_access_token(50)
        bad_response = self.client.put(
            "/users/50/preferences/lifestyle",
            data={
                "quietness_score": 6,
                "cleanliness_score": 3,
                "sleep_schedule_score": 2,
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(bad_response.status_code, 400)

        ok_response = self.client.put(
            "/users/50/preferences/lifestyle",
            data={
                "quietness_score": 4,
                "cleanliness_score": 5,
                "sleep_schedule_score": 2,
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(ok_response.status_code, 200)

    def test_profile_completion_endpoint(self):
        token = build_access_token(60)
        self.client.put(
            "/users/60/profile",
            data={
                "first_name": "Score",
                "last_name": "Test",
                "phone": "1234567",
                "university": "University of Aleppo",
                "governorate": "Aleppo",
                "bio": "Some bio",
                "media": [{"media_type": "avatar", "url": "https://cdn.example.com/a.png"}],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.client.put(
            "/users/60/preferences/housing",
            data={
                "min_budget": "200.00",
                "max_budget": "900.00",
                "preferred_locations": ["Aleppo"],
                "preferred_types": ["shared"],
                "preferred_services": ["wifi"],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.client.put(
            "/users/60/preferences/lifestyle",
            data={
                "quietness_score": 3,
                "cleanliness_score": 4,
                "sleep_schedule_score": 2,
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        completion_response = self.client.get(
            "/users/60/profile-completion",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(completion_response.status_code, 200)
        self.assertGreaterEqual(completion_response.json()["completion_percent"], 90)
