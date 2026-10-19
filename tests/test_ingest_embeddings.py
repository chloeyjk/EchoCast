from types import SimpleNamespace
from unittest.mock import MagicMock

from app.ingest.embeddings import embed_texts


def test_embed_texts_returns_vectors_in_input_order():
    data = [SimpleNamespace(index=1, embedding=[2.0]), SimpleNamespace(index=0, embedding=[1.0])]
    client = MagicMock()
    client.embeddings.create.return_value = SimpleNamespace(data=data)

    vectors = embed_texts(client, ["a", "b"], model="m")

    assert vectors == [[1.0], [2.0]]
    client.embeddings.create.assert_called_once_with(model="m", input=["a", "b"])


def test_embed_texts_skips_api_call_for_empty_input():
    client = MagicMock()

    assert embed_texts(client, [], model="m") == []
    client.embeddings.create.assert_not_called()


def test_embed_texts_batches_large_inputs():
    client = MagicMock()
    client.embeddings.create.side_effect = lambda model, input: SimpleNamespace(
        data=[SimpleNamespace(index=i, embedding=[0.0]) for i in range(len(input))]
    )

    vectors = embed_texts(client, ["x"] * 5, model="m", batch_size=2)

    assert len(vectors) == 5
    assert client.embeddings.create.call_count == 3
