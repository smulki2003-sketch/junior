from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from django.db import transaction
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances

from .models import Question, RoommateMatchResult, UserLifestyleVector, UserQuestionnaireAnswer


@dataclass
class MatchCandidate:
    candidate_user_id: int
    score: float
    rank: int
    explanation: dict


def _normalize_vector(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    max_v = values.max()
    min_v = values.min()
    if max_v == min_v:
        return np.ones_like(values)
    return (values - min_v) / (max_v - min_v)


def build_user_vectors() -> tuple[pd.DataFrame, list[str]]:
    answers = UserQuestionnaireAnswer.objects.select_related("question", "selected_option").all()
    if not answers:
        return pd.DataFrame(), []
    rows = [
        {
            "user_id": answer.user_id,
            "dimension_key": answer.question.dimension_key,
            "weight": float(answer.question.weight),
            "numeric_value": float(answer.selected_option.numeric_value),
        }
        for answer in answers
    ]
    frame = pd.DataFrame(rows)
    frame["weighted_value"] = frame["numeric_value"] * frame["weight"]

    agg = frame.groupby(["user_id", "dimension_key"], as_index=False).agg(
        dimension_score=("weighted_value", "mean")
    )
    pivot = agg.pivot(index="user_id", columns="dimension_key", values="dimension_score").fillna(0.0)
    pivot = pivot.sort_index(axis=1)
    for col in pivot.columns:
        pivot[col] = _normalize_vector(pivot[col].to_numpy(dtype=float))
    return pivot, list(pivot.columns)


@transaction.atomic
def persist_vectors(pivot: pd.DataFrame, dimensions: list[str]):
    for user_id, row in pivot.iterrows():
        UserLifestyleVector.objects.update_or_create(
            user_id=int(user_id),
            defaults={
                "vector_json": [float(v) for v in row.to_numpy(dtype=float).tolist()],
                "dimensions_json": dimensions,
            },
        )


def compute_matches_for_user(
    user_id: int,
    pivot: pd.DataFrame,
    dimensions: list[str],
    top_n: int,
    scoring_mode: str,
) -> list[MatchCandidate]:
    if user_id not in pivot.index:
        return []
    candidates = pivot.drop(index=user_id)
    if candidates.empty:
        return []
    user_vector = pivot.loc[user_id].to_numpy(dtype=float).reshape(1, -1)
    candidate_matrix = candidates.to_numpy(dtype=float)
    candidate_ids = candidates.index.tolist()

    if scoring_mode == "euclidean":
        distances = euclidean_distances(candidate_matrix, user_vector).reshape(-1)
        # convert distance to bounded similarity-like score
        scores = 1.0 / (1.0 + distances)
    else:
        scores = cosine_similarity(candidate_matrix, user_vector).reshape(-1)

    sorted_idx = np.argsort(-scores)
    results: list[MatchCandidate] = []
    for rank, idx in enumerate(sorted_idx[:top_n], start=1):
        candidate_vector = candidate_matrix[idx]
        user_flat = user_vector.reshape(-1)
        delta = np.abs(user_flat - candidate_vector)
        top_dim_idx = np.argsort(delta)[:5]
        explanation = {
            "top_aligned_dimensions": [
                {"dimension": dimensions[i], "difference": float(round(delta[i], 6))}
                for i in top_dim_idx
            ],
            "scoring_mode": scoring_mode,
            "raw_score": float(scores[idx]),
        }
        results.append(
            MatchCandidate(
                candidate_user_id=int(candidate_ids[idx]),
                score=float(round(scores[idx], 6)),
                rank=rank,
                explanation=explanation,
            )
        )
    return results


@transaction.atomic
def persist_matches(user_id: int, matches: list[MatchCandidate], scoring_mode: str):
    RoommateMatchResult.objects.filter(user_id=user_id).delete()
    for match in matches:
        RoommateMatchResult.objects.create(
            user_id=user_id,
            candidate_user_id=match.candidate_user_id,
            score=match.score,
            rank=match.rank,
            scoring_mode=scoring_mode,
            explanation_json=match.explanation,
        )


def validate_answer_option_mapping(answer_pairs: list[dict]) -> tuple[bool, str]:
    question_ids = [int(item.get("question_id", 0)) for item in answer_pairs]
    option_ids = [int(item.get("selected_option_id", 0)) for item in answer_pairs]
    if any(qid <= 0 for qid in question_ids) or any(oid <= 0 for oid in option_ids):
        return False, "question_id and selected_option_id must be positive integers."

    questions = {q.id: q for q in Question.objects.filter(id__in=question_ids)}
    if len(questions) != len(set(question_ids)):
        return False, "One or more question IDs are invalid."

    option_map = {}
    for question in Question.objects.filter(id__in=question_ids).prefetch_related("options"):
        option_map[question.id] = {opt.id for opt in question.options.all()}
    for item in answer_pairs:
        qid = int(item["question_id"])
        oid = int(item["selected_option_id"])
        if oid not in option_map.get(qid, set()):
            return False, f"Option {oid} does not belong to question {qid}."
    return True, ""

