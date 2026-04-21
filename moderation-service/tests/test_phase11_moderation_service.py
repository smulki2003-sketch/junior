from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.moderation.models import CaseComment, Complaint, ModerationAction, ModerationCase


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


class ModerationServiceTests(TestCase):
    @patch("apps.moderation.integrations.NotificationServiceClient.send_notification", return_value=(201, {"ok": True}))
    @patch("apps.moderation.services.resolve_target_user_id", return_value=19)
    def test_submit_complaint_and_get_detail(self, _resolve_mock, _notify_mock):
        reporter_token = build_access_token(12, ["student"])
        create_response = self.client.post(
            "/moderation/complaints",
            data={
                "target_type": "housing",
                "target_id": 44,
                "reason": "The listing has misleading information and incorrect location details.",
                "evidence": [
                    {"file_url": "https://cdn.example.com/evidence/1.png", "file_type": "image"},
                    {"file_url": "https://cdn.example.com/evidence/2.pdf", "file_type": "document"},
                ],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        self.assertEqual(create_response.status_code, 201)
        complaint_id = create_response.json()["id"]
        self.assertEqual(create_response.json()["status"], "submitted")
        self.assertIsNotNone(create_response.json()["moderation_case"]["id"])

        detail_response = self.client.get(
            f"/moderation/complaints/{complaint_id}",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(len(detail_response.json()["evidence"]), 2)
        self.assertEqual(detail_response.json()["target_type"], "housing")

    @patch("apps.moderation.integrations.NotificationServiceClient.send_notification", return_value=(201, {"ok": True}))
    @patch("apps.moderation.services.resolve_target_user_id", return_value=11)
    def test_admin_list_status_update_action_and_comment(self, _resolve_mock, _notify_mock):
        reporter_token = build_access_token(7, ["student"])
        create_response = self.client.post(
            "/moderation/complaints",
            data={
                "target_type": "user",
                "target_id": 11,
                "reason": "User sent abusive messages in chat and threatened another user repeatedly.",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        complaint_id = create_response.json()["id"]
        case_id = create_response.json()["moderation_case"]["id"]

        admin_token = build_access_token(1, ["admin"])
        list_response = self.client.get("/moderation/complaints", HTTP_AUTHORIZATION=f"Bearer {admin_token}")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        status_response = self.client.patch(
            f"/moderation/complaints/{complaint_id}/status",
            data={
                "status": "in_review",
                "case_status": "in_progress",
                "priority": "high",
                "assigned_admin_id": 1,
                "internal_note": "Escalated due to repeat reports against the same user.",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(status_response.status_code, 200)
        self.assertEqual(status_response.json()["status"], "in_review")

        with patch("apps.moderation.integrations.EnforcementGateway.apply_action", return_value={"ok": True}):
            action_response = self.client.post(
                f"/moderation/cases/{case_id}/actions",
                data={
                    "action_type": "suspend",
                    "target_type": "user",
                    "target_id": 11,
                    "metadata_json": {"reason": "Repeat policy violations"},
                },
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {admin_token}",
            )
        self.assertEqual(action_response.status_code, 201)
        self.assertEqual(action_response.json()["action_type"], "suspend")

        comment_response = self.client.post(
            f"/moderation/cases/{case_id}/comments",
            data={"comment": "Suspension applied for 7 days pending appeal review."},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(comment_response.status_code, 201)
        self.assertIn("Suspension applied", comment_response.json()["comment"])

        self.assertEqual(ModerationAction.objects.count(), 1)
        self.assertGreaterEqual(CaseComment.objects.count(), 3)

    @patch("apps.moderation.integrations.NotificationServiceClient.send_notification", return_value=(201, {"ok": True}))
    @patch("apps.moderation.services.resolve_target_user_id", return_value=77)
    @patch(
        "apps.moderation.integrations.BookingServiceClient.fetch_booking",
        return_value=(200, {"id": 9, "user_id": 3, "status": "confirmed"}),
    )
    def test_non_admin_rejected_for_admin_endpoints(self, _booking_mock, _resolve_mock, _notify_mock):
        reporter_token = build_access_token(3, ["student"])
        create_response = self.client.post(
            "/moderation/complaints",
            data={
                "target_type": "booking",
                "target_id": 9,
                "reason": "Booking appears fraudulent and associated payment evidence looks forged.",
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        complaint_id = create_response.json()["id"]
        case_id = create_response.json()["moderation_case"]["id"]

        denied_list = self.client.get("/moderation/complaints", HTTP_AUTHORIZATION=f"Bearer {reporter_token}")
        self.assertEqual(denied_list.status_code, 200)
        self.assertEqual(len(denied_list.json()), 1)

        denied_status = self.client.patch(
            f"/moderation/complaints/{complaint_id}/status",
            data={"status": "triaged"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        self.assertEqual(denied_status.status_code, 403)

        denied_action = self.client.post(
            f"/moderation/cases/{case_id}/actions",
            data={"action_type": "warn", "target_type": "booking", "target_id": 9},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {reporter_token}",
        )
        self.assertEqual(denied_action.status_code, 403)

        complaint = Complaint.objects.get(id=complaint_id)
        moderation_case = ModerationCase.objects.get(complaint=complaint)
        self.assertEqual(complaint.status, Complaint.STATUS_SUBMITTED)
        self.assertEqual(moderation_case.status, ModerationCase.STATUS_OPEN)
