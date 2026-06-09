import asyncio
import json
from collections.abc import AsyncIterator

from app.db.schemas import SearchRequest
from app.services import retrieval_service


async def stream_search(payload: SearchRequest) -> AsyncIterator[str]:
    yield _sse_event({"type": "start"})

    try:
        response = retrieval_service.search_knowledge_base(payload)
        yield _sse_event({"type": "delta", "content": "找到相关内容："})

        for result in response.results:
            yield _sse_event(
                {
                    "type": "result",
                    "document_id": result.document_id,
                    "title": result.title,
                    "chunk": result.chunk,
                    "score": result.score,
                    "chunk_id": result.chunk_id,
                    "chunk_index": result.chunk_index,
                }
            )
            await asyncio.sleep(0)

        yield _sse_event({"type": "done"})
    except retrieval_service.RetrievalError as exc:
        yield _sse_event({"type": "error", "message": str(exc)})
        yield _sse_event({"type": "done"})


def _sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

