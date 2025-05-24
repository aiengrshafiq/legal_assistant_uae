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

TEMPLATE = """You are a professional UAE legal assistant. A legal case has been submitted for summary. 
Use the document content and retrieved legal context to summarize the case clearly, accurately, and completely.

Instructions:
- Provide both extractive and abstractive summaries.
- Annotate key segments like "Facts", "Arguments", "Judgment", and "Legal Issues".
- Reference original sections where possible.
- Use UAE legal terms and maintain clarity for non-lawyers.

---

📄 Case Content:
\"\"\"{document}\"\"\"

📚 Legal Context:
\"\"\"{context}\"\"\"

---

✍️ Write the structured summary with headings and annotations:
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

    context = compress_chunks_if_needed(docs)

    llm = ChatOpenAI(temperature=0.3, model_name="gpt-4")
    chain = PROMPT | llm

    try:
        result = chain.invoke({"document": raw_text[:8000], "context": context})
        return str(result.content).strip()
    except Exception as e:
        logger.exception("❌ Failed to summarize legal case")
        return "❌ An error occurred while summarizing the case."