# File: app/services/research_service.py
import fitz  # PyMuPDF
from typing import Tuple, List
from app.utils import extract_text, detect_language, direct_qdrant_search
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")

async def process_legal_research(
    topic: str,
    jurisdiction: str,
    domain: str,
    question: str,
    file,
    language: str
) -> Tuple[str, List[str], List[str], List[str]]:
    # Prepare base query
    base_query = f"Topic: {topic}. Jurisdiction: {jurisdiction}. Domain: {domain}. Question: {question}."

    # Include text from uploaded file if any
    if file:
        content = await file.read()
        text = extract_text(content)
        base_query += f"\nSupporting Document: {text[:2000]}"

    # Qdrant Search
    results = direct_qdrant_search(base_query,language)
    context_chunks = [r.page_content for r in results]
    joined_context = "\n\n".join(context_chunks[:10])

    # GPT Summary
    prompt = f"""
You are a UAE Legal Research Assistant.

Given the following legal topic, jurisdiction, and optional case document, summarize all relevant laws and legal actions in a structured way.

Format your response with the following sections:

1. 🔍 Summary (plain language summary)
2. 📑 Applicable Laws and Articles (bullet points with article numbers and short descriptions)
3. ⚖️ Related Precedents (known rulings or common applications)
4. 🧾 Required Legal Documentation (any specific doc requirements)
5. 🔗 References and Sources (if any)

Query:
{base_query}

Context:
{joined_context}
"""


    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    summary = response.choices[0].message.content
    articles = [r.page_content for r in results if 'article' in r.metadata.get("tags", [])]
    cases = [r.page_content for r in results if 'case' in r.metadata.get("tags", [])]
    sources = list({r.metadata.get("source", "Unknown") for r in results})

    return summary, articles, cases, sources
