"""ArtifactsAPI — generate and download notebook artifacts."""

import asyncio
from pathlib import Path
from typing import Optional

from .http import AsyncHTTPClient
from .models import ArtifactStatus

_POLL = 5  # seconds between job-status polls

# Map of artifact type → artifact API endpoint segment
_ARTIFACT_ENDPOINTS: dict[str, str] = {
    "audio": "audio",
    "video": "video",
    "cinematic_video": "cinematic_video",
    "quiz": "quiz",
    "flashcards": "flashcards",
    "slide_deck": "slide_deck",
    "infographic": "infographic",
    "mind_map": "mind_map",
    "data_table": "data_table",
}


def _parse_status(data: dict, task_id: str = "") -> ArtifactStatus:
    return ArtifactStatus(
        task_id=task_id or data.get("jobId") or data.get("id", ""),
        state=data.get("state", "PENDING"),
        artifact_id=data.get("artifactId"),
        error=data.get("error", {}).get("message") if isinstance(data.get("error"), dict) else data.get("error"),
    )


class ArtifactsAPI:
    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _generate(self, notebook_id: str, payload: dict) -> ArtifactStatus:
        data = await self._http.post(
            f"/notebooks/{notebook_id}/generate", json=payload
        )
        return _parse_status(data)

    async def _download(
        self,
        notebook_id: str,
        endpoint: str,
        dest: str | Path,
        output_format: str = "",
    ) -> None:
        params = {"format": output_format} if output_format else None
        await self._http.stream_download(
            f"/notebooks/{notebook_id}/artifacts/{endpoint}",
            dest,
            params=params,
        )

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    async def generate_audio(
        self, notebook_id: str, *, instructions: str = ""
    ) -> ArtifactStatus:
        """Start an audio (podcast) generation job."""
        payload: dict = {"type": "audio"}
        if instructions:
            payload["prompt"] = instructions
        return await self._generate(notebook_id, payload)

    async def generate_video(
        self, notebook_id: str, *, style: str = "standard"
    ) -> ArtifactStatus:
        """Start a video generation job."""
        return await self._generate(
            notebook_id, {"type": "video", "style": style}
        )

    async def generate_cinematic_video(
        self, notebook_id: str, *, instructions: str = ""
    ) -> ArtifactStatus:
        """Start a cinematic video generation job."""
        payload: dict = {"type": "cinematic_video"}
        if instructions:
            payload["prompt"] = instructions
        return await self._generate(notebook_id, payload)

    async def generate_quiz(
        self, notebook_id: str, *, difficulty: str = "medium"
    ) -> ArtifactStatus:
        """Start a quiz generation job."""
        return await self._generate(
            notebook_id, {"type": "quiz", "difficulty": difficulty}
        )

    async def generate_flashcards(
        self, notebook_id: str, *, quantity: str = "standard"
    ) -> ArtifactStatus:
        """Start a flashcard generation job."""
        return await self._generate(
            notebook_id, {"type": "flashcards", "quantity": quantity}
        )

    async def generate_slide_deck(self, notebook_id: str) -> ArtifactStatus:
        """Start a slide deck generation job."""
        return await self._generate(notebook_id, {"type": "slide_deck"})

    async def generate_infographic(
        self, notebook_id: str, *, orientation: str = "landscape"
    ) -> ArtifactStatus:
        """Start an infographic generation job."""
        return await self._generate(
            notebook_id, {"type": "infographic", "orientation": orientation}
        )

    async def generate_mind_map(self, notebook_id: str) -> ArtifactStatus:
        """Start a mind map generation job."""
        return await self._generate(notebook_id, {"type": "mind_map"})

    async def generate_data_table(
        self, notebook_id: str, *, instructions: str = ""
    ) -> ArtifactStatus:
        """Start a data table generation job."""
        payload: dict = {"type": "data_table"}
        if instructions:
            payload["prompt"] = instructions
        return await self._generate(notebook_id, payload)

    # ------------------------------------------------------------------
    # Polling
    # ------------------------------------------------------------------

    async def wait_for_completion(
        self, notebook_id: str, task_id: str
    ) -> ArtifactStatus:
        """Poll until the job reaches DONE or FAILED."""
        while True:
            data = await self._http.get(f"/notebooks/{notebook_id}/jobs/{task_id}")
            state = data.get("state", "")
            if state == "DONE":
                return ArtifactStatus(
                    task_id=task_id,
                    state="DONE",
                    artifact_id=data.get("artifactId"),
                )
            if state in ("FAILED", "CANCELLED"):
                msg = (
                    data.get("error", {}).get("message", "unknown")
                    if isinstance(data.get("error"), dict)
                    else data.get("error", "unknown")
                )
                raise RuntimeError(f"Job {task_id} {state.lower()}: {msg}")
            await asyncio.sleep(_POLL)

    # ------------------------------------------------------------------
    # Downloads
    # ------------------------------------------------------------------

    async def download_audio(self, notebook_id: str, dest: str | Path) -> None:
        await self._download(notebook_id, "audio", dest)

    async def download_video(self, notebook_id: str, dest: str | Path) -> None:
        await self._download(notebook_id, "video", dest)

    async def download_cinematic_video(
        self, notebook_id: str, dest: str | Path
    ) -> None:
        await self._download(notebook_id, "cinematic_video", dest)

    async def download_quiz(
        self,
        notebook_id: str,
        dest: str | Path,
        *,
        output_format: str = "",
    ) -> None:
        await self._download(notebook_id, "quiz", dest, output_format)

    async def download_flashcards(
        self,
        notebook_id: str,
        dest: str | Path,
        *,
        output_format: str = "",
    ) -> None:
        await self._download(notebook_id, "flashcards", dest, output_format)

    async def download_slide_deck(
        self, notebook_id: str, dest: str | Path
    ) -> None:
        await self._download(notebook_id, "slide_deck", dest)

    async def download_infographic(
        self, notebook_id: str, dest: str | Path
    ) -> None:
        await self._download(notebook_id, "infographic", dest)

    async def download_mind_map(
        self, notebook_id: str, dest: str | Path
    ) -> None:
        await self._download(notebook_id, "mind_map", dest)

    async def download_data_table(
        self, notebook_id: str, dest: str | Path
    ) -> None:
        await self._download(notebook_id, "data_table", dest)
