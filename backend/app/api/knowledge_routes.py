from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.schemas import KnowledgeBaseCreate, KnowledgeBasePage, KnowledgeBaseRead, KnowledgeBaseUpdate
from app.services import knowledge_service
from app.services.knowledge_service import KnowledgeBaseIndexingError


router = APIRouter(prefix="/knowledge-bases", tags=["knowledge-bases"])


@router.post("", response_model=KnowledgeBaseRead, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(payload: KnowledgeBaseCreate, db: Session = Depends(get_db)):
    return knowledge_service.create_knowledge_base(db, payload)


@router.get("", response_model=KnowledgeBasePage)
def list_knowledge_bases(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    items, total = knowledge_service.list_knowledge_bases(db, page, page_size)
    return KnowledgeBasePage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def get_knowledge_base(knowledge_base_id: int, db: Session = Depends(get_db)):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
    return knowledge_base


@router.put("/{knowledge_base_id}", response_model=KnowledgeBaseRead)
def update_knowledge_base(
    knowledge_base_id: int,
    payload: KnowledgeBaseUpdate,
    db: Session = Depends(get_db),
):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
    return knowledge_service.update_knowledge_base(db, knowledge_base, payload)


@router.delete("/{knowledge_base_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(knowledge_base_id: int, db: Session = Depends(get_db)):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
    try:
        knowledge_service.delete_knowledge_base(db, knowledge_base)
    except KnowledgeBaseIndexingError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
