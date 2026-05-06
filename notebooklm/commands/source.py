"""notebooklm source <subcommand>"""

import mimetypes
from pathlib import Path

import click

from .. import client, config


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
