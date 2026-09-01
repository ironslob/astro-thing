from __future__ import annotations

from app.domain.constants import EXCELLENT_MIN, FAIR_MIN, GOOD_MIN

LABELS = ("Excellent", "Good", "Fair", "Poor")


def rating_label(score: float) -> str:
    if score >= EXCELLENT_MIN:
        return "Excellent"
    if score >= GOOD_MIN:
        return "Good"
    if score >= FAIR_MIN:
        return "Fair"
    return "Poor"


def rating_rank(label: str) -> int:
    try:
        return LABELS.index(label)
    except ValueError:
        return len(LABELS)
