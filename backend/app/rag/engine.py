"""
Core RAG engine: ties together retrieval, reranking, prompting, and LLM calls.
"""
import time
import json
import re
from uuid import UUID, uuid4
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.vectorstore import VectorStore
from app.rag.reranker import rerank_chunks
from app.rag.prompts import build_rag_messages, NO_SOURCES_RESPONSE
from app.rag.llm_gateway import llm_completion, llm_stream
from app.models.conversation import Conversation, Message
from app.schemas.chat import CitationItem, ChatResponse
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def _build_citations(chunks: list[dict]) -> list[CitationItem]:
    citations = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        citations.append(CitationItem(
            index=i,
            doc_id=meta.get("doc_id", ""),
            doc_name=meta.get("doc_name", "Unknown"),
            page_number=meta.get("page_number"),
            snippet=chunk["text"][:300],
            source_url=meta.get("source_url"),
            score=round(chunk.get("rerank_score", chunk.get("score", 0)), 4),
        ))
    return citations


def _determine_confidence(chunks: list[dict]) -> str:
    if not chunks:
        return "low"
    best = max(c.get("rerank_score", c.get("score", 0)) for c in chunks)
    if best >= 0.8:
        return "high"
    elif best >= 0.5:
        return "medium"
    return "low"


async def rag_chat(
    db: AsyncSession,
    user_query: str,
    org_id: str,
    user_id: str,
    conversation_id: UUID | None = None,
    org_name: str = "your organization",
    provider: str | None = None,
    model: str | None = None,
) -> ChatResponse:
    """Full RAG pipeline: retrieve → rerank → prompt → LLM → respond with citations."""
    start = time.time()

    # 1. Retrieve
    vs = VectorStore()
    raw_chunks = vs.search(user_query, org_id=org_id, top_k=settings.retrieval_top_k)

    # 2. Rerank
    if raw_chunks:
        chunks = rerank_chunks(user_query, raw_chunks, top_k=settings.rerank_top_k)
    else:
        chunks = []

    # 3. Handle no-results case
    if not chunks:
        content = NO_SOURCES_RESPONSE
        citations = []
        confidence = "low"
        tokens = 0
    else:
        # 4. Build prompt + call LLM
        conversation_history = []
        if conversation_id:
            conv = await db.get(Conversation, conversation_id)
            if conv and conv.messages:
                conversation_history = [
                    {"role": m.role, "content": m.content} for m in conv.messages
                ]

        messages = build_rag_messages(user_query, chunks, org_name, conversation_history)
        result = await llm_completion(messages, provider=provider, model=model)
        content = result["content"]
        tokens = result["tokens"]
        citations = _build_citations(chunks)
        confidence = _determine_confidence(chunks)

    # 5. Persist conversation + messages
    if not conversation_id:
        conv = Conversation(id=uuid4(), org_id=UUID(org_id), user_id=UUID(user_id))
        db.add(conv)
        await db.flush()
        conversation_id = conv.id

    latency_ms = int((time.time() - start) * 1000)

    user_msg = Message(
        id=uuid4(), conversation_id=conversation_id,
        role="user", content=user_query,
    )
    assistant_msg = Message(
        id=uuid4(), conversation_id=conversation_id,
        role="assistant", content=content,
        citations=[c.model_dump() for c in citations] if citations else None,
        confidence=confidence, tokens_used=tokens, latency_ms=latency_ms,
    )
    db.add(user_msg)
    db.add(assistant_msg)

    return ChatResponse(
        conversation_id=conversation_id,
        message_id=assistant_msg.id,
        content=content,
        citations=citations,
        confidence=confidence,
        tokens_used=tokens,
        latency_ms=latency_ms,
    )


async def rag_chat_stream(
    user_query: str,
    org_id: str,
    org_name: str = "your organization",
    provider: str | None = None,
    model: str | None = None,
) -> AsyncGenerator[str, None]:
    """Streaming version: yields SSE-formatted chunks."""
    vs = VectorStore()
    raw_chunks = vs.search(user_query, org_id=org_id, top_k=settings.retrieval_top_k)

    if raw_chunks:
        chunks = rerank_chunks(user_query, raw_chunks, top_k=settings.rerank_top_k)
    else:
        chunks = []

    if not chunks:
        yield f"data: {json.dumps({'type': 'content', 'content': NO_SOURCES_RESPONSE})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'citations': []})}\n\n"
        return

    citations = _build_citations(chunks)
    messages = build_rag_messages(user_query, chunks, org_name)

    async for token in llm_stream(messages, provider=provider, model=model):
        yield f"data: {json.dumps({'type': 'content', 'content': token})}\n\n"

    yield f"data: {json.dumps({'type': 'done', 'citations': [c.model_dump() for c in citations]})}\n\n"
