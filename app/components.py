"""Shared Streamlit components for the IGNIS AI interface."""

from collections.abc import Mapping
from typing import Any

import streamlit as st

_BADGE_COLORS = {
    "experimental_evidence": "blue",
    "interpretation": "violet",
    "research_gap": "orange",
}


def _field(chunk: Any, *names: str, default: str = "Not reported") -> Any:
    """Return the first non-empty field from a mapping or object."""
    for name in names:
        value = chunk.get(name) if isinstance(chunk, Mapping) else getattr(chunk, name, None)
        if value is not None and value != "":
            return value
    return default


def inject_css() -> None:
    """No-op kept so existing pages still work; styling lives in .streamlit/config.toml."""


def honesty_banner() -> None:
    """Display the persistent scientific-integrity scope notice."""
    st.warning(
        "NASA PSI currently contains no partial-gravity combustion data "
        "(LUCI and FM2 are expected to add it). Microgravity and normal-gravity "
        "results only bound lunar conditions. Rocket and propellant fires are out of scope."
    )


def evidence_badge(kind: str) -> None:
    color = _BADGE_COLORS.get(kind.strip().lower(), "gray")
    st.badge(kind.replace("_", " ").capitalize(), color=color)


def confidence_badge(level: str) -> None:
    st.badge(f"Confidence: {level}", color="gray")


def source_card(chunk: Any) -> None:
    """Render a retrieved source chunk without inventing missing metadata."""
    chunk_id = _field(chunk, "id", "chunk_id")
    title = _field(chunk, "title", default="Untitled source")
    text = _field(chunk, "text", "content")
    source = _field(chunk, "source")

    with st.container(border=True):
        st.badge(f"Source: {source}")
        st.text(title)
        with st.expander("Retrieved text"):
            st.text(text)
        st.text(f"Chunk ID: {chunk_id}")