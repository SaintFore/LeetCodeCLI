"""Application use cases shared by Typer commands and the Textual app."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from .config import LocalConfig, config_home, data_home
from .domain import DailyPlan, EventType, PlanItem, Question, Rating, ScanProblem, StudyEvent
from .event_store import EventStore, EventStoreError
from .fsrs_engine import replay_due, scheduler_from_preferences
from .projection import Projection


class NotConfiguredError(RuntimeError):
    pass


class ReadOnlyLibraryError(RuntimeError):
    pass


class ApplicationService:
    def __init__(
        self,
        config: LocalConfig,
        *,
        config_path: Path | None = None,
        database_path: Path | None = None,
    ):
        self.config = config
        self.config_path = config_path or config_home() / "config.json"
        self.projection = Projection(database_path or data_home() / "projection.sqlite3")
        self.store: EventStore | None = None
        self.scan_problems: tuple[ScanProblem, ...] = ()
        self.semantic_errors: tuple[str, ...] = ()
        self.read_only = False
        if config.shared_path:
            self.store = EventStore(config.shared_path, config.device_id)
            try:
                self.refresh()
            except (OSError, EventStoreError, ValueError) as error:
                # Keep the last local projection readable while an external sync
                # mount is offline or has delivered an invalid manifest.
                self.read_only = True
                self.semantic_errors = (str(error),)

    @classmethod
    def load(cls) -> "ApplicationService":
        path = config_home() / "config.json"
        return cls(LocalConfig.load(path), config_path=path)

    def initialize_library(self, path: Path, timezone: str, username: str | None = None) -> None:
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError as error:
            raise ValueError(f"Unknown IANA timezone: {timezone}") from error
        resolved = path.expanduser().resolve()
        self.store = EventStore.create(resolved, self.config.device_id)
        self.read_only = False
        self.config.shared_dir = str(resolved)
        self.config.save(self.config_path)
        self._append(EventType.PREFERENCE_SET, {"key": "timezone", "value": timezone})
        if username:
            self.bind_account(username)

    def refresh(self) -> None:
        store = self._require_store()
        store.manifest()
        result = store.scan()
        self.scan_problems = result.problems
        self.semantic_errors = tuple(self.projection.rebuild(result.events))
        self.read_only = not store.writable()

    def bind_account(self, username: str) -> StudyEvent:
        existing = self.projection.account()
        if existing and existing != username:
            raise ValueError(f"This library is already bound to {existing}")
        return self._append(
            EventType.ACCOUNT_BOUND,
            {"username": username, "site": "leetcode.com"},
        )

    def enroll(self, question_key: str, source: str = "manual") -> StudyEvent | None:
        if self.projection.card(question_key):
            return None
        return self._append(
            EventType.CARD_ENROLLED,
            {"question_key": question_key, "source": source},
        )

    def suspend(self, question_key: str) -> StudyEvent:
        self._require_card(question_key)
        return self._append(EventType.CARD_SUSPENDED, {"question_key": question_key})

    def resume(self, question_key: str) -> StudyEvent:
        self._require_card(question_key)
        return self._append(EventType.CARD_RESUMED, {"question_key": question_key})

    def rate(
        self,
        question_key: str,
        rating: Rating,
        *,
        occurred_at: datetime | None = None,
    ) -> StudyEvent:
        self._require_card(question_key)
        return self._append(
            EventType.REVIEW_RECORDED,
            {"question_key": question_key, "rating": rating.value},
            occurred_at=occurred_at,
        )

    def correct_review(self, event_id: str, rating: Rating | None) -> StudyEvent:
        return self._append(
            EventType.REVIEW_CORRECTED,
            {"target_event_id": event_id, "rating": rating.value if rating else None},
        )

    def set_preference(self, key: str, value: Any) -> StudyEvent:
        if key == "timezone":
            try:
                ZoneInfo(str(value))
            except ZoneInfoNotFoundError as error:
                raise ValueError(f"Unknown IANA timezone: {value}") from error
        elif key in {"daily_limit", "new_limit"}:
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{key} must be a non-negative integer")
        elif key == "desired_retention":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 < value <= 1:
                raise ValueError("desired_retention must be greater than 0 and at most 1")
        elif key == "language" and value not in {"zh", "en"}:
            raise ValueError("language must be zh or en")
        elif key == "fsrs_parameters":
            if value is not None and (
                not isinstance(value, list)
                or not value
                or any(isinstance(item, bool) or not isinstance(item, (int, float)) for item in value)
            ):
                raise ValueError("fsrs_parameters must be null or a non-empty JSON number array")
        if key in {"desired_retention", "fsrs_parameters"}:
            candidate = self.preferences()
            candidate[key] = value
            scheduler_from_preferences(candidate)
        return self._append(EventType.PREFERENCE_SET, {"key": key, "value": value})

    def preferences(self) -> dict[str, object]:
        return {
            "timezone": self.projection.preference("timezone", "UTC"),
            "daily_limit": self.projection.preference("daily_limit", 20),
            "new_limit": self.projection.preference("new_limit", 5),
            "desired_retention": self.projection.preference("desired_retention", 0.9),
            "language": self.projection.preference("language", "zh"),
            "fsrs_parameters": self.projection.preference("fsrs_parameters", None),
        }

    def daily_plan(self, now: datetime | None = None) -> DailyPlan:
        preferences = self.preferences()
        instant = (now or datetime.now(UTC)).astimezone(UTC)
        timezone = ZoneInfo(str(preferences["timezone"]))
        local_now = instant.astimezone(timezone)
        start_of_day = local_now.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(UTC)
        reviewed_today, new_reviewed_today = self.projection.review_activity_since(start_of_day)
        due: list[PlanItem] = []
        new: list[PlanItem] = []
        for row in self.projection.card_rows():
            enrolled_at = datetime.fromisoformat(str(row["enrolled_at"]))
            reviews = self.projection.reviews(str(row["question_key"]))
            due_at = replay_due(enrolled_at, reviews, preferences)
            item = PlanItem(
                question_key=str(row["question_key"]),
                frontend_id=str(row["frontend_id"] or "?"),
                slug=str(row["slug"] or str(row["question_key"]).split(":", 1)[-1]),
                title=str(row["title"] or row["question_key"]),
                difficulty=str(row["difficulty"] or "Unknown"),
                due_at=due_at,
                is_new=not reviews,
            )
            if item.is_new:
                new.append(item)
            elif due_at <= instant:
                due.append(item)
        due.sort(key=lambda item: (item.due_at, item.question_key))
        new.sort(key=lambda item: (item.due_at, item.question_key))
        daily_limit = max(0, int(preferences["daily_limit"]) - reviewed_today)
        new_limit = max(0, int(preferences["new_limit"]) - new_reviewed_today)
        selected_due = due[:daily_limit]
        remaining = max(0, daily_limit - len(selected_due))
        selected_new = new[: min(new_limit, remaining)]
        return DailyPlan(tuple(selected_due + selected_new), len(due), len(new))

    def cache_questions(self, questions: list[Question]) -> int:
        self.projection.upsert_questions(questions)
        return len(questions)

    def import_accepted(self, questions: list[Question]) -> int:
        self.projection.upsert_questions(questions)
        enrolled = 0
        for question in questions:
            if question.accepted and self.enroll(question.key, source="leetcode-import"):
                enrolled += 1
        return enrolled

    def _require_store(self) -> EventStore:
        if self.store is None:
            raise NotConfiguredError("No study library configured; run `leetcode-fsrs init`")
        return self.store

    def _require_card(self, question_key: str) -> None:
        if not self.projection.card(question_key):
            raise ValueError(f"Question is not enrolled: {question_key}")

    def _append(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        *,
        occurred_at: datetime | None = None,
    ) -> StudyEvent:
        store = self._require_store()
        if self.read_only or not store.writable():
            raise ReadOnlyLibraryError(f"Study library is read-only: {store.root}")
        event = store.append(event_type, payload, occurred_at=occurred_at)
        self.refresh()
        return event
