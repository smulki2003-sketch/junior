from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

from django.utils import timezone

from .models import AdminActionLog, AdminNote, AdminSavedView


def parse_id_csv(raw: str | None) -> list[int]:
    if not raw:
        return []
    values: list[int] = []
    for piece in raw.split(","):
        chunk = piece.strip()
        if chunk.isdigit():
            values.append(int(chunk))
    return values


def log_admin_action(
    *,
    admin_user_id: int,
    action_key: str,
    target_type: str,
    target_id: str = "",
    metadata: dict | None = None,
):
    return AdminActionLog.objects.create(
        admin_user_id=admin_user_id,
        action_key=action_key,
        target_type=target_type,
        target_id=target_id,
        metadata_json=metadata or {},
    )


def create_admin_note(*, admin_user_id: int, target_type: str, target_id: str, note: str):
    return AdminNote.objects.create(
        admin_user_id=admin_user_id,
        target_type=target_type,
        target_id=target_id,
        note=note,
    )


def remember_saved_view(admin_user_id: int, name: str, filters_json: dict):
    return AdminSavedView.objects.update_or_create(
        admin_user_id=admin_user_id,
        name=name,
        defaults={"filters_json": filters_json},
    )[0]


def recent_action_counts(hours: int = 24) -> dict:
    since = timezone.now() - timedelta(hours=hours)
    queryset = AdminActionLog.objects.filter(created_at__gte=since)
    return {
        "actions_total": queryset.count(),
        "booking_overrides": queryset.filter(action_key="booking.status_override").count(),
        "housing_approvals": queryset.filter(action_key="housing.approval_update").count(),
        "user_status_changes": queryset.filter(action_key="user.status_update").count(),
        "broadcasts": queryset.filter(action_key="notification.broadcast").count(),
    }


@dataclass
class DashboardOverview:
    total_users: int
    active_listings: int
    bookings_this_month: int
    revenue: float
    approved_listings: int
    rejected_listings: int
    booking_trend: list[dict]
    activity: list[dict]
    pending_housing_count: int
    open_complaints_count: int
    recent_admin_actions: dict
    questionnaire_available: bool

    def to_dict(self):
        return {
            "total_users": self.total_users,
            "active_listings": self.active_listings,
            "bookings_this_month": self.bookings_this_month,
            "revenue": self.revenue,
            "approved_listings": self.approved_listings,
            "rejected_listings": self.rejected_listings,
            "booking_trend": self.booking_trend,
            "activity": self.activity,
            "pending_housing_count": self.pending_housing_count,
            "open_complaints_count": self.open_complaints_count,
            "recent_admin_actions": self.recent_admin_actions,
            "questionnaire_available": self.questionnaire_available,
        }
