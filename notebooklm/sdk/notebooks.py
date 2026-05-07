"""NotebooksAPI — CRUD for notebooks."""

from typing import List

from .http import AsyncHTTPClient
from .models import Notebook


def _parse(data: dict) -> Notebook:
    return Notebook(
        id=data.get("id") or data.get("notebookId", ""),
        title=data.get("title", ""),
        created_at=data.get("createTime"),
        updated_at=data.get("updateTime"),
        source_count=len(data.get("sources", [])),
    )


class NotebooksAPI:
    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def create(self, title: str) -> Notebook:
        """Create a new notebook and return it."""
        data = await self._http.post("/notebooks", json={"title": title})
        return _parse(data)

    async def get(self, notebook_id: str) -> Notebook:
        """Fetch a single notebook by ID."""
        data = await self._http.get(f"/notebooks/{notebook_id}")
        return _parse(data)

    async def list(self) -> List[Notebook]:
        """Return all notebooks owned by the authenticated user."""
        data = await self._http.get("/notebooks")
        return [_parse(n) for n in data.get("notebooks", [])]
