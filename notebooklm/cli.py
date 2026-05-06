"""Main CLI entry point for the notebooklm command."""

import sys

import click
from rich.console import Console

from . import auth, config
from .commands.download import download
from .commands.generate import generate
from .commands.source import source

console = Console()
err_console = Console(stderr=True)


@click.group()
@click.version_option(package_name="notebooklm")
def main():
    """NotebookLM — command-line interface."""


# ---------------------------------------------------------------------------
# Authentication
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
# Attach sub-command groups
# ---------------------------------------------------------------------------

main.add_command(source)
main.add_command(generate)
main.add_command(download)
