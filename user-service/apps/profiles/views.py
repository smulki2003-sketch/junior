from __future__ import annotations

from decimal import Decimal

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .catalog import SYRIAN_GOVERNORATES, SYRIAN_UNIVERSITIES, UNIVERSITY_TO_GOVERNORATE
from .models import HousingPreference, LifestylePreference, ProfileMedia, UserProfile
from .permissions import IsOwnerOrAdmin
from .serializers import (
    HousingPreferenceSerializer,
    LifestylePreferenceSerializer,
    ProfileMediaSerializer,
    UserProfileSerializer,
)


class UserProfileView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @staticmethod
    def _get_or_create_profile(user_id: int) -> UserProfile:
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        return profile

    def get(self, request, user_id: int):
        profile = self._get_or_create_profile(user_id)
        media = ProfileMedia.objects.filter(user_id=user_id).order_by("id")
        payload = UserProfileSerializer(profile).data
        payload["media"] = ProfileMediaSerializer(media, many=True).data
        return Response(payload, status=status.HTTP_200_OK)

    def put(self, request, user_id: int):
        profile = self._get_or_create_profile(user_id)
        serializer = UserProfileSerializer(profile, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if "media" in request.data:
            media_serializer = ProfileMediaSerializer(data=request.data.get("media", []), many=True)
            media_serializer.is_valid(raise_exception=True)
            ProfileMedia.objects.filter(user_id=user_id).delete()
            media_records = [
                ProfileMedia(user_id=user_id, media_type=entry["media_type"], url=entry["url"])
                for entry in media_serializer.validated_data
            ]
            if media_records:
                ProfileMedia.objects.bulk_create(media_records)

        media = ProfileMedia.objects.filter(user_id=user_id).order_by("id")
        payload = UserProfileSerializer(profile).data
        payload["media"] = ProfileMediaSerializer(media, many=True).data
        return Response(payload, status=status.HTTP_200_OK)


class HousingPreferenceView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @staticmethod
    def _get_or_create_pref(user_id: int) -> HousingPreference:
        pref, _ = HousingPreference.objects.get_or_create(user_id=user_id)
        return pref

    def get(self, request, user_id: int):
        pref = self._get_or_create_pref(user_id)
        return Response(HousingPreferenceSerializer(pref).data, status=status.HTTP_200_OK)

    def put(self, request, user_id: int):
        pref = self._get_or_create_pref(user_id)
        serializer = HousingPreferenceSerializer(pref, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class LifestylePreferenceView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @staticmethod
    def _get_or_create_pref(user_id: int) -> LifestylePreference:
        pref, _ = LifestylePreference.objects.get_or_create(user_id=user_id)
        return pref

    def get(self, request, user_id: int):
        pref = self._get_or_create_pref(user_id)
        return Response(LifestylePreferenceSerializer(pref).data, status=status.HTTP_200_OK)

    def put(self, request, user_id: int):
        pref = self._get_or_create_pref(user_id)
        serializer = LifestylePreferenceSerializer(pref, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)


class ProfileCompletionView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    @staticmethod
    def _score_profile(profile: UserProfile, housing: HousingPreference, lifestyle: LifestylePreference, media_count: int):
        checks = []
        checks.extend(
            [
                bool(profile.first_name.strip()),
                bool(profile.last_name.strip()),
                bool(profile.phone.strip()),
                bool(profile.university.strip()),
                bool(profile.governorate.strip()),
                bool(profile.bio.strip()),
            ]
        )
        checks.extend(
            [
                housing.min_budget is not None and housing.min_budget > Decimal("0"),
                housing.max_budget is not None and housing.max_budget > Decimal("0"),
                len(housing.preferred_locations) > 0,
                len(housing.preferred_types) > 0,
            ]
        )
        checks.extend(
            [
                lifestyle.quietness_score > 0,
                lifestyle.cleanliness_score > 0,
                lifestyle.sleep_schedule_score > 0,
            ]
        )
        checks.append(media_count > 0)

        completed = sum(1 for item in checks if item)
        total = len(checks)
        percent = int(round((completed / total) * 100)) if total else 0
        return completed, total, percent

    def get(self, request, user_id: int):
        profile, _ = UserProfile.objects.get_or_create(user_id=user_id)
        housing, _ = HousingPreference.objects.get_or_create(user_id=user_id)
        lifestyle, _ = LifestylePreference.objects.get_or_create(user_id=user_id)
        media_count = ProfileMedia.objects.filter(user_id=user_id).count()

        completed, total, percent = self._score_profile(profile, housing, lifestyle, media_count)
        payload = {
            "user_id": user_id,
            "completion_percent": percent,
            "completed_items": completed,
            "total_items": total,
        }
        return Response(payload, status=status.HTTP_200_OK)


class ProfileMetadataView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        return Response(
            {
                "governorates": SYRIAN_GOVERNORATES,
                "universities": [
                    {
                        "name": name,
                        "governorate": UNIVERSITY_TO_GOVERNORATE[name],
                    }
                    for name in SYRIAN_UNIVERSITIES
                ],
            },
            status=status.HTTP_200_OK,
        )
