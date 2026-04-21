from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
from django.conf import settings
from django.test import TestCase

from apps.roommate.models import Question, QuestionOption, Questionnaire, RoommateMatchResult


def build_access_token(user_id: int, roles: list[str] | None = None):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": f"user{user_id}@example.com",
        "roles": roles or ["student"],
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }
    return jwt.encode(payload, settings.AUTH_SERVICE_JWT_SECRET, algorithm=settings.AUTH_SERVICE_JWT_ALGORITHM)


class AIRoommateMatchingTests(TestCase):
    def _seed_questionnaire(self):
        q = Questionnaire.objects.create(title="Lifestyle", version=1, is_active=True)
        quiet = Question.objects.create(questionnaire=q, dimension_key="quietness", prompt="Quiet level", weight=1.0, order_index=1)
        clean = Question.objects.create(questionnaire=q, dimension_key="cleanliness", prompt="Cleanliness", weight=1.0, order_index=2)
        for question in (quiet, clean):
            QuestionOption.objects.create(question=question, label="Low", numeric_value=1, order_index=1)
            QuestionOption.objects.create(question=question, label="Medium", numeric_value=3, order_index=2)
            QuestionOption.objects.create(question=question, label="High", numeric_value=5, order_index=3)
        return q

    @patch("apps.roommate.integrations.NotificationClient.send_matches_ready", return_value=None)
    def test_questionnaire_admin_and_match_flow(self, _notification_mock):
        admin_token = build_access_token(1, ["admin"])
        create_response = self.client.post(
            "/ai/roommates/questionnaire",
            data={
                "title": "Lifestyle v2",
                "version": 2,
                "is_active": True,
                "questions": [
                    {
                        "dimension_key": "quietness",
                        "prompt": "Quiet level?",
                        "weight": 1.0,
                        "options": [{"label": "Low", "numeric_value": 1}, {"label": "High", "numeric_value": 5}],
                    }
                ],
            },
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {admin_token}",
        )
        self.assertEqual(create_response.status_code, 201)

    @patch("apps.roommate.integrations.UserServiceClient.get_housing_preferences", return_value={"preferred_locations": ["Damascus"]})
    @patch("apps.roommate.integrations.NotificationClient.send_matches_ready", return_value=None)
    def test_answer_and_deterministic_matching(self, _notification_mock, _pref_mock):
        self._seed_questionnaire()
        quiet = Question.objects.get(dimension_key="quietness")
        clean = Question.objects.get(dimension_key="cleanliness")

        option_low_q = quiet.options.get(label="Low")
        option_high_q = quiet.options.get(label="High")
        option_low_c = clean.options.get(label="Low")
        option_high_c = clean.options.get(label="High")
        option_med_q = quiet.options.get(label="Medium")
        option_med_c = clean.options.get(label="Medium")

        u1 = build_access_token(101, ["student"])
        u2 = build_access_token(102, ["student"])
        u3 = build_access_token(103, ["student"])

        self.client.post(
            "/ai/roommates/answers/101",
            data={"answers": [{"question_id": quiet.id, "selected_option_id": option_high_q.id}, {"question_id": clean.id, "selected_option_id": option_high_c.id}]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {u1}",
        )
        self.client.post(
            "/ai/roommates/answers/102",
            data={"answers": [{"question_id": quiet.id, "selected_option_id": option_med_q.id}, {"question_id": clean.id, "selected_option_id": option_med_c.id}]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {u2}",
        )
        self.client.post(
            "/ai/roommates/answers/103",
            data={"answers": [{"question_id": quiet.id, "selected_option_id": option_low_q.id}, {"question_id": clean.id, "selected_option_id": option_low_c.id}]},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {u3}",
        )

        refresh = self.client.post(
            "/ai/roommates/matches/101/refresh",
            data={"top_n": 2, "scoring_mode": "cosine"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {u1}",
        )
        self.assertEqual(refresh.status_code, 200)
        self.assertEqual(refresh.json()["generated_count"], 2)
        self.assertEqual(refresh.json()["results"][0]["candidate_user_id"], 102)

        explain = self.client.get(
            "/ai/roommates/matches/101/explain/102",
            HTTP_AUTHORIZATION=f"Bearer {u1}",
        )
        self.assertEqual(explain.status_code, 200)
        self.assertEqual(explain.json()["candidate_user_id"], 102)
        self.assertTrue(RoommateMatchResult.objects.filter(user_id=101).exists())

    @patch("apps.roommate.integrations.NotificationClient.send_matches_ready", return_value=None)
    def test_euclidean_mode_and_empty_candidates(self, _notification_mock):
        self._seed_questionnaire()
        token = build_access_token(201, ["student"])
        response = self.client.post(
            "/ai/roommates/matches/201/refresh",
            data={"top_n": 5, "scoring_mode": "euclidean"},
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["generated_count"], 0)

