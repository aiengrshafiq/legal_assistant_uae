# 📁 app/services/document_service.py
from app.qachain import call_llm_chain  # Use your existing LLM orchestration logic

async def analyze_legal_document(text: str, doc_type: str, jurisdiction: str):
    prompt = f"""
You are a legal AI assistant. Please analyze the legal document below and return the following:

1. 📘 Summary
2. 🔑 Key Clauses
3. ⚠️ Risks (describe and classify as Low, Medium, High)
4. 📜 Compliance Issues (if any)
5. 📚 Relevant UAE Laws or Articles

Document Type: {doc_type}
Jurisdiction: {jurisdiction}

Text:
{text[:4000]}  # Limit to avoid token overload
"""
    response = call_llm_chain(prompt)
    return response
