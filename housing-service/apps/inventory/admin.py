from django.contrib import admin

from .models import Amenity, HousingUnit, HousingUnitAmenity, HousingUnitImage, UnitAvailabilityCalendar


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(HousingUnit)
class HousingUnitAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner_user_id",
        "title",
        "price",
        "location",
        "unit_type",
        "star_rating",
        "worker_count",
        "current_occupancy",
        "max_occupancy",
        "moderation_status",
    )
    list_filter = ("moderation_status", "unit_type")
    search_fields = ("title", "location")


@admin.register(HousingUnitImage)
class HousingUnitImageAdmin(admin.ModelAdmin):
    list_display = ("id", "unit", "sort_order", "image_url")
    search_fields = ("unit__title", "image_url")


@admin.register(HousingUnitAmenity)
class HousingUnitAmenityAdmin(admin.ModelAdmin):
    list_display = ("id", "unit", "amenity", "created_at")
    search_fields = ("unit__title", "amenity__name")


@admin.register(UnitAvailabilityCalendar)
class UnitAvailabilityCalendarAdmin(admin.ModelAdmin):
    list_display = ("id", "unit", "start_date", "end_date", "status")
    list_filter = ("status",)
