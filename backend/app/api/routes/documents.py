import os
import shutil
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.document import Document
from app.schemas.document import (
    DocumentResponse, DocumentUploadResponse, DocumentListResponse,
    WebsiteIngestRequest, GDocIngestRequest, NotionIngestRequest,
)
from app.schemas.common import APIResponse
from app.ingestion.pipeline import ingest_pdf, ingest_csv, ingest_website, ingest_gdoc, ingest_notion
from app.rag.vectorstore import VectorStore
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf", ".csv", ".txt", ".docx", ".xlsx"}


def _validate_extension(filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    return ext


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Upload a PDF or CSV file for ingestion."""
    ext = _validate_extension(file.filename)
    file_id = uuid4().hex[:12]
    filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    org_id = str(user.org_id)

    if ext == ".pdf":
        doc = await ingest_pdf(db, file_path, file.filename, org_id)
    elif ext == ".csv":
        doc = await ingest_csv(db, file_path, file.filename, org_id)
    else:
        doc = await ingest_pdf(db, file_path, file.filename, org_id)

    return DocumentUploadResponse(document=DocumentResponse.model_validate(doc))


@router.post("/ingest-website", response_model=DocumentUploadResponse)
async def ingest_website_endpoint(
    body: WebsiteIngestRequest,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a website URL."""
    doc = await ingest_website(db, body.url, body.name, str(user.org_id))
    return DocumentUploadResponse(document=DocumentResponse.model_validate(doc))


@router.post("/ingest-gdoc", response_model=DocumentUploadResponse)
async def ingest_gdoc_endpoint(
    body: GDocIngestRequest,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a Google Doc by its document ID."""
    doc = await ingest_gdoc(db, body.doc_id, body.name, str(user.org_id))
    return DocumentUploadResponse(document=DocumentResponse.model_validate(doc))


@router.post("/ingest-notion", response_model=DocumentUploadResponse)
async def ingest_notion_endpoint(
    body: NotionIngestRequest,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Ingest a Notion page by its page ID."""
    doc = await ingest_notion(db, body.page_id, body.name, str(user.org_id))
    return DocumentUploadResponse(document=DocumentResponse.model_validate(doc))


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all documents for the user's organization."""
    result = await db.execute(
        select(Document)
        .where(Document.org_id == user.org_id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in docs],
        total=len(docs),
    )


@router.get("/{doc_id}", response_model=DocumentResponse)
async def get_document(
    doc_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.org_id == user.org_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentResponse.model_validate(doc)


@router.delete("/{doc_id}", response_model=APIResponse)
async def delete_document(
    doc_id: UUID,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Delete a document and its chunks from the vector store."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.org_id == user.org_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Remove from vector store
    try:
        vs = VectorStore()
        vs.delete_by_doc_id(str(doc_id))
    except Exception as e:
        logger.error("Failed to delete chunks from vector store", error=str(e))

    # Remove file if exists
    if doc.file_path and os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    await db.delete(doc)
    return APIResponse(message="Document deleted successfully")


@router.post("/{doc_id}/reindex", response_model=DocumentResponse)
async def reindex_document(
    doc_id: UUID,
    user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db),
):
    """Re-ingest a document (delete old chunks, re-process)."""
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.org_id == user.org_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Delete old chunks
    vs = VectorStore()
    vs.delete_by_doc_id(str(doc_id))

    doc.status = "processing"
    doc.chunk_count = 0
    await db.flush()

    org_id = str(user.org_id)
    if doc.source_type == "pdf" and doc.file_path:
        doc = await ingest_pdf(db, doc.file_path, doc.name, org_id)
    elif doc.source_type == "csv" and doc.file_path:
        doc = await ingest_csv(db, doc.file_path, doc.name, org_id)
    elif doc.source_type == "website" and doc.source_url:
        doc = await ingest_website(db, doc.source_url, doc.name, org_id)
    elif doc.source_type == "gdoc" and doc.source_url:
        gdoc_id = doc.source_url.split("/d/")[1].split("/")[0] if "/d/" in doc.source_url else doc.source_url
        doc = await ingest_gdoc(db, gdoc_id, doc.name, org_id)
    elif doc.source_type == "notion" and doc.source_url:
        notion_id = doc.source_url.rstrip("/").split("/")[-1].split("-")[-1]
        doc = await ingest_notion(db, notion_id, doc.name, org_id)

    return DocumentResponse.model_validate(doc)
