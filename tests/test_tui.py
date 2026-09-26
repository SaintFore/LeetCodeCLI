from leetcode_fsrs.domain import Question
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
