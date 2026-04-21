from rest_framework import serializers

from .catalog import SYRIAN_GOVERNORATES, SYRIAN_UNIVERSITIES, governorate_for_university
from .models import HousingPreference, LifestylePreference, ProfileMedia, UserProfile


class ProfileMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileMedia
        fields = ("id", "media_type", "url", "created_at")
        read_only_fields = ("id", "created_at")


class UserProfileSerializer(serializers.ModelSerializer):
    media = ProfileMediaSerializer(many=True, required=False)

    class Meta:
        model = UserProfile
        fields = (
            "id",
            "user_id",
            "first_name",
            "last_name",
            "phone",
            "university",
            "governorate",
            "bio",
            "created_at",
            "updated_at",
            "media",
        )
        read_only_fields = ("id", "user_id", "created_at", "updated_at")

    def validate_phone(self, value: str) -> str:
        clean = value.strip()
        if clean and len(clean) < 7:
            raise serializers.ValidationError("Phone number must be at least 7 characters.")
        return clean

    def validate_university(self, value: str) -> str:
        clean = value.strip()
        if clean and clean not in SYRIAN_UNIVERSITIES:
            raise serializers.ValidationError("University must be selected from the official Syrian universities list.")
        return clean

    def validate_governorate(self, value: str) -> str:
        clean = value.strip()
        if clean and clean not in SYRIAN_GOVERNORATES:
            raise serializers.ValidationError("Governorate must be selected from the official Syrian governorates list.")
        return clean

    def validate(self, attrs):
        attrs = super().validate(attrs)
        university = attrs.get("university", getattr(self.instance, "university", ""))
        governorate = attrs.get("governorate", getattr(self.instance, "governorate", ""))
        inferred_governorate = governorate_for_university(university)
        if inferred_governorate:
            if governorate and governorate != inferred_governorate:
                raise serializers.ValidationError(
                    {"governorate": f"Governorate must match selected university ({inferred_governorate})."}
                )
            attrs["governorate"] = inferred_governorate
        return attrs


class HousingPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingPreference
        fields = (
            "id",
            "user_id",
            "min_budget",
            "max_budget",
            "preferred_locations",
            "preferred_types",
            "preferred_services",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user_id", "created_at", "updated_at")

    def validate(self, attrs):
        min_budget = attrs.get("min_budget", getattr(self.instance, "min_budget", None))
        max_budget = attrs.get("max_budget", getattr(self.instance, "max_budget", None))
        if min_budget is not None and max_budget is not None and min_budget > max_budget:
            raise serializers.ValidationError("min_budget cannot be greater than max_budget.")
        return attrs

    def validate_preferred_locations(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("preferred_locations must be a list.")
        return [str(item).strip() for item in value if str(item).strip()]

    def validate_preferred_types(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("preferred_types must be a list.")
        return [str(item).strip() for item in value if str(item).strip()]

    def validate_preferred_services(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("preferred_services must be a list.")
        return [str(item).strip() for item in value if str(item).strip()]


class LifestylePreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = LifestylePreference
        fields = (
            "id",
            "user_id",
            "quietness_score",
            "cleanliness_score",
            "sleep_schedule_score",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "user_id", "created_at", "updated_at")

    def validate(self, attrs):
        for key in ("quietness_score", "cleanliness_score", "sleep_schedule_score"):
            value = attrs.get(key, getattr(self.instance, key, 3))
            if value < 1 or value > 5:
                raise serializers.ValidationError({key: "Score must be between 1 and 5."})
        return attrs
