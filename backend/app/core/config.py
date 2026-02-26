from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "RAG Chatbot"
    app_env: str = "development"
    debug: bool = True
    secret_key: str = "change-me"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"

    # Database
    database_url: str = "postgresql+asyncpg://raguser:ragpass@localhost:5432/ragchatbot"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # ChromaDB
    chroma_host: str = "localhost"
    chroma_port: int = 8100
    chroma_collection: str = "rag_documents"

    # LLM
    default_llm_provider: str = "openai"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    google_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_model: str = "claude-3-5-sonnet-20241022"
    google_model: str = "gemini-1.5-flash"

    # Embeddings
    embedding_provider: str = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimension: int = 1536

    # Retrieval
    retrieval_top_k: int = 20
    rerank_top_k: int = 5
    similarity_threshold: float = 0.72
    rerank_threshold: float = 0.25
    max_context_tokens: int = 6000
    chunk_size: int = 512
    chunk_overlap: int = 64

    # Auth
    jwt_secret: str = "change-me-jwt"
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # Rate Limiting
    rate_limit_per_minute: int = 30
    daily_token_budget: int = 500000
    monthly_token_budget: int = 10000000

    # Integrations
    slack_bot_token: str = ""
    slack_signing_secret: str = ""
    google_sheets_credentials_json: str = "{}"
    google_sheets_spreadsheet_id: str = ""
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "noreply@yourcompany.com"
    hubspot_api_key: str = ""

    # Observability
    log_level: str = "INFO"
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
