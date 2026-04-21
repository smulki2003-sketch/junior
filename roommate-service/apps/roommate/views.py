from __future__ import annotations

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .integrations import NotificationClient, UserServiceClient
from .models import Question, QuestionOption, Questionnaire, RoommateMatchResult, UserQuestionnaireAnswer
from .permissions import IsAdminOrServiceRole, IsOwnerOrAdmin
from .serializers import (
    AnswerSubmissionSerializer,
    MatchResultSerializer,
    QuestionnaireAdminUpsertSerializer,
    QuestionnaireSerializer,
    RefreshMatchesSerializer,
)
from .services import (
    build_user_vectors,
    compute_matches_for_user,
    persist_matches,
    persist_vectors,
    validate_answer_option_mapping,
)


def _normalize_text(value) -> str:
    return str(value or "").strip().lower()


def _resolve_target_governorate(user_id: int, explicit_location: str, user_client: UserServiceClient) -> str:
    if explicit_location:
        return _normalize_text(explicit_location)
    profile = user_client.get_profile(user_id) or {}
    profile_governorate = _normalize_text(profile.get("governorate"))
    if profile_governorate:
        return profile_governorate
    pref = user_client.get_housing_preferences(user_id) or {}
    preferred_locations = [_normalize_text(x) for x in pref.get("preferred_locations", []) if _normalize_text(x)]
    return preferred_locations[0] if preferred_locations else ""


def _same_governorate(candidate_user_id: int, target_governorate: str, user_client: UserServiceClient) -> bool:
    if not target_governorate:
        return True
    profile = user_client.get_profile(candidate_user_id) or {}
    if _normalize_text(profile.get("governorate")) == target_governorate:
        return True
    pref = user_client.get_housing_preferences(candidate_user_id) or {}
    preferred_locations = [_normalize_text(x) for x in pref.get("preferred_locations", []) if _normalize_text(x)]
    return target_governorate in preferred_locations


def _build_candidate_profile(candidate_user_id: int, user_client: UserServiceClient) -> dict:
    profile = user_client.get_profile(candidate_user_id) or {}
    first_name = str(profile.get("first_name", "") or "").strip()
    last_name = str(profile.get("last_name", "") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part).strip()
    return {
        "full_name": full_name or f"Student {candidate_user_id}",
        "first_name": first_name,
        "last_name": last_name,
        "phone": str(profile.get("phone", "") or "").strip(),
        "university": str(profile.get("university", "") or "").strip(),
        "governorate": str(profile.get("governorate", "") or "").strip(),
    }


def _serialize_matches_with_profiles(matches_queryset, user_client: UserServiceClient):
    base_rows = MatchResultSerializer(matches_queryset, many=True).data
    enriched_rows = []
    for row in base_rows:
        candidate_user_id = int(row["candidate_user_id"])
        enriched_rows.append(
            {
                **row,
                "candidate_profile": _build_candidate_profile(candidate_user_id, user_client),
            }
        )
    return enriched_rows


DEFAULT_QUESTIONNAIRE = {
    "title": "Default Roommate Compatibility Questionnaire",
    "version": 1,
    "questions": [
        {
            "dimension_key": "quietness",
            "prompt": "How quiet do you prefer your shared room?",
            "weight": 1.2,
            "options": [
                {"label": "Very quiet", "numeric_value": 5},
                {"label": "Mostly quiet", "numeric_value": 4},
                {"label": "Balanced", "numeric_value": 3},
                {"label": "A bit social/noisy", "numeric_value": 2},
                {"label": "Very social/noisy", "numeric_value": 1},
            ],
        },
        {
            "dimension_key": "cleanliness",
            "prompt": "How important is daily cleanliness to you?",
            "weight": 1.3,
            "options": [
                {"label": "Very important", "numeric_value": 5},
                {"label": "Important", "numeric_value": 4},
                {"label": "Moderate", "numeric_value": 3},
                {"label": "Low", "numeric_value": 2},
                {"label": "Not important", "numeric_value": 1},
            ],
        },
        {
            "dimension_key": "sleep_schedule",
            "prompt": "What best describes your sleep schedule?",
            "weight": 1.0,
            "options": [
                {"label": "Sleep early / wake early", "numeric_value": 5},
                {"label": "Mostly early", "numeric_value": 4},
                {"label": "Flexible", "numeric_value": 3},
                {"label": "Mostly late", "numeric_value": 2},
                {"label": "Sleep very late", "numeric_value": 1},
            ],
        },
        {
            "dimension_key": "study_habits",
            "prompt": "How often do you study at home?",
            "weight": 1.0,
            "options": [
                {"label": "Very often", "numeric_value": 5},
                {"label": "Often", "numeric_value": 4},
                {"label": "Sometimes", "numeric_value": 3},
                {"label": "Rarely", "numeric_value": 2},
                {"label": "Almost never", "numeric_value": 1},
            ],
        },
    ],
}


def _create_default_questionnaire() -> Questionnaire:
    with transaction.atomic():
        questionnaire, _ = Questionnaire.objects.update_or_create(
            version=DEFAULT_QUESTIONNAIRE["version"],
            defaults={"title": DEFAULT_QUESTIONNAIRE["title"], "is_active": True},
        )
        Question.objects.filter(questionnaire=questionnaire).delete()
        for question_order, question_payload in enumerate(DEFAULT_QUESTIONNAIRE["questions"], start=1):
            question = Question.objects.create(
                questionnaire=questionnaire,
                dimension_key=question_payload["dimension_key"],
                prompt=question_payload["prompt"],
                weight=float(question_payload.get("weight", 1.0)),
                order_index=question_order,
            )
            for option_order, option_payload in enumerate(question_payload["options"], start=1):
                QuestionOption.objects.create(
                    question=question,
                    label=option_payload["label"],
                    numeric_value=float(option_payload["numeric_value"]),
                    order_index=option_order,
                )
        Questionnaire.objects.exclude(id=questionnaire.id).update(is_active=False)
    return questionnaire


class QuestionnaireView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        questionnaire = Questionnaire.objects.filter(is_active=True).order_by("-version", "-id").first()
        if questionnaire is None:
            questionnaire = _create_default_questionnaire()
        return Response(QuestionnaireSerializer(questionnaire).data, status=200)

    def post(self, request):
        if not IsAdminOrServiceRole().has_permission(request, self):
            return Response(status=403)
        serializer = QuestionnaireAdminUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data

        with transaction.atomic():
            questionnaire, _ = Questionnaire.objects.update_or_create(
                version=payload["version"],
                defaults={"title": payload["title"], "is_active": payload["is_active"]},
            )
            Question.objects.filter(questionnaire=questionnaire).delete()
            for order_idx, question_payload in enumerate(payload["questions"], start=1):
                question = Question.objects.create(
                    questionnaire=questionnaire,
                    dimension_key=str(question_payload["dimension_key"]).strip(),
                    prompt=str(question_payload["prompt"]).strip(),
                    weight=float(question_payload.get("weight", 1.0)),
                    order_index=order_idx,
                )
                for option_idx, option_payload in enumerate(question_payload.get("options", []), start=1):
                    QuestionOption.objects.create(
                        question=question,
                        label=str(option_payload["label"]).strip(),
                        numeric_value=float(option_payload["numeric_value"]),
                        order_index=option_idx,
                    )
            if payload["is_active"]:
                Questionnaire.objects.exclude(id=questionnaire.id).update(is_active=False)

        return Response(QuestionnaireSerializer(questionnaire).data, status=201)


class QuestionnaireAnswerSubmissionView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, user_id: int):
        serializer = AnswerSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        answers = serializer.validated_data["answers"]
        valid, error_message = validate_answer_option_mapping(answers)
        if not valid:
            return Response({"error": {"code": "invalid_answers", "message": error_message}}, status=400)

        with transaction.atomic():
            UserQuestionnaireAnswer.objects.filter(user_id=user_id).delete()
            for answer in answers:
                UserQuestionnaireAnswer.objects.create(
                    user_id=user_id,
                    question_id=int(answer["question_id"]),
                    selected_option_id=int(answer["selected_option_id"]),
                )
        return Response({"user_id": user_id, "saved_answers": len(answers)}, status=201)


class RoommateMatchesRefreshView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def post(self, request, user_id: int):
        serializer = RefreshMatchesSerializer(data=request.data or {})
        serializer.is_valid(raise_exception=True)
        top_n = serializer.validated_data["top_n"]
        scoring_mode = serializer.validated_data["scoring_mode"]
        location = serializer.validated_data.get("location", "").strip()

        pivot, dimensions = build_user_vectors()
        persist_vectors(pivot, dimensions)
        matches = compute_matches_for_user(user_id, pivot, dimensions, top_n=top_n * 3, scoring_mode=scoring_mode)

        user_client = UserServiceClient(settings.USER_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN)
        target_governorate = _resolve_target_governorate(user_id, location, user_client)
        if target_governorate:
            matches = [
                match
                for match in matches
                if _same_governorate(match.candidate_user_id, target_governorate, user_client)
            ]

        matches = matches[:top_n]
        persist_matches(user_id, matches, scoring_mode=scoring_mode)
        NotificationClient(settings.NOTIFICATION_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN).send_matches_ready(
            user_id=user_id,
            candidate_count=len(matches),
        )

        persisted_matches = RoommateMatchResult.objects.filter(user_id=user_id).order_by("rank")
        return Response(
            {
                "user_id": user_id,
                "scoring_mode": scoring_mode,
                "generated_count": len(matches),
                "results": _serialize_matches_with_profiles(persisted_matches, user_client),
            },
            status=200,
        )


class RoommateMatchesListView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, user_id: int):
        matches = RoommateMatchResult.objects.filter(user_id=user_id).order_by("rank")
        user_client = UserServiceClient(settings.USER_SERVICE_BASE_URL, settings.INTERNAL_SERVICE_TOKEN)
        return Response(_serialize_matches_with_profiles(matches, user_client), status=200)


class RoommateExplainView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, user_id: int, candidate_user_id: int):
        item = (
            RoommateMatchResult.objects.filter(user_id=user_id, candidate_user_id=candidate_user_id)
            .order_by("-generated_at")
            .first()
        )
        if item is None:
            return Response({"error": {"code": "match_not_found", "message": "Match explanation not found."}}, status=404)
        return Response(
            {
                "user_id": user_id,
                "candidate_user_id": candidate_user_id,
                "score": item.score,
                "rank": item.rank,
                "scoring_mode": item.scoring_mode,
                "explanation": item.explanation_json,
                "generated_at": item.generated_at,
            },
            status=200,
        )
