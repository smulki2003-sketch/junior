from django.db import models


class KPIDaily(models.Model):
    date = models.DateField(unique=True, db_index=True)
    active_users = models.PositiveIntegerField(default=0)
    new_registrations = models.PositiveIntegerField(default=0)
    total_bookings = models.PositiveIntegerField(default=0)
    gross_volume = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    pending_housing_count = models.PositiveIntegerField(default=0)
    approved_housing_count = models.PositiveIntegerField(default=0)
    notification_sent_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "kpi_daily"
        ordering = ["-date"]


class BookingMetricsDaily(models.Model):
    date = models.DateField(unique=True, db_index=True)
    pending_count = models.PositiveIntegerField(default=0)
    confirmed_count = models.PositiveIntegerField(default=0)
    cancelled_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "booking_metrics_daily"
        ordering = ["-date"]


class PaymentMetricsDaily(models.Model):
    date = models.DateField(unique=True, db_index=True)
    success_count = models.PositiveIntegerField(default=0)
    failure_count = models.PositiveIntegerField(default=0)
    refund_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "payment_metrics_daily"
        ordering = ["-date"]


class AIMetricsDaily(models.Model):
    date = models.DateField(unique=True, db_index=True)
    recommendation_click_rate = models.FloatField(default=0.0)
    match_accept_rate = models.FloatField(default=0.0)
    recommendation_events = models.PositiveIntegerField(default=0)
    roommate_match_events = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_metrics_daily"
        ordering = ["-date"]


class ModerationMetricsDaily(models.Model):
    date = models.DateField(unique=True, db_index=True)
    complaints_opened = models.PositiveIntegerField(default=0)
    complaints_resolved = models.PositiveIntegerField(default=0)
    avg_resolution_hours = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "moderation_metrics_daily"
        ordering = ["-date"]

