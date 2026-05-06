"""notebooklm generate <type> [prompt] [options]"""

import time

import click
from rich.console import Console

from .. import client, config

console = Console()

_POLL_INTERVAL = 5  # seconds between status polls


def _wait_for_job(notebook_id: str, job_id: str, label: str) -> dict:
    with console.status(f"[bold green]Generating {label}…"):
        while True:
            resp = client.get(f"/notebooks/{notebook_id}/jobs/{job_id}")
            data = resp.json()
            state = data.get("state", "")
            if state == "DONE":
                return data
            if state in ("FAILED", "CANCELLED"):
                raise click.ClickException(
                    f"Job {state.lower()}: {data.get('error', {}).get('message', 'unknown error')}"
                )
            time.sleep(_POLL_INTERVAL)


@click.group()
def generate():
    """Generate content from notebook sources."""


# ---------------------------------------------------------------------------
# audio
# ---------------------------------------------------------------------------

@generate.command("audio")
@click.argument("prompt", default="")
@click.option("--wait", is_flag=True, help="Wait for generation to complete.")
def gen_audio(prompt: str, wait: bool):
    """Generate a podcast-style audio overview."""
    notebook_id = config.require_active_notebook()
    payload = {"type": "audio"}
    if prompt:
        payload["prompt"] = prompt
    resp = client.post(f"/notebooks/{notebook_id}/generate", json=payload)
    data = resp.json()
    job_id = data.get("jobId") or data.get("id")
    click.echo(f"Audio generation started (job: {job_id})")
    if wait and job_id:
        result = _wait_for_job(notebook_id, job_id, "audio")
        click.echo(f"Done. Artifact ID: {result.get('artifactId')}")


# ---------------------------------------------------------------------------
# video
# ---------------------------------------------------------------------------

@generate.command("video")
@click.option(
    "--style",
    default="standard",
    show_default=True,
    type=click.Choice(["standard", "whiteboard", "slides"], case_sensitive=False),
    help="Visual style for the video.",
)
@click.option("--wait", is_flag=True, help="Wait for generation to complete.")
def gen_video(style: str, wait: bool):
    """Generate a video overview."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "video", "style": style},
    )
    data = resp.json()
    job_id = data.get("jobId") or data.get("id")
    click.echo(f"Video generation started (job: {job_id})")
    if wait and job_id:
        result = _wait_for_job(notebook_id, job_id, "video")
        click.echo(f"Done. Artifact ID: {result.get('artifactId')}")


# ---------------------------------------------------------------------------
# cinematic-video
# ---------------------------------------------------------------------------

@generate.command("cinematic-video")
@click.argument("prompt", default="")
@click.option("--wait", is_flag=True, help="Wait for generation to complete.")
def gen_cinematic_video(prompt: str, wait: bool):
    """Generate a cinematic-style video."""
    notebook_id = config.require_active_notebook()
    payload = {"type": "cinematic_video"}
    if prompt:
        payload["prompt"] = prompt
    resp = client.post(f"/notebooks/{notebook_id}/generate", json=payload)
    data = resp.json()
    job_id = data.get("jobId") or data.get("id")
    click.echo(f"Cinematic video generation started (job: {job_id})")
    if wait and job_id:
        result = _wait_for_job(notebook_id, job_id, "cinematic video")
        click.echo(f"Done. Artifact ID: {result.get('artifactId')}")


# ---------------------------------------------------------------------------
# quiz
# ---------------------------------------------------------------------------

@generate.command("quiz")
@click.option(
    "--difficulty",
    default="medium",
    show_default=True,
    type=click.Choice(["easy", "medium", "hard"], case_sensitive=False),
)
def gen_quiz(difficulty: str):
    """Generate a quiz."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "quiz", "difficulty": difficulty},
    )
    data = resp.json()
    click.echo(f"Quiz generated (artifact: {data.get('artifactId', 'ok')})")


# ---------------------------------------------------------------------------
# flashcards
# ---------------------------------------------------------------------------

@generate.command("flashcards")
@click.option(
    "--quantity",
    default="standard",
    show_default=True,
    type=click.Choice(["fewer", "standard", "more"], case_sensitive=False),
)
def gen_flashcards(quantity: str):
    """Generate flashcards."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "flashcards", "quantity": quantity},
    )
    data = resp.json()
    click.echo(f"Flashcards generated (artifact: {data.get('artifactId', 'ok')})")


# ---------------------------------------------------------------------------
# slide-deck
# ---------------------------------------------------------------------------

@generate.command("slide-deck")
def gen_slide_deck():
    """Generate a slide deck."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "slide_deck"},
    )
    data = resp.json()
    click.echo(f"Slide deck generated (artifact: {data.get('artifactId', 'ok')})")


# ---------------------------------------------------------------------------
# infographic
# ---------------------------------------------------------------------------

@generate.command("infographic")
@click.option(
    "--orientation",
    default="landscape",
    show_default=True,
    type=click.Choice(["landscape", "portrait"], case_sensitive=False),
)
def gen_infographic(orientation: str):
    """Generate an infographic."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "infographic", "orientation": orientation},
    )
    data = resp.json()
    click.echo(f"Infographic generated (artifact: {data.get('artifactId', 'ok')})")


# ---------------------------------------------------------------------------
# mind-map
# ---------------------------------------------------------------------------

@generate.command("mind-map")
def gen_mind_map():
    """Generate a mind map."""
    notebook_id = config.require_active_notebook()
    resp = client.post(
        f"/notebooks/{notebook_id}/generate",
        json={"type": "mind_map"},
    )
    data = resp.json()
    click.echo(f"Mind map generated (artifact: {data.get('artifactId', 'ok')})")


# ---------------------------------------------------------------------------
# data-table
# ---------------------------------------------------------------------------

@generate.command("data-table")
@click.argument("prompt", default="")
def gen_data_table(prompt: str):
    """Generate a structured data table."""
    notebook_id = config.require_active_notebook()
    payload = {"type": "data_table"}
    if prompt:
        payload["prompt"] = prompt
    resp = client.post(f"/notebooks/{notebook_id}/generate", json=payload)
    data = resp.json()
    click.echo(f"Data table generated (artifact: {data.get('artifactId', 'ok')})")
