"""Small adapter around py-fsrs; the rest of the app uses domain types."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Iterable, Mapping

from fsrs import Card, Rating as FsrsRating, Scheduler

from .domain import Rating


def scheduler_from_preferences(preferences: Mapping[str, object]) -> Scheduler:
    arguments: dict[str, object] = {
        "desired_retention": float(preferences.get("desired_retention", 0.9)),
        # Rebuilding the same event log must always produce the same due dates.
        "enable_fuzzing": False,
    }
    parameters = preferences.get("fsrs_parameters")
    if isinstance(parameters, list) and parameters:
        arguments["parameters"] = tuple(float(value) for value in parameters)
    return Scheduler(**arguments)


def replay_due(
    enrolled_at: datetime,
    reviews: Iterable[Mapping[str, object]],
    preferences: Mapping[str, object],
) -> datetime:
    """Replay immutable review rows and return the current UTC due time."""
    ordered = sorted(reviews, key=lambda row: (str(row["occurred_at"]), str(row["event_id"])))
    if not ordered:
        return _utc(enrolled_at)

    first_at = _parse_time(str(ordered[0]["occurred_at"]))
    card = Card(due=first_at)
    scheduler = scheduler_from_preferences(preferences)
    for row in ordered:
        reviewed_at = _parse_time(str(row["occurred_at"]))
        card, _ = scheduler.review_card(
            card,
            FsrsRating(Rating(str(row["rating"])).number),
            review_datetime=reviewed_at,
        )
    return _utc(card.due)


def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("review timestamp must include a timezone")
    return parsed.astimezone(UTC)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)
