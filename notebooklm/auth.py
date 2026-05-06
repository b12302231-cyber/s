"""Browser-based OAuth2 authentication for NotebookLM."""

import json
import os
import secrets
import socket
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Optional

import httpx

# Google OAuth2 endpoints
_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_REVOKE_URL = "https://oauth2.googleapis.com/revoke"

# Scopes required for NotebookLM
_SCOPES = [
    "https://www.googleapis.com/auth/notebooklm",
    "openid",
    "email",
    "profile",
]

# Public OAuth client for CLI (installed-app flow)
_CLIENT_ID = os.environ.get(
    "NOTEBOOKLM_CLIENT_ID",
    "notebooklm-cli",
)
_CLIENT_SECRET = os.environ.get("NOTEBOOKLM_CLIENT_SECRET", "")

_CREDENTIALS_FILE = Path.home() / ".config" / "notebooklm" / "credentials.json"

# How long before expiry to proactively refresh (seconds)
_REFRESH_BUFFER = 300


class AuthError(Exception):
    pass


class _CallbackHandler(BaseHTTPRequestHandler):
    """Local HTTP server that catches the OAuth redirect."""

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = dict(urllib.parse.parse_qsl(parsed.query))
        self.server.callback_params = params  # type: ignore[attr-defined]

        if "error" in params:
            body = f"Authentication failed: {params['error']}. You may close this tab."
            status = 400
        else:
            body = "Authentication successful! You may close this tab."
            status = 200

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(
            f"<html><body><p>{body}</p></body></html>".encode()
        )

    def log_message(self, *args):  # suppress access log
        pass


def _find_free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def login(browser: Optional[str] = None) -> dict:
    """Run the browser-based OAuth2 flow and persist credentials.

    Parameters
    ----------
    browser:
        Optional browser name passed to :func:`webbrowser.get`
        (e.g. ``"msedge"``).  If *None*, the system default is used.

    Returns
    -------
    dict
        The stored credentials dict.
    """
    port = _find_free_port()
    redirect_uri = f"http://127.0.0.1:{port}/callback"
    state = secrets.token_urlsafe(32)
    code_verifier = secrets.token_urlsafe(64)

    # Build authorisation URL
    params = {
        "client_id": _CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(_SCOPES),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
        "code_challenge_method": "S256",
        "code_challenge": _pkce_challenge(code_verifier),
    }
    auth_url = _AUTH_URL + "?" + urllib.parse.urlencode(params)

    # Start the local callback server
    server = HTTPServer(("127.0.0.1", port), _CallbackHandler)
    server.callback_params = {}  # type: ignore[attr-defined]
    server.timeout = 120

    t = threading.Thread(target=_serve_once, args=(server,), daemon=True)
    t.start()

    # Open the browser
    _open_browser(auth_url, browser)

    # Wait for the callback
    t.join(timeout=125)
    params_received: dict = server.callback_params  # type: ignore[attr-defined]

    if not params_received:
        raise AuthError(
            "Timed out waiting for the browser callback. "
            "Please run 'notebooklm login' again."
        )
    if params_received.get("state") != state:
        raise AuthError("State mismatch — possible CSRF. Please try again.")
    if "error" in params_received:
        raise AuthError(f"OAuth error: {params_received['error']}")
    if "code" not in params_received:
        raise AuthError("No authorisation code received.")

    # Exchange code for tokens
    credentials = _exchange_code(
        params_received["code"], redirect_uri, code_verifier
    )
    _save_credentials(credentials)
    return credentials


def logout() -> None:
    """Revoke the stored token and delete local credentials."""
    creds = _load_credentials()
    if creds:
        token = creds.get("access_token") or creds.get("refresh_token")
        if token:
            try:
                httpx.post(_REVOKE_URL, params={"token": token}, timeout=10)
            except Exception:
                pass
    if _CREDENTIALS_FILE.exists():
        _CREDENTIALS_FILE.unlink()


def get_access_token() -> str:
    """Return a valid access token, refreshing if necessary."""
    creds = _load_credentials()
    if not creds:
        raise AuthError(
            "Not authenticated. Run 'notebooklm login' first."
        )

    expires_at = creds.get("expires_at", 0)
    if time.time() < expires_at - _REFRESH_BUFFER:
        return creds["access_token"]

    # Refresh
    if not creds.get("refresh_token"):
        raise AuthError(
            "Session expired and no refresh token available. "
            "Run 'notebooklm login' again."
        )
    creds = _refresh_token(creds["refresh_token"])
    _save_credentials(creds)
    return creds["access_token"]


def is_authenticated() -> bool:
    return _CREDENTIALS_FILE.exists()


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _serve_once(server: HTTPServer) -> None:
    """Handle exactly one request then shut down."""
    server.handle_request()


def _open_browser(url: str, browser_name: Optional[str]) -> None:
    if browser_name:
        try:
            b = webbrowser.get(browser_name)
            b.open(url)
            return
        except webbrowser.Error:
            pass  # fall through to default
    webbrowser.open(url)


def _pkce_challenge(verifier: str) -> str:
    import base64
    import hashlib

    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode()


def _exchange_code(code: str, redirect_uri: str, code_verifier: str) -> dict:
    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
            "code_verifier": code_verifier,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    data["expires_at"] = time.time() + data.get("expires_in", 3600)
    return data


def _refresh_token(refresh_token: str) -> dict:
    resp = httpx.post(
        _TOKEN_URL,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": _CLIENT_ID,
            "client_secret": _CLIENT_SECRET,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    data["refresh_token"] = refresh_token  # preserve original refresh token
    data["expires_at"] = time.time() + data.get("expires_in", 3600)
    return data


def _save_credentials(creds: dict) -> None:
    _CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _CREDENTIALS_FILE.write_text(json.dumps(creds, indent=2))
    _CREDENTIALS_FILE.chmod(0o600)


def _load_credentials() -> Optional[dict]:
    if not _CREDENTIALS_FILE.exists():
        return None
    try:
        return json.loads(_CREDENTIALS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return None
