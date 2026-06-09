from fastapi.testclient import TestClient

from tests.conftest import create_kb


def test_create_knowledge_base_success(client: TestClient):
    data = create_kb(client)

    assert data["id"] == 1
    assert data["name"] == "现代文学"
    assert data["description"] == "朱自清和鲁迅文章"
    assert data["created_at"]
    assert data["updated_at"]


def test_list_knowledge_bases_paginated(client: TestClient):
    create_kb(client, "现代文学")
    create_kb(client, "古典诗词")
    create_kb(client, "科技文章")

    response = client.get("/api/knowledge-bases?page=1&page_size=2")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["items"]) == 2


def test_get_knowledge_base_success(client: TestClient):
    kb = create_kb(client)

    response = client.get(f"/api/knowledge-bases/{kb['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "现代文学"


def test_get_knowledge_base_not_found(client: TestClient):
    response = client.get("/api/knowledge-bases/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Knowledge base not found."


def test_update_knowledge_base_success(client: TestClient):
    kb = create_kb(client)

    response = client.put(
        f"/api/knowledge-bases/{kb['id']}",
        json={"name": "现代散文", "description": "更新后的描述"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "现代散文"
    assert data["description"] == "更新后的描述"


def test_update_knowledge_base_not_found(client: TestClient):
    response = client.put(
        "/api/knowledge-bases/999",
        json={"name": "不存在"},
    )

    assert response.status_code == 404


def test_delete_knowledge_base_success(client: TestClient):
    kb = create_kb(client)

    delete_response = client.delete(f"/api/knowledge-bases/{kb['id']}")
    get_response = client.get(f"/api/knowledge-bases/{kb['id']}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404


def test_delete_knowledge_base_not_found(client: TestClient):
    response = client.delete("/api/knowledge-bases/999")

    assert response.status_code == 404
