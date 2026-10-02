"""Textual user interface for daily reviews and library management."""

from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, DataTable, Footer, Header, Input, Label, Static, TabbedContent, TabPane

from .domain import PlanItem, Rating
from .credentials import CredentialStore
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
            yield Static("选择一个由 Syncthing 或 WebDAV 客户端同步的目录。应用本身不会联网同步该目录。")
            yield Input(placeholder="共享目录，例如 ~/Sync/leetcode-fsrs", id="setup-directory")
            yield Input(value="Asia/Shanghai", placeholder="IANA timezone", id="setup-timezone")
            yield Input(placeholder="LeetCode username（可选）", id="setup-username")
            yield Label("", id="setup-error")
            yield Button("创建 / Attach", id="setup-submit", variant="primary")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "setup-submit":
            return
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
    BINDINGS = [("q", "quit", "Quit"), ("r", "refresh_data", "Refresh")]
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
                    yield Button(self._text("打开解题器", "Open solver"), id="solve", variant="primary")
                    yield Button(self._text("跳过", "Skip"), id="skip")
                    yield Button("1 Again", id="again", variant="error")
                    yield Button("2 Hard", id="hard", variant="warning")
                    yield Button("3 Good", id="good", variant="success")
                    yield Button("4 Easy", id="easy")
            with TabPane(self._text("题库", "Questions"), id="questions"):
                yield Input(placeholder=self._text("搜索标题、slug 或题号", "Search title, slug, or ID"), id="question-search")
                yield DataTable(id="questions-table", cursor_type="row")
                with Horizontal(classes="toolbar"):
                    yield Button(self._text("加入复习", "Enroll"), id="enroll")
                    yield Button(self._text("暂停", "Suspend"), id="suspend")
                    yield Button(self._text("恢复", "Resume"), id="resume")
            with TabPane(self._text("统计", "Stats"), id="stats-tab"):
                yield Static(id="stats")
            with TabPane(self._text("数据", "Data"), id="data-tab"):
                yield Static(id="data-status")
                yield Button(self._text("从 LeetCode 导入 Accepted", "Import Accepted from LeetCode"), id="import-accepted")
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

    def _setup_tables(self) -> None:
        self.query_one("#today-table", DataTable).add_columns(
            self._text("状态", "State"), self._text("题号", "ID"), self._text("题目", "Title"),
            self._text("难度", "Difficulty"), self._text("到期", "Due")
        )
        self.query_one("#questions-table", DataTable).add_columns(
            self._text("题号", "ID"), self._text("题目", "Title"),
            self._text("难度", "Difficulty"), self._text("状态", "State")
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
            questions.add_row(question.frontend_id, question.title, question.difficulty, state, key=question.key)

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

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        if event.row_key.value:
            self.current_key = str(event.row_key.value)

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "question-search" and self.service.health().access is not LibraryAccess.UNCONFIGURED:
            self.refresh_views()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        try:
            if button_id == "solve":
                self._solve_current()
            elif button_id == "skip":
                self._advance_today()
            elif button_id in {rating.value for rating in Rating}:
                self._grade(Rating(button_id))
            elif button_id in {"enroll", "suspend", "resume"}:
                self._change_card(button_id)
            elif button_id == "import-accepted":
                self.notify(self._text("正在从 LeetCode 导入…", "Importing from LeetCode…"))
                self.run_worker(self._import_accepted, thread=True, exclusive=True, group="leetcode-import")
        except (ApplicationError, ValueError) as error:
            self.notify(str(error), severity="error")

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
        self.notify(f"解题器已退出（{exit_code}）。请选择 Again / Hard / Good / Easy，或跳过。")

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

    def _change_card(self, action: str) -> None:
        key = self._selected_key("#questions-table")
        if not key:
            raise ValueError("请先选择一道题。")
        if action == "enroll":
            self.service.enroll(key)
        elif action == "suspend":
            self.service.suspend(key)
        else:
            self.service.resume(key)
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
