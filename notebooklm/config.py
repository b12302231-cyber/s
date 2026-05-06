"""Persistent session state (active notebook, API base URL)."""

import json
from pathlib import Path
from typing import Optional

_STATE_FILE = Path.home() / ".config" / "notebooklm" / "state.json"

API_BASE = "https://notebooklm.googleapis.com/v1"


def _load() -> dict:
    if _STATE_FILE.exists():
        try:
            return json.loads(_STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save(state: dict) -> None:
    _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    _STATE_FILE.write_text(json.dumps(state, indent=2))


def get_active_notebook() -> Optional[str]:
    return _load().get("active_notebook")


def set_active_notebook(notebook_id: str) -> None:
    state = _load()
    state["active_notebook"] = notebook_id
    _save(state)


def require_active_notebook() -> str:
    nb = get_active_notebook()
    if not nb:
        raise RuntimeError(
            "No active notebook. Run 'notebooklm use <notebook_id>' first."
        )
    return nb
