# === File: app/services/research_service.py ===

import os
import fitz
from typing import Tuple, List
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI



TEMPLATE = """
You are a UAE senior legal research associate. Based on the user's legal query and UAE law context, generate a professional legal research report with strategic recommendations.

📌 Research Query:
\"\"\"{query}\"\"\"

📚 Legal Context:
\"\"\"{context}\"\"\"

📘 Output Format:

### 🔍 Executive Summary
- Plain-language summary of user's query and its legal significance.

### 📑 Relevant UAE Laws and Articles
- Mention law_name, article_number, clause, and explain their meaning.

### ⚖️ Related Legal Precedents
- Summarize related UAE court cases or rulings (if any).

### 🧾 Required Legal Documents
- List key documents needed to proceed legally.

### 🧭 Strategic Legal Path
- Court or arbitration?
- Estimated timeline (weeks/months)
- Cost estimate range (if possible)

### 📌 Final Legal Opinion
- Formal recommendation

### 🔗 Citations
- For each law/article: include law_name, article_number, clause, version, and URL if available.

If you cannot find UAE legal basis, say: "❌ Unable to provide advice without legal grounding from UAE law."
"""


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

    required = [topic, jurisdiction]
    if not all(required) or len(question.strip()) < 10:
        return (
            "❌ Please provide a more detailed legal question with proper context (e.g., dispute value, legal status, involved parties).",
            [], [], []
        )


    lang = detect_language(base_query)
    results = search_qdrant(base_query, lang=lang, k=15)
    context = compress_chunks_if_needed(results)

    citations = []
    for doc in results:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(
                f"{meta.get('law_name')} | Article {meta.get('article_number')} | Clause {meta.get('clause')} | Version: {meta.get('version')} | URL: {meta.get('source_url')}"
            )

    context += "\n\n📌 Legal References:\n" + "\n".join(citations)

    
    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    chain = PROMPT | llm

    result = chain.invoke({"query": base_query, "context": context})
    summary = str(result.content).strip()

    
    articles = [
        r.page_content for r in results
        if 'article' in (r.metadata.get("tags") or []) or r.metadata.get("law_name")
    ]
    cases = [
        r.page_content for r in results
        if 'case' in (r.metadata.get("tags") or []) or "judgment" in r.metadata.get("source", "").lower()
    ]
    sources = list({r.metadata.get("source", "Unknown") for r in results})

    return summary, articles, cases, sources
