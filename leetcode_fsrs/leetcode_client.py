"""Narrow LeetCode HTTP adapter used only for explicit imports."""

from __future__ import annotations

from typing import Any

import requests

from .domain import Question

BASE_URL = "https://leetcode.com"
GRAPHQL_URL = f"{BASE_URL}/graphql"


class LeetCodeError(RuntimeError):
    pass


class LeetCodeClient:
    def __init__(self, cookie: str, timeout: float = 20):
        self.timeout = timeout
        self.session = requests.Session()
        cookie = cookie.strip()
        if "LEETCODE_SESSION=" not in cookie:
            cookie = f"LEETCODE_SESSION={cookie}"
        self.session.headers.update(
            {
                "Cookie": cookie,
                "User-Agent": "leetcode-fsrs/2",
                "Referer": BASE_URL,
                "Origin": BASE_URL,
            }
        )
        for part in cookie.split(";"):
            name, separator, value = part.strip().partition("=")
            if separator and name == "csrftoken":
                self.session.headers["X-CSRFToken"] = value
                break

    def username(self) -> str:
        data = (
            self._graphql(
                "query globalData { userStatus { isSignedIn username } }"
            ).get("userStatus")
            or {}
        )
        if not data.get("isSignedIn") or not data.get("username"):
            raise LeetCodeError("LeetCode session is invalid or expired")
        return str(data["username"])

    def questions(self) -> list[Question]:
        try:
            response = self.session.get(
                f"{BASE_URL}/api/problems/all/", timeout=self.timeout
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as error:
            raise LeetCodeError(
                f"Could not fetch LeetCode problem catalog: {error}"
            ) from error

        questions: list[Question] = []
        difficulties = {1: "Easy", 2: "Medium", 3: "Hard"}
        for pair in payload.get("stat_status_pairs", []):
            stat = pair.get("stat") or {}
            slug = str(stat.get("question__title_slug") or "")
            if not slug:
                continue
            level = (pair.get("difficulty") or {}).get("level")
            questions.append(
                Question(
                    key=f"leetcode.com:{slug}",
                    frontend_id=str(
                        stat.get("frontend_question_id")
                        or stat.get("question_id")
                        or "?"
                    ),
                    slug=slug,
                    title=str(stat.get("question__title") or slug),
                    difficulty=(
                        difficulties.get(level, "Unknown")
                        if isinstance(level, int)
                        else "Unknown"
                    ),
                    url=f"{BASE_URL}/problems/{slug}/",
                    accepted=pair.get("status") == "ac",
                )
            )
        if not questions:
            raise LeetCodeError("LeetCode returned an empty problem catalog")
        return questions

    def _graphql(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        try:
            response = self.session.post(
                GRAPHQL_URL,
                json={"query": query, "variables": variables or {}},
                timeout=self.timeout,
            )
            response.raise_for_status()
            body = response.json()
        except (requests.RequestException, ValueError) as error:
            raise LeetCodeError(f"LeetCode request failed: {error}") from error
        if body.get("errors"):
            raise LeetCodeError(str(body["errors"][0].get("message", "GraphQL error")))
        return dict(body.get("data") or {})
