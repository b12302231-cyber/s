"""notebooklm download <type> [options] <dest>"""

from pathlib import Path

import click
import httpx

from .. import auth, config

_API_BASE = "https://notebooklm.googleapis.com/v1"


def _fetch(notebook_id: str, endpoint: str, dest: Path, fmt: str = "") -> None:
    url = f"{_API_BASE}/notebooks/{notebook_id}/artifacts/{endpoint}"
    params = {"format": fmt} if fmt else {}
    headers = {"Authorization": f"Bearer {auth.get_access_token()}"}

    with httpx.stream("GET", url, headers=headers, params=params, timeout=None) as r:
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as fh:
            for chunk in r.iter_bytes(chunk_size=65536):
                fh.write(chunk)

    click.echo(f"Saved to {dest}")


@click.group()
def download():
    """Download generated artifacts."""


@download.command("audio")
@click.argument("dest", type=click.Path())
def dl_audio(dest: str):
    """Download audio overview."""
    _fetch(config.require_active_notebook(), "audio", Path(dest))


@download.command("video")
@click.argument("dest", type=click.Path())
def dl_video(dest: str):
    """Download video overview."""
    _fetch(config.require_active_notebook(), "video", Path(dest))


@download.command("cinematic-video")
@click.argument("dest", type=click.Path())
def dl_cinematic_video(dest: str):
    """Download cinematic video."""
    _fetch(config.require_active_notebook(), "cinematic_video", Path(dest))


@download.command("quiz")
@click.option("--format", "fmt", default="", help="Output format (e.g. markdown).")
@click.argument("dest", type=click.Path())
def dl_quiz(fmt: str, dest: str):
    """Download quiz."""
    _fetch(config.require_active_notebook(), "quiz", Path(dest), fmt)


@download.command("flashcards")
@click.option("--format", "fmt", default="", help="Output format (e.g. json).")
@click.argument("dest", type=click.Path())
def dl_flashcards(fmt: str, dest: str):
    """Download flashcards."""
    _fetch(config.require_active_notebook(), "flashcards", Path(dest), fmt)


@download.command("slide-deck")
@click.argument("dest", type=click.Path())
def dl_slide_deck(dest: str):
    """Download slide deck."""
    _fetch(config.require_active_notebook(), "slide_deck", Path(dest))


@download.command("infographic")
@click.argument("dest", type=click.Path())
def dl_infographic(dest: str):
    """Download infographic."""
    _fetch(config.require_active_notebook(), "infographic", Path(dest))


@download.command("mind-map")
@click.argument("dest", type=click.Path())
def dl_mind_map(dest: str):
    """Download mind map."""
    _fetch(config.require_active_notebook(), "mind_map", Path(dest))


@download.command("data-table")
@click.argument("dest", type=click.Path())
def dl_data_table(dest: str):
    """Download data table."""
    _fetch(config.require_active_notebook(), "data_table", Path(dest))
