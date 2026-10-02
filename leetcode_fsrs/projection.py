"""Local SQLite projection of immutable study events and LeetCode cache."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable, Iterator

from .domain import EventType, Question, Rating, Review, StudyEvent


@dataclass(frozen=True, slots=True)
class CardRecord:
    question_key: str
    enrolled_at: datetime
    source: str
    suspended: bool
    frontend_id: str | None = None
    slug: str | None = None
    title: str | None = None
    difficulty: str | None = None


class Projection:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    payload_json TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS cards (
                    question_key TEXT PRIMARY KEY,
                    enrolled_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    suspended INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS reviews (
                    event_id TEXT PRIMARY KEY,
                    question_key TEXT NOT NULL,
                    rating TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    corrected_by TEXT,
                    voided INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS preferences (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    event_id TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS account (
                    singleton INTEGER PRIMARY KEY CHECK(singleton = 1),
                    username TEXT NOT NULL,
                    site TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS questions (
                    question_key TEXT PRIMARY KEY,
                    frontend_id TEXT NOT NULL,
                    slug TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    difficulty TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    url TEXT NOT NULL,
                    accepted INTEGER NOT NULL DEFAULT 0,
                    content TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL
                );
                """
            )

    def rebuild(self, events: Iterable[StudyEvent]) -> list[str]:
        ordered = sorted(events, key=lambda event: (event.occurred_at, event.event_id))
        corrections: dict[str, StudyEvent] = {}
        for event in ordered:
            if event.type == EventType.REVIEW_CORRECTED:
                target = str(event.payload.get("target_event_id", ""))
                corrections[target] = event
        errors: list[str] = []
        with self.connect() as db:
            db.execute("DELETE FROM events")
            db.execute("DELETE FROM cards")
            db.execute("DELETE FROM reviews")
            db.execute("DELETE FROM preferences")
            db.execute("DELETE FROM account")
            for event in ordered:
                payload = event.payload
                db.execute(
                    "INSERT INTO events VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        event.event_id,
                        event.type.value,
                        event.occurred_at.isoformat(),
                        event.device_id,
                        event.sequence,
                        json.dumps(payload, ensure_ascii=False),
                    ),
                )
                if event.type == EventType.ACCOUNT_BOUND:
                    username = str(payload["username"])
                    existing = db.execute("SELECT username FROM account WHERE singleton = 1").fetchone()
                    if existing and existing["username"] != username:
                        errors.append(f"study library is already bound to {existing['username']}")
                    else:
                        db.execute(
                            "INSERT OR REPLACE INTO account VALUES (1, ?, ?)",
                            (username, str(payload.get("site", "leetcode.com"))),
                        )
                elif event.type == EventType.CARD_ENROLLED:
                    db.execute(
                        "INSERT OR IGNORE INTO cards(question_key, enrolled_at, source) VALUES (?, ?, ?)",
                        (str(payload["question_key"]), event.occurred_at.isoformat(), str(payload.get("source", "manual"))),
                    )
                elif event.type in (EventType.CARD_SUSPENDED, EventType.CARD_RESUMED):
                    db.execute(
                        "UPDATE cards SET suspended = ? WHERE question_key = ?",
                        (event.type == EventType.CARD_SUSPENDED, str(payload["question_key"])),
                    )
                elif event.type == EventType.REVIEW_RECORDED:
                    correction = corrections.get(event.event_id)
                    rating = str(payload["rating"])
                    voided = 0
                    corrected_by = None
                    if correction:
                        corrected_by = correction.event_id
                        replacement = correction.payload.get("rating")
                        if replacement is None:
                            voided = 1
                        else:
                            rating = Rating(str(replacement)).value
                    db.execute(
                        "INSERT INTO reviews VALUES (?, ?, ?, ?, ?, ?)",
                        (
                            event.event_id,
                            str(payload["question_key"]),
                            Rating(rating).value,
                            event.occurred_at.isoformat(),
                            corrected_by,
                            voided,
                        ),
                    )
                elif event.type == EventType.PREFERENCE_SET:
                    db.execute(
                        "INSERT OR REPLACE INTO preferences VALUES (?, ?, ?, ?)",
                        (
                            str(payload["key"]),
                            json.dumps(payload.get("value"), ensure_ascii=False),
                            event.occurred_at.isoformat(),
                            event.event_id,
                        ),
                    )
        return errors

    def upsert_questions(self, questions: Iterable[Question]) -> None:
        now = datetime.now(UTC).isoformat()
        with self.connect() as db:
            db.executemany(
                """
                INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(question_key) DO UPDATE SET
                    frontend_id=excluded.frontend_id,
                    slug=excluded.slug,
                    title=excluded.title,
                    difficulty=excluded.difficulty,
                    tags_json=excluded.tags_json,
                    url=excluded.url,
                    accepted=excluded.accepted,
                    content=CASE WHEN excluded.content = '' THEN questions.content ELSE excluded.content END,
                    updated_at=excluded.updated_at
                """,
                [
                    (
                        q.key,
                        q.frontend_id,
                        q.slug,
                        q.title,
                        q.difficulty,
                        json.dumps(q.tags, ensure_ascii=False),
                        q.url,
                        q.accepted,
                        q.content,
                        now,
                    )
                    for q in questions
                ],
            )

    def questions(self, search: str = "", enrolled_only: bool = False) -> list[Question]:
        clauses: list[str] = []
        params: list[object] = []
        if search:
            clauses.append("(q.title LIKE ? OR q.slug LIKE ? OR q.frontend_id LIKE ?)")
            value = f"%{search}%"
            params.extend((value, value, value))
        if enrolled_only:
            clauses.append("c.question_key IS NOT NULL")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        with self.connect() as db:
            rows = db.execute(
                "SELECT q.* FROM questions q LEFT JOIN cards c ON c.question_key = q.question_key"
                + where
                + " ORDER BY CAST(q.frontend_id AS INTEGER), q.frontend_id",
                params,
            ).fetchall()
        return [_row_question(row) for row in rows]

    def question(self, key: str) -> Question | None:
        with self.connect() as db:
            row = db.execute("SELECT * FROM questions WHERE question_key = ?", (key,)).fetchone()
        return _row_question(row) if row else None

    def resolve_question(self, reference: str) -> Question | None:
        with self.connect() as db:
            row = None
            for column in ("question_key", "slug", "frontend_id"):
                row = db.execute(
                    f"SELECT * FROM questions WHERE {column} = ? ORDER BY question_key LIMIT 1",
                    (reference,),
                ).fetchone()
                if row is not None:
                    break
        return _row_question(row) if row else None

    def card_rows(self) -> list[CardRecord]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT c.*, q.frontend_id, q.slug, q.title, q.difficulty
                FROM cards c LEFT JOIN questions q ON q.question_key = c.question_key
                WHERE c.suspended = 0
                """
            ).fetchall()
        return [_row_card(row) for row in rows]

    def card(self, question_key: str) -> CardRecord | None:
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM cards WHERE question_key = ?", (question_key,)
            ).fetchone()
        return _row_card(row) if row else None

    def all_card_rows(self) -> list[CardRecord]:
        with self.connect() as db:
            rows = db.execute(
                """
                SELECT c.*, q.frontend_id, q.slug, q.title, q.difficulty
                FROM cards c LEFT JOIN questions q ON q.question_key = c.question_key
                ORDER BY c.enrolled_at, c.question_key
                """
            ).fetchall()
        return [_row_card(row) for row in rows]

    def reviews(self, question_key: str) -> list[Review]:
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM reviews WHERE question_key = ? AND voided = 0 ORDER BY occurred_at, event_id",
                (question_key,),
            ).fetchall()
        return [_row_review(row) for row in rows]

    def has_review(self, event_id: str) -> bool:
        with self.connect() as db:
            row = db.execute("SELECT 1 FROM reviews WHERE event_id = ?", (event_id,)).fetchone()
        return row is not None

    def review_activity_since(self, since: datetime) -> tuple[int, int]:
        """Return total and first-ever reviews since an aware UTC instant."""
        with self.connect() as db:
            row = db.execute(
                """
                SELECT COUNT(*) AS total,
                       COALESCE(SUM(
                           NOT EXISTS (
                               SELECT 1 FROM reviews earlier
                               WHERE earlier.question_key = current.question_key
                                 AND earlier.voided = 0
                                 AND (earlier.occurred_at < current.occurred_at OR
                                      (earlier.occurred_at = current.occurred_at AND earlier.event_id < current.event_id))
                           )
                       ), 0) AS first_reviews
                FROM reviews current
                WHERE current.voided = 0 AND current.occurred_at >= ?
                """,
                (since.astimezone(UTC).isoformat(),),
            ).fetchone()
        return int(row["total"]), int(row["first_reviews"])

    def preference(self, key: str, default: object = None) -> object:
        with self.connect() as db:
            row = db.execute("SELECT value_json FROM preferences WHERE key = ?", (key,)).fetchone()
        return json.loads(row["value_json"]) if row else default

    def account(self) -> str | None:
        with self.connect() as db:
            row = db.execute("SELECT username FROM account WHERE singleton = 1").fetchone()
        return str(row["username"]) if row else None

    def counts(self) -> dict[str, int]:
        with self.connect() as db:
            return {
                "questions": db.execute("SELECT COUNT(*) FROM questions").fetchone()[0],
                "cards": db.execute("SELECT COUNT(*) FROM cards").fetchone()[0],
                "reviews": db.execute("SELECT COUNT(*) FROM reviews WHERE voided = 0").fetchone()[0],
                "suspended": db.execute("SELECT COUNT(*) FROM cards WHERE suspended = 1").fetchone()[0],
            }


def _row_question(row: sqlite3.Row) -> Question:
    return Question(
        key=str(row["question_key"]),
        frontend_id=str(row["frontend_id"]),
        slug=str(row["slug"]),
        title=str(row["title"]),
        difficulty=str(row["difficulty"]),
        tags=tuple(json.loads(row["tags_json"])),
        url=str(row["url"]),
        accepted=bool(row["accepted"]),
        content=str(row["content"]),
    )


def _row_card(row: sqlite3.Row) -> CardRecord:
    keys = set(row.keys())
    return CardRecord(
        question_key=str(row["question_key"]),
        enrolled_at=datetime.fromisoformat(str(row["enrolled_at"])),
        source=str(row["source"]),
        suspended=bool(row["suspended"]),
        frontend_id=(
            str(row["frontend_id"])
            if "frontend_id" in keys and row["frontend_id"] is not None
            else None
        ),
        slug=str(row["slug"]) if "slug" in keys and row["slug"] is not None else None,
        title=str(row["title"]) if "title" in keys and row["title"] is not None else None,
        difficulty=str(row["difficulty"]) if "difficulty" in keys and row["difficulty"] is not None else None,
    )


def _row_review(row: sqlite3.Row) -> Review:
    return Review(
        event_id=str(row["event_id"]),
        question_key=str(row["question_key"]),
        rating=Rating(str(row["rating"])),
        occurred_at=datetime.fromisoformat(str(row["occurred_at"])),
        corrected_by=str(row["corrected_by"]) if row["corrected_by"] is not None else None,
    )
