from pydantic import BaseModel, Field, HttpUrl
from uuid import UUID
from datetime import datetime

__all__ = [
    "DocumentUploadResponse", "DocumentResponse", "DocumentListResponse",
    "WebsiteIngestRequest", "NotionIngestRequest", "GDocIngestRequest",
]


class DocumentResponse(BaseModel):
    id: UUID
    name: str
    source_type: str
    source_url: str | None
    content_hash: str
    chunk_count: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentUploadResponse(BaseModel):
    document: DocumentResponse
    message: str = "Document uploaded and queued for processing"


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class WebsiteIngestRequest(BaseModel):
    url: str
    name: str | None = None


class NotionIngestRequest(BaseModel):
    page_id: str
    name: str | None = None


class GDocIngestRequest(BaseModel):
    doc_id: str
    name: str | None = None
