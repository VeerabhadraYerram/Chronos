"""Canonical UTC timestamps with a fixed precision for safe lexical intervals."""

from datetime import datetime, timezone


def canonical(value):
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("Timezone is required")
    return (
        stamp.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )
