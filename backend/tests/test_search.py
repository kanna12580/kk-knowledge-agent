import json

from fastapi.testclient import TestClient

from app.services import retrieval_service
from tests.conftest import create_kb


def fake_chroma_results() -> dict:
    return {
        "documents": [["盼望着，盼望着，东风来了。", "小草偷偷地从土里钻出来。"]],
        "metadatas": [
            [
                {
                    "knowledge_base_id": 1,
                    "document_id": 2,
                    "chunk_id": 10,
                    "chunk_index": 0,
                    "title": "春",
                },
                {
                    "knowledge_base_id": 1,
                    "document_id": 2,
                    "chunk_id": 11,
                    "chunk_index": 1,
                    "title": "春",
                },
            ]
        ],
        "distances": [[0.12, 0.3]],
    }


def patch_search_dependencies(monkeypatch, raw_results: dict | None = None) -> None:
    monkeypatch.setattr(retrieval_service.embedding_service, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])
    monkeypatch.setattr(
        retrieval_service.chroma_client,
        "query_chunks",
        lambda query_embedding, knowledge_base_id, top_k: raw_results or fake_chroma_results(),
    )


def parse_sse_events(content: str) -> list[dict]:
    events = []
    for block in content.strip().split("\n\n"):
        if not block.startswith("data: "):
            continue
        events.append(json.loads(block.removeprefix("data: ")))
    return events


def test_search_success(client: TestClient, monkeypatch):
    kb = create_kb(client)
    patch_search_dependencies(monkeypatch)

    response = client.post(
        "/api/search",
        json={"knowledge_base_id": kb["id"], "query": "春天", "top_k": 2},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "春天"
    assert len(data["results"]) == 2
    assert data["results"][0]["document_id"] == 2
    assert data["results"][0]["title"] == "春"
    assert data["results"][0]["score"] == 0.8929


def test_search_empty_query_fails(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        "/api/search",
        json={"knowledge_base_id": kb["id"], "query": "   ", "top_k": 2},
    )

    assert response.status_code == 422


def test_search_knowledge_base_not_found_fails(client: TestClient):
    response = client.post(
        "/api/search",
        json={"knowledge_base_id": 999, "query": "春天", "top_k": 2},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge base not found."


def test_search_retrieval_failure_returns_500(client: TestClient, monkeypatch):
    kb = create_kb(client)
    monkeypatch.setattr(retrieval_service.embedding_service, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])

    def fail_query(*args, **kwargs):
        raise RuntimeError("vector query failed")

    monkeypatch.setattr(retrieval_service.chroma_client, "query_chunks", fail_query)

    response = client.post(
        "/api/search",
        json={"knowledge_base_id": kb["id"], "query": "春天", "top_k": 2},
    )

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to search knowledge base."


def test_stream_search_success(client: TestClient, monkeypatch):
    kb = create_kb(client)
    patch_search_dependencies(monkeypatch)

    response = client.post(
        "/api/search/stream",
        json={"knowledge_base_id": kb["id"], "query": "春天", "top_k": 2},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse_events(response.text)
    assert [event["type"] for event in events] == ["start", "delta", "result", "result", "done"]
    assert events[2]["title"] == "春"


def test_stream_search_retrieval_failure_yields_error_event(client: TestClient, monkeypatch):
    kb = create_kb(client)
    monkeypatch.setattr(retrieval_service.embedding_service, "embed_texts", lambda texts: [[0.1, 0.2, 0.3]])

    def fail_query(*args, **kwargs):
        raise RuntimeError("vector query failed")

    monkeypatch.setattr(retrieval_service.chroma_client, "query_chunks", fail_query)

    response = client.post(
        "/api/search/stream",
        json={"knowledge_base_id": kb["id"], "query": "春天", "top_k": 2},
    )

    assert response.status_code == 200
    events = parse_sse_events(response.text)
    assert [event["type"] for event in events] == ["start", "error", "done"]
    assert events[1]["message"] == "Failed to search knowledge base."
