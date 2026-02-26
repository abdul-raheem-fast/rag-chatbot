"""
Slack integration: receive questions via Slack, respond with cited answers.
Uses Slack Events API with bolt-style handling.
"""
import json
import hashlib
import hmac
import time
from fastapi import APIRouter, Request, HTTPException
from app.core.config import get_settings
from app.rag.vectorstore import VectorStore
from app.rag.reranker import rerank_chunks
from app.rag.prompts import build_rag_messages, NO_SOURCES_RESPONSE
from app.rag.llm_gateway import llm_completion
from app.core.logging import get_logger

try:
    from slack_sdk.web.async_client import AsyncWebClient
except ImportError:
    AsyncWebClient = None

settings = get_settings()
logger = get_logger(__name__)
router = APIRouter(prefix="/integrations/slack", tags=["Slack"])


def _verify_slack_signature(body: bytes, timestamp: str, signature: str) -> bool:
    if not settings.slack_signing_secret:
        return False
    basestring = f"v0:{timestamp}:{body.decode('utf-8')}"
    computed = "v0=" + hmac.new(
        settings.slack_signing_secret.encode(),
        basestring.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(computed, signature)


@router.post("/events")
async def slack_events(request: Request):
    """Handle Slack Events API webhook."""
    body = await request.body()
    data = json.loads(body)

    # URL verification challenge
    if data.get("type") == "url_verification":
        return {"challenge": data["challenge"]}

    # Verify signature
    timestamp = request.headers.get("X-Slack-Request-Timestamp", "")
    signature = request.headers.get("X-Slack-Signature", "")
    if settings.slack_signing_secret and not _verify_slack_signature(body, timestamp, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")

    event = data.get("event", {})
    if event.get("type") == "app_mention" or (
        event.get("type") == "message" and event.get("channel_type") == "im"
    ):
        await _handle_message(event)

    return {"ok": True}


async def _handle_message(event: dict):
    """Process a Slack message and reply with RAG answer."""
    if not settings.slack_bot_token or not AsyncWebClient:
        logger.warning("Slack bot token not configured or slack_sdk not installed")
        return

    client = AsyncWebClient(token=settings.slack_bot_token)
    channel = event["channel"]
    thread_ts = event.get("thread_ts", event.get("ts"))
    user_query = event.get("text", "").strip()

    # Remove bot mention from query
    user_query = " ".join(
        word for word in user_query.split() if not word.startswith("<@")
    ).strip()

    if not user_query:
        return

    try:
        # Simplified RAG call (no org scoping for Slack — uses default org)
        vs = VectorStore()
        raw_chunks = vs.search(user_query, org_id="", top_k=settings.retrieval_top_k)
        chunks = rerank_chunks(user_query, raw_chunks, top_k=settings.rerank_top_k) if raw_chunks else []

        if not chunks:
            answer = NO_SOURCES_RESPONSE
        else:
            messages = build_rag_messages(user_query, chunks, settings.app_name)
            result = await llm_completion(messages)
            answer = result["content"]

        await client.chat_postMessage(channel=channel, thread_ts=thread_ts, text=answer)

    except Exception as e:
        logger.error("Slack message handling failed", error=str(e))
        await client.chat_postMessage(
            channel=channel,
            thread_ts=thread_ts,
            text="Sorry, I encountered an error processing your question.",
        )
