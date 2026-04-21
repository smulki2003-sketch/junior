from django.db import models


class UserProfile(models.Model):
    user_id = models.PositiveIntegerField(unique=True, db_index=True)
    first_name = models.CharField(max_length=64, blank=True, default="")
    last_name = models.CharField(max_length=64, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    university = models.CharField(max_length=128, blank=True, default="")
    governorate = models.CharField(max_length=64, blank=True, default="")
    bio = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profiles"
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"profile:{self.user_id}"


class HousingPreference(models.Model):
    user_id = models.PositiveIntegerField(unique=True, db_index=True)
    min_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    preferred_locations = models.JSONField(default=list, blank=True)
    preferred_types = models.JSONField(default=list, blank=True)
    preferred_services = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_preferences"
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"housing-pref:{self.user_id}"


class LifestylePreference(models.Model):
    user_id = models.PositiveIntegerField(unique=True, db_index=True)
    quietness_score = models.PositiveSmallIntegerField(default=3)
    cleanliness_score = models.PositiveSmallIntegerField(default=3)
    sleep_schedule_score = models.PositiveSmallIntegerField(default=3)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "lifestyle_preferences"
        ordering = ["user_id"]

    def __str__(self) -> str:
        return f"lifestyle-pref:{self.user_id}"


class ProfileMedia(models.Model):
    MEDIA_AVATAR = "avatar"
    MEDIA_DOCUMENT = "document"
    MEDIA_OTHER = "other"
    MEDIA_TYPE_CHOICES = (
        (MEDIA_AVATAR, "Avatar"),
        (MEDIA_DOCUMENT, "Document"),
        (MEDIA_OTHER, "Other"),
    )

    user_id = models.PositiveIntegerField(db_index=True)
    media_type = models.CharField(max_length=16, choices=MEDIA_TYPE_CHOICES, default=MEDIA_OTHER)
    url = models.URLField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "profile_media"
        ordering = ["id"]

    def __str__(self) -> str:
        return f"media:{self.user_id}:{self.media_type}"
