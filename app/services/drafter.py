# === File: app/services/drafter.py ===

import os
import io
import fitz
import logging
from typing import Optional
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

logger = logging.getLogger("drafter")


TEMPLATE = """You are a senior UAE legal draftsman. Based on the user's input and UAE legal context, generate a professional {draft_type} in {language}.

📌 Requirements:
- Use UAE law excerpts from context where relevant.
- Cite law name, article number, clause, version.
- Follow proper legal format (petition, notice, complaint, etc).
- Write in formal legal tone.

📩 Recipient: {recipient}
☎️ Contact: {contact}
📝 Special Instructions: {instructions}

📄 Case Description or Uploaded Text:
\"\"\"{user_content}\"\"\"

📚 UAE Legal Context:
\"\"\"{context}\"\"\"

📑 Format:
{format_section}

✍️ Generate the full draft below:
"""



DRAFT_PROMPT = PromptTemplate(
    template=TEMPLATE,
    input_variables=[
        "draft_type", "language", "recipient", "contact",
        "instructions", "user_content", "context", "format_section"
    ]
)

def extract_text_from_content(content: bytes) -> str:
    try:
        doc = fitz.open(stream=content, filetype="pdf")
        return "\n".join([page.get_text() for page in doc]).strip()
    except Exception:
        return content.decode(errors="ignore")

def generate_legal_draft(
    file_bytes: Optional[bytes],
    description: Optional[str],
    draft_type: str,
    language: str,
    recipient: str,
    contact: str,
    instructions: str
) -> str:

    user_content = ""
    if file_bytes:
        user_content = extract_text_from_content(file_bytes)
    if description:
        user_content += "\n" + description.strip()

    if not user_content.strip():
        return "❌ No valid content provided. Please upload a readable file or enter case description."

    lang = detect_language(user_content[:1000])
    docs = search_qdrant(user_content[:1500], lang=lang, k=10)
    context = compress_chunks_if_needed(docs)

    if not docs or not context.strip():
        return "❌ Cannot generate draft. No relevant UAE law was found. Please refine the description or upload a more detailed document."



    citations = []
    for doc in docs:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(
                f"{meta.get('law_name')} | Article {meta.get('article_number')} | Clause {meta.get('clause')} | Version: {meta.get('version')} | URL: {meta.get('source_url')}"
            )

    context += "\n\n📌 Legal References:\n" + "\n".join(citations)


    llm = ChatOpenAI(temperature=0.4, model_name="gpt-4")

    format_section = get_draft_format_section(draft_type)

    chain = DRAFT_PROMPT | llm

    try:
        result = chain.invoke({
            "draft_type": draft_type,
            "language": language,
            "recipient": recipient,
            "contact": contact,
            "instructions": instructions,
            "user_content": user_content[:8000],
            "context": context,
            "format_section": format_section
        })
        
        return str(result.content).strip()
    except Exception as e:
        logger.exception("Draft generation failed")
        return "❌ An error occurred while generating the draft."

def generate_pdf_from_text(draft_text: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    styles = getSampleStyleSheet()
    story = []

    for para in draft_text.strip().split("\n\n"):
        paragraph = Paragraph(para.strip().replace("\n", "<br />"), styles["Normal"])
        story.append(paragraph)
        story.append(Spacer(1, 12))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def get_draft_format_section(draft_type: str) -> str:
    draft_type_lower = draft_type.lower()
    if draft_type_lower in ['petition', 'court complaint', 'family law petition']:
        return (
            "1. Introduction\n"
            "2. Statement of Facts\n"
            "3. Legal Basis (with citations)\n"
            "4. Prayer for Relief"
        )
    else:
        return (
            "- Date\n"
            "- Subject\n"
            "- Body (clear legal narrative)\n"
            "- Cited Law Provisions\n"
            "- Closing and Signature"
        )