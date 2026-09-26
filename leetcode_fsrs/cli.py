"""Typer administration interface and TUI entry point."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Annotated

import typer

from .credentials import CredentialStore
from .domain import Rating
from .leetcode_client import LeetCodeClient
from .services import ApplicationService


app = typer.Typer(
    name="leetcode-fsrs",
    help="Terminal-first LeetCode review planner.",
    no_args_is_help=False,
)
auth_app = typer.Typer(help="Manage the device-local LeetCode session.")
card_app = typer.Typer(help="Manage study cards.")
config_app = typer.Typer(help="Manage portable study preferences.")
app.add_typer(auth_app, name="auth")
app.add_typer(card_app, name="card")
app.add_typer(config_app, name="config")


@app.callback(invoke_without_command=True)
def root(ctx: typer.Context) -> None:
    """Launch the TUI when no subcommand is supplied."""
    if ctx.invoked_subcommand is None:
        launch_tui()


@app.command("tui")
def launch_tui() -> None:
    """Open the interactive terminal UI."""
    from .tui import LeetCodeFsrsApp

    LeetCodeFsrsApp().run()


@app.command("init")
def initialize(
    directory: Annotated[Path, typer.Argument(help="Syncthing/WebDAV-synced study directory")],
    timezone: Annotated[str, typer.Option("--timezone", "-z")] = "Asia/Shanghai",
    username: Annotated[str | None, typer.Option("--username", "-u")] = None,
) -> None:
    """Create or attach to a study library."""
    service = ApplicationService.load()
    service.initialize_library(directory, timezone, username)
    typer.echo(f"Study library: {directory.expanduser().resolve()}")


@app.command("today")
def today(as_json: Annotated[bool, typer.Option("--json")] = False) -> None:
    """Print today's due-first study queue."""
    service = ApplicationService.load()
    plan = service.daily_plan()
    rows = [
        {
            "key": item.question_key,
            "id": item.frontend_id,
            "title": item.title,
            "difficulty": item.difficulty,
            "due_at": item.due_at.isoformat(),
            "new": item.is_new,
        }
        for item in plan.items
    ]
    if as_json:
        typer.echo(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    typer.echo(f"Due: {plan.due_backlog}  New: {plan.new_backlog}  Selected: {len(rows)}")
    for row in rows:
        marker = "NEW" if row["new"] else "DUE"
        typer.echo(f"{marker:3} {row['id']:>5}  {row['title']}  [{row['difficulty']}]")


@app.command("rate")
def rate(
    question: Annotated[str, typer.Argument(help="Question key, slug, or frontend ID")],
    rating: Annotated[Rating, typer.Argument()],
    at: Annotated[str | None, typer.Option("--at", help="ISO-8601 timestamp for imports")] = None,
) -> None:
    """Record one of the four FSRS ratings."""
    service = ApplicationService.load()
    item = _question(service, question)
    timestamp = datetime.fromisoformat(at) if at else None
    event = service.rate(item.key, rating, occurred_at=timestamp)
    typer.echo(event.event_id)


@app.command("import-accepted")
def import_accepted() -> None:
    """Fetch the catalog and enroll newly accepted LeetCode questions."""
    service = ApplicationService.load()
    cookie = CredentialStore().load()
    if not cookie:
        raise typer.BadParameter("No session. Run `leetcode-fsrs auth login` or set LEETCODE_SESSION.")
    client = LeetCodeClient(cookie)
    username = client.username()
    service.bind_account(username)
    questions = client.questions()
    enrolled = service.import_accepted(questions)
    typer.echo(f"Cached {len(questions)} questions; enrolled {enrolled} newly accepted cards.")


@app.command("status")
def status() -> None:
    """Show library, projection, and synchronization health."""
    service = ApplicationService.load()
    counts = service.projection.counts()
    typer.echo(f"Library: {service.config.shared_dir or 'not configured'}")
    typer.echo(f"Account: {service.projection.account() or 'not bound'}")
    typer.echo(f"Read-only: {'yes' if service.read_only else 'no'}")
    typer.echo("  ".join(f"{key}: {value}" for key, value in counts.items()))
    for problem in service.scan_problems:
        location = f"{problem.path}:{problem.line}" if problem.line else problem.path
        typer.echo(f"warning: {location}: {problem.message}", err=True)
    for error in service.semantic_errors:
        typer.echo(f"warning: {error}", err=True)


@auth_app.command("login")
def auth_login(
    session: Annotated[str | None, typer.Option("--session", help="Prefer the hidden prompt")]=None,
) -> None:
    """Validate and save LEETCODE_SESSION in the system keyring."""
    value = session or typer.prompt("LEETCODE_SESSION", hide_input=True)
    client = LeetCodeClient(value)
    username = client.username()
    CredentialStore().save(value)
    typer.echo(f"Authenticated as {username}.")


@auth_app.command("status")
def auth_status() -> None:
    cookie = CredentialStore().load()
    typer.echo("Session available." if cookie else "No session available.")


@auth_app.command("logout")
def auth_logout() -> None:
    CredentialStore().clear()
    typer.echo("Stored session removed (environment variables are unchanged).")


@card_app.command("enroll")
def card_enroll(question: str) -> None:
    service = ApplicationService.load()
    item = _question(service, question)
    event = service.enroll(item.key)
    typer.echo(event.event_id if event else "Already enrolled.")


@card_app.command("suspend")
def card_suspend(question: str) -> None:
    service = ApplicationService.load()
    typer.echo(service.suspend(_question(service, question).key).event_id)


@card_app.command("resume")
def card_resume(question: str) -> None:
    service = ApplicationService.load()
    typer.echo(service.resume(_question(service, question).key).event_id)


@config_app.command("set")
def config_set(key: str, value: str) -> None:
    """Set a portable preference (JSON values are accepted)."""
    allowed = {"timezone", "daily_limit", "new_limit", "desired_retention", "language", "fsrs_parameters"}
    if key not in allowed:
        raise typer.BadParameter(f"Unknown preference; choose one of: {', '.join(sorted(allowed))}")
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        parsed = value
    ApplicationService.load().set_preference(key, parsed)
    typer.echo(f"{key} = {parsed!r}")


@config_app.command("solver")
def config_solver(command: str) -> None:
    """Set this device's solver command; placeholders include {slug} and {url}."""
    service = ApplicationService.load()
    service.config.set_solver_command(command)
    service.config.save(service.config_path)
    typer.echo("Solver command updated for this device.")


def _question(service: ApplicationService, reference: str):
    question = service.projection.resolve_question(reference)
    if not question:
        raise typer.BadParameter(f"Unknown question: {reference}. Run import-accepted first.")
    return question


def main() -> None:
    app()
