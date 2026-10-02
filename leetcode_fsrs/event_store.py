"""Sync-safe, append-only study event storage."""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .domain import EventType, ScanProblem, StudyEvent


SCHEMA_VERSION = 1


class EventStoreError(RuntimeError):
    pass


class EventStoreUnavailableError(EventStoreError):
    pass


@dataclass(frozen=True, slots=True)
class LibraryManifest:
    schema_version: int
    library_id: str
    site: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ScanResult:
    events: tuple[StudyEvent, ...]
    problems: tuple[ScanProblem, ...]


class EventStore:
    def __init__(self, root: Path, device_id: str):
        self.root = root
        self.device_id = device_id
        self._sequence = 0

    @property
    def manifest_path(self) -> Path:
        return self.root / "library.json"

    @classmethod
    def create(cls, root: Path, device_id: str, site: str = "leetcode.com") -> "EventStore":
        root.mkdir(parents=True, exist_ok=True)
        path = root / "library.json"
        if path.exists():
            return cls(root, device_id)
        manifest = LibraryManifest(
            schema_version=SCHEMA_VERSION,
            library_id=str(uuid.uuid4()),
            site=site,
            created_at=datetime.now(UTC).isoformat(),
        )
        encoded = (json.dumps(asdict(manifest), indent=2) + "\n").encode()
        try:
            descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            return cls(root, device_id)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        except OSError:
            path.unlink(missing_ok=True)
            raise
        (root / "events").mkdir(exist_ok=True)
        return cls(root, device_id)

    def manifest(self) -> LibraryManifest:
        try:
            data = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            manifest = LibraryManifest(**data)
        except (OSError, ValueError, TypeError) as error:
            raise EventStoreError(f"Invalid study library manifest: {error}") from error
        if manifest.schema_version != SCHEMA_VERSION:
            raise EventStoreError(
                f"Unsupported library schema {manifest.schema_version}; expected {SCHEMA_VERSION}"
            )
        if manifest.site != "leetcode.com":
            raise EventStoreError(f"Unsupported LeetCode site: {manifest.site}")
        return manifest

    def writable(self) -> bool:
        return self.root.is_dir() and os.access(self.root, os.R_OK | os.W_OK)

    def append(
        self,
        event_type: EventType,
        payload: dict[str, Any],
        *,
        occurred_at: datetime | None = None,
    ) -> StudyEvent:
        if not self.writable():
            raise EventStoreUnavailableError(
                f"Study data directory is unavailable or read-only: {self.root}"
            )
        manifest = self.manifest()
        supplied = occurred_at or datetime.now(UTC)
        if supplied.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        now = supplied.astimezone(UTC)
        self._sequence = max(self._sequence, self._max_device_sequence()) + 1
        event = StudyEvent(
            schema_version=SCHEMA_VERSION,
            event_id=str(uuid.uuid4()),
            library_id=manifest.library_id,
            device_id=self.device_id,
            sequence=self._sequence,
            occurred_at=now,
            type=event_type,
            payload=payload,
        )
        _validate_event(event)
        target = self.root / "events" / self.device_id / f"{now.date().isoformat()}.ndjson"
        target.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(_event_to_dict(event), ensure_ascii=False, separators=(",", ":")) + "\n"
        with target.open("a", encoding="utf-8") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        return event

    def scan(self) -> ScanResult:
        manifest = self.manifest()
        events: dict[str, StudyEvent] = {}
        problems: list[ScanProblem] = []
        event_root = self.root / "events"
        if not event_root.exists():
            return ScanResult((), ())
        for path in sorted(event_root.glob("*/*.ndjson")):
            try:
                source = path.read_text(encoding="utf-8")
            except OSError as error:
                problems.append(ScanProblem(str(path), None, str(error)))
                continue
            lines = source.splitlines(keepends=True)
            for line_number, raw in enumerate(lines, 1):
                if not raw.endswith("\n"):
                    continue
                try:
                    event = _event_from_dict(json.loads(raw))
                    if event.library_id != manifest.library_id:
                        raise ValueError("event belongs to another study library")
                    previous = events.get(event.event_id)
                    if previous is not None and previous != event:
                        raise ValueError("event ID has conflicting contents")
                    events[event.event_id] = event
                except (ValueError, TypeError, KeyError, json.JSONDecodeError) as error:
                    problems.append(ScanProblem(str(path), line_number, str(error)))
        ordered = sorted(events.values(), key=lambda item: (item.occurred_at, item.event_id))
        return ScanResult(tuple(ordered), tuple(problems))

    def _max_device_sequence(self) -> int:
        maximum = 0
        event_root = self.root / "events" / self.device_id
        if not event_root.exists():
            return maximum
        for path in event_root.glob("*.ndjson"):
            try:
                for raw in path.read_text(encoding="utf-8").splitlines():
                    data = json.loads(raw)
                    maximum = max(maximum, int(data.get("sequence", 0)))
            except (OSError, ValueError, TypeError):
                continue
        return maximum


def _event_to_dict(event: StudyEvent) -> dict[str, Any]:
    return {
        "schema_version": event.schema_version,
        "event_id": event.event_id,
        "library_id": event.library_id,
        "device_id": event.device_id,
        "sequence": event.sequence,
        "occurred_at": event.occurred_at.astimezone(UTC).isoformat(),
        "type": event.type.value,
        "payload": event.payload,
    }


def _event_from_dict(data: dict[str, Any]) -> StudyEvent:
    version = int(data["schema_version"])
    if version != SCHEMA_VERSION:
        raise ValueError(f"unsupported event schema {version}")
    occurred_at = datetime.fromisoformat(str(data["occurred_at"]))
    if occurred_at.tzinfo is None:
        raise ValueError("occurred_at must include a timezone")
    event = StudyEvent(
        schema_version=version,
        event_id=str(uuid.UUID(str(data["event_id"]))),
        library_id=str(uuid.UUID(str(data["library_id"]))),
        device_id=str(uuid.UUID(str(data["device_id"]))),
        sequence=int(data["sequence"]),
        occurred_at=occurred_at.astimezone(UTC),
        type=EventType(str(data["type"])),
        payload=dict(data["payload"]),
    )
    _validate_event(event)
    return event


def _validate_event(event: StudyEvent) -> None:
    if event.sequence < 1:
        raise ValueError("sequence must be positive")
    payload = event.payload
    required: dict[EventType, tuple[str, ...]] = {
        EventType.ACCOUNT_BOUND: ("username",),
        EventType.CARD_ENROLLED: ("question_key",),
        EventType.CARD_SUSPENDED: ("question_key",),
        EventType.CARD_RESUMED: ("question_key",),
        EventType.REVIEW_RECORDED: ("question_key", "rating"),
        EventType.REVIEW_CORRECTED: ("target_event_id", "rating"),
        EventType.PREFERENCE_SET: ("key", "value"),
    }
    missing = [key for key in required[event.type] if key not in payload]
    if missing:
        raise ValueError(f"{event.type.value} payload is missing {', '.join(missing)}")
    for key in ("username", "question_key", "target_event_id", "key"):
        if key in payload and not str(payload[key]).strip():
            raise ValueError(f"{key} cannot be empty")
    if event.type == EventType.REVIEW_RECORDED:
        from .domain import Rating

        Rating(str(payload["rating"]))
    if event.type == EventType.REVIEW_CORRECTED and payload["rating"] is not None:
        from .domain import Rating

        Rating(str(payload["rating"]))


def write_events(store: EventStore, events: Iterable[tuple[EventType, dict[str, Any]]]) -> None:
    for event_type, payload in events:
        store.append(event_type, payload)
