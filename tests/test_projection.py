from datetime import UTC, datetime
from pathlib import Path

from leetcode_fsrs.domain import EventType, Question, Rating, Review
from leetcode_fsrs.event_store import EventStore
from leetcode_fsrs.projection import CardRecord, Projection


def test_projection_maps_sql_rows_to_typed_values(tmp_path: Path) -> None:
    library = EventStore.create(
        tmp_path / "shared", "11111111-1111-4111-8111-111111111111"
    )
    occurred_at = datetime(2026, 1, 1, tzinfo=UTC)
    library.append(
        EventType.CARD_ENROLLED,
        {"question_key": "leetcode.com:two-sum", "source": "manual"},
        occurred_at=occurred_at,
    )
    library.append(
        EventType.REVIEW_RECORDED,
        {"question_key": "leetcode.com:two-sum", "rating": "good"},
        occurred_at=occurred_at,
    )
    projection = Projection(tmp_path / "projection.sqlite3")
    projection.upsert_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy")]
    )

    assert projection.rebuild(library.scan().events) == []

    card = projection.card_rows()[0]
    review = projection.reviews(card.question_key)[0]
    assert isinstance(card, CardRecord)
    assert card.frontend_id == "1"
    assert isinstance(review, Review)
    assert review.rating is Rating.GOOD
