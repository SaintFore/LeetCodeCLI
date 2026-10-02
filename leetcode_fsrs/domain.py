"""Interface-independent domain types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Final, TypedDict
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


class Rating(StrEnum):
    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"

    @property
    def number(self) -> int:
        return list(type(self)).index(self) + 1


class EventType(StrEnum):
    ACCOUNT_BOUND = "account_bound"
    CARD_ENROLLED = "card_enrolled"
    CARD_SUSPENDED = "card_suspended"
    CARD_RESUMED = "card_resumed"
    REVIEW_RECORDED = "review_recorded"
    REVIEW_CORRECTED = "review_corrected"
    PREFERENCE_SET = "preference_set"


class StudyPreferences(TypedDict):
    timezone: str
    daily_limit: int
    new_limit: int
    desired_retention: float
    language: str
    fsrs_parameters: list[float] | None


DEFAULT_STUDY_PREFERENCES: Final[StudyPreferences] = StudyPreferences(
    timezone="UTC",
    daily_limit=20,
    new_limit=5,
    desired_retention=0.9,
    language="zh",
    fsrs_parameters=None,
)


def validate_preference(key: str, value: Any) -> None:
    """Validate one portable Study Preference without storage concerns."""
    if key not in DEFAULT_STUDY_PREFERENCES:
        raise ValueError(f"Unknown preference: {key}")
    if key == "timezone":
        if not isinstance(value, str):
            raise ValueError("timezone must be an IANA timezone name")
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"Unknown IANA timezone: {value}") from error
    elif key in {"daily_limit", "new_limit"}:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError(f"{key} must be a non-negative integer")
    elif key == "desired_retention":
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not 0 < value <= 1
        ):
            raise ValueError("desired_retention must be greater than 0 and at most 1")
    elif key == "language" and value not in {"zh", "en"}:
        raise ValueError("language must be zh or en")
    elif key == "fsrs_parameters" and value is not None:
        if (
            not isinstance(value, list)
            or not value
            or any(
                isinstance(item, bool) or not isinstance(item, (int, float))
                for item in value
            )
        ):
            raise ValueError(
                "fsrs_parameters must be null or a non-empty JSON number array"
            )


@dataclass(frozen=True, slots=True)
class StudyEvent:
    schema_version: int
    event_id: str
    library_id: str
    device_id: str
    sequence: int
    occurred_at: datetime
    type: EventType
    payload: dict[str, Any]


@dataclass(frozen=True, slots=True)
class Question:
    key: str
    frontend_id: str
    slug: str
    title: str
    difficulty: str
    tags: tuple[str, ...] = ()
    url: str = ""
    accepted: bool = False
    content: str = ""


@dataclass(frozen=True, slots=True)
class PlanItem:
    question_key: str
    frontend_id: str
    slug: str
    title: str
    difficulty: str
    due_at: datetime
    is_new: bool


@dataclass(frozen=True, slots=True)
class DailyPlan:
    items: tuple[PlanItem, ...]
    due_backlog: int
    new_backlog: int


@dataclass(frozen=True, slots=True)
class Review:
    event_id: str
    question_key: str
    rating: Rating
    occurred_at: datetime
    corrected_by: str | None


@dataclass(frozen=True, slots=True)
class ScanProblem:
    path: str
    line: int | None
    message: str
