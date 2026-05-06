"""notebooklm source <subcommand>"""

import mimetypes
import time
from pathlib import Path

import click
from rich.console import Console

from .. import client, config

console = Console()


@click.group()
def source():
    """Manage notebook sources."""


@source.command("add")
@click.argument("location")
def source_add(location: str):
    """Add a URL or local file as a source."""
    notebook_id = config.require_active_notebook()

    if location.startswith("http://") or location.startswith("https://"):
        payload = {"url": location}
        resp = client.post(f"/notebooks/{notebook_id}/sources", json=payload)
        data = resp.json()
        click.echo(f"Source added: {data.get('id', 'ok')}")
    else:
        path = Path(location)
        if not path.exists():
            raise click.ClickException(f"File not found: {location}")
        mime, _ = mimetypes.guess_type(str(path))
        mime = mime or "application/octet-stream"
        with path.open("rb") as fh:
            resp = client.post(
                f"/notebooks/{notebook_id}/sources",
                files={"file": (path.name, fh, mime)},
            )
        data = resp.json()
        click.echo(f"Source added: {data.get('id', 'ok')}")


@source.command("add-research")
@click.argument("query")
@click.option(
    "--no-wait",
    is_flag=True,
    default=False,
    help="Return immediately without polling for results.",
)
def source_add_research(query: str, no_wait: bool):
    """Start a web research job and import the results as sources."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/research",
        json={"query": query},
    )
    data = resp.json()
    job_id = data.get("jobId") or data.get("id")
    click.echo(f"Research started for '{query}' (job: {job_id})")

    if no_wait or not job_id:
        return

    _POLL = 5
    with console.status("[bold green]Researching…"):
        while True:
            status_resp = client.get(
                f"/notebooks/{notebook_id}/research/{job_id}"
            )
            status_data = status_resp.json()
            state = status_data.get("state", "")
            if state == "DONE":
                sources = status_data.get("sources", [])
                click.echo(
                    f"Research complete — {len(sources)} source(s) imported."
                )
                for s in sources:
                    click.echo(
                        f"  {s.get('id', '?')}  "
                        f"{s.get('title', s.get('url', ''))}"
                    )
                return
            if state in ("FAILED", "CANCELLED"):
                raise click.ClickException(
                    f"Research job {state.lower()}: "
                    f"{status_data.get('error', {}).get('message', 'unknown')}"
                )
            time.sleep(_POLL)
