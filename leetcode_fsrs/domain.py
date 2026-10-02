"""Interface-independent domain types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any


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
