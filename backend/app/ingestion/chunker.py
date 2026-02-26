from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import get_settings

settings = get_settings()


def create_chunker() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", ", ", " ", ""],
        is_separator_regex=False,
    )


def chunk_text(text: str, metadata: dict | None = None) -> list[dict]:
    """Split text into chunks with metadata attached to each chunk."""
    chunker = create_chunker()
    chunks = chunker.split_text(text)
    result = []
    for i, chunk in enumerate(chunks):
        chunk_meta = {
            **(metadata or {}),
            "chunk_index": i,
            "total_chunks": len(chunks),
        }
        result.append({"text": chunk, "metadata": chunk_meta})
    return result
