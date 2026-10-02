"""Small adapter around py-fsrs; the rest of the app uses domain types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable

from fsrs import Card, Rating as FsrsRating, Scheduler

from .domain import Review, StudyPreferences


def scheduler_from_preferences(preferences: StudyPreferences) -> Scheduler:
    desired_retention = float(preferences["desired_retention"])
    parameters = preferences["fsrs_parameters"]
    if parameters:
        return Scheduler(
            parameters=tuple(float(value) for value in parameters),
            desired_retention=desired_retention,
            # Rebuilding the same event log must always produce the same due dates.
            enable_fuzzing=False,
        )
    return Scheduler(desired_retention=desired_retention, enable_fuzzing=False)


def replay_due(
    enrolled_at: datetime,
    reviews: Iterable[Review],
    preferences: StudyPreferences,
) -> datetime:
    """Replay immutable review rows and return the current UTC due time."""
    ordered = sorted(reviews, key=lambda review: (review.occurred_at, review.event_id))
    if not ordered:
        return _utc(enrolled_at)

    first_at = _utc(ordered[0].occurred_at)
    card = Card(due=first_at)
    scheduler = scheduler_from_preferences(preferences)
    for review in ordered:
        reviewed_at = _utc(review.occurred_at)
        card, _ = scheduler.review_card(
            card,
            FsrsRating(review.rating.number),
            review_datetime=reviewed_at,
        )
    return _utc(card.due)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)
