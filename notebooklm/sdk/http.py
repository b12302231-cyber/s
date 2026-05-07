"""Async HTTP client that injects the current OAuth bearer token."""

from pathlib import Path
from typing import Any, Callable, Coroutine, Dict, Optional

import httpx

_API_BASE = "https://notebooklm.googleapis.com/v1"

TokenGetter = Callable[[], Coroutine[Any, Any, str]]


class AsyncHTTPClient:
    def __init__(self, token_getter: TokenGetter) -> None:
        self._token_getter = token_getter
        self._session: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "AsyncHTTPClient":
        self._session = httpx.AsyncClient(timeout=60)
        return self

    async def __aexit__(self, *_: Any) -> None:
        if self._session:
            await self._session.aclose()
            self._session = None

    @property
    def _client(self) -> httpx.AsyncClient:
        if self._session is None:
            raise RuntimeError(
                "HTTP session is not open — use 'async with client:' first."
            )
        return self._session

    async def _auth_headers(self) -> Dict[str, str]:
        token = await self._token_getter()
        return {"Authorization": f"Bearer {token}"}

    async def get(self, path: str, **kwargs: Any) -> Any:
        r = await self._client.get(
            _API_BASE + path, headers=await self._auth_headers(), **kwargs
        )
        r.raise_for_status()
        return r.json()

    async def post(self, path: str, **kwargs: Any) -> Any:
        r = await self._client.post(
            _API_BASE + path, headers=await self._auth_headers(), **kwargs
        )
        r.raise_for_status()
        return r.json()

    async def stream_download(
        self, path: str, dest: str | Path, params: Optional[Dict] = None
    ) -> None:
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        headers = await self._auth_headers()
        async with self._client.stream(
            "GET", _API_BASE + path, headers=headers, params=params or {}, timeout=None
        ) as r:
            r.raise_for_status()
            with dest.open("wb") as fh:
                async for chunk in r.aiter_bytes(65_536):
                    fh.write(chunk)
