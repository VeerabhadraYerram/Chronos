from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Investigation(BaseModel):
    question: str = Field(
        default="Can we remove the payment retry delay?", min_length=5, max_length=2000
    )
    partner: Literal["all", "a", "b"] = "all"
    proposed_ms: int = Field(default=0, ge=0, le=10000)
    effective_at: str = "2026-10-15T12:00:00Z"
    known_at: str = "2026-10-15T12:00:00Z"
    use_gemini: bool = False

    @field_validator("effective_at", "known_at")
    @classmethod
    def timestamp(cls, v):
        dt = datetime.fromisoformat(v.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("Timezone is required")
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Replay(BaseModel):
    event: Literal["migration", "proposal", "withdraw-evidence"]
