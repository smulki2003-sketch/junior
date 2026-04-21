from __future__ import annotations

from datetime import date

from django.db.models import Q

from .models import Booking


VALID_TRANSITIONS = {
    Booking.STATUS_PENDING: {Booking.STATUS_CONFIRMED, Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED, Booking.STATUS_FAILED},
    Booking.STATUS_CONFIRMED: {Booking.STATUS_COMPLETED, Booking.STATUS_CANCELLED},
    Booking.STATUS_COMPLETED: set(),
    Booking.STATUS_CANCELLED: set(),
    Booking.STATUS_FAILED: set(),
}


def can_transition_status(from_status: str, to_status: str, *, is_admin_override: bool = False) -> bool:
    if from_status == to_status:
        return True
    if is_admin_override:
        return to_status in {
            Booking.STATUS_PENDING,
            Booking.STATUS_CONFIRMED,
            Booking.STATUS_COMPLETED,
            Booking.STATUS_CANCELLED,
            Booking.STATUS_FAILED,
        }
    return to_status in VALID_TRANSITIONS.get(from_status, set())


def overlapping_date_filter(start_date: date, end_date: date):
    return Q(start_date__lte=end_date, end_date__gte=start_date)
