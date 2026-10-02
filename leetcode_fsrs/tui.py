"""Textual user interface for daily reviews and library management."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import ClassVar

from textual.app import App, ComposeResult
from textual.binding import Binding, BindingType
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    Label,
    Static,
    TabbedContent,
    TabPane,
    Tabs,
)

from .credentials import CredentialStore
from .domain import PlanItem, Rating
from .leetcode_client import LeetCodeClient, LeetCodeError
from .services import ApplicationError, ApplicationService, CardState, LibraryAccess
from .solver import run_solver


class SetupScreen(ModalScreen[tuple[Path, str, str | None]]):
    """Minimal first-run wizard; sync remains an external tool's job."""

    CSS = """
    SetupScreen { align: center middle; }
    #setup { width: 72; height: auto; padding: 1 2; border: round $accent; background: $surface; }
    #setup Input { margin-bottom: 1; }
    #setup-error { color: $error; }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="setup"):
            yield Label("首次设置 / First-run setup", classes="title")
            yield Static(
                "选择一个由 Syncthing 或 WebDAV 客户端同步的目录。应用本身不会联网同步该目录。"
            )
            yield Input(
                placeholder="共享目录，例如 ~/Sync/leetcode-fsrs", id="setup-directory"
            )
            yield Input(
                value="Asia/Shanghai", placeholder="IANA timezone", id="setup-timezone"
            )
            yield Input(placeholder="LeetCode username（可选）", id="setup-username")
            yield Label("", id="setup-error")
            yield Button("创建 / Attach", id="setup-submit", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "setup-submit":
            return
        self._submit()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._submit()

    def _submit(self) -> None:
        directory = self.query_one("#setup-directory", Input).value.strip()
        timezone = self.query_one("#setup-timezone", Input).value.strip()
        username = self.query_one("#setup-username", Input).value.strip() or None
        if not directory or not timezone:
            self.query_one("#setup-error", Label).update("目录和时区不能为空。")
            return
        self.dismiss((Path(directory).expanduser(), timezone, username))


class LeetCodeFsrsApp(App[None]):
    TITLE = "LeetCode FSRS"
    SUB_TITLE = "TUI review planner"
    BINDINGS: ClassVar[list[BindingType]] = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_data", "Refresh"),
        Binding("h", "previous_tab", "Previous tab"),
        Binding("l", "next_tab", "Next tab"),
        Binding("j", "cursor_down", "Down"),
        Binding("k", "cursor_up", "Up"),
        Binding("g", "first_row", "First row"),
        Binding("G", "last_row", "Last row"),
        Binding("e", "enroll", "Enroll"),
        Binding("s", "skip", "Skip"),
        Binding("s", "suspend", "Suspend"),
        Binding("u", "resume", "Resume"),
        Binding("/", "focus_search", "Search"),
        Binding("escape", "exit_search", "Back to table", show=False),
        Binding("o", "open_solver", "Open solver"),
        Binding("enter", "open_selected", "Open solver", priority=True),
        Binding("1", "grade('again')", "Again"),
        Binding("2", "grade('hard')", "Hard"),
        Binding("3", "grade('good')", "Good"),
        Binding("4", "grade('easy')", "Easy"),
        Binding("i", "import_accepted", "Import Accepted"),
    ]
    CSS = """
    #health { dock: bottom; height: 1; color: $text-muted; }
    .toolbar { height: auto; margin: 1 0; }
    .toolbar Button { margin-right: 1; }
    DataTable { height: 1fr; }
    #stats, #data-status, #settings { padding: 1 2; }
    """

    def __init__(self, service: ApplicationService | None = None) -> None:
        super().__init__()
        self.service = service or ApplicationService.load()
        self.english = self.service.settings().language == "en"
        self.plan_items: list[PlanItem] = []
        self.current_key: str | None = None
        self.solved_key: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with TabPane(self._text("今日", "Today"), id="today"):
                yield DataTable(id="today-table", cursor_type="row")
                with Horizontal(classes="toolbar"):
                    yield Button(
                        self._text("打开解题器", "Open solver"),
                        id="solve",
                        variant="primary",
                    )
                    yield Button(self._text("跳过", "Skip"), id="skip")
                    yield Button("1 Again", id="again", variant="error")
                    yield Button("2 Hard", id="hard", variant="warning")
                    yield Button("3 Good", id="good", variant="success")
                    yield Button("4 Easy", id="easy")
            with TabPane(self._text("题库", "Questions"), id="questions"):
                yield Input(
                    placeholder=self._text(
                        "搜索标题、slug 或题号", "Search title, slug, or ID"
                    ),
                    id="question-search",
                )
                yield DataTable(id="questions-table", cursor_type="row")
                with Horizontal(classes="toolbar"):
                    yield Button(self._text("加入复习", "Enroll"), id="enroll")
                    yield Button(self._text("暂停", "Suspend"), id="suspend")
                    yield Button(self._text("恢复", "Resume"), id="resume")
            with TabPane(self._text("统计", "Stats"), id="stats-tab"):
                yield Static(id="stats")
            with TabPane(self._text("数据", "Data"), id="data-tab"):
                yield Static(id="data-status")
                yield Button(
                    self._text(
                        "从 LeetCode 导入 Accepted", "Import Accepted from LeetCode"
                    ),
                    id="import-accepted",
                )
            with TabPane(self._text("设置", "Settings"), id="settings-tab"):
                yield Static(id="settings")
        yield Label("", id="health")
        yield Footer()

    def on_mount(self) -> None:
        self._setup_tables()
        if self.service.health().access is LibraryAccess.UNCONFIGURED:
            self.push_screen(SetupScreen(), self._finish_setup)
        else:
            self.refresh_views()
            self._focus_active_pane()

    def _finish_setup(self, result: tuple[Path, str, str | None] | None) -> None:
        if result is None:
            self.exit()
            return
        path, timezone, username = result
        try:
            self.service.initialize_library(path, timezone, username)
        except ApplicationError as error:
            self.notify(str(error), severity="error")
            self.push_screen(SetupScreen(), self._finish_setup)
            return
        self.refresh_views()
        self._focus_active_pane()

    def _setup_tables(self) -> None:
        self.query_one("#today-table", DataTable).add_columns(
            self._text("状态", "State"),
            self._text("题号", "ID"),
            self._text("题目", "Title"),
            self._text("难度", "Difficulty"),
            self._text("到期", "Due"),
        )
        self.query_one("#questions-table", DataTable).add_columns(
            self._text("题号", "ID"),
            self._text("题目", "Title"),
            self._text("难度", "Difficulty"),
            self._text("状态", "State"),
        )

    def _text(self, chinese: str, english: str) -> str:
        return english if self.english else chinese

    def refresh_views(self) -> None:
        try:
            plan = self.service.daily_plan()
        except ApplicationError as error:
            self.query_one("#health", Label).update(f"调度错误: {error}")
            return

        self.plan_items = list(plan.items)
        today = self.query_one("#today-table", DataTable)
        today.clear()
        for item in self.plan_items:
            today.add_row(
                "NEW" if item.is_new else "DUE",
                item.frontend_id,
                item.title,
                item.difficulty,
                item.due_at.astimezone().strftime("%m-%d %H:%M"),
                key=item.question_key,
            )

        questions = self.query_one("#questions-table", DataTable)
        questions.clear()
        search = self.query_one("#question-search", Input).value
        for item in self.service.questions(search):
            question = item.question
            state = {
                CardState.NOT_ENROLLED: "—",
                CardState.ACTIVE: "学习中",
                CardState.SUSPENDED: "暂停",
            }[item.state]
            questions.add_row(
                question.frontend_id,
                question.title,
                question.difficulty,
                state,
                key=question.key,
            )

        health = self.service.health()
        counts = health.counts
        self.query_one("#stats", Static).update(
            f"题目缓存: {counts.questions}\n复习卡片: {counts.cards}\n复习记录: {counts.reviews}\n暂停: {counts.suspended}\n"
            f"今日到期积压: {plan.due_backlog}\n新题积压: {plan.new_backlog}"
        )
        problems = len(health.scan_problems) + len(health.semantic_problems)
        self.query_one("#data-status", Static).update(
            f"共享目录: {health.shared_path or ''}\n"
            f"账号: {health.account or '未绑定'}\n"
            f"模式: {'只读' if health.access is LibraryAccess.READ_ONLY else '可写'}\n"
            f"扫描问题: {problems}\n\n同步提示：让 Syncthing/WebDAV 客户端同步整个共享目录；请勿同步本机 SQLite。"
        )
        settings = self.service.settings()
        self.query_one("#settings", Static).update(
            f"时区: {settings.timezone}\n每日上限: {settings.daily_limit}\n新题上限: {settings.new_limit}\n"
            f"期望记忆率: {settings.desired_retention}\n语言: {settings.language}\n"
            f"本机解题器: {' '.join(settings.solver_command)}\n\n更多设置请使用 leetcode-fsrs config。"
        )
        self.query_one("#health", Label).update(
            f"Due {plan.due_backlog} · New {plan.new_backlog} · Selected {len(plan.items)}"
        )

    def action_refresh_data(self) -> None:
        try:
            self.service.refresh()
        except ApplicationError as error:
            self.notify(str(error), severity="error")
            return
        self.refresh_views()
        self.notify("已从共享事件日志重建。")

    def action_next_tab(self) -> None:
        self._switch_tab(1)

    def action_previous_tab(self) -> None:
        self._switch_tab(-1)

    def _switch_tab(self, offset: int) -> None:
        tabs = self.query_one(TabbedContent)
        pane_ids = [pane.id for pane in tabs.query(TabPane) if pane.id]
        index = pane_ids.index(tabs.active)
        tabs.active = pane_ids[(index + offset) % len(pane_ids)]
        self._focus_active_pane()

    def action_cursor_down(self) -> None:
        table = self._active_table()
        if table is not None:
            table.action_cursor_down()

    def action_cursor_up(self) -> None:
        table = self._active_table()
        if table is not None:
            table.action_cursor_up()

    def action_first_row(self) -> None:
        table = self._active_table()
        if table is not None:
            table.action_scroll_top()

    def action_last_row(self) -> None:
        table = self._active_table()
        if table is not None:
            table.action_scroll_bottom()

    def action_enroll(self) -> None:
        self._run_question_action(self.service.enroll)

    def action_suspend(self) -> None:
        self._run_question_action(self.service.suspend)

    def action_resume(self) -> None:
        self._run_question_action(self.service.resume)

    def action_skip(self) -> None:
        self._advance_today()

    def action_focus_search(self) -> None:
        if self.query_one(TabbedContent).active == "questions":
            self.query_one("#question-search", Input).focus()

    def action_exit_search(self) -> None:
        focused = self.focused
        if isinstance(focused, Input) and focused.id == "question-search":
            self.query_one("#questions-table", DataTable).focus()

    def action_open_solver(self) -> None:
        try:
            self._solve_current()
        except (ApplicationError, ValueError) as error:
            self.notify(str(error), severity="error")

    def action_grade(self, rating: str) -> None:
        try:
            self._grade(Rating(rating))
        except (ApplicationError, ValueError) as error:
            self.notify(str(error), severity="error")

    def action_open_selected(self) -> None:
        self.action_open_solver()

    def action_import_accepted(self) -> None:
        self.notify(self._text("正在从 LeetCode 导入…", "Importing from LeetCode…"))
        self.run_worker(
            self._import_accepted, thread=True, exclusive=True, group="leetcode-import"
        )

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        active = self.query_one(TabbedContent).active if self.is_mounted else ""
        focused = self.focused
        if action in {"cursor_down", "cursor_up", "first_row", "last_row"}:
            return active in {"today", "questions"}
        if action in {"open_solver", "skip", "grade"}:
            return active == "today"
        if action == "open_selected":
            return active == "today" and getattr(focused, "id", None) == "today-table"
        if action in {"enroll", "suspend", "resume", "focus_search"}:
            return active == "questions"
        if action == "exit_search":
            return isinstance(focused, Input) and focused.id == "question-search"
        if action == "import_accepted":
            return active == "data-tab"
        return True

    def _focus_active_pane(self) -> None:
        active = self.query_one(TabbedContent).active
        target_id = {
            "today": "#today-table",
            "questions": "#questions-table",
            "data-tab": "#import-accepted",
        }.get(active)
        if target_id:
            self.query_one(target_id).focus()
        else:
            self.query_one(TabbedContent).query_one(Tabs).focus()

    def _active_table(self) -> DataTable | None:
        active = self.query_one(TabbedContent).active
        table_id = {"today": "#today-table", "questions": "#questions-table"}.get(
            active
        )
        return self.query_one(table_id, DataTable) if table_id else None

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            self.current_key = str(event.row_key.value)

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        self._focus_active_pane()
        self.refresh_bindings()

    def on_input_changed(self, event: Input.Changed) -> None:
        if (
            event.input.id == "question-search"
            and self.service.health().access is not LibraryAccess.UNCONFIGURED
        ):
            self.refresh_views()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "solve":
            self.action_open_solver()
        elif button_id == "skip":
            self.action_skip()
        elif button_id in {rating.value for rating in Rating}:
            self.action_grade(button_id)
        elif button_id == "enroll":
            self.action_enroll()
        elif button_id == "suspend":
            self.action_suspend()
        elif button_id == "resume":
            self.action_resume()
        elif button_id == "import-accepted":
            self.action_import_accepted()

    def _selected_key(self, table_id: str) -> str | None:
        table = self.query_one(table_id, DataTable)
        if table.row_count == 0:
            return None
        return str(table.coordinate_to_cell_key(table.cursor_coordinate).row_key.value)

    def _solve_current(self) -> None:
        key = self._selected_key("#today-table")
        if not key:
            raise ValueError("今日没有可复习题目。")
        solver_input = self.service.solver_input(key)
        with self.suspend():
            exit_code = run_solver(solver_input.command, solver_input.question)
        self.solved_key = key
        self.notify(
            f"解题器已退出（{exit_code}）。请选择 Again / Hard / Good / Easy，或跳过。"
        )

    def _grade(self, rating: Rating) -> None:
        key = self._selected_key("#today-table")
        if not key or self.solved_key != key:
            raise ValueError("请先打开并退出当前题目的解题器，再评分。")
        self.service.rate(key, rating)
        self.solved_key = None
        self.refresh_views()
        self.notify(f"已记录 {rating.value}。")

    def _advance_today(self) -> None:
        table = self.query_one("#today-table", DataTable)
        if table.row_count:
            table.move_cursor(row=(table.cursor_row + 1) % table.row_count)
        self.solved_key = None

    def _run_question_action(self, operation: Callable[[str], object]) -> None:
        key = self._selected_key("#questions-table")
        if not key:
            self.notify("请先选择一道题。", severity="error")
            return
        try:
            operation(key)
        except ApplicationError as error:
            self.notify(str(error), severity="error")
            return
        self.refresh_views()

    def _import_accepted(self) -> None:
        cookie = CredentialStore().load()
        if not cookie:
            self.call_from_thread(
                self.notify,
                "No session; run `leetcode-fsrs auth login` or set LEETCODE_SESSION.",
                severity="error",
            )
            return
        try:
            client = LeetCodeClient(cookie)
            username = client.username()
            self.service.bind_account(username)
            questions = client.questions()
            enrolled = self.service.import_accepted(questions)
        except (ApplicationError, LeetCodeError) as error:
            self.call_from_thread(self.notify, str(error), severity="error")
            return
        self.call_from_thread(self.refresh_views)
        self.call_from_thread(
            self.notify,
            self._text(
                f"已缓存 {len(questions)} 题，新加入 {enrolled} 道 Accepted。",
                f"Cached {len(questions)} questions; enrolled {enrolled} Accepted cards.",
            ),
        )
