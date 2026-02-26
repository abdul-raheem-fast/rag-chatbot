import hashlib
import fitz  # pymupdf
import pandas as pd
import trafilatura
import httpx
from pathlib import Path
from app.core.logging import get_logger

logger = get_logger(__name__)


def compute_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def extract_pdf(file_path: str) -> list[dict]:
    """Extract text from PDF, one entry per page."""
    pages = []
    doc = fitz.open(file_path)
    for page_num, page in enumerate(doc, start=1):
        text = page.get_text("text").strip()
        if text:
            pages.append({
                "text": text,
                "metadata": {"page_number": page_num},
            })
    doc.close()
    if not pages:
        logger.warning("PDF extraction returned no text", file_path=file_path)
    return pages


def extract_csv(file_path: str) -> list[dict]:
    """Each row becomes a text entry with column headers as context."""
    df = pd.read_csv(file_path)
    entries = []
    columns = list(df.columns)
    for idx, row in df.iterrows():
        parts = [f"{col}: {row[col]}" for col in columns if pd.notna(row[col])]
        text = " | ".join(parts)
        if text.strip():
            entries.append({
                "text": text,
                "metadata": {"row_number": int(idx) + 1},
            })
    return entries


def extract_website(url: str) -> list[dict]:
    """Scrape a URL and extract clean text."""
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Could not fetch URL: {url}")
    text = trafilatura.extract(downloaded, include_links=False, include_tables=True)
    if not text:
        raise ValueError(f"Could not extract text from: {url}")
    return [{"text": text, "metadata": {"source_url": url}}]


async def extract_gdoc(doc_id: str, credentials_json: str) -> list[dict]:
    """Fetch Google Doc content via export URL.
    Requires a service account or OAuth token. Simplified version uses export link."""
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
    async with httpx.AsyncClient() as client:
        resp = await client.get(export_url)
        if resp.status_code != 200:
            raise ValueError(f"Failed to fetch Google Doc {doc_id}: {resp.status_code}")
        text = resp.text.strip()
    return [{"text": text, "metadata": {"gdoc_id": doc_id}}]


async def extract_notion(page_id: str, api_token: str) -> list[dict]:
    """Fetch Notion page blocks and concatenate text.
    Uses the Notion API to get block children."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Notion-Version": "2022-06-28",
    }
    url = f"https://api.notion.com/v1/blocks/{page_id}/children?page_size=100"
    texts = []
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code != 200:
            raise ValueError(f"Notion API error: {resp.status_code}")
        data = resp.json()
        for block in data.get("results", []):
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            rich_texts = block_data.get("rich_text", [])
            for rt in rich_texts:
                plain = rt.get("plain_text", "")
                if plain.strip():
                    texts.append(plain)

    full_text = "\n".join(texts)
    if not full_text.strip():
        raise ValueError(f"No text found in Notion page {page_id}")
    return [{"text": full_text, "metadata": {"notion_page_id": page_id}}]
