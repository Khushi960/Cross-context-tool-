import uuid
from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Target = Literal["claude", "chatgpt", "gemini"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return uuid.uuid4().hex[:10]


class PacketIn(BaseModel):
    """The editable part of a packet (what the frontend sends)."""
    title: str = "Untitled"
    source: str = "Claude"
    goal: str = ""
    status: str = ""
    decisions: List[str] = Field(default_factory=list)
    constraints: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    open: List[str] = Field(default_factory=list)
    style: str = ""
    transcript: str = ""


class Packet(PacketIn):
    id: str
    created: str
    updated: str


class ExtractRequest(BaseModel):
    transcript: str = Field(min_length=1)
    source: str = "Claude"


class HandoffRequest(BaseModel):
    packet: PacketIn
    updated: Optional[str] = None
    target: Target = "claude"
    limit_tokens: int = Field(default=8000, ge=500, le=200000)
    condense: bool = False


class HandoffResult(BaseModel):
    text: str
    tokens: int
    limit: int
    over_limit: bool
    transcript_chars: int
    transcript_used: int
    trimmed: bool
    condensed: bool
