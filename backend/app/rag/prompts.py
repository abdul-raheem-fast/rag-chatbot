"""Prompt templates for the RAG chatbot."""

SYSTEM_PROMPT = """You are a helpful assistant for {org_name}. Answer questions using ONLY the provided source documents. Follow these rules strictly:

1. Base every factual statement on the provided sources.
2. Cite sources using [1], [2], etc. corresponding to the numbered documents below.
3. If the sources don't contain enough information to answer, say:
   "I don't have enough information in the available documents to answer this question. You may want to contact your administrator for help."
4. Never fabricate information not present in the sources.
5. If a question is ambiguous, ask for clarification before answering.
6. Keep answers concise but complete. Use bullet points for lists.
7. When multiple sources agree, cite all of them.
8. Always respond in the same language the user writes in."""

NO_SOURCES_RESPONSE = (
    "I don't have enough information in the available documents to answer this question. "
    "You may want to contact your administrator for help."
)

OFF_TOPIC_RESPONSE = (
    "I'm configured to answer questions about your organization's documents. "
    "I can't help with that request."
)


def format_chunks_for_prompt(chunks: list[dict]) -> str:
    """Format retrieved chunks into numbered source blocks for the prompt."""
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        meta = chunk.get("metadata", {})
        doc_name = meta.get("doc_name", "Unknown Document")
        page = meta.get("page_number")
        source_label = f"({doc_name}"
        if page:
            source_label += f", Page {page}"
        source_label += ")"

        parts.append(f'[{i}] {source_label}\n"{chunk["text"]}"')
    return "\n\n".join(parts)


def build_rag_messages(
    user_query: str,
    chunks: list[dict],
    org_name: str = "your organization",
    conversation_history: list[dict] | None = None,
) -> list[dict]:
    """Build the full message list for the LLM call."""
    system_content = SYSTEM_PROMPT.format(org_name=org_name)
    if chunks:
        sources_text = format_chunks_for_prompt(chunks)
        system_content += f"\n\nSources:\n{sources_text}"

    messages = [{"role": "system", "content": system_content}]

    if conversation_history:
        for msg in conversation_history[-6:]:  # last 3 turns (6 messages)
            messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": user_query})
    return messages
