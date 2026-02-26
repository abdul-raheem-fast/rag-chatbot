import chromadb
from chromadb.config import Settings as ChromaSettings
from app.core.config import get_settings
from app.rag.embeddings import get_embedding_function

settings = get_settings()

_client = None
_collection = None


def get_chroma_client() -> chromadb.HttpClient:
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=settings.chroma_port,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_vectorstore():
    global _collection
    if _collection is None:
        client = get_chroma_client()
        _collection = client.get_or_create_collection(
            name=settings.chroma_collection,
            embedding_function=get_embedding_function(),
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


class VectorStore:
    """Wrapper around ChromaDB collection for RAG operations."""

    def __init__(self):
        self.collection = get_vectorstore()

    def add_texts(self, texts: list[str], metadatas: list[dict], ids: list[str]):
        batch_size = 100
        for i in range(0, len(texts), batch_size):
            self.collection.add(
                documents=texts[i:i + batch_size],
                metadatas=metadatas[i:i + batch_size],
                ids=ids[i:i + batch_size],
            )

    def search(self, query: str, org_id: str, top_k: int = 20) -> list[dict]:
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
            where={"org_id": org_id},
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                distance = results["distances"][0][i] if results["distances"] else 0
                similarity = 1 - distance  # cosine distance → similarity
                chunks.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": similarity,
                })
        return chunks

    def delete_by_doc_id(self, doc_id: str):
        self.collection.delete(where={"doc_id": doc_id})
