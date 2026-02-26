# RAG Chatbot with Citations + AI Integrations

A production-ready Retrieval-Augmented Generation (RAG) chatbot for small businesses. Answers questions using your organization's documents with precise citations to source material.

## Features

- **Cited Answers** — Every response includes `[1]`, `[2]` references to exact source documents
- **Multi-format Ingestion** — PDF, CSV, TXT, DOCX, XLSX, websites, Google Docs, Notion pages
- **Streaming Chat** — Real-time token streaming via Server-Sent Events
- **Multi-LLM Support** — Switch between OpenAI, Claude, Gemini from admin panel
- **Role-Based Access** — Admin, Member, Viewer roles with JWT authentication
- **Citations Panel** — Side panel shows document name, page number, highlighted snippet, relevance score
- **Admin Dashboard** — Analytics, document management, user management, cost controls
- **Token Budgets** — Configurable daily/monthly token limits per organization
- **Slack Bot** — Ask questions directly in Slack, get cited answers in-thread
- **Google Sheets** — Auto-log Q&A pairs for review
- **Email Digests** — Weekly summary of top questions and unanswered queries
- **Docker Ready** — One-command deployment with `docker-compose`

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14, React 18, Tailwind CSS, Zustand |
| Backend | FastAPI (Python 3.12), SQLAlchemy 2.0, Pydantic v2 |
| Vector DB | ChromaDB |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| LLM Gateway | LiteLLM (OpenAI / Anthropic / Google) |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) |
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
# Edit .env — at minimum set OPENAI_API_KEY

# 3. Start everything
docker-compose up -d

# 4. Open the app
# Frontend: http://localhost:3000
# Backend API docs: http://localhost:8000/docs
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

> **Note:** You'll need PostgreSQL, Redis, and ChromaDB running locally. You can start only the infrastructure services with Docker:
> ```bash
> docker-compose up -d postgres redis chromadb
> ```

## Project Structure

```
rag-chatbot/
├── backend/
│   ├── app/
│   │   ├── api/routes/          # Auth, Chat, Documents, Admin endpoints
│   │   ├── core/                # Config, DB, Redis, Security, Logging
│   │   ├── ingestion/           # PDF/CSV/Web/GDocs/Notion extractors + chunking
│   │   ├── integrations/        # Slack, Google Sheets, Email
│   │   ├── models/              # SQLAlchemy ORM models
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
| POST | `/api/auth/login` | Sign in, get JWT token | No |
| GET | `/api/auth/me` | Current user info | Yes |
| GET | `/api/auth/org` | Current organization info | Yes |
| POST | `/api/chat` | Send message, get cited response | Yes |
| POST | `/api/chat/stream` | Streaming chat (SSE) | Yes |
| POST | `/api/chat/feedback` | Thumbs up/down on a message | Yes |
| GET | `/api/chat/conversations` | List conversation history | Yes |
| GET | `/api/chat/conversations/{id}` | Get conversation with messages | Yes |
| POST | `/api/documents/upload` | Upload PDF/CSV/TXT/DOCX/XLSX file | Admin |
| POST | `/api/documents/ingest-website` | Scrape + index a URL | Admin |
| POST | `/api/documents/ingest-gdoc` | Ingest a Google Doc by ID/URL | Admin |
| POST | `/api/documents/ingest-notion` | Ingest a Notion page by ID/URL | Admin |
| GET | `/api/documents` | List all documents | Yes |
| GET | `/api/documents/{id}` | Get single document details | Yes |
| DELETE | `/api/documents/{id}` | Delete document + vector chunks | Admin |
| POST | `/api/documents/{id}/reindex` | Re-process a document | Admin |
| GET | `/api/admin/analytics` | Dashboard analytics | Admin |
| PUT | `/api/admin/settings` | Update LLM provider/budget | Admin |
| GET | `/api/admin/users` | List organization users | Admin |
| PUT | `/api/admin/users/{id}/role` | Change user role | Admin |
| POST | `/api/admin/reset-token-usage` | Reset daily token counter | Admin |
| POST | `/api/integrations/slack/events` | Slack Events API webhook | Slack |

## Configuration

All settings are in `.env`. Key ones:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | *(required)* |
| `DEFAULT_LLM_PROVIDER` | `openai`, `anthropic`, or `google` | `openai` |
| `OPENAI_MODEL` | Default OpenAI model | `gpt-4o-mini` |
| `CHUNK_SIZE` | Token size per chunk | `512` |
| `CHUNK_OVERLAP` | Overlap between chunks | `64` |
| `SIMILARITY_THRESHOLD` | Min cosine score for retrieval | `0.72` |
| `RERANK_THRESHOLD` | Min cross-encoder score | `0.25` |
| `DAILY_TOKEN_BUDGET` | Max tokens/day per org | `500000` |
| `NOTION_API_TOKEN` | Notion integration token | *(optional)* |
| `SLACK_BOT_TOKEN` | Slack bot OAuth token | *(optional)* |

## Production Deployment Guide

### Required Environment Variables

These **must** be set before running in production:

```bash
# Security — generate random strings (e.g., openssl rand -hex 32)
SECRET_KEY=<random-64-char-string>
JWT_SECRET=<random-64-char-string>

# Database
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@<host>:5432/<dbname>

# Redis
REDIS_URL=redis://<host>:6379/0

# ChromaDB
CHROMA_HOST=<host>
CHROMA_PORT=8000

# LLM (at least one provider key)
OPENAI_API_KEY=sk-...

# App URLs
BACKEND_URL=https://api.yourdomain.com
FRONTEND_URL=https://yourdomain.com
```

### Deployment Steps

```bash
# 1. Clone and configure
git clone https://github.com/abdul-raheem-fast/rag-chatbot.git
cd rag-chatbot
cp .env.example .env
# Edit .env with production values

# 2. Start with Docker
docker-compose up -d

# 3. Run database migrations
docker-compose exec backend alembic upgrade head

# 4. Verify
curl http://localhost:8000/health
# Should return: {"status":"healthy","app":"RAG Chatbot","env":"production"}
```

### Frontend Environment

Set this in your frontend deployment (Vercel, Netlify, or Docker):

```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

### Production Checklist

- [ ] Set `APP_ENV=production` and `DEBUG=false`
- [ ] Generate unique `SECRET_KEY` and `JWT_SECRET`
- [ ] Set real `DATABASE_URL` (not localhost)
- [ ] Configure HTTPS/TLS termination (nginx or cloud LB)
- [ ] Set `DAILY_TOKEN_BUDGET` and `MONTHLY_TOKEN_BUDGET`
- [ ] Disable Swagger docs: `docs_url` becomes `None` when `DEBUG=false`
- [ ] Set up log aggregation (stdout → CloudWatch / Datadog / etc.)
- [ ] Back up PostgreSQL on schedule

## Security

> **WARNING:** Never commit your `.env` file or expose API keys. Only `.env.example` (with placeholder values) is tracked in git. If you fork this repo, ensure your `.env` is in `.gitignore` (it already is).

- **Authentication**: JWT tokens with configurable expiry (default 24h)
- **Authorization**: Role-based access — `admin`, `member`, `viewer`
- **Data isolation**: All queries are scoped to `org_id`; no cross-tenant data leakage
- **Rate limiting**: Configurable per-minute request limits via SlowAPI
- **Token budgets**: Daily and monthly caps prevent runaway LLM costs
- **Secrets**: All credentials loaded from environment variables, never hardcoded
- **CORS**: Restricted to configured frontend URL only

## Milestone Checklist

- [x] Project scaffolding + Docker Compose setup
- [x] PostgreSQL models + Alembic migration setup
- [x] JWT authentication + role-based access control
- [x] PDF ingestion + recursive chunking into ChromaDB
- [x] CSV ingestion (row-level chunking with column context)
- [x] TXT plain text ingestion
- [x] DOCX (Word) document ingestion with paragraph + table extraction
- [x] XLSX (Excel) ingestion with multi-sheet support
- [x] Website scraping + ingestion (trafilatura)
- [x] Google Docs ingestion (by doc ID or URL)
- [x] Notion page ingestion (by page ID or URL)
- [x] RAG engine (retrieve → rerank → prompt → LLM)
- [x] Streaming chat API with Server-Sent Events
- [x] Citation extraction and mapping
- [x] Next.js chat UI with real-time streaming
- [x] Citations side panel with snippets and scores
- [x] Admin dashboard (analytics, token usage)
- [x] Document management (upload, delete, reindex)
- [x] Settings page (LLM provider swap, token budgets, team roles)
- [x] Slack bot integration
- [x] Google Sheets Q&A logging
- [x] Email weekly digest
- [x] Production deployment guide
- [ ] HubSpot CRM integration
- [ ] Langfuse observability tracing
- [ ] Comprehensive evaluation test suite

## License

MIT
