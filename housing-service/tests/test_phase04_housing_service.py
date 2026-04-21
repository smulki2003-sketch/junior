from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.test import TestCase

from apps.inventory.models import Amenity, HousingUnit


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


class HousingServiceIntegrationTests(TestCase):
    def test_admin_can_create_amenity(self):
        admin_token = build_access_token(1, ["admin"])
        response = self.client.post(
            "/housing/amenities",
            data={"name": "wifi", "is_active": True},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["name"], "wifi")

    def test_non_admin_cannot_create_amenity(self):
        user_token = build_access_token(2, ["student"])
        response = self.client.post(
            "/housing/amenities",
            data={"name": "parking", "is_active": True},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {user_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_owner_can_create_and_update_listing(self):
        amenity = Amenity.objects.create(name="wifi", is_active=True)
        owner_token = build_access_token(10, ["student"])

        create_response = self.client.post(
            "/housing/units",
            data={
                "title": "Studio near campus",
                "description": "Clean studio",
                "price": "500.00",
                "location": "Damascus",
                "unit_type": "studio",
                "amenity_ids": [amenity.id],
                "images": [{"image_url": "https://cdn.example.com/studio.png", "sort_order": 1}],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(create_response.status_code, 201)
        unit_id = create_response.json()["id"]

        patch_response = self.client.patch(
            f"/housing/units/{unit_id}",
            data={"price": "550.00"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(patch_response.status_code, 200)
        self.assertEqual(patch_response.json()["price"], "550.00")

    def test_public_cannot_view_pending_listing_detail(self):
        unit = HousingUnit.objects.create(
            owner_user_id=10,
            title="Pending Unit",
            description="desc",
            price="350.00",
            location="Damascus",
            unit_type="shared",
            moderation_status=HousingUnit.STATUS_PENDING,
        )

        public_response = self.client.get(f"/housing/units/{unit.id}")
        self.assertEqual(public_response.status_code, 404)

        owner_token = build_access_token(10, ["student"])
        owner_response = self.client.get(
            f"/housing/units/{unit.id}",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(owner_response.status_code, 200)

    def test_non_owner_cannot_modify_listing(self):
        unit = HousingUnit.objects.create(
            owner_user_id=30,
            title="Owner listing",
            description="desc",
            price="420.00",
            location="Homs",
            unit_type="studio",
            moderation_status=HousingUnit.STATUS_PENDING,
        )
        other_token = build_access_token(31, ["student"])
        response = self.client.patch(
            f"/housing/units/{unit.id}",
            data={"title": "Updated"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
        )
        self.assertEqual(response.status_code, 403)

    def test_availability_validation_for_overlap(self):
        unit = HousingUnit.objects.create(
            owner_user_id=40,
            title="Avail unit",
            description="desc",
            price="600.00",
            location="Aleppo",
            unit_type="shared",
            moderation_status=HousingUnit.STATUS_APPROVED,
        )
        owner_token = build_access_token(40, ["student"])
        overlap_response = self.client.put(
            f"/housing/units/{unit.id}/availability",
            data={
                "slots": [
                    {"start_date": "2026-05-01", "end_date": "2026-05-10", "status": "available"},
                    {"start_date": "2026-05-05", "end_date": "2026-05-20", "status": "unavailable"},
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(overlap_response.status_code, 400)

    def test_availability_success_and_invalid_date_range(self):
        unit = HousingUnit.objects.create(
            owner_user_id=50,
            title="Calendar unit",
            description="desc",
            price="700.00",
            location="Latakia",
            unit_type="apartment",
            moderation_status=HousingUnit.STATUS_APPROVED,
        )
        owner_token = build_access_token(50, ["student"])

        invalid_response = self.client.put(
            f"/housing/units/{unit.id}/availability",
            data={
                "slots": [
                    {"start_date": "2026-06-10", "end_date": "2026-06-01", "status": "available"},
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(invalid_response.status_code, 400)

        valid_response = self.client.put(
            f"/housing/units/{unit.id}/availability",
            data={
                "slots": [
                    {"start_date": "2026-06-01", "end_date": "2026-06-10", "status": "available"},
                    {"start_date": "2026-06-11", "end_date": "2026-06-20", "status": "unavailable"},
                ]
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(valid_response.status_code, 200)
        self.assertEqual(len(valid_response.json()["slots"]), 2)
