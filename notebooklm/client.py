"""HTTP client that injects the current OAuth token."""

import httpx

from . import auth, config


def _headers() -> dict:
    return {"Authorization": f"Bearer {auth.get_access_token()}"}


def get(path: str, **kwargs) -> httpx.Response:
    url = config.API_BASE + path
    r = httpx.get(url, headers=_headers(), timeout=60, **kwargs)
    r.raise_for_status()
    return r


def post(path: str, **kwargs) -> httpx.Response:
    url = config.API_BASE + path
    r = httpx.post(url, headers=_headers(), timeout=60, **kwargs)
    r.raise_for_status()
    return r


def delete(path: str, **kwargs) -> httpx.Response:
    url = config.API_BASE + path
    r = httpx.delete(url, headers=_headers(), timeout=60, **kwargs)
    r.raise_for_status()
    return r


def stream_get(path: str, **kwargs):
    """Return a context manager for a streaming GET."""
    url = config.API_BASE + path
    return httpx.stream("GET", url, headers=_headers(), timeout=None, **kwargs)
