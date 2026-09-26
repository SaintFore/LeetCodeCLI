from datetime import UTC, datetime, timedelta

from leetcode_fsrs.domain import Question, Rating


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
    review = service.rate(question.key, Rating.AGAIN)
    service.correct_review(review.event_id, Rating.EASY)

    rows = service.projection.reviews(question.key)

    assert len(rows) == 1
    assert rows[0]["rating"] == "easy"
    assert rows[0]["corrected_by"]


def test_first_review_today_consumes_daily_new_limit(service) -> None:
    catalog = questions(8)
    service.import_accepted(catalog)
    now = datetime.now(UTC)
    service.rate(catalog[0].key, Rating.GOOD, occurred_at=now)

    plan = service.daily_plan(now)

    assert len([item for item in plan.items if item.is_new]) == 4
