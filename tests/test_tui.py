import pytest

from leetcode_fsrs.domain import Question
from leetcode_fsrs.services import InvalidOperationError
from leetcode_fsrs.tui import LeetCodeFsrsApp


async def test_tui_mounts_all_primary_views(service) -> None:
    service.cache_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy", accepted=True)]
    )
    service.enroll("leetcode.com:two-sum")
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#today-table").row_count == 1
        assert app.query_one("#questions-table").row_count == 1
        assert app._selected_key("#today-table") == "leetcode.com:two-sum"
        assert app.query_one("#stats")
        assert app.query_one("#data-status")
        assert app.query_one("#settings")


async def test_explicit_refresh_does_not_report_success_after_failure(service, monkeypatch) -> None:
    app = LeetCodeFsrsApp(service)
    notifications: list[tuple[str, str | None]] = []

    async with app.run_test() as pilot:
        await pilot.pause()

        def failed_refresh() -> None:
            raise InvalidOperationError("library unavailable")

        def record_notification(message: str, **kwargs) -> None:
            notifications.append((message, kwargs.get("severity")))

        monkeypatch.setattr(service, "refresh", failed_refresh)
        monkeypatch.setattr(app, "notify", record_notification)
        app.action_refresh_data()

    assert notifications == [("library unavailable", "error")]


async def test_import_does_not_mask_unexpected_application_failures(service, monkeypatch) -> None:
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr("leetcode_fsrs.tui.CredentialStore.load", lambda self: "session")
        monkeypatch.setattr("leetcode_fsrs.tui.LeetCodeClient.username", lambda self: "alice")
        monkeypatch.setattr("leetcode_fsrs.tui.LeetCodeClient.questions", lambda self: [])

        def unexpected_failure(questions):
            raise RuntimeError("programming defect")

        monkeypatch.setattr(service, "import_accepted", unexpected_failure)
        with pytest.raises(RuntimeError, match="programming defect"):
            app._import_accepted()
