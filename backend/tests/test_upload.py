from fastapi.testclient import TestClient

from tests.conftest import create_kb


def test_text_upload_success_creates_chunks(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={
            "title": "春",
            "content": "盼望着，盼望着，东风来了，春天的脚步近了。\n\n小草偷偷地从土里钻出来。",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "春"
    assert data["source_type"] == "text"
    assert data["file_name"] is None
    assert len(data["chunks"]) >= 1
    assert data["chunks"][0]["chunk_index"] == 0


def test_text_upload_empty_content_fails(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={"title": "空文档", "content": "   "},
    )

    assert response.status_code == 422


def test_text_upload_knowledge_base_not_found_fails(client: TestClient):
    response = client.post(
        "/api/knowledge-bases/999/documents/text",
        json={"title": "春", "content": "盼望着，盼望着。"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge base not found."


def test_txt_upload_success(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/file",
        data={"title": "故乡"},
        files={"file": ("guxiang.txt", "深蓝的天空中挂着一轮金黄的圆月。", "text/plain")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "故乡"
    assert data["source_type"] == "file"
    assert data["file_name"] == "guxiang.txt"
    assert len(data["chunks"]) == 1


def test_non_txt_upload_fails(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/file",
        data={"title": "错误文件"},
        files={"file": ("notes.md", "content", "text/markdown")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only .txt files are supported."


def test_txt_upload_empty_content_fails(client: TestClient):
    kb = create_kb(client)

    response = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/file",
        data={"title": "空文件"},
        files={"file": ("empty.txt", "   ", "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Document content cannot be empty."


def test_list_documents_paginated(client: TestClient):
    kb = create_kb(client)
    for title in ["春", "故乡", "背影"]:
        client.post(
            f"/api/knowledge-bases/{kb['id']}/documents/text",
            json={"title": title, "content": f"{title} 内容"},
        )

    response = client.get(f"/api/knowledge-bases/{kb['id']}/documents?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


def test_get_document_detail(client: TestClient):
    kb = create_kb(client)
    created = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={"title": "春", "content": "春天的脚步近了。"},
    ).json()

    response = client.get(f"/api/documents/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "春"
    assert len(data["chunks"]) == 1


def test_delete_document_success(client: TestClient):
    kb = create_kb(client)
    created = client.post(
        f"/api/knowledge-bases/{kb['id']}/documents/text",
        json={"title": "春", "content": "春天的脚步近了。"},
    ).json()

    delete_response = client.delete(f"/api/documents/{created['id']}")
    get_response = client.get(f"/api/documents/{created['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_document_not_found(client: TestClient):
    response = client.delete("/api/documents/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Document not found."

