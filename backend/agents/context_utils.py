from __future__ import annotations

import re
from typing import Any, Mapping, Optional


# ---------------------------------------------------------------------------
# Context formatting
# ---------------------------------------------------------------------------

def format_shared_context(shared: Mapping[str, Any]) -> str:
    """Build a readable context block from prior agent outputs."""
    parts: list[str] = []
    for key in ("planner", "researcher", "coder", "reviewer"):
        value = shared.get(key)
        if value:
            parts.append(f"=== {key.upper()} ===\n{value}")
    return "\n\n".join(parts)


def excerpt(text: str, *, max_chars: int = 1200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


# ---------------------------------------------------------------------------
# Structured field parsers
# ---------------------------------------------------------------------------

def parse_float(text: str, key: str, *, default: float) -> float:
    """Extract a float value from `KEY: <float>` lines."""
    m = re.search(rf"^{key}:\s*([\d.]+)", text, re.IGNORECASE | re.MULTILINE)
    if m:
        try:
            return max(0.0, min(1.0, float(m.group(1))))
        except ValueError:
            pass
    return default


def parse_int(text: str, key: str, *, default: int) -> int:
    """Extract an integer value from `KEY: <int>` lines."""
    m = re.search(rf"^{key}:\s*(\d+)", text, re.IGNORECASE | re.MULTILINE)
    if m:
        try:
            return int(m.group(1))
        except ValueError:
            pass
    return default


def parse_bool(text: str, key: str, *, default: bool) -> bool:
    """Extract a boolean (true/false/yes/no) from `KEY: <value>` lines."""
    m = re.search(rf"^{key}:\s*(\S+)", text, re.IGNORECASE | re.MULTILINE)
    if m:
        return m.group(1).strip().lower() in ("true", "yes", "1")
    return default


def parse_field(text: str, key: str, *, default: str = "") -> str:
    """Extract a single-line string value from `KEY: <value>` lines."""
    m = re.search(rf"^{key}:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
    return m.group(1).strip() if m else default


def parse_list_field(text: str, key: str) -> list[str]:
    """
    Extract a bullet list that follows a `KEY:` header.
    Stops at the next header (ALL_CAPS: ...) or end of string.
    """
    m = re.search(
        rf"^{key}:\s*\n((?:[ \t]*[-*•]\s*.+\n?)+)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if not m:
        return []
    block = m.group(1)
    return [
        re.sub(r"^[ \t]*[-*•]\s*", "", line).strip()
        for line in block.splitlines()
        if line.strip() and re.match(r"^[ \t]*[-*•]", line)
    ]


def parse_csv_field(text: str, key: str) -> list[str]:
    """Extract a comma-separated list from `KEY: a, b, c` lines."""
    raw = parse_field(text, key)
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]
