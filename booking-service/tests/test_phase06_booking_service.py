from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase, TransactionTestCase

from apps.bookings.models import Booking, BookingStatusHistory


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


class BookingServiceIntegrationTests(TestCase):
    @patch("apps.bookings.integrations.NotificationServiceClient.publish_booking_event", return_value=None)
    @patch("apps.bookings.integrations.PaymentServiceClient.create_payment_intent", return_value="pi_123")
    @patch("apps.bookings.integrations.HousingServiceClient.adjust_unit_occupancy", return_value=True)
    @patch("apps.bookings.integrations.HousingServiceClient.is_unit_available", return_value=True)
    def test_create_booking_and_fetch_detail(
        self,
        _availability_mock,
        _occupancy_mock,
        _payment_mock,
        _notification_mock,
    ):
        token = build_access_token(10, ["student"])
        create_response = self.client.post(
            "/bookings",
            data={
                "unit_id": 501,
                "start_date": "2026-06-10",
                "end_date": "2026-06-20",
                "total_price": "1200.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(create_response.status_code, 201)
        booking_id = create_response.json()["id"]
        self.assertEqual(create_response.json()["status"], "pending")

        detail_response = self.client.get(
            f"/bookings/{booking_id}",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.json()["payment_intent_id"], "pi_123")

    @patch("apps.bookings.integrations.NotificationServiceClient.publish_booking_event", return_value=None)
    @patch("apps.bookings.integrations.PaymentServiceClient.create_payment_intent", return_value=None)
    @patch("apps.bookings.integrations.HousingServiceClient.adjust_unit_occupancy", return_value=True)
    @patch("apps.bookings.integrations.HousingServiceClient.is_unit_available", return_value=True)
    def test_overlap_booking_is_rejected(
        self,
        _availability_mock,
        _occupancy_mock,
        _payment_mock,
        _notification_mock,
    ):
        token = build_access_token(11, ["student"])
        self.client.post(
            "/bookings",
            data={
                "unit_id": 777,
                "start_date": "2026-07-01",
                "end_date": "2026-07-10",
                "total_price": "800.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        overlap_response = self.client.post(
            "/bookings",
            data={
                "unit_id": 777,
                "start_date": "2026-07-05",
                "end_date": "2026-07-12",
                "total_price": "850.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(overlap_response.status_code, 409)

    @patch("apps.bookings.integrations.NotificationServiceClient.publish_booking_event", return_value=None)
    @patch("apps.bookings.integrations.PaymentServiceClient.create_payment_intent", return_value=None)
    @patch("apps.bookings.integrations.HousingServiceClient.adjust_unit_occupancy", return_value=True)
    @patch("apps.bookings.integrations.HousingServiceClient.is_unit_available", return_value=True)
    def test_status_update_cancel_and_timeline(
        self,
        _availability_mock,
        _occupancy_mock,
        _payment_mock,
        _notification_mock,
    ):
        owner_token = build_access_token(12, ["student"])
        create_response = self.client.post(
            "/bookings",
            data={
                "unit_id": 888,
                "start_date": "2026-08-01",
                "end_date": "2026-08-10",
                "total_price": "600.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        booking_id = create_response.json()["id"]

        admin_token = build_access_token(1, ["admin"])
        status_response = self.client.patch(
            f"/bookings/{booking_id}/status",
            data={"status": "confirmed"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "confirmed")

        cancel_response = self.client.post(
            f"/bookings/{booking_id}/cancel",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(cancel_response.status_code, 200)
        self.assertEqual(cancel_response.json()["status"], "cancelled")

        timeline_response = self.client.get(
            f"/bookings/{booking_id}/timeline",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(timeline_response.status_code, 200)
        self.assertEqual(len(timeline_response.json()), 3)

    @patch("apps.bookings.integrations.NotificationServiceClient.publish_booking_event", return_value=None)
    @patch("apps.bookings.integrations.PaymentServiceClient.create_payment_intent", return_value=None)
    @patch("apps.bookings.integrations.HousingServiceClient.adjust_unit_occupancy", return_value=True)
    @patch("apps.bookings.integrations.HousingServiceClient.is_unit_available", return_value=True)
    def test_user_booking_history_access_control(
        self,
        _availability_mock,
        _occupancy_mock,
        _payment_mock,
        _notification_mock,
    ):
        owner_token = build_access_token(15, ["student"])
        self.client.post(
            "/bookings",
            data={
                "unit_id": 901,
                "start_date": "2026-09-01",
                "end_date": "2026-09-03",
                "total_price": "300.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )

        owner_history = self.client.get("/bookings/users/15", HTTP_AUTHORIZATION=f"Bearer {owner_token}")
        self.assertEqual(owner_history.status_code, 200)
        self.assertEqual(len(owner_history.json()), 1)

        other_token = build_access_token(16, ["student"])
        denied_history = self.client.get("/bookings/users/15", HTTP_AUTHORIZATION=f"Bearer {other_token}")
        self.assertEqual(denied_history.status_code, 403)


class BookingConcurrencyTests(TransactionTestCase):
    reset_sequences = True

    @patch("apps.bookings.integrations.NotificationServiceClient.publish_booking_event", return_value=None)
    @patch("apps.bookings.integrations.PaymentServiceClient.create_payment_intent", return_value=None)
    @patch("apps.bookings.integrations.HousingServiceClient.adjust_unit_occupancy", return_value=True)
    @patch("apps.bookings.integrations.HousingServiceClient.is_unit_available", return_value=True)
    def test_concurrent_overlapping_requests_only_one_booking_created(
        self,
        _availability_mock,
        _occupancy_mock,
        _payment_mock,
        _notification_mock,
    ):
        token_one = build_access_token(20, ["student"])
        token_two = build_access_token(21, ["student"])

        first_response = self.client.post(
            "/bookings",
            data={
                "unit_id": 999,
                "start_date": "2026-10-01",
                "end_date": "2026-10-10",
                "total_price": "1000.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token_one}",
        )
        second_response = self.client.post(
            "/bookings",
            data={
                "unit_id": 999,
                "start_date": "2026-10-01",
                "end_date": "2026-10-10",
                "total_price": "1000.00",
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token_two}",
        )

        self.assertEqual(first_response.status_code, 201)
        self.assertEqual(second_response.status_code, 409)
        self.assertEqual(Booking.objects.count(), 1)
        self.assertEqual(BookingStatusHistory.objects.count(), 1)
