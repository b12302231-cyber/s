"""NotebookLM — CLI and async Python SDK.

Quick start::

    from notebooklm import NotebookLMClient

    async with await NotebookLMClient.from_storage() as client:
        nb = await client.notebooks.create("Research")
        await client.sources.add_url(nb.id, "https://example.com", wait=True)
        result = await client.chat.ask(nb.id, "Summarize this")
        print(result.answer)
"""

from .sdk import NotebookLMClient
from .sdk.models import ArtifactStatus, ChatResult, Notebook, Source

__version__ = "0.1.0"

__all__ = [
    "NotebookLMClient",
    "Notebook",
    "Source",
    "ChatResult",
    "ArtifactStatus",
]
