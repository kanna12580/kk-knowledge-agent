import os
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


DEFAULT_BACKEND_API_URL = "http://localhost:8000"
DEFAULT_TIMEOUT_SECONDS = 10.0


def backend_api_url() -> str:
    return os.getenv("BACKEND_API_URL", DEFAULT_BACKEND_API_URL).rstrip("/")


def backend_timeout_seconds() -> float:
    raw_timeout = os.getenv("BACKEND_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS))
    try:
        return float(raw_timeout)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS


async def search_knowledge_base(query: str, knowledge_base_id: int, top_k: int = 5) -> dict[str, Any]:
    query = query.strip()
    if not query:
        return _error("query cannot be empty.", query=query)
    if knowledge_base_id <= 0:
        return _error("knowledge_base_id must be greater than 0.", query=query)
    if top_k <= 0:
        return _error("top_k must be greater than 0.", query=query)

    payload = {
        "knowledge_base_id": knowledge_base_id,
        "query": query,
        "top_k": top_k,
    }
    response = await _request("POST", "/api/search", json=payload)
    if "error" in response:
        return _error(response["error"], query=query)

    results = response.get("results", [])
    if not results:
        return {
            "query": query,
            "results": [],
            "message": "No matching knowledge chunks found.",
        }

    return response


async def list_knowledge_bases(page: int = 1, page_size: int = 20) -> dict[str, Any]:
    if page <= 0:
        return _error("page must be greater than 0.")
    if page_size <= 0:
        return _error("page_size must be greater than 0.")

    response = await _request("GET", f"/api/knowledge-bases?page={page}&page_size={page_size}")
    if "error" in response:
        return _error(response["error"])
    return response


async def add_text_document(knowledge_base_id: int, title: str, content: str) -> dict[str, Any]:
    title = title.strip()
    content = content.strip()
    if knowledge_base_id <= 0:
        return _error("knowledge_base_id must be greater than 0.")
    if not title:
        return _error("title cannot be empty.")
    if not content:
        return _error("content cannot be empty.")

    response = await _request(
        "POST",
        f"/api/knowledge-bases/{knowledge_base_id}/documents/text",
        json={"title": title, "content": content},
    )
    if "error" in response:
        return _error(response["error"])
    return response


async def _request(method: str, path: str, **kwargs: Any) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(
            base_url=backend_api_url(),
            timeout=backend_timeout_seconds(),
            trust_env=False,
        ) as client:
            response = await client.request(method, path, **kwargs)
    except httpx.TimeoutException:
        return {"error": "Backend request timed out."}
    except httpx.RequestError:
        return {"error": "Backend service unavailable."}

    if response.status_code == 404:
        return {"error": "Backend resource not found."}
    if response.status_code >= 400:
        return {"error": await _read_error_message(response)}
    if response.status_code == 204:
        return {}
    return response.json()


async def _read_error_message(response: httpx.Response) -> str:
    try:
        data = response.json()
    except ValueError:
        return response.text or response.reason_phrase

    detail = data.get("detail") if isinstance(data, dict) else None
    if isinstance(detail, str):
        return detail
    if isinstance(detail, list):
        return "; ".join(str(item.get("msg", item)) for item in detail)
    return response.reason_phrase


def _error(message: str, query: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"error": message}
    if query is not None:
        payload["query"] = query
        payload["results"] = []
    return payload
