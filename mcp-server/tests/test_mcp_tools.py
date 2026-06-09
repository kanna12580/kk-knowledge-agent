import importlib.util
from pathlib import Path

import httpx
import pytest


TOOLS_PATH = Path(__file__).resolve().parents[1] / "tools.py"
spec = importlib.util.spec_from_file_location("mcp_tools", TOOLS_PATH)
tools = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(tools)


class FakeAsyncClient:
    transport: httpx.MockTransport | None = None
    last_trust_env: bool | None = None

    def __init__(self, *args, **kwargs):
        self.base_url = kwargs.get("base_url")
        self.timeout = kwargs.get("timeout")
        self.__class__.last_trust_env = kwargs.get("trust_env")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, traceback):
        return None

    async def request(self, method: str, path: str, **kwargs):
        assert self.transport is not None
        assert self.last_trust_env is False
        request = httpx.Request(method, f"http://backend.test{path}", json=kwargs.get("json"))
        return await self.transport.handle_async_request(request)


@pytest.fixture(autouse=True)
def patch_async_client(monkeypatch):
    monkeypatch.setattr(tools.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setenv("BACKEND_API_URL", "http://backend.test")
    monkeypatch.setenv("BACKEND_TIMEOUT_SECONDS", "10")


@pytest.fixture
def anyio_backend():
    return "asyncio"


def set_transport(handler):
    FakeAsyncClient.transport = httpx.MockTransport(handler)


@pytest.mark.anyio
async def test_search_knowledge_base_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/search"
        return httpx.Response(
            200,
            json={
                "query": "春天",
                "results": [
                    {
                        "document_id": 1,
                        "title": "春",
                        "chunk": "春天的脚步近了。",
                        "score": 0.88,
                    }
                ],
            },
        )

    set_transport(handler)

    result = await tools.search_knowledge_base("春天", 1, 5)

    assert result["query"] == "春天"
    assert result["results"][0]["title"] == "春"


@pytest.mark.anyio
async def test_search_knowledge_base_empty_query_returns_error():
    result = await tools.search_knowledge_base("   ", 1, 5)

    assert result["error"] == "query cannot be empty."
    assert result["results"] == []


@pytest.mark.anyio
async def test_search_knowledge_base_backend_404_returns_error():
    set_transport(lambda request: httpx.Response(404, json={"detail": "Knowledge base not found."}))

    result = await tools.search_knowledge_base("春天", 999, 5)

    assert result["error"] == "Backend resource not found."
    assert result["results"] == []


@pytest.mark.anyio
async def test_search_knowledge_base_timeout_returns_error(monkeypatch):
    class TimeoutClient(FakeAsyncClient):
        async def request(self, method: str, path: str, **kwargs):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr(tools.httpx, "AsyncClient", TimeoutClient)

    result = await tools.search_knowledge_base("春天", 1, 5)

    assert result["error"] == "Backend request timed out."


@pytest.mark.anyio
async def test_search_knowledge_base_empty_results_returns_message():
    set_transport(lambda request: httpx.Response(200, json={"query": "未知", "results": []}))

    result = await tools.search_knowledge_base("未知", 1, 5)

    assert result["results"] == []
    assert result["message"] == "No matching knowledge chunks found."


@pytest.mark.anyio
async def test_list_knowledge_bases_success():
    set_transport(
        lambda request: httpx.Response(
            200,
            json={"items": [{"id": 1, "name": "现代文学"}], "total": 1, "page": 1, "page_size": 20},
        )
    )

    result = await tools.list_knowledge_bases()

    assert result["total"] == 1
    assert result["items"][0]["name"] == "现代文学"


@pytest.mark.anyio
async def test_add_text_document_success():
    set_transport(
        lambda request: httpx.Response(
            201,
            json={
                "id": 1,
                "title": "春",
                "knowledge_base_id": 1,
                "source_type": "text",
                "file_name": None,
                "content": "春天的脚步近了。",
                "created_at": "2026-06-09T00:00:00",
                "updated_at": "2026-06-09T00:00:00",
                "chunks": [],
            },
        )
    )

    result = await tools.add_text_document(1, "春", "春天的脚步近了。")

    assert result["title"] == "春"
