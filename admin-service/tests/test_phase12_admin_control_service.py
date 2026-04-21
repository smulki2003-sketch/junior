from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.control.models import AdminActionLog, AdminNote


def build_access_token(user_id: int, roles: list[str] | None = None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": f"user{user_id}@example.com",
        "roles": roles or ["admin"],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_SERVICE_JWT_SECRET, algorithm=settings.AUTH_SERVICE_JWT_ALGORITHM)


class AdminControlServiceTests(TestCase):
    @patch(
        "apps.control.integrations.AuthServiceClient.list_users",
        return_value=(200, {"results": [{"id": 7, "email": "u7@example.com", "is_active": True, "roles": ["student"]}]}),
    )
    @patch("apps.control.integrations.HousingServiceClient.list_by_status", side_effect=[(200, [{"id": 1}]), (200, [{"id": 2}])])
    @patch("apps.control.integrations.RoommateServiceClient.questionnaire", return_value=(200, {"questions": [{"id": 1}]}))
    @patch("apps.control.integrations.ModerationServiceClient.list_complaints", return_value=(200, [{"id": 1, "status": "submitted"}]))
    @patch("apps.control.integrations.HousingServiceClient.list_pending", return_value=(200, [{"id": 10}, {"id": 11}]))
    def test_dashboard_overview(self, _housing_mock, _moderation_mock, _roommate_mock, _list_by_status_mock, _auth_users_mock):
        token = build_access_token(1, ["admin"])
        response = self.client.get("/admin/dashboard/overview", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_users"], 1)
        self.assertEqual(data["active_listings"], 1)
        self.assertEqual(data["pending_housing_count"], 2)
        self.assertEqual(data["bookings_this_month"], 0)
        self.assertEqual(data["revenue"], 0.0)
        self.assertEqual(data["approved_listings"], 1)
        self.assertEqual(data["rejected_listings"], 1)
        self.assertEqual(len(data["booking_trend"]), 30)
        self.assertEqual(sum(item["value"] for item in data["booking_trend"]), 0)
        self.assertEqual(data["open_complaints_count"], 1)
        self.assertIn("activity", data)
        self.assertTrue(data["questionnaire_available"])

    @patch("apps.control.integrations.UserServiceClient.fetch_profile", return_value=(200, {"first_name": "Ali"}))
    @patch(
        "apps.control.integrations.AuthServiceClient.list_users",
        return_value=(
            200,
            {
                "results": [
                    {"id": 44, "email": "u44@example.com", "is_active": True, "roles": ["student"]},
                    {"id": 45, "email": "u45@example.com", "is_active": True, "roles": ["student"]},
                ]
            },
        ),
    )
    @patch("apps.control.integrations.AuthServiceClient.update_user_roles", return_value=(200, {"user_id": 44, "roles": ["student"]}))
    def test_users_list_and_status_update_logging(self, _roles_mock, _users_mock, _profile_mock):
        token = build_access_token(2, ["admin"])
        users_response = self.client.get("/admin/users?user_ids=44,45", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(users_response.status_code, 200)
        self.assertEqual(users_response.json()["count"], 2)

        update_response = self.client.patch(
            "/admin/users/44/status",
            data={"status": "suspended", "reason": "Fraud investigation hold"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(update_response.status_code, 200)
        self.assertEqual(update_response.json()["status"], "suspended")
        self.assertEqual(AdminActionLog.objects.filter(action_key="user.status_update").count(), 1)
        self.assertEqual(AdminNote.objects.count(), 1)

    @patch("apps.control.integrations.HousingServiceClient.list_pending", return_value=(200, [{"id": 100}]))
    @patch("apps.control.integrations.HousingServiceClient.update_approval", return_value=(200, {"id": 100, "moderation_status": "approved"}))
    @patch("apps.control.integrations.BookingServiceClient.list_user_bookings", return_value=(200, [{"id": 901, "status": "pending"}]))
    @patch("apps.control.integrations.BookingServiceClient.fetch_booking", return_value=(200, {"id": 901, "user_id": 55, "unit_id": 100, "status": "pending"}))
    @patch("apps.control.integrations.BookingServiceClient.override_status", return_value=(200, {"id": 901, "status": "confirmed"}))
    @patch("apps.control.integrations.PaymentServiceClient.list_payments", return_value=(200, [{"id": 301, "booking_id": 901, "status": "succeeded"}]))
    @patch("apps.control.integrations.NotificationServiceClient.send_notification", return_value=(201, {"id": 1}))
    @patch("apps.control.integrations.ModerationServiceClient.list_complaints", return_value=(200, [{"id": 77, "status": "in_review"}]))
    def test_housing_booking_payment_notification_and_complaints(
        self,
        _moderation_mock,
        _notification_mock,
        _payment_list_mock,
        _booking_override_mock,
        _booking_fetch_mock,
        _booking_list_mock,
        _housing_update_mock,
        _housing_list_mock,
    ):
        token = build_access_token(4, ["admin"])

        pending_response = self.client.get("/admin/housing/pending", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(pending_response.status_code, 200)
        self.assertEqual(pending_response.json()["count"], 1)

        approval_response = self.client.patch(
            "/admin/housing/100/approval",
            data={"approval": "approved", "reason": "Meets listing policy"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(approval_response.status_code, 200)

        bookings_response = self.client.get("/admin/bookings?user_id=55", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(bookings_response.status_code, 200)
        self.assertEqual(bookings_response.json()["count"], 1)

        booking_override_response = self.client.patch(
            "/admin/bookings/901/status",
            data={"status": "confirmed", "reason": "Manual recovery by operations"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(booking_override_response.status_code, 200)

        payments_response = self.client.get("/admin/payments?payment_ids=301", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(payments_response.status_code, 200)
        self.assertEqual(payments_response.json()["count"], 1)

        broadcast_response = self.client.post(
            "/admin/notifications/broadcast",
            data={"title": "System Notice", "body": "Scheduled maintenance window.", "target_user_ids": [1, 2]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(broadcast_response.status_code, 201)
        self.assertEqual(broadcast_response.json()["recipient_count"], 2)

        complaints_response = self.client.get("/admin/complaints", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(complaints_response.status_code, 200)
        self.assertEqual(complaints_response.json()["count"], 1)

    def test_non_admin_denied(self):
        token = build_access_token(9, ["student"])
        response = self.client.get("/admin/dashboard/overview", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 403)

    @patch("apps.control.integrations.AuthServiceClient.list_users", return_value=(None, None))
    @patch("apps.control.integrations.HousingServiceClient.list_by_status", side_effect=[(None, None), (None, None)])
    @patch("apps.control.integrations.RoommateServiceClient.questionnaire", return_value=(None, None))
    @patch("apps.control.integrations.ModerationServiceClient.list_complaints", return_value=(None, None))
    @patch("apps.control.integrations.HousingServiceClient.list_pending", return_value=(None, None))
    def test_dashboard_overview_handles_unavailable_upstreams(
        self,
        _housing_pending_mock,
        _moderation_mock,
        _roommate_mock,
        _housing_status_mock,
        _auth_users_mock,
    ):
        token = build_access_token(11, ["admin"])
        response = self.client.get("/admin/dashboard/overview", HTTP_AUTHORIZATION=f"Bearer {token}")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["total_users"], 0)
        self.assertEqual(data["pending_housing_count"], 0)
        self.assertEqual(data["approved_listings"], 0)
        self.assertEqual(data["rejected_listings"], 0)
        self.assertEqual(data["open_complaints_count"], 0)
        self.assertFalse(data["questionnaire_available"])
