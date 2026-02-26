# RAG Chatbot with Citations + AI Integrations

A production-ready Retrieval-Augmented Generation (RAG) chatbot for small businesses. Answers questions using your organization's documents with precise citations to source material.

## Features

- **Cited Answers** — Every response includes `[1]`, `[2]` references to exact source documents
- **Multi-format Ingestion** — PDF, CSV, websites, Google Docs, Notion
- **Streaming Chat** — Real-time token streaming via Server-Sent Events
- **Multi-LLM Support** — Switch between OpenAI, Claude, Gemini from admin panel
- **Role-Based Access** — Admin, Member, Viewer roles
- **Citations Panel** — Side panel shows document name, page number, highlighted snippet
- **Admin Dashboard** — Analytics, document management, user management, cost controls
- **Token Budgets** — Configurable daily/monthly token limits per organization
- **Slack Bot** — Ask questions directly in Slack
- **Google Sheets** — Auto-log Q&A pairs for review
- **Email Digests** — Weekly summary of top questions and unanswered queries
- **Docker Ready** — One-command deployment with `docker-compose`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Zustand |
| Backend | FastAPI (Python), SQLAlchemy, Pydantic |
| Vector DB | ChromaDB |
| Database | PostgreSQL |
| Cache | Redis |
| LLM Gateway | LiteLLM (OpenAI / Anthropic / Google) |
| Embeddings | OpenAI `text-embedding-3-small` |
| Reranking | `cross-encoder/ms-marco-MiniLM-L-6-v2` |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker & Docker Compose (recommended)

### Option 1: Docker (Recommended)

```bash
# 1. Clone the repo
git clone https://github.com/abdul-raheem-fast/rag-chatbot.git
cd rag-chatbot

# 2. Copy environment file and configure
cp .env.example .env
# Edit .env with your API keys (at minimum set OPENAI_API_KEY)

# 3. Start everything
docker-compose up -d

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```

### Option 2: Local Development

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

> **Note:** You'll need PostgreSQL, Redis, and ChromaDB running locally (or use docker-compose for just the infrastructure services).

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Auth, Chat, Documents, Admin endpoints
│   │   ├── core/                # Config, DB, Redis, Security, Logging
│   │   ├── ingestion/           # PDF/CSV/Web extractors, chunking pipeline
│   │   ├── integrations/        # Slack, Google Sheets, Email
│   │   ├── models/              # SQLAlchemy models
│   │   ├── rag/                 # Vector store, embeddings, reranker, LLM gateway, prompts
│   │   ├── schemas/             # Pydantic request/response models
│   │   └── main.py              # FastAPI app entry point
│   ├── alembic/                 # Database migrations
│   ├── tests/                   # API and unit tests
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages (chat, login, register, admin)
│   │   ├── components/          # Sidebar, ChatMessage, CitationsPanel, ChatInput
│   │   └── lib/                 # API client, Zustand store
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
| POST | `/api/auth/login` | Sign in, get JWT | No |
| GET | `/api/auth/me` | Current user info | Yes |
| POST | `/api/chat` | Send message, get cited response | Yes |
| POST | `/api/chat/stream` | Streaming chat (SSE) | Yes |
| POST | `/api/chat/feedback` | Thumbs up/down on a message | Yes |
| GET | `/api/chat/conversations` | List conversation history | Yes |
| POST | `/api/documents/upload` | Upload PDF/CSV | Admin |
| POST | `/api/documents/ingest-website` | Scrape + index a URL | Admin |
| GET | `/api/documents` | List all documents | Yes |
| DELETE | `/api/documents/{id}` | Delete document + chunks | Admin |
| POST | `/api/documents/{id}/reindex` | Re-process a document | Admin |
| GET | `/api/admin/analytics` | Dashboard analytics | Admin |
| PUT | `/api/admin/settings` | Update LLM/budget settings | Admin |
| GET | `/api/admin/users` | List org users | Admin |
| PUT | `/api/admin/users/{id}/role` | Change user role | Admin |

## Configuration

All settings are in `.env`. Key ones:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | (required) |
| `DEFAULT_LLM_PROVIDER` | `openai`, `anthropic`, or `google` | `openai` |
| `OPENAI_MODEL` | Default OpenAI model | `gpt-4o-mini` |
| `CHUNK_SIZE` | Token size per chunk | `512` |
| `SIMILARITY_THRESHOLD` | Min cosine score for retrieval | `0.72` |
| `DAILY_TOKEN_BUDGET` | Max tokens/day per org | `500000` |

## Milestone Checklist

- [x] Project scaffolding + Docker setup
- [x] PostgreSQL models + Alembic migrations
- [x] JWT authentication + role-based access
- [x] PDF/CSV ingestion + chunking into ChromaDB
- [x] Website scraping + ingestion
- [x] RAG engine (retrieve → rerank → prompt → LLM)
- [x] Streaming chat API with citations
- [x] Next.js chat UI with streaming
- [x] Citations side panel
- [x] Admin dashboard (analytics)
- [x] Document management (upload, delete, reindex)
- [x] Settings page (LLM provider swap, token budgets)
- [x] Slack bot integration
- [x] Google Sheets logging
- [x] Email digest
- [ ] Google Docs connector
- [ ] Notion connector
- [ ] HubSpot CRM integration
- [ ] Langfuse observability integration
- [ ] Comprehensive test suite
- [ ] Production deployment guide

## License

MIT
