import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.ingestion.extractors import (
    extract_pdf, extract_csv, extract_txt, extract_docx, extract_xlsx,
    extract_website, extract_gdoc, extract_notion, compute_hash,
)
from app.ingestion.chunker import chunk_text
from app.rag.vectorstore import get_vectorstore
from app.models.document import Document
from app.core.logging import get_logger

logger = get_logger(__name__)


async def ingest_document(
    db: AsyncSession,
    doc_record: Document,
    raw_entries: list[dict],
    org_id: str,
) -> Document:
    """
    Process extracted text entries into chunks and store in vector DB.
    raw_entries: list of {"text": str, "metadata": dict}
    """
    try:
        all_chunks = []
        all_metadatas = []
        all_ids = []

        for entry in raw_entries:
            chunks = chunk_text(entry["text"], metadata={
                "doc_id": str(doc_record.id),
                "doc_name": doc_record.name,
                "source_type": doc_record.source_type,
                "org_id": org_id,
                **entry.get("metadata", {}),
            })
            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                all_chunks.append(chunk["text"])
                all_metadatas.append(chunk["metadata"])
                all_ids.append(chunk_id)

        if not all_chunks:
            doc_record.status = "failed"
            doc_record.error_message = "No text content extracted"
            return doc_record

        vs = get_vectorstore()
        vs.add_texts(
            texts=all_chunks,
            metadatas=all_metadatas,
            ids=all_ids,
        )

        doc_record.chunk_count = len(all_chunks)
        doc_record.status = "ready"
        doc_record.updated_at = datetime.utcnow()

        logger.info(
            "Document ingested successfully",
            doc_id=str(doc_record.id),
            chunks=len(all_chunks),
        )
        return doc_record

    except Exception as e:
        logger.error("Ingestion failed", doc_id=str(doc_record.id), error=str(e))
        doc_record.status = "failed"
        doc_record.error_message = str(e)
        return doc_record


async def ingest_pdf(db: AsyncSession, file_path: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_pdf(file_path)
    content = "\n".join(e["text"] for e in raw_entries)
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name,
        source_type="pdf",
        file_path=file_path,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_csv(db: AsyncSession, file_path: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_csv(file_path)
    content = "\n".join(e["text"] for e in raw_entries)
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name,
        source_type="csv",
        file_path=file_path,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_txt(db: AsyncSession, file_path: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_txt(file_path)
    content = "\n".join(e["text"] for e in raw_entries)
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name,
        source_type="txt",
        file_path=file_path,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_docx(db: AsyncSession, file_path: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_docx(file_path)
    content = "\n".join(e["text"] for e in raw_entries)
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name,
        source_type="docx",
        file_path=file_path,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_xlsx(db: AsyncSession, file_path: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_xlsx(file_path)
    content = "\n".join(e["text"] for e in raw_entries)
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name,
        source_type="xlsx",
        file_path=file_path,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_website(db: AsyncSession, url: str, doc_name: str, org_id: str) -> Document:
    raw_entries = extract_website(url)
    content = raw_entries[0]["text"]
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name or url,
        source_type="website",
        source_url=url,
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_gdoc(db: AsyncSession, doc_id: str, doc_name: str, org_id: str) -> Document:
    """Ingest a Google Doc by its document ID (public or shared via link)."""
    from app.core.config import get_settings
    settings = get_settings()
    raw_entries = await extract_gdoc(doc_id, settings.google_sheets_credentials_json)
    content = raw_entries[0]["text"]
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name or f"Google Doc ({doc_id[:12]}...)",
        source_type="gdoc",
        source_url=f"https://docs.google.com/document/d/{doc_id}",
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)


async def ingest_notion(db: AsyncSession, page_id: str, doc_name: str, org_id: str) -> Document:
    """Ingest a Notion page by its page ID."""
    from app.core.config import get_settings
    settings = get_settings()
    if not settings.notion_api_token:
        raise ValueError("NOTION_API_TOKEN is not configured")
    raw_entries = await extract_notion(page_id, settings.notion_api_token)
    content = raw_entries[0]["text"]
    doc = Document(
        id=uuid.uuid4(),
        org_id=uuid.UUID(org_id),
        name=doc_name or f"Notion Page ({page_id[:12]}...)",
        source_type="notion",
        source_url=f"https://notion.so/{page_id.replace('-', '')}",
        content_hash=compute_hash(content),
    )
    db.add(doc)
    await db.flush()
    return await ingest_document(db, doc, raw_entries, org_id)
