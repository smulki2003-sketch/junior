from datetime import datetime, timedelta, timezone

import jwt
from django.conf import settings
from django.test import TestCase

from apps.notifications.models import Notification, NotificationTemplate, UserNotificationPreference


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


class NotificationServiceIntegrationTests(TestCase):
    def test_send_notification_with_template(self):
        NotificationTemplate.objects.create(
            event_key="payment.succeeded",
            title_template="Payment {{payment_id}} succeeded",
            body_template="Amount: {{amount}}",
            is_active=True,
        )
        service_token = build_access_token(1, ["service"])
        response = self.client.post(
            "/notifications/send",
            data={
                "user_id": 50,
                "event_key": "payment.succeeded",
                "context": {"payment_id": 77, "amount": "10.00"},
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertIn("succeeded", response.json()["title"].lower())

    def test_events_bridge_endpoint(self):
        NotificationTemplate.objects.create(
            event_key="booking.created",
            title_template="Booking created",
            body_template="Booking event for user {{user_id}}",
            is_active=True,
        )
        service_token = build_access_token(2, ["service"])
        response = self.client.post(
            "/notifications/events",
            data={"event_type": "booking_created", "payload": {"user_id": 15, "booking_id": 5}},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 1)

    def test_inbox_and_read_actions(self):
        Notification.objects.create(user_id=30, event_key="auth.security", title="T1", body="B1")
        Notification.objects.create(user_id=30, event_key="auth.security", title="T2", body="B2")
        token = build_access_token(30, ["student"])

        inbox = self.client.get("/notifications/users/30", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(inbox.status_code, 200)
        self.assertEqual(inbox.json()["unread_count"], 2)
        first_id = inbox.json()["results"][0]["id"]

        mark_one = self.client.patch(
            f"/notifications/{first_id}/read",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(mark_one.status_code, 200)
        mark_all = self.client.patch(
            "/notifications/users/30/read-all",
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(mark_all.status_code, 200)
        self.assertEqual(mark_all.json()["marked_read_count"], 1)

    def test_preferences_update_and_skip_send(self):
        token = build_access_token(40, ["student"])
        pref_response = self.client.put(
            "/notifications/users/40/preferences",
            data={"preferences": [{"event_key": "ai.recommendation", "is_enabled": False}]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(pref_response.status_code, 200)
        self.assertTrue(UserNotificationPreference.objects.filter(user_id=40, event_key="ai.recommendation").exists())

        service_token = build_access_token(1, ["service"])
        send_response = self.client.post(
            "/notifications/send",
            data={"user_id": 40, "event_key": "ai.recommendation", "title": "AI", "body": "new match"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {service_token}",
        )
        self.assertEqual(send_response.status_code, 200)
        self.assertEqual(Notification.objects.filter(user_id=40).count(), 0)

