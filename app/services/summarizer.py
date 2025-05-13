import fitz  # PyMuPDF
from app.utils import detect_language, direct_qdrant_search, extract_keywords
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")

def summarize_pdf(file_bytes: bytes) -> str:
    # 1. Extract PDF text
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    if not full_text.strip():
        return "❌ No readable text found in the uploaded PDF."

    # 2. Detect language of content
    lang = detect_language(full_text[:300])

    # 3. Retrieve relevant legal context from Qdrant
    search_query = extract_keywords(full_text[:1000])  # Extract short query for Qdrant
    docs = direct_qdrant_search(search_query, lang=lang, k=10)

    legal_context = "\n\n".join([doc.page_content for doc in docs if doc.page_content.strip()])
    if not legal_context:
        return "❌ No relevant legal context found in Qdrant."

    # 4. Generate summary using OpenAI
    prompt = f"""You are a UAE legal assistant. Given the legal case content and relevant UAE law context, write a concise and professional summary.

Legal Case Content:
{full_text[:3000]}

Relevant UAE Legal Context:
{legal_context[:3000]}

Summary:"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content
