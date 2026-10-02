from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from leetcode_fsrs.config import LocalConfig
from leetcode_fsrs.domain import Question, Rating
from leetcode_fsrs.services import (
    ApplicationService,
    ApplicationSettings,
    CardState,
    InvalidOperationError,
    LibraryAccess,
    NotConfiguredError,
    QuestionListItem,
    QuestionNotFoundError,
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
