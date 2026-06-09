from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.database import get_db
from app.db.schemas import DocumentDetail, DocumentPage, DocumentRead, TextDocumentCreate
from app.services import document_service, knowledge_service


router = APIRouter(tags=["documents"])


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents/text",
    response_model=DocumentDetail,
    status_code=status.HTTP_201_CREATED,
)
def create_text_document(
    knowledge_base_id: int,
    payload: TextDocumentCreate,
    db: Session = Depends(get_db),
):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")
    return document_service.create_text_document(db, knowledge_base, payload)


@router.post(
    "/knowledge-bases/{knowledge_base_id}/documents/file",
    response_model=DocumentDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_file_document(
    knowledge_base_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

    title = title.strip()
    if not title:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Document title cannot be empty.")

    if not file.filename or not file.filename.lower().endswith(".txt"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only .txt files are supported.")

    settings = get_settings()
    raw_content = await file.read()
    if len(raw_content) > settings.max_txt_file_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large.")

    try:
        content = raw_content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be UTF-8 encoded.") from exc

    content = content.strip()
    if not content:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Document content cannot be empty.")

    return document_service.create_file_document(db, knowledge_base, title, content, file.filename)


@router.get("/knowledge-bases/{knowledge_base_id}/documents", response_model=DocumentPage)
def list_documents(
    knowledge_base_id: int,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    knowledge_base = knowledge_service.get_knowledge_base(db, knowledge_base_id)
    if knowledge_base is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge base not found.")

    items, total = document_service.list_documents(db, knowledge_base_id, page, page_size)
    return DocumentPage(items=items, total=total, page=page, page_size=page_size)


@router.get("/documents/{document_id}", response_model=DocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    document = document_service.get_document(db, document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")
    document_service.delete_document(db, document)
