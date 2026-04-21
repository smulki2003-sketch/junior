from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.reports.models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily
from apps.reports.services import aggregate_daily_metrics


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


class ReportingAnalyticsTests(TestCase):
    def test_aggregate_daily_metrics_from_snapshot(self):
        snapshot_date = date(2026, 4, 11)
        aggregate_daily_metrics(
            snapshot_date=snapshot_date,
            snapshot={
                "kpi": {
                    "active_users": 12,
                    "new_registrations": 3,
                    "total_bookings": 19,
                    "gross_volume": Decimal("5420.50"),
                    "pending_housing_count": 5,
                    "approved_housing_count": 22,
                    "notification_sent_count": 41,
                },
                "bookings": {"pending_count": 4, "confirmed_count": 10, "cancelled_count": 5},
                "payments": {"success_count": 9, "failure_count": 2, "refund_count": 1},
                "ai": {
                    "recommendation_click_rate": 0.42,
                    "match_accept_rate": 0.33,
                    "recommendation_events": 30,
                    "roommate_match_events": 15,
                },
                "moderation": {"complaints_opened": 8, "complaints_resolved": 6, "avg_resolution_hours": 20.5},
            },
        )

        self.assertEqual(KPIDaily.objects.count(), 1)
        self.assertEqual(BookingMetricsDaily.objects.count(), 1)
        self.assertEqual(PaymentMetricsDaily.objects.count(), 1)
        self.assertEqual(AIMetricsDaily.objects.count(), 1)
        self.assertEqual(ModerationMetricsDaily.objects.count(), 1)
        self.assertEqual(KPIDaily.objects.get().total_bookings, 19)

    def test_reports_endpoints_and_export(self):
        aggregate_daily_metrics(
            snapshot_date=date(2026, 4, 10),
            snapshot={
                "kpi": {
                    "active_users": 10,
                    "new_registrations": 2,
                    "total_bookings": 5,
                    "gross_volume": Decimal("1000.00"),
                    "pending_housing_count": 2,
                    "approved_housing_count": 8,
                    "notification_sent_count": 9,
                },
                "bookings": {"pending_count": 2, "confirmed_count": 2, "cancelled_count": 1},
                "payments": {"success_count": 2, "failure_count": 1, "refund_count": 0},
                "ai": {
                    "recommendation_click_rate": 0.2,
                    "match_accept_rate": 0.3,
                    "recommendation_events": 7,
                    "roommate_match_events": 4,
                },
                "moderation": {"complaints_opened": 3, "complaints_resolved": 1, "avg_resolution_hours": 12.0},
            },
        )
        aggregate_daily_metrics(
            snapshot_date=date(2026, 4, 11),
            snapshot={
                "kpi": {
                    "active_users": 14,
                    "new_registrations": 4,
                    "total_bookings": 7,
                    "gross_volume": Decimal("1500.00"),
                    "pending_housing_count": 1,
                    "approved_housing_count": 11,
                    "notification_sent_count": 13,
                },
                "bookings": {"pending_count": 1, "confirmed_count": 5, "cancelled_count": 1},
                "payments": {"success_count": 5, "failure_count": 0, "refund_count": 1},
                "ai": {
                    "recommendation_click_rate": 0.5,
                    "match_accept_rate": 0.4,
                    "recommendation_events": 11,
                    "roommate_match_events": 6,
                },
                "moderation": {"complaints_opened": 4, "complaints_resolved": 3, "avg_resolution_hours": 8.0},
            },
        )

        token = build_access_token(1, ["admin"])
        kpi_response = self.client.get(
            "/reports/kpis?start_date=2026-04-10&end_date=2026-04-11",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(kpi_response.status_code, 200)
        self.assertEqual(kpi_response.json()["summary"]["total_bookings"], 12)

        bookings_response = self.client.get("/reports/bookings", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(bookings_response.status_code, 200)
        self.assertEqual(len(bookings_response.json()), 2)

        payments_response = self.client.get("/reports/payments", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(payments_response.status_code, 200)
        self.assertIn("conversion_rate", payments_response.json()[0])

        housing_response = self.client.get("/reports/housing", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(housing_response.status_code, 200)
        self.assertEqual(len(housing_response.json()), 2)

        ai_recommendations_response = self.client.get("/reports/ai/recommendations", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(ai_recommendations_response.status_code, 200)
        self.assertIn("quality_score", ai_recommendations_response.json()[0])

        ai_roommates_response = self.client.get("/reports/ai/roommates", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(ai_roommates_response.status_code, 200)
        self.assertIn("match_quality_score", ai_roommates_response.json()[0])

        moderation_response = self.client.get("/reports/moderation", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(moderation_response.status_code, 200)
        self.assertEqual(len(moderation_response.json()), 2)

        export_response = self.client.get(
            "/reports/export?report_type=payments&start_date=2026-04-10&end_date=2026-04-11",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(export_response.status_code, 200)
        self.assertEqual(export_response["Content-Type"], "text/csv")
        self.assertIn("success_count,failure_count,refund_count", export_response.content.decode("utf-8"))

    @patch("apps.reports.views.aggregate_daily_metrics")
    def test_kpi_refresh_query_param_triggers_collection(self, aggregate_mock):
        token = build_access_token(2, ["service"])
        response = self.client.get("/reports/kpis?refresh=true", HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        aggregate_mock.assert_called_once()

