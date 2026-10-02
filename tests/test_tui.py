from contextlib import nullcontext
from pathlib import Path

import pytest
from textual.widgets import Button, DataTable, Input, Select, Static, TabbedContent

from leetcode_fsrs.config import LocalConfig
from leetcode_fsrs.domain import Question
from leetcode_fsrs.services import ApplicationService, CardState, InvalidOperationError
from leetcode_fsrs.tui import LeetCodeFsrsApp


async def test_tui_mounts_all_primary_views(service) -> None:
    service.cache_questions(
        [
            Question(
                "leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy", accepted=True
            )
        ]
    )
    service.enroll("leetcode.com:two-sum")
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.pause()
        assert app.query_one("#today-table", DataTable).row_count == 1
        assert app.query_one("#questions-table", DataTable).row_count == 1
        assert app._selected_key("#today-table") == "leetcode.com:two-sum"
        assert app.query_one("#stats")
        assert app.query_one("#data-status")
        assert app.query_one("#settings")


async def test_explicit_refresh_does_not_report_success_after_failure(
    service, monkeypatch
) -> None:
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


async def test_import_does_not_mask_unexpected_application_failures(
    service, monkeypatch
) -> None:
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.pause()
        monkeypatch.setattr(
            "leetcode_fsrs.tui.CredentialStore.load", lambda self: "session"
        )
        monkeypatch.setattr(
            "leetcode_fsrs.tui.LeetCodeClient.username", lambda self: "alice"
        )
        monkeypatch.setattr(
            "leetcode_fsrs.tui.LeetCodeClient.questions", lambda self: []
        )

        def unexpected_failure(questions):
            raise RuntimeError("programming defect")

        monkeypatch.setattr(service, "import_accepted", unexpected_failure)
        with pytest.raises(RuntimeError, match="programming defect"):
            app._import_accepted()


async def test_question_action_wiring_updates_public_service_state(service) -> None:
    service.cache_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy")]
    )
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.click("#--content-tab-questions")
        await pilot.click("#enroll")
        await pilot.pause()

        assert service.questions()[0].state is CardState.ACTIVE
        assert "复习卡片: 1" in str(app.query_one("#stats", Static).content)


async def test_vim_navigation_switches_tabs_and_enrolls_selected_question(
    service,
) -> None:
    service.cache_questions(
        [
            Question("leetcode.com:one", "1", "one", "One", "Easy"),
            Question("leetcode.com:two", "2", "two", "Two", "Medium"),
        ]
    )
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.press("l")

        tabs = app.query_one(TabbedContent)
        table = app.query_one("#questions-table", DataTable)
        assert tabs.active == "questions"
        assert table.has_focus

        await pilot.press("j", "e")

        states = {item.question.slug: item.state for item in service.questions()}
        assert states == {"one": CardState.NOT_ENROLLED, "two": CardState.ACTIVE}


async def test_search_input_consumes_shortcut_letters_until_escape(service) -> None:
    service.cache_questions([Question("leetcode.com:jle", "1", "jle", "JLE", "Easy")])
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.press("l", "slash", "j", "l", "e")

        search = app.query_one("#question-search", Input)
        assert search.has_focus
        assert search.value == "jle"
        assert service.questions()[0].state is CardState.NOT_ENROLLED

        await pilot.press("escape")

        assert app.query_one("#questions-table", DataTable).has_focus


async def test_user_can_solve_and_grade_from_the_keyboard(service, monkeypatch) -> None:
    service.cache_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy")]
    )
    service.enroll("leetcode.com:two-sum")
    launched: list[str] = []

    def record_solver(command, question) -> int:
        launched.append(question.slug)
        return 0

    monkeypatch.setattr("leetcode_fsrs.tui.run_solver", record_solver)
    app = LeetCodeFsrsApp(service)
    monkeypatch.setattr(app, "suspend", nullcontext)

    async with app.run_test() as pilot:
        assert app.query_one("#today-table", DataTable).has_focus
        await pilot.press("enter", "3")

        assert launched == ["two-sum"]
        assert service.health().counts.reviews == 1


async def test_question_keys_navigate_and_change_card_state(service) -> None:
    service.cache_questions(
        [
            Question("leetcode.com:one", "1", "one", "One", "Easy"),
            Question("leetcode.com:two", "2", "two", "Two", "Medium"),
            Question("leetcode.com:three", "3", "three", "Three", "Hard"),
        ]
    )
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.press("l", "G", "k", "e")
        assert service.questions()[1].state is CardState.ACTIVE

        await pilot.press("j", "s")
        assert service.questions()[1].state is CardState.SUSPENDED

        await pilot.press("j", "u")
        assert service.questions()[1].state is CardState.ACTIVE

        await pilot.press("g")
        assert app.query_one("#questions-table", DataTable).cursor_row == 0


async def test_data_tab_focuses_import_and_starts_it_from_the_keyboard(
    service, monkeypatch
) -> None:
    app = LeetCodeFsrsApp(service)
    submitted: list[dict[str, object]] = []

    def record_worker(work, **kwargs):
        submitted.append(kwargs)

    monkeypatch.setattr(app, "run_worker", record_worker)

    async with app.run_test() as pilot:
        await pilot.press("l", "l", "l")

        assert app.query_one(TabbedContent).active == "data-tab"
        assert app.query_one("#import-accepted", Button).has_focus

        await pilot.press("i")

        assert submitted == [
            {"thread": True, "exclusive": True, "group": "leetcode-import"}
        ]

        await pilot.press("h")
        assert app.query_one(TabbedContent).active == "stats-tab"


async def test_first_run_setup_submits_with_enter_and_focuses_today(
    tmp_path: Path,
) -> None:
    service = ApplicationService(
        LocalConfig(),
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        directory = app.screen.query_one("#setup-directory", Input)
        timezone = app.screen.query_one("#setup-timezone", Input)
        directory.value = str(tmp_path / "shared")
        timezone.focus()

        await pilot.press("enter")
        await pilot.pause()

        assert service.health().shared_path == str((tmp_path / "shared").resolve())
        assert app.query_one("#today-table", DataTable).has_focus


async def test_settings_save_portable_and_device_values_independently(service) -> None:
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.click("#--content-tab-settings-tab")
        app.query_one("#settings-timezone", Input).value = "UTC"
        app.query_one("#settings-daily", Input).value = "12"
        app.query_one("#settings-new", Input).value = "0"
        app.query_one("#settings-retention", Input).value = "0.91"
        app.query_one("#settings-language", Select).value = "en"
        app._save_study_preferences()
        await pilot.pause()

        settings = service.settings()
        assert settings.timezone == "UTC"
        assert settings.daily_limit == 12
        assert settings.new_limit == 0
        assert settings.desired_retention == 0.91
        assert settings.language == "en"
        assert str(app.query_one("#stats", Static).content).startswith(
            "Cached questions:"
        )
        assert str(app.query_one("#settings-study-save", Button).label) == (
            "Save preferences"
        )

        app.query_one("#settings-solver", Input).value = "code {slug}"
        app._save_device_settings()

        assert service.settings().solver_command == ("code", "{slug}")


async def test_read_only_settings_still_allow_device_changes(
    service, monkeypatch
) -> None:
    monkeypatch.setattr(
        "leetcode_fsrs.event_store.EventStore.writable", lambda self: False
    )
    service.refresh()
    app = LeetCodeFsrsApp(service)

    async with app.run_test() as pilot:
        await pilot.pause()

        assert app.query_one("#settings-study-save", Button).disabled
        assert not app.query_one("#settings-device-save", Button).disabled
