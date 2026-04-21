from django.contrib import admin

from .models import AIMetricsDaily, BookingMetricsDaily, KPIDaily, ModerationMetricsDaily, PaymentMetricsDaily


@admin.register(KPIDaily)
class KPIDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "active_users", "new_registrations", "total_bookings", "gross_volume")


@admin.register(BookingMetricsDaily)
class BookingMetricsDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "pending_count", "confirmed_count", "cancelled_count")


@admin.register(PaymentMetricsDaily)
class PaymentMetricsDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "success_count", "failure_count", "refund_count")


@admin.register(AIMetricsDaily)
class AIMetricsDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "recommendation_click_rate", "match_accept_rate")


@admin.register(ModerationMetricsDaily)
class ModerationMetricsDailyAdmin(admin.ModelAdmin):
    list_display = ("date", "complaints_opened", "complaints_resolved", "avg_resolution_hours")

