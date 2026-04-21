from rest_framework import serializers

from .models import HousingSearchIndex, SavedFilter


class HousingSearchIndexSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingSearchIndex
        fields = (
            "unit_id",
            "title",
            "description",
            "price",
            "location",
            "unit_type",
            "star_rating",
            "worker_count",
            "max_occupancy",
            "current_occupancy",
            "amenities_json",
            "is_available",
            "source_updated_at",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("created_at", "updated_at")

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("price must be greater than zero.")
        return value

    def validate_amenities_json(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("amenities_json must be a list.")
        return [str(item).strip() for item in value if str(item).strip()]


class SearchIndexSyncRecordSerializer(serializers.Serializer):
    unit_id = serializers.IntegerField(min_value=1)
    title = serializers.CharField(required=False, allow_blank=True, default="")
    description = serializers.CharField(required=False, allow_blank=True, default="")
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    location = serializers.CharField(max_length=200)
    unit_type = serializers.CharField(max_length=64)
    star_rating = serializers.DecimalField(max_digits=2, decimal_places=1, required=False, default=3.0)
    worker_count = serializers.IntegerField(min_value=1, required=False, default=1)
    max_occupancy = serializers.IntegerField(min_value=1, required=False, default=1)
    current_occupancy = serializers.IntegerField(min_value=0, required=False, default=0)
    amenities_json = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
    )
    is_available = serializers.BooleanField(required=False, default=True)
    source_updated_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get("current_occupancy", 0) > attrs.get("max_occupancy", 1):
            raise serializers.ValidationError("current_occupancy cannot be greater than max_occupancy.")
        return attrs


class SearchIndexSyncRequestSerializer(serializers.Serializer):
    records = SearchIndexSyncRecordSerializer(many=True, required=False, default=list)
    removed_unit_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        default=list,
    )
    pull_from_housing = serializers.BooleanField(required=False, default=False)
    full_refresh = serializers.BooleanField(required=False, default=False)


class SearchHousingQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, allow_blank=True, default="")
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    location = serializers.CharField(required=False, allow_blank=True, max_length=200, default="")
    unit_type = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    min_stars = serializers.DecimalField(max_digits=2, decimal_places=1, required=False)
    min_workers = serializers.IntegerField(min_value=1, required=False)
    amenities = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        default=list,
    )
    is_available = serializers.BooleanField(required=False)
    sort = serializers.ChoiceField(choices=("price", "newest", "relevance"), required=False, default="relevance")
    page = serializers.IntegerField(min_value=1, required=False, default=1)
    page_size = serializers.IntegerField(min_value=1, max_value=100, required=False, default=20)

    def validate(self, attrs):
        min_price = attrs.get("min_price")
        max_price = attrs.get("max_price")
        if min_price is not None and max_price is not None and min_price > max_price:
            raise serializers.ValidationError("min_price cannot be greater than max_price.")
        min_stars = attrs.get("min_stars")
        if min_stars is not None and (min_stars < 1 or min_stars > 5):
            raise serializers.ValidationError("min_stars must be between 1 and 5.")
        attrs["amenities"] = [item.strip() for item in attrs.get("amenities", []) if item.strip()]
        return attrs


class SavedFilterSerializer(serializers.ModelSerializer):
    filters = serializers.JSONField(source="filters_json")

    class Meta:
        model = SavedFilter
        fields = ("id", "user_id", "name", "filters", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_name(self, value):
        cleaned = value.strip()
        if not cleaned:
            raise serializers.ValidationError("name cannot be empty.")
        return cleaned
