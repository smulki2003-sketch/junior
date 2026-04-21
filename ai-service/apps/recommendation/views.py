from __future__ import annotations

from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import HousingDataClient, NotificationClient, UserServiceClient
from .models import HousingRecommendationResult, RecommendationFeedback
from .permissions import IsOwnerOrAdmin
from .serializers import FeedbackSerializer, RecommendationResultSerializer, RefreshRequestSerializer
from .services import build_vectors, persist_run, score_and_rank


def _normalize_text(value) -> str:
    return str(value or "").strip().lower()


def _resolve_target_governorate(profile: dict | None, preferences: dict | None) -> str:
    preferred_locations = (preferences or {}).get("preferred_locations", [])
    if isinstance(preferred_locations, list):
        for location in preferred_locations:
            normalized = _normalize_text(location)
            if normalized:
                return normalized
    profile_governorate = _normalize_text((profile or {}).get("governorate"))
    if profile_governorate:
        return profile_governorate
    return ""


def _filter_listings_by_governorate(listings: list[dict], governorate: str) -> list[dict]:
    if not governorate:
        return listings
    lowered_target = _normalize_text(governorate)
    return [
        listing
        for listing in listings
        if lowered_target in _normalize_text(listing.get("location"))
    ]


def _filter_listings_by_budget(listings: list[dict], preferences: dict | None) -> list[dict]:
    max_budget = _safe_float((preferences or {}).get("max_budget"), default=0.0)
    if max_budget <= 0:
        return listings
    return [listing for listing in listings if _safe_float(listing.get("price")) <= max_budget]


def _safe_float(value, default: float = 10**12) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _build_fallback_preferences(profile: dict | None) -> dict:
    governorate = _normalize_text((profile or {}).get("governorate"))
    preferred_locations = [governorate] if governorate else []
    return {
        "min_budget": 0,
        "max_budget": 0,
        "preferred_locations": preferred_locations,
        "preferred_types": [],
        "preferred_services": [],
    }


class HousingRecommendationRefreshView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, user_id: int):
        serializer = RefreshRequestSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        top_n = serializer.validated_data["top_n"]

        user_client = UserServiceClient(settings.USER_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN)
        housing_client = HousingDataClient(
            settings.HOUSING_SERVICE_BASE_URL,
            settings.SEARCH_SERVICE_BASE_URL,
            settings.INTERNAL_SERVICE_TOKEN,
        )

        profile = user_client.get_profile(user_id)
        preferences = user_client.get_housing_preferences(user_id) or _build_fallback_preferences(profile)
        target_governorate = _resolve_target_governorate(profile, preferences)
        existing_locations = [str(x).strip().lower() for x in preferences.get("preferred_locations", []) if str(x).strip()]
        if target_governorate and not existing_locations:
            preferences = {**preferences, "preferred_locations": [target_governorate]}
        listings = housing_client.get_indexed_units()
        listings = _filter_listings_by_governorate(listings, target_governorate)
        listings = _filter_listings_by_budget(listings, preferences)
        user_vector, listing_matrix, unit_ids, dimensions = build_vectors(preferences, listings)
        recommendations = score_and_rank(user_vector, listing_matrix, unit_ids, dimensions, top_n)
        if target_governorate and recommendations:
            listing_by_unit_id = {}
            for listing in listings:
                unit_id = listing.get("unit_id", listing.get("id"))
                if unit_id is None:
                    continue
                listing_by_unit_id[int(unit_id)] = listing

            recommendations = sorted(
                recommendations,
                key=lambda item: (
                    0
                    if target_governorate in _normalize_text(listing_by_unit_id.get(item.unit_id, {}).get("location"))
                    else 1,
                    _safe_float(listing_by_unit_id.get(item.unit_id, {}).get("price")),
                    -float(item.score),
                ),
            )[:top_n]
            for index, recommendation in enumerate(recommendations, start=1):
                recommendation.rank = index
        persist_run(user_id, user_vector, dimensions, recommendations)

        NotificationClient(settings.NOTIFICATION_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN).send_recommendation_ready(
            user_id=user_id,
            recommendation_count=len(recommendations),
        )

        return Response(
            {
                "user_id": user_id,
                "generated_count": len(recommendations),
                "results": [
                    {
                        "unit_id": item.unit_id,
                        "similarity_score": item.score,
                        "rank": item.rank,
                        "reasoning": item.reasoning,
                    }
                    for item in recommendations
                ],
            },
            status=200,
        )


class HousingRecommendationListView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, user_id: int):
        results = HousingRecommendationResult.objects.filter(user_id=user_id).order_by("rank", "-similarity_score")
        return Response(RecommendationResultSerializer(results, many=True).data, status=200)


class HousingRecommendationFeedbackView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, user_id: int):
        payload = {**request.data, "user_id": user_id}
        serializer = FeedbackSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        feedback = serializer.save()
        return Response(FeedbackSerializer(feedback).data, status=201)


class HousingRecommendationExplainView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, user_id: int, unit_id: int):
        item = (
            HousingRecommendationResult.objects.filter(user_id=user_id, unit_id=unit_id)
            .order_by("-generated_at")
            .first()
        )
        if item is None:
            return Response(
                {"error": {"code": "recommendation_not_found", "message": "Recommendation explanation not found."}},
                status=404,
            )
        return Response(
            {
                "user_id": user_id,
                "unit_id": unit_id,
                "similarity_score": item.similarity_score,
                "rank": item.rank,
                "reasoning": item.reasoning_json,
                "generated_at": item.generated_at,
            },
            status=200,
        )
