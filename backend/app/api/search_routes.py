from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import SearchRequest, SearchResponse
from app.services import knowledge_service, retrieval_service, stream_service


router = APIRouter(prefix="/search", tags=["search"])


@router.post("", response_model=SearchResponse)
def search(payload: SearchRequest, db: Session = Depends(get_db)):
    _ensure_knowledge_base_exists(db, payload.knowledge_base_id)

    try:
        return retrieval_service.search_knowledge_base(payload)
    except retrieval_service.RetrievalError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/stream")
def stream_search(payload: SearchRequest, db: Session = Depends(get_db)):
    _ensure_knowledge_base_exists(db, payload.knowledge_base_id)

    return StreamingResponse(
        stream_service.stream_search(payload),
        media_type="text/event-stream",
    )


def _ensure_knowledge_base_exists(db: Session, knowledge_base_id: int) -> None:
    if knowledge_service.get_knowledge_base(db, knowledge_base_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

