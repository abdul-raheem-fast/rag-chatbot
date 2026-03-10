from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)

_reranker = None
_has_sentence_transformers = False

try:
    from sentence_transformers import CrossEncoder
    _has_sentence_transformers = True
except ImportError:
    logger.warning("sentence_transformers not installed — skipping reranking, using retrieval scores only")


def get_reranker():
    global _reranker
    if _reranker is None and _has_sentence_transformers:
        logger.info("Loading cross-encoder reranker model...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2", max_length=512)
    return _reranker


def rerank_chunks(query: str, chunks: list[dict], top_k: int = 5) -> list[dict]:
    """Rerank retrieved chunks using a cross-encoder model, or use retrieval scores if not available."""
    if not chunks:
        return []

    if _has_sentence_transformers:
        model = get_reranker()
        pairs = [(query, chunk["text"]) for chunk in chunks]
        scores = model.predict(pairs)
        for i, chunk in enumerate(chunks):
            chunk["rerank_score"] = float(scores[i])
        ranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        filtered = [c for c in ranked if c["rerank_score"] >= settings.rerank_threshold]
    else:
        for c in chunks:
            c["rerank_score"] = c.get("score", 0.0)
        ranked = sorted(chunks, key=lambda x: x["rerank_score"], reverse=True)
        filtered = [c for c in ranked if c["rerank_score"] >= settings.similarity_threshold]

    return filtered[:top_k]
