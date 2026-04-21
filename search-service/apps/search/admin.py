from django.contrib import admin

from .models import HousingSearchIndex, SavedFilter, SearchQueryLog


@admin.register(HousingSearchIndex)
class HousingSearchIndexAdmin(admin.ModelAdmin):
    list_display = ("unit_id", "title", "price", "location", "unit_type", "is_available", "updated_at")
    search_fields = ("title", "location", "unit_type")
    list_filter = ("unit_type", "is_available")


@admin.register(SearchQueryLog)
class SearchQueryLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "query_text", "created_at")
    search_fields = ("query_text",)
    list_filter = ("created_at",)


@admin.register(SavedFilter)
class SavedFilterAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "name", "updated_at")
    search_fields = ("name",)
    list_filter = ("updated_at",)

