from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from leetcode_fsrs.config import LocalConfig
from leetcode_fsrs.domain import EventType, Question, Rating
from leetcode_fsrs.event_store import EventStore
from leetcode_fsrs.services import (
    ApplicationService,
    ApplicationSettings,
    CardState,
    InvalidOperationError,
    LibraryAccess,
    NotConfiguredError,
    QuestionListItem,
    QuestionNotFoundError,
    ReadOnlyLibraryError,
    SolverInput,
)


def questions(count: int) -> list[Question]:
    return [
        Question(
            key=f"leetcode.com:q-{number}",
            frontend_id=str(number),
            slug=f"q-{number}",
            title=f"Question {number}",
            difficulty="Easy",
            accepted=True,
        )
        for number in range(1, count + 1)
    ]


def test_accepted_import_enrolls_once_and_limits_new_cards(service) -> None:
    catalog = questions(8)

    assert service.import_accepted(catalog) == 8
    assert service.import_accepted(catalog) == 0

    plan = service.daily_plan()
    assert len(plan.items) == 5
    assert plan.new_backlog == 8
    assert all(item.is_new for item in plan.items)


def test_due_cards_precede_new_and_suspend_is_excluded(service) -> None:
    catalog = questions(3)
    service.import_accepted(catalog)
    reviewed_at = datetime.now(UTC) - timedelta(days=30)
    service.rate(catalog[0].key, Rating.GOOD, occurred_at=reviewed_at)
    service.suspend(catalog[1].key)

    plan = service.daily_plan()

    assert [item.question_key for item in plan.items] == [catalog[0].key, catalog[2].key]
    assert plan.items[0].is_new is False


def test_review_correction_is_applied_during_rebuild(service) -> None:
    question = questions(1)[0]
    service.import_accepted([question])
    reviewed_at = datetime(2026, 1, 1, tzinfo=UTC)
    review = service.rate(question.key, Rating.AGAIN, occurred_at=reviewed_at)
    service.correct_review(review.event_id, Rating.EASY)

    plan = service.daily_plan(reviewed_at + timedelta(days=2))

    assert plan.items == ()
    assert plan.due_backlog == 0


def test_first_review_today_consumes_daily_new_limit(service) -> None:
    catalog = questions(8)
    service.import_accepted(catalog)
    now = datetime.now(UTC)
    service.rate(catalog[0].key, Rating.GOOD, occurred_at=now)

    plan = service.daily_plan(now)

    assert len([item for item in plan.items if item.is_new]) == 4


def test_question_queries_return_immutable_typed_values_and_resolve_every_reference(service) -> None:
    question = questions(1)[0]
    service.cache_questions([question])

    assert service.questions() == (QuestionListItem(question, CardState.NOT_ENROLLED),)
    assert service.question(question.key) == question
    assert service.question(question.slug) == question
    assert service.question(question.frontend_id) == question

    service.enroll(question.slug)

    assert service.questions("Question") == (QuestionListItem(question, CardState.ACTIVE),)
    with pytest.raises(QuestionNotFoundError, match="Unknown question"):
        service.question("missing")


def test_health_settings_and_solver_input_hide_application_internals(service) -> None:
    question = questions(1)[0]
    service.cache_questions([question])
    service.enroll(question.key)
    service.set_preference("daily_limit", 12)
    service.set_solver_command("nvim +Leet {slug}")

    health = service.health()
    settings = service.settings()

    assert health.access is LibraryAccess.WRITABLE
    assert health.account == "alice"
    assert health.counts.questions == 1
    assert health.counts.cards == 1
    assert health.scan_problems == ()
    assert settings == ApplicationSettings(
        timezone="Asia/Shanghai",
        daily_limit=12,
        new_limit=5,
        desired_retention=0.9,
        language="zh",
        fsrs_parameters=None,
        solver_command=("nvim", "+Leet", "{slug}"),
    )
    assert service.solver_input("1") == SolverInput(question, ("nvim", "+Leet", "{slug}"))


def test_commands_resolve_references_and_report_invalid_transitions(service) -> None:
    question = questions(1)[0]
    service.cache_questions([question])

    service.enroll(question.slug)
    service.suspend(question.frontend_id)
    assert service.questions()[0].state is CardState.SUSPENDED

    with pytest.raises(InvalidOperationError, match="already suspended"):
        service.suspend(question.key)
    with pytest.raises(InvalidOperationError, match="suspended"):
        service.rate(question.key, Rating.GOOD)

    service.resume(question.slug)
    review = service.rate(question.frontend_id, Rating.GOOD)
    assert review.payload["question_key"] == question.key
    with pytest.raises(InvalidOperationError, match="already active"):
        service.resume(question.key)


def test_question_search_does_not_refresh_study_events(service, monkeypatch) -> None:
    question = questions(1)[0]
    service.cache_questions([question])

    def unexpected_refresh() -> None:
        raise AssertionError("question search must only query the local Question Cache")

    monkeypatch.setattr(service, "refresh", unexpected_refresh)

    assert service.questions("q-1") == (QuestionListItem(question, CardState.NOT_ENROLLED),)


def test_unconfigured_health_is_readable_but_solver_input_is_not(tmp_path: Path) -> None:
    service = ApplicationService(
        LocalConfig(),
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )
    question = questions(1)[0]
    service.cache_questions([question])

    assert service.health().access is LibraryAccess.UNCONFIGURED
    assert service.questions()[0].question == question
    with pytest.raises(NotConfiguredError, match="No study library configured"):
        service.solver_input(question.key)


def test_review_correction_rejects_an_unknown_study_event(service) -> None:
    with pytest.raises(InvalidOperationError, match="Review event not found"):
        service.correct_review("missing", Rating.GOOD)


def test_ambiguous_frontend_id_is_not_resolved(service) -> None:
    first, second = questions(2)
    second = Question(
        second.key,
        first.frontend_id,
        second.slug,
        second.title,
        second.difficulty,
    )
    service.cache_questions([first, second])

    with pytest.raises(QuestionNotFoundError):
        service.question(first.frontend_id)


def test_write_time_permission_failure_is_a_read_only_error(service, monkeypatch) -> None:
    question = questions(1)[0]
    service.cache_questions([question])

    def permission_denied(*args, **kwargs):
        raise PermissionError("permission denied")

    monkeypatch.setattr(EventStore, "append", permission_denied)

    with pytest.raises(ReadOnlyLibraryError, match="read-only"):
        service.enroll(question.key)


def test_explicit_refresh_reports_replicated_events_and_problems(service, tmp_path: Path) -> None:
    replica = EventStore(
        tmp_path / "shared",
        "22222222-2222-4222-8222-222222222222",
    )
    replica.append(EventType.CARD_ENROLLED, {"question_key": "leetcode.com:replicated"})
    event_file = next((tmp_path / "shared" / "events").glob("*/*.ndjson"))
    with event_file.open("a", encoding="utf-8") as stream:
        stream.write("{bad json}\n")

    service.refresh()

    health = service.health()
    assert health.counts.cards == 1
    assert len(health.scan_problems) == 1


def test_startup_refreshes_an_existing_study_library(tmp_path: Path) -> None:
    shared = tmp_path / "shared"
    store = EventStore.create(shared, "22222222-2222-4222-8222-222222222222")
    store.append(EventType.CARD_ENROLLED, {"question_key": "leetcode.com:replicated"})

    service = ApplicationService(
        LocalConfig(shared_dir=str(shared)),
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )

    assert service.health().counts.cards == 1


def test_health_reports_semantic_problems(service, tmp_path: Path) -> None:
    replica = EventStore(
        tmp_path / "shared",
        "22222222-2222-4222-8222-222222222222",
    )
    replica.append(
        EventType.ACCOUNT_BOUND,
        {"username": "bob", "site": "leetcode.com"},
    )

    service.refresh()

    assert service.health().semantic_problems == (
        "study library is already bound to alice",
    )


def test_all_study_event_commands_reject_a_read_only_library(service, monkeypatch) -> None:
    first, second, third = questions(3)
    service.cache_questions([first, second, third])
    service.enroll(first.key)
    service.enroll(second.key)
    service.suspend(second.key)
    review = service.rate(first.key, Rating.GOOD)
    monkeypatch.setattr(EventStore, "writable", lambda self: False)

    operations = (
        lambda: service.bind_account("alice"),
        lambda: service.enroll(third.key),
        lambda: service.suspend(first.key),
        lambda: service.resume(second.key),
        lambda: service.rate(first.key, Rating.GOOD),
        lambda: service.correct_review(review.event_id, Rating.EASY),
        lambda: service.set_preference("daily_limit", 10),
    )
    for operation in operations:
        with pytest.raises(ReadOnlyLibraryError):
            operation()


def test_all_write_intents_return_expected_results_and_refresh_reads(service) -> None:
    first, second = questions(2)
    assert service.cache_questions([first, second]) == 2

    account = service.bind_account("alice")
    enrolled = service.enroll(first.slug)
    suspended = service.suspend(first.frontend_id)
    resumed = service.resume(first.key)
    reviewed = service.rate(first.slug, Rating.AGAIN)
    corrected = service.correct_review(reviewed.event_id, Rating.EASY)
    preference = service.set_preference("daily_limit", 12)
    imported = service.import_accepted([second])
    service.set_solver_command("nvim +Leet {slug}")

    assert account.type is EventType.ACCOUNT_BOUND
    assert enrolled and enrolled.type is EventType.CARD_ENROLLED
    assert suspended.type is EventType.CARD_SUSPENDED
    assert resumed.type is EventType.CARD_RESUMED
    assert reviewed.type is EventType.REVIEW_RECORDED
    assert corrected.type is EventType.REVIEW_CORRECTED
    assert preference.type is EventType.PREFERENCE_SET
    assert imported == 1
    assert [item.state for item in service.questions()] == [CardState.ACTIVE, CardState.ACTIVE]
    assert service.health().counts == service.health().counts.__class__(2, 2, 1, 0)
    assert service.settings().daily_limit == 12
    assert service.solver_input(first.key).command == ("nvim", "+Leet", "{slug}")


def test_readable_nonwritable_library_keeps_passive_queries_available(
    tmp_path: Path,
    monkeypatch,
) -> None:
    shared = tmp_path / "shared"
    config = LocalConfig(shared_dir=str(shared))
    store = EventStore.create(shared, config.device_id)
    store.append(EventType.CARD_ENROLLED, {"question_key": "leetcode.com:two-sum"})
    writable = ApplicationService(
        config,
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )
    writable.cache_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy")]
    )
    monkeypatch.setattr(EventStore, "writable", lambda self: False)

    read_only = ApplicationService(
        config,
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )

    assert read_only.health().access is LibraryAccess.READ_ONLY
    assert read_only.questions()[0].state is CardState.ACTIVE
    assert len(read_only.daily_plan().items) == 1
