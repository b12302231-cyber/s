"""ChatAPI — question-answering grounded in notebook sources."""

from .http import AsyncHTTPClient
from .models import ChatResult


class ChatAPI:
    def __init__(self, http: AsyncHTTPClient) -> None:
        self._http = http

    async def ask(self, notebook_id: str, question: str) -> ChatResult:
        """Send a question and return the grounded answer."""
        data = await self._http.post(
            f"/notebooks/{notebook_id}/chat",
            json={"message": question},
        )
        return ChatResult(
            answer=data.get("text") or data.get("answer") or data.get("response", ""),
            citations=data.get("citations", []),
        )
