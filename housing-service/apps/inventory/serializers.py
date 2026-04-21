from rest_framework import serializers

from .models import Amenity, HousingUnit, HousingUnitAmenity, HousingUnitImage, UnitAvailabilityCalendar


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = ("id", "name", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class HousingUnitImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingUnitImage
        fields = ("id", "image_url", "sort_order", "created_at")
        read_only_fields = ("id", "created_at")


class UnitAvailabilitySlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitAvailabilityCalendar
        fields = ("id", "start_date", "end_date", "status", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate(self, attrs):
        start = attrs.get("start_date", getattr(self.instance, "start_date", None))
        end = attrs.get("end_date", getattr(self.instance, "end_date", None))
        if start and end and start > end:
            raise serializers.ValidationError("start_date cannot be after end_date.")
        return attrs


class HousingUnitSerializer(serializers.ModelSerializer):
    images = HousingUnitImageSerializer(many=True, required=False)
    availability_slots = UnitAvailabilitySlotSerializer(many=True, read_only=True)
    amenity_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )
    amenities = AmenitySerializer(many=True, read_only=True)
    is_available = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = HousingUnit
        fields = (
            "id",
            "owner_user_id",
            "title",
            "description",
            "price",
            "location",
            "unit_type",
            "star_rating",
            "worker_count",
            "max_occupancy",
            "current_occupancy",
            "is_available",
            "moderation_status",
            "created_at",
            "updated_at",
            "images",
            "availability_slots",
            "amenity_ids",
            "amenities",
        )
        read_only_fields = ("id", "owner_user_id", "current_occupancy", "is_available", "created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("price must be greater than zero.")
        return value

    def validate_amenity_ids(self, value):
        amenity_count = Amenity.objects.filter(id__in=value, is_active=True).count()
        if amenity_count != len(set(value)):
            raise serializers.ValidationError("One or more amenity IDs are invalid or inactive.")
        return list(dict.fromkeys(value))

    def validate_star_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("star_rating must be between 1 and 5.")
        return value

    def validate_worker_count(self, value):
        if value < 1:
            raise serializers.ValidationError("worker_count must be at least 1.")
        return value

    def validate_max_occupancy(self, value):
        if value < 1:
            raise serializers.ValidationError("max_occupancy must be at least 1.")
        return value

    def validate(self, attrs):
        max_occupancy = attrs.get("max_occupancy", getattr(self.instance, "max_occupancy", 1))
        current_occupancy = getattr(self.instance, "current_occupancy", 0)
        if max_occupancy < current_occupancy:
            raise serializers.ValidationError("max_occupancy cannot be less than current_occupancy.")
        return attrs

    def to_representation(self, instance):
        payload = super().to_representation(instance)
        payload["amenities"] = AmenitySerializer(
            Amenity.objects.filter(unit_links__unit=instance, is_active=True).order_by("name"),
            many=True,
        ).data
        return payload

    def get_is_available(self, instance):
        return instance.is_available


class AvailabilityUpdateRequestSerializer(serializers.Serializer):
    slots = UnitAvailabilitySlotSerializer(many=True)

    @staticmethod
    def validate_slots(value):
        normalized = sorted(value, key=lambda item: (item["start_date"], item["end_date"]))
        for idx in range(1, len(normalized)):
            previous = normalized[idx - 1]
            current = normalized[idx]
            if current["start_date"] <= previous["end_date"]:
                raise serializers.ValidationError("Availability slots cannot overlap.")
        return normalized


class OccupancyAdjustSerializer(serializers.Serializer):
    delta = serializers.IntegerField()


def check_slot_overlaps(slots: list[dict]) -> bool:
    if len(slots) <= 1:
        return False
    normalized = sorted(slots, key=lambda item: (item["start_date"], item["end_date"]))
    for idx in range(1, len(normalized)):
        previous = normalized[idx - 1]
        current = normalized[idx]
        if current["start_date"] <= previous["end_date"]:
            return True
    return False
