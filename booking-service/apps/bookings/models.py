from django.db import models


class Booking(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_FAILED, "Failed"),
    )

    user_id = models.PositiveIntegerField(db_index=True)
    unit_id = models.PositiveIntegerField(db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True)
    occupancy_reserved = models.BooleanField(default=False)
    payment_intent_id = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["unit_id", "start_date", "end_date"]),
            models.Index(fields=["user_id", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"booking:{self.id}:{self.status}"


class BookingLock(models.Model):
    unit_id = models.PositiveIntegerField(db_index=True)
    start_date = models.DateField()
    end_date = models.DateField()
    locked_until = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_locks"
        ordering = ["-locked_until", "-id"]
        unique_together = ("unit_id", "start_date", "end_date")
        indexes = [
            models.Index(fields=["unit_id", "start_date", "end_date"]),
            models.Index(fields=["locked_until"]),
        ]

    def __str__(self) -> str:
        return f"booking-lock:{self.unit_id}:{self.start_date}->{self.end_date}"


class BookingStatusHistory(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=16, choices=Booking.STATUS_CHOICES, null=True, blank=True)
    to_status = models.CharField(max_length=16, choices=Booking.STATUS_CHOICES)
    changed_by_user_id = models.PositiveIntegerField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_status_history"
        ordering = ["changed_at", "id"]

    def __str__(self) -> str:
        return f"booking-history:{self.booking_id}:{self.from_status}->{self.to_status}"


class BookingEvent(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=64, db_index=True)
    payload_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "booking_events"
        ordering = ["created_at", "id"]

    def __str__(self) -> str:
        return f"booking-event:{self.booking_id}:{self.event_type}"
