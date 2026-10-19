import pytest

from app.ingest.chunking import chunk_text


def test_returns_empty_list_for_blank_text():
    assert chunk_text("   \n ", size=5, overlap=1) == []


def test_short_text_is_a_single_chunk():
    assert chunk_text("one two three", size=5, overlap=1) == ["one two three"]


def test_chunks_overlap_by_requested_words():
    text = " ".join(str(i) for i in range(10))

    chunks = chunk_text(text, size=4, overlap=1)

    assert chunks == ["0 1 2 3", "3 4 5 6", "6 7 8 9"]


def test_every_word_appears_in_some_chunk():
    words = [f"w{i}" for i in range(23)]

    chunks = chunk_text(" ".join(words), size=6, overlap=2)

    assert set(" ".join(chunks).split()) == set(words)


@pytest.mark.parametrize("size,overlap", [(0, 0), (5, 5), (5, 6), (5, -1)])
def test_rejects_invalid_size_or_overlap(size, overlap):
    with pytest.raises(ValueError):
        chunk_text("a b c", size=size, overlap=overlap)
