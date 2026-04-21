from django.contrib import admin

from .models import Booking, BookingEvent, BookingLock, BookingStatusHistory


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "unit_id", "start_date", "end_date", "status", "total_price")
    list_filter = ("status", "start_date")
    search_fields = ("id", "user_id", "unit_id")


@admin.register(BookingLock)
class BookingLockAdmin(admin.ModelAdmin):
    list_display = ("id", "unit_id", "start_date", "end_date", "locked_until")
    list_filter = ("locked_until",)


@admin.register(BookingStatusHistory)
class BookingStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_id", "from_status", "to_status", "changed_at", "changed_by_user_id")
    list_filter = ("to_status", "changed_at")


@admin.register(BookingEvent)
class BookingEventAdmin(admin.ModelAdmin):
    list_display = ("id", "booking_id", "event_type", "created_at")
    list_filter = ("event_type", "created_at")

