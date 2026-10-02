from pathlib import Path
import json

from typer.testing import CliRunner

from leetcode_fsrs.cli import app
from leetcode_fsrs.domain import Question
from leetcode_fsrs.services import ApplicationService


def test_init_and_status_use_xdg_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    shared = tmp_path / "shared"
    runner = CliRunner()

    initialized = runner.invoke(app, ["init", str(shared), "--timezone", "UTC", "--username", "alice"])
    status = runner.invoke(app, ["status"])

    assert initialized.exit_code == 0, initialized.output
    assert status.exit_code == 0, status.output
    assert str(shared) in status.output
    assert "alice" in status.output


def test_question_errors_are_translated_to_typer_errors(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))

    result = CliRunner().invoke(app, ["card", "enroll", "missing"])

    assert result.exit_code == 2
    assert "Unknown question: missing" in result.output


def test_cli_commands_preserve_parsing_outputs_and_service_wiring(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "data"))
    runner = CliRunner()
    shared = tmp_path / "shared"
    assert runner.invoke(app, ["init", str(shared), "--timezone", "UTC"]).exit_code == 0
    service = ApplicationService.load()
    service.cache_questions(
        [Question("leetcode.com:two-sum", "1", "two-sum", "Two Sum", "Easy")]
    )

    enrolled = runner.invoke(app, ["card", "enroll", "two-sum"])
    suspended = runner.invoke(app, ["card", "suspend", "1"])
    resumed = runner.invoke(app, ["card", "resume", "leetcode.com:two-sum"])
    configured = runner.invoke(app, ["config", "set", "daily_limit", "12"])
    solver = runner.invoke(app, ["config", "solver", "nvim +Leet {slug}"])
    today = runner.invoke(app, ["today", "--json"])
    status = runner.invoke(app, ["status"])

    assert all(result.exit_code == 0 for result in (enrolled, suspended, resumed, configured, solver, today, status))
    assert configured.output == "daily_limit = 12\n"
    assert solver.output == "Solver command updated for this device.\n"
    assert json.loads(today.output)[0]["key"] == "leetcode.com:two-sum"
    assert "cards: 1" in status.output
