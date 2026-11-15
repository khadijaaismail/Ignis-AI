from core.chunking import chunk_text


def test_short_text_is_one_nonempty_chunk():
    chunks = chunk_text("A short synthetic paragraph.")
    assert len(chunks) == 1
    assert chunks[0]["text"] == "A short synthetic paragraph."


def test_chunks_are_nonempty_and_overlap():
    text = "Sentence one. " * 220
    chunks = chunk_text(text, size=200, overlap=40)
    assert all(chunk["text"] for chunk in chunks)
    assert len(chunks) > 1
    for previous, current in zip(chunks, chunks[1:]):
        assert any(
            current["text"].startswith(previous["text"][-size:])
            for size in range(1, 41)
        )


def test_page_and_section_metadata_are_preserved():
    chunks = chunk_text(
        "Synthetic source text.",
        page=4,
        meta={"psi_id": "PSI-1", "section": "objective"},
    )
    assert chunks[0]["page"] == 4
    assert chunks[0]["meta"] == {"psi_id": "PSI-1", "section": "objective"}
