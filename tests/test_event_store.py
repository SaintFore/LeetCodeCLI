import json
from pathlib import Path

from leetcode_fsrs.domain import EventType
from leetcode_fsrs.event_store import EventStore
from leetcode_fsrs.config import LocalConfig
from leetcode_fsrs.services import ApplicationService, LibraryAccess


def test_two_devices_merge_without_editing_the_same_file(tmp_path: Path) -> None:
    first = EventStore.create(tmp_path, "11111111-1111-4111-8111-111111111111")
    second = EventStore(tmp_path, "22222222-2222-4222-8222-222222222222")
    first.append(EventType.CARD_ENROLLED, {"question_key": "leetcode.com:two-sum"})
    second.append(EventType.PREFERENCE_SET, {"key": "daily_limit", "value": 10})

    result = first.scan()

    assert len(result.events) == 2
    assert not result.problems
    assert len(list((tmp_path / "events").glob("*/*.ndjson"))) == 2


def test_scan_skips_corruption_and_incomplete_final_write(tmp_path: Path) -> None:
    store = EventStore.create(tmp_path, "11111111-1111-4111-8111-111111111111")
    store.append(EventType.PREFERENCE_SET, {"key": "daily_limit", "value": 10})
    event_file = next((tmp_path / "events").glob("*/*.ndjson"))
    with event_file.open("a", encoding="utf-8") as stream:
        stream.write("{bad json}\n")
        stream.write(json.dumps({"partial": True}))

    result = store.scan()

    assert len(result.events) == 1
    assert len(result.problems) == 1
    assert result.problems[0].line == 2


def test_missing_shared_directory_keeps_local_projection_readable(tmp_path: Path) -> None:
    missing = tmp_path / "offline-mount"
    config = LocalConfig(shared_dir=str(missing))

    service = ApplicationService(
        config,
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )

    health = service.health()
    assert health.access is LibraryAccess.READ_ONLY
    assert health.semantic_problems
    assert health.counts.cards == 0
