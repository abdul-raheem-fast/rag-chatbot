from sentence_transformers import CrossEncoder
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_reranker = None


def get_reranker() -> CrossEncoder:
    global _reranker
    if _reranker is None:
        logger.info("Loading cross-encoder reranker model...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
    return _reranker


def rerank_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank retrieved chunks using a cross-encoder model."""
    if not chunks:
        return []

    model = get_reranker()
    pairs = [(query, chunk["text"]) for chunk in chunks]
    scores = model.predict(pairs)

    for i, chunk in enumerate(chunks):
        chunk["rerank_score"] = float(scores[i])

    ranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)

    filtered = [c for c in ranked if c["rerank_score"] >= settings.rerank_threshold]

    return filtered[:top_k]
