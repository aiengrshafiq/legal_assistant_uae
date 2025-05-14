import os
from openai import OpenAI
import fitz
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")


def generate_pdf_from_text(draft_text: str) -> bytes:
    buffer = BytesIO()
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



def generate_draft(content: bytes, draft_type: str, language: str, recipient: str, contact: str, instructions: str) -> str:
    try:
        # Try parsing PDF
        doc = fitz.open(stream=content, filetype="pdf")
        case_text = ""
        for page in doc:
            case_text += page.get_text()
        doc.close()
    except Exception:
        # If not a PDF or fails, fallback to decoding as plain text
        case_text = content.decode(errors="ignore")

    if not case_text.strip():
        return "❌ No readable text extracted from the uploaded file."

    prompt = f"""
You are a UAE legal draftsman. Based on the following case, generate a professional {draft_type} in {language}.

If the draft type is 'Court Complaint' or 'Petition', structure it into sections:
1. Introduction
2. Statement of Facts
3. Legal Basis
4. Prayer / Relief Requested

If it's a letter or notice, use standard legal letter format.

Recipient: {recipient or 'N/A'}
Contact: {contact or 'N/A'}
Special Instructions: {instructions or 'None'}

Case Details:
{case_text}

Return only the formatted draft.
"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    message = response.choices[0].message.content.strip()
    if not message:
        raise ValueError("GPT returned empty message")

    return message
