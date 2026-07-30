from __future__ import annotations

from typing import Any, Mapping


def format_shared_context(shared: Mapping[str, Any]) -> str:
    """Build a readable context block from prior agent outputs."""
    parts: list[str] = []
    for key in ("planner", "researcher", "coder"):
        value = shared.get(key)
        if value:
            parts.append(f"=== {key.upper()} ===\n{value}")
    return "\n\n".join(parts)


def excerpt(text: str, *, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."
