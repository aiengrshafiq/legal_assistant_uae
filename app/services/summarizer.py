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
        return "❌ No readable text found in the uploaded PDF. Please make sure the file is not scanned or image-based."

    # 2. Detect language (fallback to English)
    try:
        lang = detect_language(full_text[:1000])
    except Exception:
        lang = "en"

    # 3. Retrieve relevant UAE legal context from Qdrant
    search_query = extract_keywords(full_text[:1500])  # Wider scope for better keyword match
    docs = direct_qdrant_search(search_query, lang=lang, k=10)

    legal_context = "\n\n".join([doc.page_content for doc in docs if doc.page_content.strip()])
    if not legal_context:
        return "❌ Sorry, no relevant legal information was found in the database for this case."

    # 4. Construct prompt as a UAE legal advisor
    prompt = f"""
You are a highly knowledgeable UAE legal advisor. A client has uploaded their legal case for professional analysis. Your task is to write a detailed, legally accurate, and easy-to-understand summary of their case.

🔹 Your response must:
- Be structured and clear (use sections if needed).
- Reflect applicable UAE laws or principles from the provided context.
- Offer a complete explanation so the client doesn’t need to consult any other lawyer.
- Be professional but understandable to a non-lawyer.

Below is the case content and relevant UAE legal context.

📄 Legal Case Content:
\"\"\"
{full_text[:3000]}
\"\"\"

📚 Relevant UAE Legal Context:
\"\"\"
{legal_context[:3000]}
\"\"\"

✍️ Please write the full professional legal summary below:
"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=1000  # Adjust as needed
    )

    return response.choices[0].message.content.strip()
