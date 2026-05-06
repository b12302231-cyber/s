"""notebooklm auth <subcommand>"""

import sys
import time

import click
import httpx
from rich.console import Console
from rich.table import Table

from .. import auth as _auth

console = Console()
err = Console(stderr=True)


@click.group("auth")
def auth_group():
    """Authentication utilities."""


@auth_group.command("check")
@click.option(
    "--test",
    "do_test",
    is_flag=True,
    help="Make a live API call to verify the token works.",
)
def auth_check(do_test: bool):
    """Diagnose authentication and cookie issues."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("check", style="bold")
    table.add_column("result")

    # 1. Credentials file
    creds_file = _auth._CREDENTIALS_FILE
    if creds_file.exists():
        table.add_row("Credentials file", f"[green]found[/green]  {creds_file}")
    else:
        table.add_row("Credentials file", "[red]missing[/red] — run 'notebooklm login'")
        console.print(table)
        sys.exit(1)

    # 2. Load and validate structure
    creds = _auth._load_credentials()
    if not creds:
        table.add_row("Credentials JSON", "[red]unreadable[/red]")
        console.print(table)
        sys.exit(1)
    table.add_row("Credentials JSON", "[green]ok[/green]")

    # 3. Expiry
    expires_at = creds.get("expires_at", 0)
    remaining = expires_at - time.time()
    if remaining > 0:
        mins = int(remaining // 60)
        table.add_row("Access token expiry", f"[green]{mins} min remaining[/green]")
    else:
        table.add_row("Access token expiry", "[yellow]expired — will refresh on next use[/yellow]")

    # 4. Refresh token present
    has_refresh = bool(creds.get("refresh_token"))
    table.add_row(
        "Refresh token",
        "[green]present[/green]" if has_refresh else "[red]missing[/red]",
    )

    # 5. Live test
    if do_test:
        try:
            token = _auth.get_access_token()
            resp = httpx.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            if resp.is_success:
                info = resp.json()
                table.add_row(
                    "Live token test",
                    f"[green]ok[/green]  ({info.get('email', 'unknown')})",
                )
            else:
                table.add_row(
                    "Live token test",
                    f"[red]failed[/red]  HTTP {resp.status_code}",
                )
        except _auth.AuthError as exc:
            table.add_row("Live token test", f"[red]error[/red]  {exc}")
        except httpx.HTTPError as exc:
            table.add_row("Live token test", f"[red]network error[/red]  {exc}")

    console.print(table)
