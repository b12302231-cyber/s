"""NotebookLMClient — top-level async client."""

import asyncio
import time
from typing import Any

from ..auth import (
    AuthError,
    _load_credentials,
    _refresh_token,
    _save_credentials,
)
from .artifacts import ArtifactsAPI
from .chat import ChatAPI
from .http import AsyncHTTPClient
from .notebooks import NotebooksAPI
from .sources import SourcesAPI

_REFRESH_BUFFER = 300  # seconds before expiry to proactively refresh


class NotebookLMClient:
    """Async client for the NotebookLM API.

    Usage::

        async with await NotebookLMClient.from_storage() as client:
            nb = await client.notebooks.create("My Research")
            result = await client.chat.ask(nb.id, "Summarize")
            print(result.answer)
    """

    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http
        self.notebooks = NotebooksAPI(http)
        self.sources = SourcesAPI(http)
        self.chat = ChatAPI(http)
        self.artifacts = ArtifactsAPI(http)

    @classmethod
    async def from_storage(cls) -> "NotebookLMClient":
        """Build a client from credentials stored by ``notebooklm login``.

        Raises :class:`~notebooklm.auth.AuthError` if no credentials exist.
        """
        creds: dict = _load_credentials() or {}  # type: ignore[assignment]
        if not creds:
            raise AuthError(
                "Not authenticated. Run 'notebooklm login' first."
            )

        # Mutable cell so the closure can update creds after a refresh.
        state: list[dict] = [creds]

        async def _token_getter() -> str:
            c = state[0]
            expires_at = c.get("expires_at", 0)
            if time.time() < expires_at - _REFRESH_BUFFER:
                return c["access_token"]
            if not c.get("refresh_token"):
                raise AuthError(
                    "Session expired and no refresh token available. "
                    "Run 'notebooklm login' again."
                )
            loop = asyncio.get_event_loop()
            refreshed = await loop.run_in_executor(
                None, _refresh_token, c["refresh_token"]
            )
            _save_credentials(refreshed)
            state[0] = refreshed
            return refreshed["access_token"]

        return cls(AsyncHTTPClient(_token_getter))

    async def __aenter__(self) -> "NotebookLMClient":
        await self._http.__aenter__()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self._http.__aexit__(*args)
