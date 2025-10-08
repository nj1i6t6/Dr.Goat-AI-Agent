import numpy as np
import pytest

from app.ai import embedding


class DummyResponse:
    def __init__(self, status_code=200, json_data=None, text_data="", raise_json=False):
        self.status_code = status_code
        self._json_data = json_data
        self._text = text_data
        self._raise_json = raise_json

    def json(self):
        if self._raise_json:
            raise ValueError("invalid json")
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data

    @property
    def text(self):
        return self._text


class DummySession:
    def __init__(self, responses):
        self._responses = list(responses)
        self.calls = []

    def post(self, url, params=None, json=None, timeout=None):
        self.calls.append((url, params, json, timeout))
        if not self._responses:
            raise AssertionError("Unexpected post call")
        return self._responses.pop(0)


def test_resolve_api_key_validation(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(embedding.EmbeddingError):
        embedding._resolve_api_key(None)

    assert embedding._resolve_api_key("explicit-key") == "explicit-key"
    monkeypatch.setenv("GOOGLE_API_KEY", "env-key")
    assert embedding._resolve_api_key(None) == "env-key"


@pytest.mark.parametrize(
    "vector,expected",
    [([3.0, 4.0], np.array([0.6, 0.8], dtype=np.float32)), ([0.0, 0.0], np.array([0.0, 0.0], dtype=np.float32))],
)
def test_normalize_vector(vector, expected):
    out = embedding._normalize_vector(vector)
    np.testing.assert_allclose(out, expected)


def test_perform_embedding_requests_success(monkeypatch):
    response = DummyResponse(
        status_code=200,
        json_data={"embeddings": [{"values": [3.0, 4.0]}]},
    )
    session = DummySession([response])
    monkeypatch.setattr(embedding, "_get_session", lambda: session)
    requests_batch = [embedding._EmbeddingRequest(text="hello", task_type="query")]
    vectors = embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert len(vectors) == 1
    assert float(np.linalg.norm(vectors[0])) == pytest.approx(1.0)
    assert session.calls[0][2]["requests"][0]["content"]["parts"][0]["text"] == "hello"


def test_perform_embedding_requests_http_error(monkeypatch):
    response = DummyResponse(status_code=500, json_data={"error": "failed"})
    session = DummySession([response])
    monkeypatch.setattr(embedding, "_get_session", lambda: session)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "Embedding API error" in str(exc.value)


def test_perform_embedding_requests_invalid_json(monkeypatch):
    response = DummyResponse(status_code=200, raise_json=True)
    session = DummySession([response])
    monkeypatch.setattr(embedding, "_get_session", lambda: session)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "Failed to parse embedding response" in str(exc.value)


def test_perform_embedding_requests_missing_vectors(monkeypatch):
    response = DummyResponse(status_code=200, json_data={"embeddings": []})
    session = DummySession([response])
    monkeypatch.setattr(embedding, "_get_session", lambda: session)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "missing expected vectors" in str(exc.value)


def test_perform_embedding_requests_invalid_values(monkeypatch):
    response = DummyResponse(status_code=200, json_data={"embeddings": [{}]})
    session = DummySession([response])
    monkeypatch.setattr(embedding, "_get_session", lambda: session)
    requests_batch = [embedding._EmbeddingRequest(text="bad", task_type="query")]
    with pytest.raises(embedding.EmbeddingError) as exc:
        embedding._perform_embedding_requests(requests_batch, api_key="test-key")
    assert "empty vector" in str(exc.value)


def test_embed_documents_batches(monkeypatch):
    vectors_returned = []

    def fake_perform(batch, api_key):
        vectors_returned.append(len(batch))
        return [np.ones(3, dtype=np.float32) for _ in batch]

    monkeypatch.setattr(embedding, "_perform_embedding_requests", fake_perform)
    monkeypatch.setenv("GOOGLE_API_KEY", "batch-key")
    texts = [f"text-{i}" for i in range(embedding.BATCH_SIZE + 3)]
    vectors = embedding.embed_documents(texts)
    assert len(vectors) == len(texts)
    assert vectors_returned == [embedding.BATCH_SIZE, 3]


def test_embed_query_requires_vector(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")
    monkeypatch.setattr(embedding, "_perform_embedding_requests", lambda batch, api_key: [])
    with pytest.raises(embedding.EmbeddingError):
        embedding.embed_query("question")


def test_embed_query_success(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")

    def fake_perform(batch, api_key):
        assert len(batch) == 1
        return [np.array([1.0, 0.0], dtype=np.float32)]

    monkeypatch.setattr(embedding, "_perform_embedding_requests", fake_perform)
    vector = embedding.embed_query("question")
    np.testing.assert_allclose(vector, np.array([1.0, 0.0], dtype=np.float32))


def test_embed_no_texts_returns_empty(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "query-key")
    result = embedding.embed_documents([])
    assert result == []
