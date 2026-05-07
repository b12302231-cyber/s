"""SourcesAPI — add and inspect notebook sources."""

import asyncio
import mimetypes
from pathlib import Path
from typing import List

from .http import AsyncHTTPClient
from .models import Source

_POLL = 3  # seconds between status polls when wait=True


def _parse(data: dict) -> Source:
    return Source(
        id=data.get("id", ""),
        type=data.get("type", ""),
        title=data.get("title", ""),
        url=data.get("url", ""),
        status=data.get("state") or data.get("status", ""),
    )


class SourcesAPI:
    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def add_url(
        self, notebook_id: str, url: str, *, wait: bool = False
    ) -> Source:
        """Add a public URL as a source."""
        data = await self._http.post(
            f"/notebooks/{notebook_id}/sources", json={"url": url}
        )
        source = _parse(data)
        return await self._wait_ready(notebook_id, source.id) if wait else source

    async def add_file(
        self, notebook_id: str, path: str | Path, *, wait: bool = False
    ) -> Source:
        """Upload a local file as a source."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(p)
        mime, _ = mimetypes.guess_type(str(p))
        mime = mime or "application/octet-stream"
        with p.open("rb") as fh:
            data = await self._http.post(
                f"/notebooks/{notebook_id}/sources",
                files={"file": (p.name, fh, mime)},
            )
        source = _parse(data)
        return await self._wait_ready(notebook_id, source.id) if wait else source

    async def list(self, notebook_id: str) -> List[Source]:
        """Return all sources in a notebook."""
        data = await self._http.get(f"/notebooks/{notebook_id}/sources")
        return [_parse(s) for s in data.get("sources", [])]

    async def get(self, notebook_id: str, source_id: str) -> Source:
        """Fetch a single source by ID."""
        data = await self._http.get(f"/notebooks/{notebook_id}/sources/{source_id}")
        return _parse(data)

    async def _wait_ready(self, notebook_id: str, source_id: str) -> Source:
        while True:
            source = await self.get(notebook_id, source_id)
            if source.status in ("READY", "FAILED"):
                return source
            await asyncio.sleep(_POLL)
