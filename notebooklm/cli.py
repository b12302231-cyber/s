"""Main CLI entry point for the notebooklm command."""

import json
import sys
from pathlib import Path

import click
from rich.console import Console

from . import auth, config
from .commands.agent import agent_group
from .commands.auth_cmds import auth_group
from .commands.download import download
from .commands.generate import generate
from .commands.source import source

console = Console()
err_console = Console(stderr=True)

# ---------------------------------------------------------------------------
# Supported output languages
# ---------------------------------------------------------------------------

_LANGUAGES = [
    ("ar", "Arabic"),
    ("zh-CN", "Chinese (Simplified)"),
    ("zh-TW", "Chinese (Traditional)"),
    ("nl", "Dutch"),
    ("en", "English"),
    ("fr", "French"),
    ("de", "German"),
    ("hi", "Hindi"),
    ("id", "Indonesian"),
    ("it", "Italian"),
    ("ja", "Japanese"),
    ("ko", "Korean"),
    ("pl", "Polish"),
    ("pt", "Portuguese"),
    ("ru", "Russian"),
    ("es", "Spanish"),
    ("sv", "Swedish"),
    ("tr", "Turkish"),
    ("uk", "Ukrainian"),
    ("vi", "Vietnamese"),
]

# Path where the Claude Code skill template is expected when installed
_SKILL_PATH = Path.home() / ".claude" / "notebooklm.md"


# ---------------------------------------------------------------------------
# Root group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="notebooklm")
def main():
    """NotebookLM — command-line interface."""


# ---------------------------------------------------------------------------
# Authentication (top-level shortcuts kept for ergonomics)
# ---------------------------------------------------------------------------

@main.command("login")
@click.option(
    "--browser",
    default=None,
    metavar="BROWSER",
    help="Browser to open for authentication (e.g. msedge, firefox).",
)
def cmd_login(browser):
    """Authenticate with your Google account."""
    console.print("Opening browser for authentication…")
    try:
        creds = auth.login(browser=browser)
    except auth.AuthError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)
    email = (creds.get("id_token_payload") or {}).get("email", "")
    if email:
        console.print(f"[green]Logged in as[/green] {email}")
    else:
        console.print("[green]Login successful.[/green]")


@main.command("logout")
def cmd_logout():
    """Revoke credentials and remove local session."""
    auth.logout()
    console.print("Logged out.")


@main.command("whoami")
def cmd_whoami():
    """Show the currently authenticated account."""
    if not auth.is_authenticated():
        err_console.print("[yellow]Not logged in.[/yellow]")
        sys.exit(1)
    try:
        token = auth.get_access_token()
    except auth.AuthError as exc:
        err_console.print(f"[red]Error:[/red] {exc}")
        sys.exit(1)

    import httpx

    resp = httpx.get(
        "https://www.googleapis.com/oauth2/v3/userinfo",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if resp.is_success:
        info = resp.json()
        console.print(f"{info.get('name', '')} <{info.get('email', '')}>")
    else:
        console.print("Authenticated (could not fetch profile).")


# ---------------------------------------------------------------------------
# Notebook management
# ---------------------------------------------------------------------------

@main.command("create")
@click.argument("title")
def cmd_create(title: str):
    """Create a new notebook."""
    from . import client

    resp = client.post("/notebooks", json={"title": title})
    data = resp.json()
    nb_id = data.get("id") or data.get("notebookId")
    console.print(f"Created notebook [bold]{title}[/bold] (id: {nb_id})")
    config.set_active_notebook(nb_id)
    console.print(f"Active notebook set to [bold]{nb_id}[/bold]")


@main.command("use")
@click.argument("notebook_id")
def cmd_use(notebook_id: str):
    """Set the active notebook."""
    config.set_active_notebook(notebook_id)
    console.print(f"Active notebook: [bold]{notebook_id}[/bold]")


@main.command("list")
def cmd_list():
    """List all notebooks."""
    from . import client

    resp = client.get("/notebooks")
    notebooks = resp.json().get("notebooks", [])
    active = config.get_active_notebook()
    if not notebooks:
        console.print("No notebooks found.")
        return
    for nb in notebooks:
        nb_id = nb.get("id") or nb.get("notebookId")
        title = nb.get("title", "(untitled)")
        marker = " [green]*[/green]" if nb_id == active else ""
        console.print(f"  {nb_id}  {title}{marker}")


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@main.command("ask")
@click.argument("question")
def cmd_ask(question: str):
    """Ask a question about your notebook sources."""
    from . import client

    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/chat",
        json={"message": question},
    )
    data = resp.json()
    answer = data.get("text") or data.get("answer") or data.get("response", "")
    console.print(answer)


# ---------------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------------

@main.command("metadata")
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON.")
def cmd_metadata(as_json: bool):
    """Export notebook metadata and sources."""
    from . import client

    notebook_id = config.require_active_notebook()
    resp = client.get(f"/notebooks/{notebook_id}")
    data = resp.json()

    if as_json:
        click.echo(json.dumps(data, indent=2))
        return

    console.print(f"[bold]ID:[/bold]    {data.get('id', notebook_id)}")
    console.print(f"[bold]Title:[/bold] {data.get('title', '(untitled)')}")
    sources = data.get("sources", [])
    console.print(f"[bold]Sources:[/bold] {len(sources)}")
    for s in sources:
        console.print(
            f"  [{s.get('type', '?')}] {s.get('title', s.get('url', s.get('id', '?')))}"
        )


# ---------------------------------------------------------------------------
# Language
# ---------------------------------------------------------------------------

@main.group("language")
def language_group():
    """Language settings."""


@language_group.command("list")
def language_list():
    """List supported output languages."""
    from rich.table import Table

    table = Table("Code", "Language", show_header=True, header_style="bold")
    for code, name in _LANGUAGES:
        table.add_row(code, name)
    console.print(table)


# ---------------------------------------------------------------------------
# Share
# ---------------------------------------------------------------------------

@main.group("share")
def share_group():
    """Sharing settings."""


@share_group.command("status")
def share_status():
    """Inspect the sharing state of the active notebook."""
    from . import client
    from rich.table import Table

    notebook_id = config.require_active_notebook()
    resp = client.get(f"/notebooks/{notebook_id}/share")
    data = resp.json()

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("field", style="bold")
    table.add_column("value")
    table.add_row("Notebook ID", notebook_id)
    table.add_row("Visibility", data.get("visibility", "unknown"))
    table.add_row("Link sharing", "enabled" if data.get("linkSharingEnabled") else "disabled")
    link = data.get("shareLink", "")
    if link:
        table.add_row("Share link", link)
    console.print(table)


# ---------------------------------------------------------------------------
# Skill
# ---------------------------------------------------------------------------

@main.group("skill")
def skill_group():
    """Claude Code skill management."""


@skill_group.command("status")
def skill_status():
    """Check whether the notebooklm Claude Code skill is installed."""
    from rich.table import Table

    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("check", style="bold")
    table.add_column("result")

    if _SKILL_PATH.exists():
        table.add_row(
            "Skill file",
            f"[green]installed[/green]  {_SKILL_PATH}",
        )
        size = _SKILL_PATH.stat().st_size
        table.add_row("File size", f"{size} bytes")
    else:
        table.add_row(
            "Skill file",
            f"[yellow]not found[/yellow]  (expected {_SKILL_PATH})",
        )
        table.add_row(
            "Install",
            "notebooklm agent show claude > ~/.claude/notebooklm.md",
        )

    console.print(table)


# ---------------------------------------------------------------------------
# Attach sub-command groups
# ---------------------------------------------------------------------------

main.add_command(auth_group)
main.add_command(agent_group)
main.add_command(source)
main.add_command(generate)
main.add_command(download)
main.add_command(language_group)
main.add_command(share_group)
main.add_command(skill_group)
