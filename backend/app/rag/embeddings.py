from chromadb.utils import embedding_functions
from app.core.config import get_settings
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger(__name__)


def get_embedding_function():
    """Return a ChromaDB-compatible embedding function based on config."""
    if settings.embedding_provider == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    elif settings.embedding_provider == "local":
        try:
            return embedding_functions.ONNXMiniLM_L6_V2()
        except Exception as e:
            logger.warning("ONNX embedding failed, trying SentenceTransformer", error=str(e))
            return embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name="all-MiniLM-L6-v2",
            )
    else:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
