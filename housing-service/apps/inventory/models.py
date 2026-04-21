from django.db import models


class Amenity(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "amenities"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class HousingUnit(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    MODERATION_STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    owner_user_id = models.PositiveIntegerField(db_index=True)
    title = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    location = models.CharField(max_length=200)
    unit_type = models.CharField(max_length=64)
    star_rating = models.DecimalField(max_digits=2, decimal_places=1, default=3.0)
    worker_count = models.PositiveIntegerField(default=1)
    max_occupancy = models.PositiveIntegerField(default=1)
    current_occupancy = models.PositiveIntegerField(default=0)
    moderation_status = models.CharField(
        max_length=16,
        choices=MODERATION_STATUS_CHOICES,
        default=STATUS_PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "housing_units"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.id}:{self.title}"

    @property
    def is_available(self) -> bool:
        return int(self.current_occupancy) < int(self.max_occupancy)


class HousingUnitImage(models.Model):
    unit = models.ForeignKey(HousingUnit, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField(max_length=500)
    sort_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "housing_unit_images"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"{self.unit_id}:{self.sort_order}"


class HousingUnitAmenity(models.Model):
    unit = models.ForeignKey(HousingUnit, on_delete=models.CASCADE, related_name="amenity_links")
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE, related_name="unit_links")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "housing_unit_amenities"
        unique_together = ("unit", "amenity")
        ordering = ["id"]

    def __str__(self) -> str:
        return f"{self.unit_id}:{self.amenity_id}"


class UnitAvailabilityCalendar(models.Model):
    STATUS_AVAILABLE = "available"
    STATUS_UNAVAILABLE = "unavailable"
    STATUS_RESERVED = "reserved"
    AVAILABILITY_STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Available"),
        (STATUS_UNAVAILABLE, "Unavailable"),
        (STATUS_RESERVED, "Reserved"),
    )

    unit = models.ForeignKey(HousingUnit, on_delete=models.CASCADE, related_name="availability_slots")
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=16, choices=AVAILABILITY_STATUS_CHOICES, default=STATUS_AVAILABLE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "unit_availability_calendar"
        ordering = ["start_date", "end_date", "id"]

    def __str__(self) -> str:
        return f"{self.unit_id}:{self.start_date}->{self.end_date}:{self.status}"
