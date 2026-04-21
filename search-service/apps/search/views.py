from __future__ import annotations

from math import ceil

from django.conf import settings
from django.db import transaction
from django.db.models import Case, IntegerField, Q, Value, When
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import HousingServiceClient
from .models import HousingSearchIndex, SavedFilter, SearchQueryLog
from .permissions import IsAdminOrServiceRole, IsOwnerOrAdminByPath, IsSavedFilterOwnerOrAdmin
from .serializers import (
    HousingSearchIndexSerializer,
    SavedFilterSerializer,
    SearchHousingQuerySerializer,
    SearchIndexSyncRequestSerializer,
)


def _is_authenticated_user(request) -> bool:
    return bool(request.user and getattr(request.user, "is_authenticated", False))


def _is_admin(request) -> bool:
    return bool(_is_authenticated_user(request) and "admin" in getattr(request.user, "roles", []))


def _parse_boolean(value: str | None):
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return None


def refresh_index_from_housing():
    client = HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL)
    records = client.fetch_units_for_indexing()
    if not records:
        return
    incoming_ids = {item["unit_id"] for item in records}
    with transaction.atomic():
        for item in records:
            HousingSearchIndex.objects.update_or_create(
                unit_id=item["unit_id"],
                defaults={
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "price": item["price"],
                    "location": item["location"],
                    "unit_type": item["unit_type"],
                    "star_rating": item.get("star_rating", 3.0),
                    "worker_count": item.get("worker_count", 1),
                    "max_occupancy": item.get("max_occupancy", 1),
                    "current_occupancy": item.get("current_occupancy", 0),
                    "amenities_json": item.get("amenities_json", []),
                    "is_available": item.get("is_available", True),
                    "source_updated_at": item.get("source_updated_at"),
                },
            )
        HousingSearchIndex.objects.exclude(unit_id__in=incoming_ids).delete()


class SearchHousingView(APIView):
    permission_classes = [AllowAny]

    def _normalize_query_params(self, request):
        amenities = []
        for raw in request.query_params.getlist("amenities"):
            amenities.extend([item.strip() for item in raw.split(",") if item.strip()])
        normalized = {
            "q": request.query_params.get("q", ""),
            "location": request.query_params.get("location", ""),
            "unit_type": request.query_params.get("unit_type", ""),
            "amenities": amenities,
            "sort": request.query_params.get("sort", "relevance"),
            "page": request.query_params.get("page", 1),
            "page_size": request.query_params.get("page_size", 20),
        }
        min_price = request.query_params.get("min_price")
        max_price = request.query_params.get("max_price")
        min_stars = request.query_params.get("min_stars")
        min_workers = request.query_params.get("min_workers")
        if min_price not in {None, ""}:
            normalized["min_price"] = min_price
        if max_price not in {None, ""}:
            normalized["max_price"] = max_price
        if min_stars not in {None, ""}:
            normalized["min_stars"] = min_stars
        if min_workers not in {None, ""}:
            normalized["min_workers"] = min_workers
        parsed_is_available = _parse_boolean(request.query_params.get("is_available"))
        if parsed_is_available is not None:
            normalized["is_available"] = parsed_is_available
        return normalized

    def _build_queryset(self, data):
        queryset = HousingSearchIndex.objects.all()
        q = data.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q)
                | Q(description__icontains=q)
                | Q(location__icontains=q)
                | Q(unit_type__icontains=q)
                | Q(amenities_json__icontains=q)
            )
        if data.get("min_price") is not None:
            queryset = queryset.filter(price__gte=data["min_price"])
        if data.get("max_price") is not None:
            queryset = queryset.filter(price__lte=data["max_price"])
        if data.get("location"):
            queryset = queryset.filter(location__icontains=data["location"].strip())
        if data.get("unit_type"):
            queryset = queryset.filter(unit_type__iexact=data["unit_type"].strip())
        if data.get("min_stars") is not None:
            queryset = queryset.filter(star_rating__gte=data["min_stars"])
        if data.get("min_workers") is not None:
            queryset = queryset.filter(worker_count__gte=data["min_workers"])
        if data.get("is_available") is not None:
            queryset = queryset.filter(is_available=data["is_available"])
        else:
            queryset = queryset.filter(is_available=True)

        for amenity in data.get("amenities", []):
            queryset = queryset.filter(amenities_json__icontains=amenity)

        sort = data["sort"]
        if sort == "price":
            return queryset.order_by("price", "id")
        if sort == "newest":
            return queryset.order_by("-updated_at", "-id")

        if q:
            queryset = queryset.annotate(
                relevance_score=Case(
                    When(title__icontains=q, then=Value(4)),
                    When(location__icontains=q, then=Value(3)),
                    When(unit_type__icontains=q, then=Value(2)),
                    When(amenities_json__icontains=q, then=Value(1)),
                    default=Value(0),
                    output_field=IntegerField(),
                )
            )
            return queryset.order_by("-relevance_score", "-updated_at", "id")
        return queryset.order_by("-updated_at", "-id")

    def _log_query(self, request, validated_data):
        user_id = request.user.id if _is_authenticated_user(request) else None
        SearchQueryLog.objects.create(
            user_id=user_id,
            query_text=validated_data.get("q", ""),
            filters_json={
                "min_price": str(validated_data.get("min_price")) if validated_data.get("min_price") else None,
                "max_price": str(validated_data.get("max_price")) if validated_data.get("max_price") else None,
                "location": validated_data.get("location", ""),
                "unit_type": validated_data.get("unit_type", ""),
                "min_stars": str(validated_data.get("min_stars")) if validated_data.get("min_stars") else None,
                "min_workers": validated_data.get("min_workers"),
                "amenities": validated_data.get("amenities", []),
                "is_available": validated_data.get("is_available"),
                "sort": validated_data.get("sort"),
                "page": validated_data.get("page"),
                "page_size": validated_data.get("page_size"),
            },
        )

    def get(self, request):
        refresh_index_from_housing()
        serializer = SearchHousingQuerySerializer(data=self._normalize_query_params(request))
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        queryset = self._build_queryset(validated_data)
        self._log_query(request, validated_data)

        page = validated_data["page"]
        page_size = validated_data["page_size"]
        total_results = queryset.count()
        offset = (page - 1) * page_size
        items = queryset[offset : offset + page_size]

        payload = {
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_results": total_results,
                "total_pages": ceil(total_results / page_size) if total_results else 0,
            },
            "sort": validated_data["sort"],
            "results": HousingSearchIndexSerializer(items, many=True).data,
        }
        return Response(payload, status=status.HTTP_200_OK)


class SearchHousingSuggestionsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        refresh_index_from_housing()
        q = request.query_params.get("q", "").strip()
        base_queryset = HousingSearchIndex.objects.filter(is_available=True)
        if q:
            base_queryset = base_queryset.filter(
                Q(title__icontains=q)
                | Q(location__icontains=q)
                | Q(unit_type__icontains=q)
                | Q(amenities_json__icontains=q)
            )

        locations = list(base_queryset.values_list("location", flat=True).distinct()[:8])
        keywords: set[str] = set()
        for item in base_queryset[:80]:
            if item.unit_type:
                keywords.add(item.unit_type.strip())
            if item.title:
                keywords.update([segment for segment in item.title.split(" ") if len(segment) > 2])
            for amenity in item.amenities_json:
                cleaned = str(amenity).strip()
                if cleaned:
                    keywords.add(cleaned)

        if q:
            normalized_query = q.lower()
            keywords = {word for word in keywords if normalized_query in word.lower()}

        payload = {
            "query": q,
            "locations": sorted(locations)[:8],
            "keywords": sorted(keywords)[:12],
        }
        return Response(payload, status=status.HTTP_200_OK)


class SearchIndexSyncView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def _load_records(self, validated_data):
        records = validated_data["records"]
        if records or not validated_data["pull_from_housing"]:
            return records
        client = HousingServiceClient(settings.HOUSING_SERVICE_BASE_URL)
        return client.fetch_units_for_indexing()

    def post(self, request):
        serializer = SearchIndexSyncRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        records = self._load_records(validated_data)
        removed_unit_ids = validated_data["removed_unit_ids"]
        full_refresh = validated_data["full_refresh"]

        inserted = 0
        updated = 0
        with transaction.atomic():
            for item in records:
                defaults = {
                    "title": item.get("title", ""),
                    "description": item.get("description", ""),
                    "price": item["price"],
                    "location": item["location"],
                    "unit_type": item["unit_type"],
                    "star_rating": item.get("star_rating", 3.0),
                    "worker_count": item.get("worker_count", 1),
                    "max_occupancy": item.get("max_occupancy", 1),
                    "current_occupancy": item.get("current_occupancy", 0),
                    "amenities_json": item.get("amenities_json", []),
                    "is_available": item.get("is_available", True),
                    "source_updated_at": item.get("source_updated_at"),
                }
                _, created = HousingSearchIndex.objects.update_or_create(
                    unit_id=item["unit_id"],
                    defaults=defaults,
                )
                if created:
                    inserted += 1
                else:
                    updated += 1

            deleted = 0
            if removed_unit_ids:
                deleted += HousingSearchIndex.objects.filter(unit_id__in=removed_unit_ids).delete()[0]

            if full_refresh and records:
                incoming_ids = {row["unit_id"] for row in records}
                deleted += HousingSearchIndex.objects.exclude(unit_id__in=incoming_ids).delete()[0]

        return Response(
            {
                "synced_records": len(records),
                "inserted": inserted,
                "updated": updated,
                "deleted": deleted,
            },
            status=status.HTTP_200_OK,
        )


class SavedFilterCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SavedFilterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not _is_admin(request) and int(serializer.validated_data["user_id"]) != int(request.user.id):
            return Response(
                {"error": {"code": "forbidden_user", "message": "Cannot create filters for another user."}},
                status=status.HTTP_403_FORBIDDEN,
            )

        saved_filter = SavedFilter.objects.create(
            user_id=serializer.validated_data["user_id"],
            name=serializer.validated_data["name"],
            filters_json=serializer.validated_data["filters_json"],
        )
        return Response(SavedFilterSerializer(saved_filter).data, status=status.HTTP_201_CREATED)


class SavedFilterResourceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, resource_id: int):
        self.kwargs["user_id"] = resource_id
        if not IsOwnerOrAdminByPath().has_permission(request, self):
            return Response(status=status.HTTP_403_FORBIDDEN)
        queryset = SavedFilter.objects.filter(user_id=resource_id).order_by("-updated_at", "-id")
        return Response(SavedFilterSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def delete(self, request, resource_id: int):
        saved_filter = SavedFilter.objects.filter(id=resource_id).first()
        if saved_filter is None:
            return Response(
                {"error": {"code": "saved_filter_not_found", "message": "Saved filter not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsSavedFilterOwnerOrAdmin().has_object_permission(request, self, saved_filter):
            return Response(status=status.HTTP_403_FORBIDDEN)
        saved_filter.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
