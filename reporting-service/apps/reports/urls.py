from django.urls import path

from .views import (
    ReportsAIRoommatesView,
    ReportsAIRecommendationsView,
    ReportsBookingsView,
    ReportsExportView,
    ReportsHousingView,
    ReportsKPIView,
    ReportsModerationView,
    ReportsPaymentsView,
)


urlpatterns = [
    path("reports/kpis", ReportsKPIView.as_view(), name="reports-kpis"),
    path("reports/bookings", ReportsBookingsView.as_view(), name="reports-bookings"),
    path("reports/payments", ReportsPaymentsView.as_view(), name="reports-payments"),
    path("reports/housing", ReportsHousingView.as_view(), name="reports-housing"),
    path("reports/ai/recommendations", ReportsAIRecommendationsView.as_view(), name="reports-ai-recommendations"),
    path("reports/ai/roommates", ReportsAIRoommatesView.as_view(), name="reports-ai-roommates"),
    path("reports/moderation", ReportsModerationView.as_view(), name="reports-moderation"),
    path("reports/export", ReportsExportView.as_view(), name="reports-export"),
]

