from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.models import Document, DocumentChunk, KnowledgeBase
from app.db.schemas import TextDocumentCreate
from app.services import embedding_service
from app.services.chunk_service import split_text
from app.vector import chroma_client


class DocumentIndexingError(RuntimeError):
    pass


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
    if get_settings().vector_index_enabled:
        try:
            chroma_client.delete_by_document_id(document.id)
        except Exception as exc:
            raise DocumentIndexingError("Failed to delete document vectors.") from exc

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

    chunk_models: list[DocumentChunk] = []
    for index, chunk in enumerate(chunks):
        chunk_model = DocumentChunk(
            document_id=document.id,
            knowledge_base_id=knowledge_base.id,
            chunk_index=index,
            content=chunk,
        )
        db.add(chunk_model)
        chunk_models.append(chunk_model)

    db.flush()

    if get_settings().vector_index_enabled:
        try:
            _index_document_chunks(knowledge_base, document, chunk_models)
        except Exception as exc:
            db.rollback()
            raise DocumentIndexingError("Failed to index document chunks.") from exc

    db.commit()
    db.refresh(document)
    return document


def _index_document_chunks(
    knowledge_base: KnowledgeBase,
    document: Document,
    chunks: list[DocumentChunk],
) -> None:
    chunk_texts = [chunk.content for chunk in chunks]
    embeddings = embedding_service.embed_texts(chunk_texts)
    vector_ids = [f"kb-{knowledge_base.id}:doc-{document.id}:chunk-{chunk.id}" for chunk in chunks]
    metadatas = [
        {
            "knowledge_base_id": knowledge_base.id,
            "document_id": document.id,
            "chunk_id": chunk.id,
            "chunk_index": chunk.chunk_index,
            "title": document.title,
            "source_type": document.source_type,
        }
        for chunk in chunks
    ]

    chroma_client.add_chunks(
        vector_ids=vector_ids,
        embeddings=embeddings,
        documents=chunk_texts,
        metadatas=metadatas,
    )

    for chunk, vector_id in zip(chunks, vector_ids, strict=True):
        chunk.vector_id = vector_id

