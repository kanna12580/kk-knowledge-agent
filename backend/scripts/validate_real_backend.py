"""Run a real backend ingestion/search smoke test with Chroma and embeddings.

This script uses temporary SQLite and Chroma directories, so it does not touch
local development data. It intentionally exercises the FastAPI endpoints rather
than calling service functions directly.
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))


def configure_temp_environment(work_dir: Path) -> None:
    os.environ["DATABASE_URL"] = f"sqlite:///{work_dir / 'real_check.db'}"
    os.environ["CHROMA_PERSIST_DIR"] = str(work_dir / "chroma")
    os.environ["VECTOR_INDEX_ENABLED"] = "true"


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="kk-real-backend-", ignore_cleanup_errors=True) as temp_dir:
        work_dir = Path(temp_dir)
        configure_temp_environment(work_dir)

        from fastapi.testclient import TestClient

        from app.config import get_settings
        from app.main import create_app
        from app.vector import chroma_client

        get_settings.cache_clear()
        app = create_app(create_tables_on_startup=True)

        with TestClient(app) as client:
            kb_response = client.post(
                "/api/knowledge-bases",
                json={"name": "现代文学", "description": "真实后端联调知识库"},
            )
            kb_response.raise_for_status()
            kb_id = kb_response.json()["id"]

            documents = [
                {
                    "title": "春",
                    "content": (
                        "盼望着，盼望着，东风来了，春天的脚步近了。\n\n"
                        "一切都像刚睡醒的样子，欣欣然张开了眼。"
                        "山朗润起来了，水涨起来了，太阳的脸红起来了。\n\n"
                        "小草偷偷地从土里钻出来，嫩嫩的，绿绿的。"
                    ),
                },
                {
                    "title": "故乡",
                    "content": (
                        "深蓝的天空中挂着一轮金黄的圆月，下面是海边的沙地，"
                        "都种着一望无际的碧绿的西瓜。\n\n"
                        "其间有一个十一二岁的少年，项带银圈，手捏一柄钢叉，"
                        "向一匹猹尽力地刺去。"
                    ),
                },
            ]

            for document in documents:
                upload_response = client.post(
                    f"/api/knowledge-bases/{kb_id}/documents/text",
                    json=document,
                )
                upload_response.raise_for_status()

            queries = ["春天", "花草", "少年闰土", "小孩子", "乡下少年"]
            expected_top_titles = {
                "春天": "春",
                "花草": "春",
                "少年闰土": "故乡",
                "小孩子": "故乡",
                "乡下少年": "故乡",
            }
            for query in queries:
                search_response = client.post(
                    "/api/search",
                    json={"knowledge_base_id": kb_id, "query": query, "top_k": 2},
                )
                search_response.raise_for_status()
                results = search_response.json()["results"]
                if not results:
                    raise RuntimeError(f"No search results returned for query: {query}")
                top_title = results[0]["title"]
                expected_title = expected_top_titles[query]
                if top_title != expected_title:
                    raise RuntimeError(
                        f"Unexpected top result for query {query}: expected {expected_title}, got {top_title}"
                    )
                print(f"QUERY={query}")
                for result in results:
                    print(
                        f"  title={result['title']} score={result['score']:.4f} "
                        f"chunk={result['chunk'][:36]}"
                    )

        get_settings.cache_clear()
        chroma_client.get_vector_store.cache_clear()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
