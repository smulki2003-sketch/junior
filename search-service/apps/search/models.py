from django.db import models


class HousingSearchIndex(models.Model):
    unit_id = models.PositiveIntegerField(unique=True, db_index=True)
    title = models.CharField(max_length=200, blank=True, default="")
    description = models.TextField(blank=True, default="")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200, db_index=True)
    unit_type = models.CharField(max_length=64, db_index=True)
    star_rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    worker_count = models.PositiveIntegerField(default=1)
    max_occupancy = models.PositiveIntegerField(default=1)
    current_occupancy = models.PositiveIntegerField(default=0)
    amenities_json = models.JSONField(default=list, blank=True)
    is_available = models.BooleanField(default=True, db_index=True)
    source_updated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_search_index"
        ordering = ["-updated_at", "-id"]
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["location", "unit_type"]),
            models.Index(fields=["is_available", "updated_at"]),
        ]

    def __str__(self) -> str:
        return f"search-index:{self.unit_id}"


class SearchQueryLog(models.Model):
    user_id = models.PositiveIntegerField(null=True, blank=True, db_index=True)
    query_text = models.CharField(max_length=200, blank=True, default="")
    filters_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "search_query_logs"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"query-log:{self.id}"


class SavedFilter(models.Model):
    user_id = models.PositiveIntegerField(db_index=True)
    name = models.CharField(max_length=100)
    filters_json = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "saved_filters"
        ordering = ["-updated_at", "-id"]

    def __str__(self) -> str:
        return f"saved-filter:{self.user_id}:{self.name}"
