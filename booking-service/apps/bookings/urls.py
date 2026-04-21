from django.urls import path

from .views import (
    BookingCancelView,
    BookingCreateView,
    BookingDetailView,
    BookingStatusUpdateView,
    BookingTimelineView,
    BookingUserHistoryView,
)


urlpatterns = [
    path("bookings", BookingCreateView.as_view(), name="booking-create"),
    path("bookings/<int:booking_id>", BookingDetailView.as_view(), name="booking-detail"),
    path("bookings/users/<int:user_id>", BookingUserHistoryView.as_view(), name="booking-user-history"),
    path("bookings/<int:booking_id>/status", BookingStatusUpdateView.as_view(), name="booking-status-update"),
    path("bookings/<int:booking_id>/cancel", BookingCancelView.as_view(), name="booking-cancel"),
    path("bookings/<int:booking_id>/timeline", BookingTimelineView.as_view(), name="booking-timeline"),
]

