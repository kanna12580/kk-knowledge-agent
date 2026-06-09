from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Document, DocumentChunk, KnowledgeBase
from app.db.schemas import TextDocumentCreate
from app.services.chunk_service import split_text


def create_text_document(db: Session, knowledge_base: KnowledgeBase, payload: TextDocumentCreate) -> Document:
    return _create_document(
        db=db,
        knowledge_base=knowledge_base,
        title=payload.title,
        content=payload.content,
        source_type="text",
        file_name=None,
    )


def create_file_document(
    db: Session,
    knowledge_base: KnowledgeBase,
    title: str,
    content: str,
    file_name: str,
) -> Document:
    return _create_document(
        db=db,
        knowledge_base=knowledge_base,
        title=title,
        content=content,
        source_type="file",
        file_name=file_name,
    )


def list_documents(db: Session, knowledge_base_id: int, page: int, page_size: int) -> tuple[list[Document], int]:
    offset = (page - 1) * page_size
    total = db.scalar(
        select(func.count()).select_from(Document).where(Document.knowledge_base_id == knowledge_base_id)
    ) or 0
    items = db.scalars(
        select(Document)
        .where(Document.knowledge_base_id == knowledge_base_id)
        .order_by(Document.created_at.desc(), Document.id.desc())
        .offset(offset)
        .limit(page_size)
    ).all()
    return list(items), total


def get_document(db: Session, document_id: int) -> Document | None:
    return db.get(Document, document_id)


def delete_document(db: Session, document: Document) -> None:
    db.delete(document)
    db.commit()


def _create_document(
    db: Session,
    knowledge_base: KnowledgeBase,
    title: str,
    content: str,
    source_type: str,
    file_name: str | None,
) -> Document:
    chunks = split_text(content)
    if not chunks:
        raise ValueError("Document content cannot be empty.")

    document = Document(
        knowledge_base_id=knowledge_base.id,
        title=title,
        source_type=source_type,
        file_name=file_name,
        content=content,
    )
    db.add(document)
    db.flush()

    for index, chunk in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document.id,
                knowledge_base_id=knowledge_base.id,
                chunk_index=index,
                content=chunk,
            )
        )

    db.commit()
    db.refresh(document)
    return document

