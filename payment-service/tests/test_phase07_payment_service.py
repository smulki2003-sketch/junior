from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.payments.models import PaymentIntent, PaymentRefund


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


class PaymentServiceIntegrationTests(TestCase):
    @patch("apps.payments.integrations.NotificationServiceClient.send_payment_notification", return_value=None)
    @patch("apps.payments.integrations.BookingServiceClient.update_booking_status", return_value=(200, {"ok": True}))
    def test_intent_creation_and_success_flow(self, _booking_mock, _notification_mock):
        service_token = build_access_token(1, ["service"])
        create_response = self.client.post(
            "/payments/intents",
            data={
                "booking_id": 11,
                "user_id": 22,
                "payer_bank_name": "Commercial Bank of Syria",
                "payer_account_number": "123456789",
                "amount": "120.00",
                "currency": "usd",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(create_response.status_code, 201)
        payment_id = create_response.json()["payment_intent_id"]

        success_response = self.client.post(
            f"/payments/{payment_id}/simulate-success",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(success_response.status_code, 200)
        self.assertEqual(success_response.json()["status"], "succeeded")

    @patch("apps.payments.integrations.NotificationServiceClient.send_payment_notification", return_value=None)
    @patch("apps.payments.integrations.BookingServiceClient.update_booking_status", return_value=(200, {"ok": True}))
    def test_failure_simulation(self, _booking_mock, _notification_mock):
        service_token = build_access_token(2, ["service"])
        payment = PaymentIntent.objects.create(booking_id=44, user_id=55, amount="90.00", currency="USD")
        response = self.client.post(
            f"/payments/{payment.id}/simulate-failure",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "failed")

    @patch("apps.payments.integrations.NotificationServiceClient.send_payment_notification", return_value=None)
    def test_refund_idempotency(self, _notification_mock):
        owner_token = build_access_token(10, ["student"])
        payment = PaymentIntent.objects.create(
            booking_id=77,
            user_id=10,
            amount="250.00",
            currency="USD",
            status=PaymentIntent.STATUS_SUCCEEDED,
        )
        first = self.client.post(
            f"/payments/{payment.id}/refund",
            data={"refund_amount": "40.00", "idempotency_key": "idem-1"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        second = self.client.post(
            f"/payments/{payment.id}/refund",
            data={"refund_amount": "40.00", "idempotency_key": "idem-1"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {owner_token}",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.status_code, 201)
        self.assertEqual(PaymentRefund.objects.count(), 1)

    @patch("apps.payments.integrations.BookingServiceClient.update_booking_status", return_value=(200, {"updated": True}))
    def test_booking_callback_endpoint(self, _booking_mock):
        service_token = build_access_token(3, ["service"])
        payment = PaymentIntent.objects.create(booking_id=500, user_id=99, amount="33.00", currency="USD")
        response = self.client.post(
            "/payments/callbacks/booking-status",
            data={"payment_id": payment.id, "booking_status": "confirmed"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["booking_service_status"], 200)
