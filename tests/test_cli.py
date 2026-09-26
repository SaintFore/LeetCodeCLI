from pathlib import Path

from typer.testing import CliRunner

from leetcode_fsrs.cli import app


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
