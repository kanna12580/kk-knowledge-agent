from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import KnowledgeBase
from app.db.schemas import KnowledgeBaseCreate, KnowledgeBaseUpdate


def create_knowledge_base(db: Session, payload: KnowledgeBaseCreate) -> KnowledgeBase:
    knowledge_base = KnowledgeBase(name=payload.name, description=payload.description)
    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    return knowledge_base


def list_knowledge_bases(db: Session, page: int, page_size: int) -> tuple[list[KnowledgeBase], int]:
    offset = (page - 1) * page_size
    total = db.scalar(select(func.count()).select_from(KnowledgeBase)) or 0
    items = db.scalars(
        select(KnowledgeBase)
        .order_by(KnowledgeBase.created_at.desc(), KnowledgeBase.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return list(items), total


def get_knowledge_base(db: Session, knowledge_base_id: int) -> KnowledgeBase | None:
    return db.get(KnowledgeBase, knowledge_base_id)


def update_knowledge_base(
    db: Session,
    knowledge_base: KnowledgeBase,
    payload: KnowledgeBaseUpdate,
) -> KnowledgeBase:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(knowledge_base, field, value)

    db.add(knowledge_base)
    db.commit()
    db.refresh(knowledge_base)
    return knowledge_base


def delete_knowledge_base(db: Session, knowledge_base: KnowledgeBase) -> None:
    db.delete(knowledge_base)
    db.commit()

