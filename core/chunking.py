"""Boundary-aware text chunking for document retrieval."""

from __future__ import annotations

import re
from typing import Any

_SENTENCE_END = re.compile(r"[.!?](?:[\"')\]]+)?(?=\s|$)")


def _preferred_end(text: str, start: int, limit: int) -> int:
    """Find a paragraph or sentence boundary before ``limit`` when possible."""
    if limit >= len(text):
        return len(text)
    candidates = [
        match.end()
        for match in re.finditer(r"\n\s*\n", text[start:limit])
    ]
    sentence_matches = list(_SENTENCE_END.finditer(text[start:limit]))
    candidates.extend(match.end() for match in sentence_matches)
    candidates = [start + end for end in candidates if start + end > start]
    if candidates:
        useful = [end for end in candidates if end >= start + (limit - start) // 2]
        if useful:
            return max(useful)
    whitespace = text.rfind(" ", start, limit)
    return whitespace if whitespace > start else limit


def chunk_text(
    text: str,
    *,
    size: int = 2000,
    overlap: int = 300,
    page: int | None = None,
    meta: dict[str, Any] | None = None,
    max_chars: int | None = None,
) -> list[dict[str, Any]]:
    """Split text into overlapping chunks while preferring natural boundaries."""
    if max_chars is not None:
        size = max_chars
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("size must be positive and greater than overlap")
    normalized = re.sub(r"[ \t]+\n", "\n", text).strip()
    if not normalized:
        return []
    if len(normalized) <= size:
        return [{"text": normalized, "page": page, "chunk_index": 0, "meta": dict(meta or {})}]

    chunks: list[dict[str, Any]] = []
    start = 0
    while start < len(normalized):
        end = _preferred_end(normalized, start, min(start + size, len(normalized)))
        value = normalized[start:end].strip()
        if value:
            chunks.append(
                {
                    "text": value,
                    "page": page,
                    "chunk_index": len(chunks),
                    "meta": dict(meta or {}),
                }
            )
        if end >= len(normalized):
            break
        next_start = max(start + 1, end - overlap)
        start = next_start
    return chunks
