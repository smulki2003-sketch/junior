from __future__ import annotations

from django.db import models, transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Amenity, HousingUnit, HousingUnitAmenity, HousingUnitImage, UnitAvailabilityCalendar
from .permissions import IsAdminRole, IsOwnerOrAdmin
from .serializers import (
    AmenitySerializer,
    AvailabilityUpdateRequestSerializer,
    HousingUnitImageSerializer,
    HousingUnitSerializer,
    OccupancyAdjustSerializer,
    UnitAvailabilitySlotSerializer,
)


def is_authenticated_user(request) -> bool:
    return bool(request.user and getattr(request.user, "is_authenticated", False))


def is_admin(request) -> bool:
    return bool(is_authenticated_user(request) and "admin" in getattr(request.user, "roles", []))


def _parse_bool(value: str | None):
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return None


def unit_is_visible_to_requester(request, unit: HousingUnit) -> bool:
    if unit.moderation_status == HousingUnit.STATUS_APPROVED:
        return True
    if not is_authenticated_user(request):
        return False
    if is_admin(request):
        return True
    return int(unit.owner_user_id) == int(request.user.id)


def apply_unit_amenities(unit: HousingUnit, amenity_ids: list[int]):
    HousingUnitAmenity.objects.filter(unit=unit).delete()
    links = [HousingUnitAmenity(unit=unit, amenity_id=amenity_id) for amenity_id in amenity_ids]
    if links:
        HousingUnitAmenity.objects.bulk_create(links)


def apply_unit_images(unit: HousingUnit, images_payload: list[dict]):
    HousingUnitImage.objects.filter(unit=unit).delete()
    images = [
        HousingUnitImage(
            unit=unit,
            image_url=image_data["image_url"],
            sort_order=image_data.get("sort_order", 0),
        )
        for image_data in images_payload
    ]
    if images:
        HousingUnitImage.objects.bulk_create(images)


class HousingUnitListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return [AllowAny()]

    def get(self, request):
        queryset = HousingUnit.objects.all()
        if not is_authenticated_user(request):
            queryset = queryset.filter(moderation_status=HousingUnit.STATUS_APPROVED)
        elif not is_admin(request):
            queryset = queryset.filter(
                Q(moderation_status=HousingUnit.STATUS_APPROVED) | Q(owner_user_id=request.user.id)
            )

        q = request.query_params.get("q")
        location = request.query_params.get("location")
        unit_type = request.query_params.get("unit_type")
        owner_user_id = request.query_params.get("owner_user_id")
        moderation_status = request.query_params.get("moderation_status")
        min_stars = request.query_params.get("min_stars")
        min_workers = request.query_params.get("min_workers")
        is_available = _parse_bool(request.query_params.get("is_available"))

        if q:
            q = q.strip()
            if q:
                queryset = queryset.filter(
                    Q(title__icontains=q) | Q(description__icontains=q) | Q(location__icontains=q) | Q(unit_type__icontains=q)
                )

        if location:
            queryset = queryset.filter(location__icontains=location.strip())
        if unit_type:
            queryset = queryset.filter(unit_type__iexact=unit_type.strip())
        if owner_user_id and owner_user_id.isdigit():
            queryset = queryset.filter(owner_user_id=int(owner_user_id))
        if moderation_status:
            if is_admin(request):
                queryset = queryset.filter(moderation_status=moderation_status)
            else:
                queryset = queryset.filter(moderation_status=HousingUnit.STATUS_APPROVED)
        if min_stars and min_stars.replace(".", "", 1).isdigit():
            queryset = queryset.filter(star_rating__gte=min_stars)
        if min_workers and min_workers.isdigit():
            queryset = queryset.filter(worker_count__gte=int(min_workers))
        if is_available is True:
            queryset = queryset.filter(current_occupancy__lt=models.F("max_occupancy"))
        elif is_available is False:
            queryset = queryset.filter(current_occupancy__gte=models.F("max_occupancy"))

        units = list(queryset.order_by("-created_at"))
        return Response(HousingUnitSerializer(units, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = HousingUnitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amenity_ids = serializer.validated_data.pop("amenity_ids", [])
        images_payload = request.data.get("images", [])
        image_serializer = HousingUnitImageSerializer(data=images_payload, many=True, required=False)
        image_serializer.is_valid(raise_exception=True)

        with transaction.atomic():
            unit = HousingUnit.objects.create(
                owner_user_id=request.user.id,
                title=serializer.validated_data["title"],
                description=serializer.validated_data["description"],
                price=serializer.validated_data["price"],
                location=serializer.validated_data["location"],
                unit_type=serializer.validated_data["unit_type"],
                star_rating=serializer.validated_data.get("star_rating", 3.0),
                worker_count=serializer.validated_data.get("worker_count", 1),
                max_occupancy=serializer.validated_data.get("max_occupancy", 1),
                moderation_status=(
                    serializer.validated_data.get("moderation_status", HousingUnit.STATUS_PENDING)
                    if is_admin(request)
                    else HousingUnit.STATUS_PENDING
                ),
            )
            apply_unit_amenities(unit, amenity_ids)
            apply_unit_images(unit, image_serializer.validated_data)

        return Response(HousingUnitSerializer(unit).data, status=status.HTTP_201_CREATED)


class HousingUnitDetailView(APIView):
    permission_classes = [AllowAny]

    @staticmethod
    def _get_unit_or_none(unit_id: int) -> HousingUnit | None:
        return HousingUnit.objects.filter(id=unit_id).first()

    def get(self, request, unit_id: int):
        unit = self._get_unit_or_none(unit_id)
        if unit is None or not unit_is_visible_to_requester(request, unit):
            return Response(
                {"error": {"code": "unit_not_found", "message": "Housing unit not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(HousingUnitSerializer(unit).data, status=status.HTTP_200_OK)

    def patch(self, request, unit_id: int):
        if not is_authenticated_user(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        unit = self._get_unit_or_none(unit_id)
        if unit is None:
            return Response(
                {"error": {"code": "unit_not_found", "message": "Housing unit not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, unit):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = HousingUnitSerializer(unit, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        amenity_ids = serializer.validated_data.pop("amenity_ids", None)
        images_payload = request.data.get("images")
        image_serializer = None
        if images_payload is not None:
            image_serializer = HousingUnitImageSerializer(data=images_payload, many=True)
            image_serializer.is_valid(raise_exception=True)

        for field, value in serializer.validated_data.items():
            if field == "moderation_status" and not is_admin(request):
                continue
            setattr(unit, field, value)
        unit.save()

        if amenity_ids is not None:
            apply_unit_amenities(unit, amenity_ids)
        if image_serializer is not None:
            apply_unit_images(unit, image_serializer.validated_data)

        return Response(HousingUnitSerializer(unit).data, status=status.HTTP_200_OK)

    def delete(self, request, unit_id: int):
        if not is_authenticated_user(request):
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        unit = self._get_unit_or_none(unit_id)
        if unit is None:
            return Response(
                {"error": {"code": "unit_not_found", "message": "Housing unit not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, unit):
            return Response(status=status.HTTP_403_FORBIDDEN)
        unit.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class HousingUnitAvailabilityView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, unit_id: int):
        unit = HousingUnit.objects.filter(id=unit_id).first()
        if unit is None:
            return Response(
                {"error": {"code": "unit_not_found", "message": "Housing unit not found."}},
                status=status.HTTP_404_NOT_FOUND,
            )
        if not IsOwnerOrAdmin().has_object_permission(request, self, unit):
            return Response(status=status.HTTP_403_FORBIDDEN)

        serializer = AvailabilityUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        slots = serializer.validated_data["slots"]

        with transaction.atomic():
            UnitAvailabilityCalendar.objects.filter(unit=unit).delete()
            new_slots = [
                UnitAvailabilityCalendar(
                    unit=unit,
                    start_date=slot["start_date"],
                    end_date=slot["end_date"],
                    status=slot["status"],
                )
                for slot in slots
            ]
            if new_slots:
                UnitAvailabilityCalendar.objects.bulk_create(new_slots)

        payload = UnitAvailabilitySlotSerializer(
            UnitAvailabilityCalendar.objects.filter(unit=unit).order_by("start_date", "end_date"),
            many=True,
        ).data
        return Response({"unit_id": unit.id, "slots": payload}, status=status.HTTP_200_OK)


class AmenityListCreateView(APIView):
    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminRole()]
        return [AllowAny()]

    def get(self, request):
        queryset = Amenity.objects.all()
        if not is_admin(request):
            queryset = queryset.filter(is_active=True)
        return Response(AmenitySerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AmenitySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amenity, _ = Amenity.objects.update_or_create(
            name=serializer.validated_data["name"],
            defaults={"is_active": serializer.validated_data.get("is_active", True)},
        )
        return Response(AmenitySerializer(amenity).data, status=status.HTTP_201_CREATED)


class HousingUnitOccupancyAdjustView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, unit_id: int):
        serializer = OccupancyAdjustSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        delta = serializer.validated_data["delta"]
        if delta == 0:
            return Response({"error": {"code": "invalid_delta", "message": "delta must not be zero."}}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            unit = HousingUnit.objects.select_for_update().filter(id=unit_id).first()
            if unit is None:
                return Response(
                    {"error": {"code": "unit_not_found", "message": "Housing unit not found."}},
                    status=status.HTTP_404_NOT_FOUND,
                )

            next_occupancy = int(unit.current_occupancy) + int(delta)
            if next_occupancy < 0:
                return Response(
                    {"error": {"code": "invalid_occupancy", "message": "current occupancy cannot go below zero."}},
                    status=status.HTTP_409_CONFLICT,
                )
            if next_occupancy > int(unit.max_occupancy):
                return Response(
                    {"error": {"code": "unit_full", "message": "Housing unit is fully occupied."}},
                    status=status.HTTP_409_CONFLICT,
                )

            unit.current_occupancy = next_occupancy
            unit.save(update_fields=["current_occupancy", "updated_at"])

        return Response(
            {
                "unit_id": unit.id,
                "current_occupancy": unit.current_occupancy,
                "max_occupancy": unit.max_occupancy,
                "is_available": unit.is_available,
            },
            status=status.HTTP_200_OK,
        )
