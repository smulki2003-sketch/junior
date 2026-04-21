from django.contrib import admin

from .models import HousingPreference, LifestylePreference, ProfileMedia, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "first_name", "last_name", "university", "updated_at")
    search_fields = ("user_id", "first_name", "last_name", "university")


@admin.register(HousingPreference)
class HousingPreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "min_budget", "max_budget", "updated_at")
    search_fields = ("user_id",)


@admin.register(LifestylePreference)
class LifestylePreferenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "quietness_score", "cleanliness_score", "sleep_schedule_score")
    search_fields = ("user_id",)


@admin.register(ProfileMedia)
class ProfileMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "media_type", "url", "created_at")
    search_fields = ("user_id", "url")
