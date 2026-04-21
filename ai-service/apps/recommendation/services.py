from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

import numpy as np
import pandas as pd
from django.db import transaction
from sklearn.metrics.pairwise import cosine_similarity

from .models import HousingFeatureVector, HousingRecommendationResult, UserPreferenceVector

KNOWN_GOVERNORATES = [
    "damascus",
    "rural damascus",
    "aleppo",
    "homs",
    "hama",
    "latakia",
    "tartus",
    "idlib",
    "daraa",
    "as-suwayda",
    "quneitra",
    "deir ez-zor",
    "raqqa",
    "al-hasakah",
]


def _normalize_text(value) -> str:
    return str(value or "").strip().lower()


def _extract_governorate(location_text: str) -> str:
    normalized = _normalize_text(location_text)
    for governorate in KNOWN_GOVERNORATES:
        if governorate in normalized:
            return governorate
    return ""


@dataclass
class RecommendationItem:
    unit_id: int
    score: float
    rank: int
    reasoning: dict
    vector: list[float]


def _safe_decimal(value, default: Decimal = Decimal("0")) -> Decimal:
    try:
        return Decimal(str(value))
    except Exception:
        return default


def _normalize_price_series(price_values: pd.Series) -> pd.Series:
    min_v = price_values.min()
    max_v = price_values.max()
    if max_v == min_v:
        return pd.Series(np.ones(len(price_values)), index=price_values.index)
    return 1 - ((price_values - min_v) / (max_v - min_v))


def build_vectors(preferences: dict, listings: list[dict]):
    if not listings:
        return np.array([]), np.array([]), [], []

    frame = pd.DataFrame(listings).copy()
    frame["unit_id"] = frame.get("unit_id", frame.get("id")).astype(int)
    frame["price_num"] = frame["price"].apply(lambda v: float(_safe_decimal(v, Decimal("0"))))
    frame["location"] = frame["location"].fillna("").astype(str).str.strip().str.lower()
    frame["governorate"] = frame["location"].apply(_extract_governorate)
    frame["unit_type"] = frame["unit_type"].fillna("").astype(str).str.strip().str.lower()
    frame["amenities_json"] = frame["amenities_json"].apply(lambda v: v if isinstance(v, list) else [])

    pref_locations = [str(x).strip().lower() for x in preferences.get("preferred_locations", []) if str(x).strip()]
    pref_types = [str(x).strip().lower() for x in preferences.get("preferred_types", []) if str(x).strip()]
    pref_services = [str(x).strip().lower() for x in preferences.get("preferred_services", []) if str(x).strip()]

    pref_governorates = [_extract_governorate(loc) for loc in pref_locations]
    pref_governorates = [gov for gov in pref_governorates if gov]
    unique_locations = sorted({loc for loc in (frame["governorate"].tolist() + pref_governorates) if loc})
    unique_types = sorted(set(frame["unit_type"].tolist() + pref_types))
    unique_services = sorted(
        {
            service
            for amenities in frame["amenities_json"].tolist()
            for service in [str(item).strip().lower() for item in amenities]
            if service
        }.union(set(pref_services))
    )

    min_budget = _safe_decimal(preferences.get("min_budget", 0), Decimal("0"))
    max_budget = _safe_decimal(preferences.get("max_budget", 0), Decimal("0"))

    frame["price_score"] = _normalize_price_series(frame["price_num"])
    if max_budget > 0:
        frame["budget_fit"] = frame["price_num"].apply(
            lambda p: 1.0 if (min_budget <= Decimal(str(p)) <= max_budget) else 0.0
        )
    else:
        frame["budget_fit"] = 1.0

    columns = ["price_score", "budget_fit"]
    listing_matrix = frame[columns].to_numpy(dtype=float)
    user_vector = [1.0, 1.0]

    for loc in unique_locations:
        listing_col = (frame["governorate"] == loc).astype(float).to_numpy(dtype=float).reshape(-1, 1)
        listing_matrix = np.hstack([listing_matrix, listing_col])
        user_vector.append(1.0 if loc in pref_governorates else 0.0)

    for unit_type in unique_types:
        listing_col = (frame["unit_type"] == unit_type).astype(float).to_numpy(dtype=float).reshape(-1, 1)
        listing_matrix = np.hstack([listing_matrix, listing_col])
        user_vector.append(1.0 if unit_type in pref_types else 0.0)

    for service in unique_services:
        listing_col = frame["amenities_json"].apply(
            lambda amenities: 1.0
            if service in [str(item).strip().lower() for item in amenities]
            else 0.0
        ).to_numpy(dtype=float).reshape(-1, 1)
        listing_matrix = np.hstack([listing_matrix, listing_col])
        user_vector.append(1.0 if service in pref_services else 0.0)

    dimension_names = columns + [f"location:{loc}" for loc in unique_locations]
    dimension_names += [f"type:{t}" for t in unique_types]
    dimension_names += [f"service:{s}" for s in unique_services]
    return np.array(user_vector, dtype=float), listing_matrix, frame["unit_id"].tolist(), dimension_names


def score_and_rank(user_vector: np.ndarray, listing_matrix: np.ndarray, unit_ids: list[int], dimensions: list[str], top_n: int):
    if len(unit_ids) == 0:
        return []
    scores = cosine_similarity(listing_matrix, user_vector.reshape(1, -1)).reshape(-1)
    ranked_indexes = np.argsort(-scores)
    results: list[RecommendationItem] = []
    for rank_idx, matrix_idx in enumerate(ranked_indexes[:top_n], start=1):
        unit_vector = listing_matrix[matrix_idx]
        contributions = (unit_vector * user_vector).astype(float)
        top_dims_idx = np.argsort(-contributions)[:5]
        reasoning = {
            "top_dimensions": [
                {"dimension": dimensions[i], "contribution": float(round(contributions[i], 6))}
                for i in top_dims_idx
                if contributions[i] > 0
            ],
            "raw_score": float(scores[matrix_idx]),
        }
        results.append(
            RecommendationItem(
                unit_id=int(unit_ids[matrix_idx]),
                score=float(round(scores[matrix_idx], 6)),
                rank=rank_idx,
                reasoning=reasoning,
                vector=[float(v) for v in unit_vector.tolist()],
            )
        )
    return results


@transaction.atomic
def persist_run(user_id: int, user_vector: np.ndarray, dimensions: list[str], recommendations: list[RecommendationItem]):
    UserPreferenceVector.objects.update_or_create(
        user_id=user_id,
        defaults={"vector_json": [float(v) for v in user_vector.tolist()], "metadata_json": {"dimensions": dimensions}},
    )

    HousingRecommendationResult.objects.filter(user_id=user_id).delete()

    for item in recommendations:
        HousingFeatureVector.objects.update_or_create(
            unit_id=item.unit_id,
            defaults={"vector_json": item.vector, "metadata_json": {"dimensions": dimensions}},
        )
        HousingRecommendationResult.objects.create(
            user_id=user_id,
            unit_id=item.unit_id,
            similarity_score=item.score,
            rank=item.rank,
            reasoning_json=item.reasoning,
        )
