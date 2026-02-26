from chromadb.utils import embedding_functions
from app.core.config import get_settings

settings = get_settings()


def get_embedding_function():
    """Return a ChromaDB-compatible embedding function based on config."""
    if settings.embedding_provider == "openai":
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    elif settings.embedding_provider == "local":
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2",
        )
    else:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
