# === File: app/services/summarizer.py ===

import os
import io
import fitz
import docx
import logging
from typing import List
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableMap

logger = logging.getLogger("summarizer")


TEMPLATE = """You are a professional UAE legal strategist. A user has submitted a legal document (PDF or DOCX). Use the contents of the case and supporting UAE legal context to produce a comprehensive summary.

🎯 Objective:
- Summarize all key facts and arguments
- Annotate legal issues clearly
- Provide legal grounding with citations
- Recommend next legal steps

📄 Document Content:
\"\"\"{document}\"\"\"

📚 UAE Legal Context:
\"\"\"{context}\"\"\"

📘 Summary Output:

## 🧾 Case Summary

### 1. Facts:
- List core facts from the document (dates, parties, contract terms)

### 2. Legal Issues:
- Identify and explain the key legal disputes

### 3. Legal Citations:
- Mention UAE laws, articles, clauses used in context
- Format:
  - Law Name: ___
  - Article #: ___
  - Clause: ___
  - Version: ___
  - URL: ___

### 4. Arguments:
- User's position
- Opponent's position (if present)

### 5. Analysis & Reasoning:
- Interpret legal grounding for or against the user
- Show how retrieved UAE laws apply

### 6. 📌 Next Legal Steps:
- Recommend Notice, Arbitration, or Court
- Required Documents
- Time & Cost Estimate

### 7. Final Legal Opinion:
- Conclude with professional recommendation

Respond formally and clearly. If laws are missing or not applicable, state: “I cannot advise without legal grounding from UAE law.”
"""


PROMPT = PromptTemplate(
    template=TEMPLATE,
    input_variables=["document", "context"]
)

def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    if filename.endswith(".pdf"):
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            return "\n".join([page.get_text() for page in doc]).strip()
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return ""
    elif filename.endswith(".docx"):
        doc = docx.Document(io.BytesIO(file_bytes))
        return "\n".join([para.text for para in doc.paragraphs])
    elif filename.endswith(".txt"):
        return file_bytes.decode("utf-8")
    else:
        raise ValueError("Unsupported file format. Please upload PDF, DOCX, or TXT.")

def summarize_case(filename: str, file_bytes: bytes) -> str:
    raw_text = extract_text_from_file(filename, file_bytes)
    if not raw_text.strip():
        return "❌ No readable text found in the uploaded file. Ensure it's not scanned or image-only."

    lang = detect_language(raw_text[:1000])
    docs = search_qdrant(raw_text[:1500], lang=lang, k=10)

    if not docs:
        return "❌ No relevant UAE legal context was found in the knowledge base."

    citations = []
    for doc in docs:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(f"- {meta.get('law_name')} | Article: {meta.get('article_number')} | Clause: {meta.get('clause')} | Version: {meta.get('version')} | URL: {meta.get('source_url')}")


    
    context = compress_chunks_if_needed(docs) + "\n\n📌 Extracted Legal Citations:\n" + "\n".join(citations)

    llm = ChatOpenAI(temperature=0.3, model_name="gpt-4")
    chain = PROMPT | llm

    try:
        result = chain.invoke({"document": raw_text[:8000], "context": context})
        return str(result.content).strip()
    except Exception as e:
        logger.exception("❌ Failed to summarize legal case")
        return "❌ An error occurred while summarizing the case."