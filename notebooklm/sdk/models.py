"""Immutable data models returned by the SDK."""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass(frozen=True)
class Notebook:
    id: str
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    source_count: int = 0


@dataclass(frozen=True)
class Source:
    id: str
    type: str
    title: str = ""
    url: str = ""
    status: str = ""


@dataclass(frozen=True)
class ChatResult:
    answer: str
    citations: List[dict] = field(default_factory=list)


@dataclass(frozen=True)
class ArtifactStatus:
    task_id: str
    state: str = "PENDING"
    artifact_id: Optional[str] = None
    error: Optional[str] = None
