from __future__ import annotations

import csv
import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .integrations import AdminServiceClient
from .models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily


def build_clients(service_token: str | None = None):
    token = service_token or settings.INTERNAL_SERVICE_TOKEN
    return {
        "admin": AdminServiceClient(settings.ADMIN_SERVICE_BASE_URL, token),
    }


def collect_source_snapshot(snapshot_date: date, service_token: str | None = None):
    clients = build_clients(service_token=service_token)

    active_users = 0
    new_registrations = 0
    total_bookings = 0
    pending_bookings = 0
    confirmed_bookings = 0
    cancelled_bookings = 0
    gross_volume = Decimal("0.00")

    with ThreadPoolExecutor(max_workers=5) as executor:
        users_future = executor.submit(clients["admin"].users, 500, False)
        bookings_future = executor.submit(clients["admin"].bookings, 2000)
        payments_future = executor.submit(clients["admin"].payments, 2000)
        overview_future = executor.submit(clients["admin"].overview)
        complaints_future = executor.submit(clients["admin"].complaints)

        users_code, users_payload = users_future.result()
        bookings_code, bookings_payload = bookings_future.result()
        payments_code, payments_payload = payments_future.result()
        overview_code, overview_payload = overview_future.result()
        complaints_code, complaints_payload = complaints_future.result()

    user_rows = users_payload.get("results", []) if users_code == 200 and isinstance(users_payload, dict) else []
    for row in user_rows:
        if bool(row.get("is_active", True)):
            active_users += 1
        created_at_raw = str(row.get("created_at", "") or "")[:10]
        if created_at_raw == snapshot_date.isoformat():
            new_registrations += 1

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


def _extract_day(raw_value) -> date | None:
    text = str(raw_value or "").strip()
    if len(text) < 10:
        return None
    try:
        return date.fromisoformat(text[:10])
    except ValueError:
        return None


def compute_live_kpi_rows(start_date: date | None, end_date: date | None, service_token: str | None = None):
    today = timezone.now().date()
    start = start_date or (today - timedelta(days=29))
    end = end_date or today
    if start > end:
        start, end = end, start

    clients = build_clients(service_token=service_token)
    with ThreadPoolExecutor(max_workers=4) as executor:
        users_future = executor.submit(clients["admin"].users, 500, False)
        bookings_future = executor.submit(clients["admin"].bookings, 5000)
        overview_future = executor.submit(clients["admin"].overview)
        complaints_future = executor.submit(clients["admin"].complaints)

        users_code, users_payload = users_future.result()
        bookings_code, bookings_payload = bookings_future.result()
        overview_code, overview_payload = overview_future.result()
        complaints_code, complaints_payload = complaints_future.result()

    user_rows = users_payload.get("results", []) if users_code == 200 and isinstance(users_payload, dict) else []
    booking_rows = bookings_payload.get("results", []) if bookings_code == 200 and isinstance(bookings_payload, dict) else []
    complaint_rows = complaints_payload.get("results", []) if complaints_code == 200 and isinstance(complaints_payload, dict) else []

    active_total = len([row for row in user_rows if bool(row.get("is_active", True))])
    signups_by_day: dict[date, int] = {}
    for row in user_rows:
        created_day = _extract_day(row.get("created_at"))
        if created_day is None:
            continue
        signups_by_day[created_day] = signups_by_day.get(created_day, 0) + 1

    bookings_by_day: dict[date, int] = {}
    gross_by_day: dict[date, Decimal] = {}
    for booking in booking_rows:
        created_day = _extract_day(booking.get("created_at"))
        if created_day is None:
            continue
        bookings_by_day[created_day] = bookings_by_day.get(created_day, 0) + 1
        try:
            amount = Decimal(str(booking.get("total_price", "0")))
        except Exception:
            amount = Decimal("0")
        gross_by_day[created_day] = gross_by_day.get(created_day, Decimal("0")) + amount

    complaints_by_day: dict[date, int] = {}
    for complaint in complaint_rows:
        created_day = _extract_day(complaint.get("created_at"))
        if created_day is None:
            continue
        complaints_by_day[created_day] = complaints_by_day.get(created_day, 0) + 1

    pending_housing_count = 0
    approved_housing_count = 0
    if overview_code == 200 and isinstance(overview_payload, dict):
        pending_housing_count = int(overview_payload.get("pending_housing_count", 0))
        approved_housing_count = int(overview_payload.get("active_listings", 0))

    rows = []
    cursor = start
    while cursor <= end:
        rows.append(
            {
                "date": cursor.isoformat(),
                "active_users": active_total,
                "new_registrations": int(signups_by_day.get(cursor, 0)),
                "total_bookings": int(bookings_by_day.get(cursor, 0)),
                "gross_volume": str(gross_by_day.get(cursor, Decimal("0.00"))),
                "pending_housing_count": pending_housing_count,
                "approved_housing_count": approved_housing_count,
                "notification_sent_count": 0,
                "complaints_opened": int(complaints_by_day.get(cursor, 0)),
            }
        )
        cursor += timedelta(days=1)
    return rows


def summarize_kpi_rows(rows: list[dict]):
    gross_total = Decimal("0.00")
    for row in rows:
        try:
            gross_total += Decimal(str(row.get("gross_volume", "0")))
        except Exception:
            pass
    return {
        "days": len(rows),
        "active_users": int(rows[-1]["active_users"]) if rows else 0,
        "new_registrations": sum(int(row.get("new_registrations", 0)) for row in rows),
        "total_bookings": sum(int(row.get("total_bookings", 0)) for row in rows),
        "gross_volume": str(gross_total),
    }


def aggregate_daily_metrics(snapshot_date: date | None = None, snapshot: dict | None = None, service_token: str | None = None):
    day = snapshot_date or timezone.now().date()
    payload = snapshot or collect_source_snapshot(day, service_token=service_token)
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
