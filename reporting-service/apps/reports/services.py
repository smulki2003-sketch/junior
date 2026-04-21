from __future__ import annotations

import csv
import io
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .integrations import AdminServiceClient
from .models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily


def build_clients():
    token = settings.INTERNAL_SERVICE_TOKEN
    return {
        "admin": AdminServiceClient(settings.ADMIN_SERVICE_BASE_URL, token),
    }


def collect_source_snapshot(snapshot_date: date):
    clients = build_clients()

    active_users = 0
    new_registrations = 0
    total_bookings = 0
    pending_bookings = 0
    confirmed_bookings = 0
    cancelled_bookings = 0
    gross_volume = Decimal("0.00")

    users_code, users_payload = clients["admin"].users(limit=1000, include_staff=False)
    user_rows = users_payload.get("results", []) if users_code == 200 and isinstance(users_payload, dict) else []
    user_ids = []
    for row in user_rows:
        if bool(row.get("is_active", True)):
            active_users += 1
        created_at_raw = str(row.get("created_at", "") or "")[:10]
        if created_at_raw == snapshot_date.isoformat():
            new_registrations += 1
        row_user_id = row.get("user_id")
        if isinstance(row_user_id, int):
            user_ids.append(row_user_id)

    bookings_code, bookings_payload = clients["admin"].bookings(limit=2000)
    booking_rows = bookings_payload.get("results", []) if bookings_code == 200 and isinstance(bookings_payload, dict) else []
    total_bookings = len(booking_rows)
    for booking in booking_rows:
        status = str(booking.get("status", "")).strip().lower()
        if status == "pending":
            pending_bookings += 1
        elif status in {"confirmed", "completed"}:
            confirmed_bookings += 1
        elif status in {"cancelled", "failed"}:
            cancelled_bookings += 1
        amount_raw = booking.get("total_price")
        try:
            gross_volume += Decimal(str(amount_raw))
        except Exception:
            pass

    success_count = 0
    failure_count = 0
    refund_count = 0
    payments_code, payments_payload = clients["admin"].payments(limit=2000)
    payment_rows = payments_payload.get("results", []) if payments_code == 200 and isinstance(payments_payload, dict) else []
    for payment in payment_rows:
        payment_status = str(payment.get("status", "")).strip().lower()
        if payment_status == "succeeded":
            success_count += 1
        elif payment_status == "failed":
            failure_count += 1
        elif payment_status == "refunded":
            refund_count += 1

    pending_housing_count = 0
    approved_housing_count = 0
    overview_code, overview_payload = clients["admin"].overview()
    if overview_code == 200 and isinstance(overview_payload, dict):
        pending_housing_count = int(overview_payload.get("pending_housing_count", 0))
        approved_housing_count = int(overview_payload.get("active_listings", 0))

    notification_sent_count = 0

    recommendation_events = 0
    recommendation_click_rate = 0.0
    users_with_recommendations = 0

    roommate_match_events = 0
    match_accept_rate = 0.0
    users_with_matches = 0

    complaints_opened = 0
    complaints_resolved = 0
    avg_resolution_hours = 0.0
    complaints_code, complaints_payload = clients["admin"].complaints()
    complaint_rows = complaints_payload.get("results", []) if complaints_code == 200 and isinstance(complaints_payload, dict) else []
    if complaint_rows:
        complaints_opened = len(complaint_rows)
        resolved_statuses = {"resolved", "closed"}
        complaints_resolved = len([item for item in complaint_rows if str(item.get("status", "")).strip().lower() in resolved_statuses])
        avg_resolution_hours = 24.0 if complaints_resolved else 0.0

    return {
        "snapshot_date": snapshot_date,
        "kpi": {
            "active_users": active_users,
            "new_registrations": new_registrations,
            "total_bookings": total_bookings,
            "gross_volume": gross_volume,
            "pending_housing_count": pending_housing_count,
            "approved_housing_count": approved_housing_count,
            "notification_sent_count": notification_sent_count,
        },
        "bookings": {
            "pending_count": pending_bookings,
            "confirmed_count": confirmed_bookings,
            "cancelled_count": cancelled_bookings,
        },
        "payments": {
            "success_count": success_count,
            "failure_count": failure_count,
            "refund_count": refund_count,
        },
        "ai": {
            "recommendation_click_rate": recommendation_click_rate,
            "match_accept_rate": match_accept_rate,
            "recommendation_events": recommendation_events,
            "roommate_match_events": roommate_match_events,
        },
        "moderation": {
            "complaints_opened": complaints_opened,
            "complaints_resolved": complaints_resolved,
            "avg_resolution_hours": avg_resolution_hours,
        },
    }


def aggregate_daily_metrics(snapshot_date: date | None = None, snapshot: dict | None = None):
    day = snapshot_date or timezone.now().date()
    payload = snapshot or collect_source_snapshot(day)
    with transaction.atomic():
        kpi, _ = KPIDaily.objects.update_or_create(
            date=day,
            defaults=payload["kpi"],
        )
        booking, _ = BookingMetricsDaily.objects.update_or_create(
            date=day,
            defaults=payload["bookings"],
        )
        payment, _ = PaymentMetricsDaily.objects.update_or_create(
            date=day,
            defaults=payload["payments"],
        )
        ai, _ = AIMetricsDaily.objects.update_or_create(
            date=day,
            defaults=payload["ai"],
        )
        moderation, _ = ModerationMetricsDaily.objects.update_or_create(
            date=day,
            defaults=payload["moderation"],
        )
    return {"kpi": kpi, "bookings": booking, "payments": payment, "ai": ai, "moderation": moderation}


def csv_from_rows(headers: list[str], rows: list[list]):
    stream = io.StringIO()
    writer = csv.writer(stream)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return stream.getvalue()
