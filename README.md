# RAG Chatbot with Citations

A full-stack Retrieval-Augmented Generation chatbot that answers questions using your organization's documents, with inline citations back to source material. Built as a portfolio project demonstrating production-style architecture for AI-powered knowledge bases.

## What This Project Demonstrates

- **End-to-end RAG pipeline**: document ingestion → chunking → vector embedding → semantic retrieval → reranking → LLM generation with citations
- **Multi-format document support**: PDF, CSV, TXT, DOCX, XLSX file uploads, plus website scraping and Google Docs / Notion ingestion
- **Provider-agnostic LLM integration**: swap between OpenAI, Anthropic (Claude), Google (Gemini), or Groq via admin settings — powered by LiteLLM
- **Real-time streaming**: Server-Sent Events for token-by-token chat responses
- **Full admin panel**: analytics dashboard, document management, LLM/budget settings, team/role management
- **Multi-tenant architecture**: org-scoped data isolation, role-based access control (Admin / Member / Viewer)
- **Clean separation of concerns**: FastAPI backend with async SQLAlchemy, Next.js frontend with Zustand state management

## Features

| Feature | Status | Details |
|---------|--------|---------|
| Cited answers | Working | Every response includes `[1]`, `[2]` references to source chunks |
| Streaming chat | Working | Real-time token streaming via SSE |
| PDF / CSV / TXT / DOCX / XLSX upload | Working | Chunked and indexed into ChromaDB |
| Website ingestion | Working | Scrapes page content via trafilatura |
| Google Docs ingestion | Working | Public/shared-link docs via export URL |
| Notion page ingestion | Working | Requires `NOTION_API_TOKEN` in `.env` |
| Citations panel | Working | Side panel with doc name, page, snippet, relevance score |
| Multi-LLM support | Working | OpenAI, Claude, Gemini, Groq — switchable from admin panel |
| Role-based access | Working | JWT auth with Admin, Member, Viewer roles |
| Admin analytics | Working | Document count, conversations, token usage, satisfaction rate |
| Document management | Working | Upload, list, delete, reindex |
| Token budgets | Working | Configurable daily/monthly limits per organization |
| Feedback | Working | Thumbs up/down on assistant messages |
| Slack bot | Code complete | Needs Slack app configuration to activate |
| Google Sheets logging | Code complete | Q&A logging function exists but is not wired into the chat flow |
| Email digest | Code complete | Send function exists but is not wired into a scheduler |
| Rate limiting | Partial | SlowAPI configured but not applied to individual routes |
| Conversation history API | Partial | Backend endpoints exist; frontend does not display past conversations |
| Reranking | Optional | Uses cross-encoder if `sentence-transformers` is installed; falls back to retrieval scores |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Zustand |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic v2 |
| Vector DB | ChromaDB (in-process persistent mode for local dev) |
| Database | SQLite (local dev) / PostgreSQL (Docker/production) |
| LLM Gateway | LiteLLM (OpenAI, Anthropic, Google, Groq) |
| Embeddings | ONNX MiniLM-L6-v2 (local, free) or OpenAI `text-embedding-3-small` |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` (optional) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- An LLM API key (OpenAI, Groq, Anthropic, or Google)

### Local Development (no Docker needed)

```bash
# 1. Clone the repo
git clone https://github.com/abdul-raheem-fast/rag-chatbot.git
cd rag-chatbot

# 2. Configure environment
cp .env.example backend/.env
# Edit backend/.env — set at least one LLM API key (e.g. OPENAI_API_KEY or GROQ_API_KEY)
# Set DEFAULT_LLM_PROVIDER to match your key (openai, groq, anthropic, or google)

# 3. Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 4. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000, register an account, and start uploading documents.

> **Note:** Local dev uses SQLite and in-process ChromaDB — no PostgreSQL, Redis, or external services required. Redis and reranking are optional and gracefully skipped if unavailable.

### Docker

```bash
cp .env.example .env
# Edit .env with your API keys and set DATABASE_URL to the PostgreSQL connection string
docker-compose up -d

# Frontend: http://localhost:3000
# Backend: http://localhost:8000/docs (Swagger UI)
```

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Auth, Chat, Documents, Admin endpoints
│   │   ├── core/                # Config, DB, Security, Logging
│   │   ├── ingestion/           # Extractors (PDF, CSV, TXT, DOCX, XLSX, Web, GDocs, Notion) + chunking
│   │   ├── integrations/        # Slack bot, Google Sheets logger, Email digest
│   │   ├── models/              # SQLAlchemy ORM (User, Org, Document, Conversation, Message)
│   │   ├── rag/                 # VectorStore, Embeddings, Reranker, LLM Gateway, Prompts, RAG Engine
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── main.py              # FastAPI entry point
│   ├── alembic/                 # Database migrations
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Pages: Chat, Login, Register, Admin (Analytics, Documents, Settings)
│   │   ├── components/          # Sidebar, ChatMessage, CitationsPanel, ChatInput
│   │   └── lib/                 # API client, Zustand stores
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/auth/register` | Create account + organization | No |
| POST | `/api/auth/login` | Sign in, get JWT token | No |
| GET | `/api/auth/me` | Current user info | Yes |
| GET | `/api/auth/org` | Current organization info | Yes |
| POST | `/api/chat` | Send message, get cited response | Yes |
| POST | `/api/chat/stream` | Streaming chat (SSE) | Yes |
| POST | `/api/chat/feedback` | Thumbs up/down on a message | Yes |
| GET | `/api/chat/conversations` | List conversation history | Yes |
| GET | `/api/chat/conversations/{id}` | Get conversation with messages | Yes |
| POST | `/api/documents/upload` | Upload PDF/CSV/TXT/DOCX/XLSX | Admin |
| POST | `/api/documents/ingest-website` | Scrape and index a URL | Admin |
| POST | `/api/documents/ingest-gdoc` | Ingest a Google Doc by ID/URL | Admin |
| POST | `/api/documents/ingest-notion` | Ingest a Notion page by ID/URL | Admin |
| GET | `/api/documents` | List all documents | Yes |
| DELETE | `/api/documents/{id}` | Delete document + vector chunks | Admin |
| POST | `/api/documents/{id}/reindex` | Re-process a document | Admin |
| GET | `/api/admin/analytics` | Dashboard analytics | Admin |
| PUT | `/api/admin/settings` | Update LLM provider/model/budgets | Admin |
| GET | `/api/admin/users` | List organization users | Admin |
| PUT | `/api/admin/users/{id}/role` | Change user role | Admin |

## Configuration

Key environment variables (see `.env.example` for full list):

| Variable | Description | Default |
|----------|-------------|---------|
| `DEFAULT_LLM_PROVIDER` | `openai`, `anthropic`, `google`, or `groq` | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | *(set if using OpenAI)* |
| `GROQ_API_KEY` | Groq API key | *(set if using Groq)* |
| `EMBEDDING_PROVIDER` | `local` (free ONNX) or `openai` | `local` |
| `CHUNK_SIZE` | Token size per chunk | `512` |
| `SIMILARITY_THRESHOLD` | Min cosine score for retrieval | `0.72` |
| `DAILY_TOKEN_BUDGET` | Max tokens/day per org | `500000` |
| `NOTION_API_TOKEN` | Notion integration token | *(optional)* |

## Security

- **Authentication**: JWT tokens with configurable expiry (default 24h)
- **Authorization**: Role-based access — Admin, Member, Viewer
- **Data isolation**: All queries scoped to `org_id`; no cross-tenant data leakage
- **Token budgets**: Daily and monthly caps to control LLM costs
- **Secrets**: All credentials loaded from environment variables, never hardcoded
- **CORS**: Restricted to configured frontend URL

> **Note:** Never commit your `.env` file. Only `.env.example` (with placeholder values) is tracked in git.

## Current Limitations / Future Improvements

- **Google Docs**: Only works with public or link-shared documents. Private docs with service account credentials have a known bug.
- **Conversation history**: Backend API exists but the frontend currently starts a fresh conversation each session.
- **Google Sheets / Email digest**: Functions are implemented but not wired into the chat flow or a job scheduler.
- **Rate limiting**: SlowAPI is configured but not applied to individual routes yet.
- **Reranking**: Requires `sentence-transformers` + PyTorch (~500MB). Falls back to retrieval scores if not installed.
- **HubSpot CRM**: Config field exists but integration is not implemented.
- **Langfuse tracing**: Config fields exist but integration is not implemented.
- **Evaluation suite**: No automated faithfulness/relevance test suite yet.

## License

MIT
