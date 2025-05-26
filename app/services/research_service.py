# === File: app/services/research_service.py ===

import os
import fitz
from typing import Tuple, List
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

TEMPLATE = (
    "You are a senior UAE legal research assistant.\n\n"
    "Given the user's query and legal context, produce a professional legal research report.\n\n"
    "Query:\n\"\"\"\n{query}\n\"\"\"\n\n"
    "Context:\n\"\"\"\n{context}\n\"\"\"\n\n"
    "Format the response in this structure:\n"
    "1. 🔍 Summary (plain language)\n"
    "2. 📑 Applicable Laws and Articles (with short explanation)\n"
    "3. ⚖️ Related Precedents (case laws or rulings)\n"
    "4. 🧾 Documentation Requirements (if any)\n"
    "5. 🔗 References and Citations (linked to original sources)\n"
)

PROMPT = PromptTemplate(template=TEMPLATE, input_variables=["query", "context"])

async def process_legal_research(
    topic: str,
    jurisdiction: str,
    domain: str,
    question: str,
    file,
    language: str
) -> Tuple[str, List[str], List[str], List[str]]:
    base_query = f"Topic: {topic}. Jurisdiction: {jurisdiction}. Domain: {domain or 'N/A'}. Question: {question or 'N/A'}."

    if file:
        content = await file.read()
        try:
            doc = fitz.open(stream=content, filetype="pdf")
            text = "\n".join([page.get_text() for page in doc])
            base_query += f"\nSupporting Document: {text[:2000]}"
        except Exception as e:
            base_query += "\n[Note: Failed to extract text from uploaded file]"

    lang = detect_language(base_query)
    results = search_qdrant(base_query, lang=lang, k=15)

    context = compress_chunks_if_needed(results)
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    chain = PROMPT | llm

    result = chain.invoke({"query": base_query, "context": context})
    summary = str(result.content).strip()

    articles = [r.page_content for r in results if 'article' in (r.metadata.get("tags") or [])]
    cases = [r.page_content for r in results if 'case' in (r.metadata.get("tags") or [])]
    sources = list({r.metadata.get("source", "Unknown") for r in results})

    return summary, articles, cases, sources
