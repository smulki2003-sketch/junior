from django.urls import path

from .views import (
    AdminBookingStatusUpdateView,
    AdminBookingsView,
    AdminComplaintsView,
    AdminDashboardOverviewView,
    AdminHousingApprovalUpdateView,
    AdminHousingPendingView,
    AdminNotificationsBroadcastView,
    AdminPaymentsView,
    AdminUserStatusUpdateView,
    AdminUsersView,
)


urlpatterns = [
    path("admin/dashboard/overview", AdminDashboardOverviewView.as_view(), name="admin-dashboard-overview"),
    path("admin/users", AdminUsersView.as_view(), name="admin-users"),
    path("admin/users/<int:user_id>/status", AdminUserStatusUpdateView.as_view(), name="admin-user-status"),
    path("admin/housing/pending", AdminHousingPendingView.as_view(), name="admin-housing-pending"),
    path("admin/housing/<int:unit_id>/approval", AdminHousingApprovalUpdateView.as_view(), name="admin-housing-approval"),
    path("admin/bookings", AdminBookingsView.as_view(), name="admin-bookings"),
    path("admin/bookings/<int:booking_id>/status", AdminBookingStatusUpdateView.as_view(), name="admin-booking-status"),
    path("admin/payments", AdminPaymentsView.as_view(), name="admin-payments"),
    path("admin/notifications/broadcast", AdminNotificationsBroadcastView.as_view(), name="admin-notifications-broadcast"),
    path("admin/complaints", AdminComplaintsView.as_view(), name="admin-complaints"),
]

