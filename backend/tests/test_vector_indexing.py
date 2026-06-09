from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.services import document_service, knowledge_service
from tests.conftest import create_kb


def enable_document_indexing(monkeypatch) -> None:
    monkeypatch.setattr(document_service, "get_settings", lambda: SimpleNamespace(vector_index_enabled=True))


def enable_knowledge_indexing(monkeypatch) -> None:
    monkeypatch.setattr(knowledge_service, "get_settings", lambda: SimpleNamespace(vector_index_enabled=True))


def test_text_upload_indexes_chunks_and_updates_vector_ids(client: TestClient, monkeypatch):
    kb = create_kb(client)
    captured: dict = {}

    enable_document_indexing(monkeypatch)
    monkeypatch.setattr(
        document_service.embedding_service,
        "embed_texts",
        lambda texts: [[float(index), 0.1] for index, _ in enumerate(texts)],
    )

    def fake_add_chunks(vector_ids, embeddings, documents, metadatas):
        captured["vector_ids"] = vector_ids
        captured["embeddings"] = embeddings
        captured["documents"] = documents
        captured["metadatas"] = metadatas

    monkeypatch.setattr(document_service.chroma_client, "add_chunks", fake_add_chunks)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={
            "title": "长段落",
            "content": "a" * 620,
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert len(data["chunks"]) > 1
    assert all(chunk["vector_id"] for chunk in data["chunks"])
    assert captured["vector_ids"] == [chunk["vector_id"] for chunk in data["chunks"]]
    assert captured["documents"] == [chunk["content"] for chunk in data["chunks"]]
    assert captured["metadatas"][0]["knowledge_base_id"] == kb["id"]
    assert captured["metadatas"][0]["document_id"] == data["id"]
    assert captured["metadatas"][0]["title"] == "长段落"


def test_text_upload_returns_500_when_vector_indexing_fails(client: TestClient, monkeypatch):
    kb = create_kb(client)

    enable_document_indexing(monkeypatch)
    monkeypatch.setattr(document_service.embedding_service, "embed_texts", lambda texts: [[0.1, 0.2]])

    def fail_add_chunks(*args, **kwargs):
        raise RuntimeError("vector store unavailable")

    monkeypatch.setattr(document_service.chroma_client, "add_chunks", fail_add_chunks)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={"title": "春", "content": "春天的脚步近了。"},
    )
    list_response = client.get(f"/api/knowledge-bases/{kb['id']}/documents")

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to index document chunks."
    assert list_response.json()["total"] == 0


def test_delete_document_deletes_vectors_first(client: TestClient, monkeypatch):
    kb = create_kb(client)
    created = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={"title": "春", "content": "春天的脚步近了。"},
    ).json()
    deleted_document_ids: list[int] = []

    enable_document_indexing(monkeypatch)
    monkeypatch.setattr(document_service.chroma_client, "delete_by_document_id", deleted_document_ids.append)

    response = client.delete(f"/api/documents/{created['id']}")

    assert response.status_code == 204
    assert deleted_document_ids == [created["id"]]


def test_delete_knowledge_base_deletes_vectors_first(client: TestClient, monkeypatch):
    kb = create_kb(client)
    deleted_knowledge_base_ids: list[int] = []

    enable_knowledge_indexing(monkeypatch)
    monkeypatch.setattr(
        knowledge_service.chroma_client,
        "delete_by_knowledge_base_id",
        deleted_knowledge_base_ids.append,
    )

    response = client.delete(f"/api/knowledge-bases/{kb['id']}")

    assert response.status_code == 204
    assert deleted_knowledge_base_ids == [kb["id"]]

