from __future__ import annotations

from math import ceil

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import ServiceEventAdapter
from .models import Notification, NotificationTemplate, UserNotificationPreference
from .permissions import IsAdminOrServiceRole, IsNotificationOwnerOrAdmin, IsUserOrAdminByPath
from .serializers import (
    NotificationSendSerializer,
    NotificationSerializer,
    NotificationTemplateSerializer,
    PreferencesUpdateSerializer,
    UserPreferenceSerializer,
)
from .services import create_notification, mark_all_read, mark_notification_read


class NotificationSendView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def post(self, request):
        serializer = NotificationSendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            notification = create_notification(**serializer.validated_data)
        except ValueError as exc:
            return Response({"error": {"code": "notification_skipped", "message": str(exc)}}, status=200)
        return Response(NotificationSerializer(notification).data, status=201)


class NotificationEventsBridgeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOrServiceRole]

    def post(self, request):
        event_type = str(request.data.get("event_type", "")).strip()
        payload = request.data.get("payload", {})
        if not event_type or not isinstance(payload, dict):
            return Response({"error": {"code": "invalid_event_payload", "message": "Invalid event payload."}}, status=400)
        try:
            adapted = ServiceEventAdapter().adapt_event_payload(event_type, payload)
            notification = create_notification(**adapted)
        except ValueError as exc:
            return Response({"error": {"code": "event_processing_error", "message": str(exc)}}, status=400)
        return Response(NotificationSerializer(notification).data, status=201)


class NotificationInboxView(APIView):
    permission_classes = [IsAuthenticated, IsUserOrAdminByPath]

    def get(self, request, user_id: int):
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page = 1 if page < 1 else page
        page_size = 20 if page_size < 1 else min(page_size, 100)
        queryset = Notification.objects.filter(user_id=user_id).order_by("-created_at", "-id")
        total_results = queryset.count()
        offset = (page - 1) * page_size
        results = queryset[offset : offset + page_size]
        unread_count = queryset.filter(is_read=False).count()
        return Response(
            {
                "pagination": {
                    "page": page,
                    "page_size": page_size,
                    "total_results": total_results,
                    "total_pages": ceil(total_results / page_size) if total_results else 0,
                },
                "unread_count": unread_count,
                "results": NotificationSerializer(results, many=True).data,
            },
            status=200,
        )


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, notification_id: int):
        notification = Notification.objects.filter(id=notification_id).first()
        if notification is None:
            return Response({"error": {"code": "notification_not_found", "message": "Notification not found."}}, status=404)
        if not IsNotificationOwnerOrAdmin().has_object_permission(request, self, notification):
            return Response(status=403)
        notification = mark_notification_read(notification)
        return Response(NotificationSerializer(notification).data, status=200)


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated, IsUserOrAdminByPath]

    def patch(self, request, user_id: int):
        updated = mark_all_read(user_id)
        return Response({"user_id": user_id, "marked_read_count": updated}, status=200)


class NotificationTemplateListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAdminOrServiceRole()]
        return [IsAuthenticated()]

    def get(self, request):
        templates = NotificationTemplate.objects.all().order_by("event_key")
        return Response(NotificationTemplateSerializer(templates, many=True).data, status=200)

    def post(self, request):
        serializer = NotificationTemplateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        template = serializer.save()
        return Response(NotificationTemplateSerializer(template).data, status=201)


class NotificationPreferenceUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsUserOrAdminByPath]

    def put(self, request, user_id: int):
        serializer = PreferencesUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        updated = []
        for item in serializer.validated_data["preferences"]:
            pref, _ = UserNotificationPreference.objects.update_or_create(
                user_id=user_id,
                event_key=item["event_key"],
                defaults={"is_enabled": item["is_enabled"]},
            )
            updated.append(pref)
        return Response(UserPreferenceSerializer(updated, many=True).data, status=200)

