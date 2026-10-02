"""Application use cases shared by Typer commands and the Textual app."""

from __future__ import annotations

import errno
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any, Never, cast
from zoneinfo import ZoneInfo

from .config import LocalConfig, config_home, data_home
from .domain import (
    DEFAULT_STUDY_PREFERENCES,
    DailyPlan,
    EventType,
    PlanItem,
    Question,
    Rating,
    ScanProblem,
    StudyEvent,
    StudyPreferences,
    validate_preference,
)
from .event_store import EventStore, EventStoreError, EventStoreUnavailableError
from .fsrs_engine import replay_due, scheduler_from_preferences
from .projection import CardRecord, Projection


class ApplicationError(RuntimeError):
    """An expected operational failure suitable for presentation adapters."""


class NotConfiguredError(ApplicationError):
    pass


class ReadOnlyLibraryError(ApplicationError):
    pass


class QuestionNotFoundError(ApplicationError):
    pass


class InvalidOperationError(ApplicationError):
    pass


class SettingsConflictError(InvalidOperationError):
    pass


class CardState(StrEnum):
    NOT_ENROLLED = "not_enrolled"
    ACTIVE = "active"
    SUSPENDED = "suspended"


@dataclass(frozen=True, slots=True)
class QuestionListItem:
    question: Question
    state: CardState


class LibraryAccess(StrEnum):
    UNCONFIGURED = "unconfigured"
    READ_ONLY = "read_only"
    WRITABLE = "writable"


@dataclass(frozen=True, slots=True)
class LibraryCounts:
    questions: int
    cards: int
    reviews: int
    suspended: int


@dataclass(frozen=True, slots=True)
class LibraryHealth:
    shared_path: str | None
    account: str | None
    access: LibraryAccess
    counts: LibraryCounts
    scan_problems: tuple[ScanProblem, ...]
    semantic_problems: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    timezone: str
    daily_limit: int
    new_limit: int
    desired_retention: float
    language: str
    fsrs_parameters: tuple[float, ...] | None
    solver_command: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SolverInput:
    question: Question
    command: tuple[str, ...]


class ApplicationService:
    def __init__(
        self,
        config: LocalConfig,
        *,
        config_path: Path | None = None,
        database_path: Path | None = None,
    ) -> None:
        self._config = config
        self._config_path = config_path or config_home() / "config.json"
        self._projection = Projection(
            database_path or data_home() / "projection.sqlite3"
        )
        self._store: EventStore | None = None
        self._scan_problems: tuple[ScanProblem, ...] = ()
        self._semantic_errors: tuple[str, ...] = ()
        self._read_only = False
        if config.shared_path:
            self._store = EventStore(config.shared_path, config.device_id)
            try:
                self.refresh()
            except ApplicationError as error:
                # Keep the last local projection readable while an external sync
                # mount is offline or has delivered an invalid manifest.
                self._read_only = True
                self._semantic_errors = (str(error),)

    @classmethod
    def load(cls) -> ApplicationService:
        path = config_home() / "config.json"
        return cls(LocalConfig.load(path), config_path=path)

    def initialize_library(
        self, path: Path, timezone: str, username: str | None = None
    ) -> None:
        try:
            validate_preference("timezone", timezone)
        except ValueError as error:
            raise InvalidOperationError(str(error)) from error
        resolved = path.expanduser().resolve()
        try:
            store = EventStore.create(resolved, self._config.device_id)
            store.manifest()
        except (OSError, EventStoreError) as error:
            raise InvalidOperationError(str(error)) from error
        self._store = store
        self._read_only = False
        self._config.shared_dir = str(resolved)
        try:
            self._config.save(self._config_path)
        except OSError as error:
            raise InvalidOperationError(
                f"Could not save local configuration: {error}"
            ) from error
        self._append(EventType.PREFERENCE_SET, {"key": "timezone", "value": timezone})
        if username:
            self.bind_account(username)

    def refresh(self) -> None:
        store = self._require_store()
        try:
            store.manifest()
            result = store.scan()
        except (OSError, EventStoreError) as error:
            raise InvalidOperationError(str(error)) from error
        valid_events, preference_errors = self._validated_events(result.events)
        self._scan_problems = result.problems
        self._semantic_errors = tuple(
            preference_errors + self._projection.rebuild(valid_events)
        )
        self._read_only = not store.writable()

    def bind_account(self, username: str) -> StudyEvent:
        existing = self._projection.account()
        if existing and existing != username:
            raise InvalidOperationError(f"This library is already bound to {existing}")
        return self._append(
            EventType.ACCOUNT_BOUND,
            {"username": username, "site": "leetcode.com"},
        )

    def enroll(self, reference: str, source: str = "manual") -> StudyEvent | None:
        question_key = self.question(reference).key
        if self._projection.card(question_key):
            return None
        return self._append(
            EventType.CARD_ENROLLED,
            {"question_key": question_key, "source": source},
        )

    def suspend(self, reference: str) -> StudyEvent:
        card = self._enrolled_card(reference)
        question_key = card.question_key
        if card.suspended:
            raise InvalidOperationError(
                f"Question is already suspended: {question_key}"
            )
        return self._append(EventType.CARD_SUSPENDED, {"question_key": question_key})

    def resume(self, reference: str) -> StudyEvent:
        card = self._enrolled_card(reference)
        question_key = card.question_key
        if not card.suspended:
            raise InvalidOperationError(f"Question is already active: {question_key}")
        return self._append(EventType.CARD_RESUMED, {"question_key": question_key})

    def rate(
        self,
        reference: str,
        rating: Rating,
        *,
        occurred_at: datetime | None = None,
    ) -> StudyEvent:
        card = self._enrolled_card(reference)
        question_key = card.question_key
        if card.suspended:
            raise InvalidOperationError(f"Question is suspended: {question_key}")
        return self._append(
            EventType.REVIEW_RECORDED,
            {"question_key": question_key, "rating": rating.value},
            occurred_at=occurred_at,
        )

    def correct_review(self, event_id: str, rating: Rating | None) -> StudyEvent:
        if not self._projection.has_review(event_id):
            raise InvalidOperationError(f"Review event not found: {event_id}")
        return self._append(
            EventType.REVIEW_CORRECTED,
            {"target_event_id": event_id, "rating": rating.value if rating else None},
        )

    def set_preference(self, key: str, value: Any) -> StudyEvent:
        return self.set_preferences({key: value}, _write_unchanged=True)[0]

    def set_preferences(
        self,
        changes: dict[str, Any],
        *,
        expected: StudyPreferences | None = None,
        _write_unchanged: bool = False,
    ) -> tuple[StudyEvent, ...]:
        """Save portable preferences after validation and one projection refresh."""
        if not changes:
            return ()
        try:
            for key, value in changes.items():
                validate_preference(key, value)
        except ValueError as error:
            raise InvalidOperationError(str(error)) from error

        if expected is not None:
            self.refresh()
            if self._preferences() != expected:
                raise SettingsConflictError(
                    "Study Preferences changed on another device; reload before saving"
                )

        current = self._preferences()
        candidate = StudyPreferences(**current)
        candidate.update(cast(StudyPreferences, changes))
        try:
            scheduler_from_preferences(candidate)
        except ValueError as error:
            raise InvalidOperationError(str(error)) from error

        store = self._writable_store()
        events: list[StudyEvent] = []
        try:
            for key, value in changes.items():
                if _write_unchanged or candidate[key] != current[key]:
                    events.append(
                        store.append(
                            EventType.PREFERENCE_SET, {"key": key, "value": value}
                        )
                    )
        except OSError as error:
            self._raise_write_error(error, store)
        except EventStoreUnavailableError as error:
            raise ReadOnlyLibraryError(str(error)) from error
        except EventStoreError as error:
            raise InvalidOperationError(str(error)) from error
        self.refresh()
        return tuple(events)

    def _preferences(self) -> StudyPreferences:
        return StudyPreferences(
            timezone=cast(
                str,
                self._projection.preference(
                    "timezone", DEFAULT_STUDY_PREFERENCES["timezone"]
                ),
            ),
            daily_limit=cast(
                int,
                self._projection.preference(
                    "daily_limit", DEFAULT_STUDY_PREFERENCES["daily_limit"]
                ),
            ),
            new_limit=cast(
                int,
                self._projection.preference(
                    "new_limit", DEFAULT_STUDY_PREFERENCES["new_limit"]
                ),
            ),
            desired_retention=cast(
                float,
                self._projection.preference(
                    "desired_retention",
                    DEFAULT_STUDY_PREFERENCES["desired_retention"],
                ),
            ),
            language=cast(
                str,
                self._projection.preference(
                    "language", DEFAULT_STUDY_PREFERENCES["language"]
                ),
            ),
            fsrs_parameters=cast(
                list[float] | None,
                self._projection.preference(
                    "fsrs_parameters", DEFAULT_STUDY_PREFERENCES["fsrs_parameters"]
                ),
            ),
        )

    def study_preferences(self) -> StudyPreferences:
        return self._preferences()

    def questions(self, search: str = "") -> tuple[QuestionListItem, ...]:
        cards = {
            row.question_key: CardState.SUSPENDED if row.suspended else CardState.ACTIVE
            for row in self._projection.all_card_rows()
        }
        return tuple(
            QuestionListItem(question, cards.get(question.key, CardState.NOT_ENROLLED))
            for question in self._projection.questions(search)
        )

    def question(self, reference: str) -> Question:
        question = self._projection.resolve_question(reference)
        if question is None:
            raise QuestionNotFoundError(f"Unknown question: {reference}")
        return question

    def health(self) -> LibraryHealth:
        raw_counts = self._projection.counts()
        if self._store is None:
            access = LibraryAccess.UNCONFIGURED
        elif self._read_only:
            access = LibraryAccess.READ_ONLY
        else:
            access = LibraryAccess.WRITABLE
        return LibraryHealth(
            shared_path=self._config.shared_dir or None,
            account=self._projection.account(),
            access=access,
            counts=LibraryCounts(**raw_counts),
            scan_problems=tuple(self._scan_problems),
            semantic_problems=tuple(self._semantic_errors),
        )

    def settings(self) -> ApplicationSettings:
        preferences = self._preferences()
        parameters = preferences["fsrs_parameters"]
        return ApplicationSettings(
            timezone=str(preferences["timezone"]),
            daily_limit=int(preferences["daily_limit"]),
            new_limit=int(preferences["new_limit"]),
            desired_retention=float(preferences["desired_retention"]),
            language=str(preferences["language"]),
            fsrs_parameters=(
                tuple(float(value) for value in parameters)
                if isinstance(parameters, list)
                else None
            ),
            solver_command=tuple(self._config.solver_argv),
        )

    def solver_input(self, reference: str) -> SolverInput:
        self._require_store()
        return SolverInput(self.question(reference), tuple(self._config.solver_argv))

    def set_solver_command(self, command: str) -> None:
        previous = list(self._config.solver_argv)
        self._config.set_solver_command(command)
        if not self._config.solver_argv:
            self._config.solver_argv = previous
            raise InvalidOperationError("Solver command cannot be empty")
        try:
            self._config.save(self._config_path)
        except OSError as error:
            self._config.solver_argv = previous
            raise InvalidOperationError(
                f"Could not save local configuration: {error}"
            ) from error

    def daily_plan(self, now: datetime | None = None) -> DailyPlan:
        preferences = self._preferences()
        instant = (now or datetime.now(UTC)).astimezone(UTC)
        timezone = ZoneInfo(str(preferences["timezone"]))
        local_now = instant.astimezone(timezone)
        start_of_day = local_now.replace(
            hour=0, minute=0, second=0, microsecond=0
        ).astimezone(UTC)
        reviewed_today, new_reviewed_today = self._projection.review_activity_since(
            start_of_day
        )
        due: list[PlanItem] = []
        new: list[PlanItem] = []
        for card in self._projection.card_rows():
            reviews = self._projection.reviews(card.question_key)
            due_at = replay_due(card.enrolled_at, reviews, preferences)
            item = PlanItem(
                question_key=card.question_key,
                frontend_id=card.frontend_id or "?",
                slug=card.slug or card.question_key.split(":", 1)[-1],
                title=card.title or card.question_key,
                difficulty=card.difficulty or "Unknown",
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
        self._projection.upsert_questions(questions)
        return len(questions)

    def import_accepted(self, questions: list[Question]) -> int:
        self._projection.upsert_questions(questions)
        enrolled = 0
        for question in questions:
            if question.accepted and self.enroll(
                question.key, source="leetcode-import"
            ):
                enrolled += 1
        return enrolled

    def _require_store(self) -> EventStore:
        if self._store is None:
            raise NotConfiguredError(
                "No study library configured; run `leetcode-fsrs init`"
            )
        return self._store

    def _enrolled_card(self, reference: str) -> CardRecord:
        question_key = self.question(reference).key
        card = self._projection.card(question_key)
        if card is None:
            raise InvalidOperationError(f"Question is not enrolled: {question_key}")
        return card

    def _append(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        *,
        occurred_at: datetime | None = None,
    ) -> StudyEvent:
        store = self._writable_store()
        try:
            event = store.append(event_type, payload, occurred_at=occurred_at)
        except OSError as error:
            self._raise_write_error(error, store)
        except EventStoreUnavailableError as error:
            raise ReadOnlyLibraryError(str(error)) from error
        except EventStoreError as error:
            raise InvalidOperationError(str(error)) from error
        self.refresh()
        return event

    def _writable_store(self) -> EventStore:
        store = self._require_store()
        if self._read_only or not store.writable():
            raise ReadOnlyLibraryError(f"Study library is read-only: {store.root}")
        return store

    @staticmethod
    def _raise_write_error(error: OSError, store: EventStore) -> Never:
        if isinstance(error, PermissionError) or error.errno in {
            errno.EACCES,
            errno.EPERM,
            errno.EROFS,
        }:
            raise ReadOnlyLibraryError(
                f"Study library is read-only: {store.root}"
            ) from error
        raise InvalidOperationError(str(error)) from error

    @staticmethod
    def _validated_events(
        events: tuple[StudyEvent, ...],
    ) -> tuple[tuple[StudyEvent, ...], list[str]]:
        preferences = StudyPreferences(**DEFAULT_STUDY_PREFERENCES)
        valid: list[StudyEvent] = []
        errors: list[str] = []
        for event in events:
            if event.type is not EventType.PREFERENCE_SET:
                valid.append(event)
                continue
            key = str(event.payload["key"])
            value = event.payload["value"]
            candidate = StudyPreferences(**preferences)
            candidate[key] = value  # type: ignore[literal-required]
            try:
                scheduler_from_preferences(candidate)
            except (TypeError, ValueError) as error:
                errors.append(f"invalid preference event {event.event_id}: {error}")
                continue
            preferences = candidate
            valid.append(event)
        return tuple(valid), errors
