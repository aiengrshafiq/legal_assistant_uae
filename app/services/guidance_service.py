# === File: app/services/guidance_service.py ===

import os
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

TEMPLATE = """You are a professional UAE legal advisor. Based on the user's query and context, generate clear, structured, and practical legal guidance.

Legal Issue: {legal_issue}
User Role: {user_role}
Urgency: {urgency}
Additional Info: {extra}

Use the context below to ensure the advice is accurate and UAE-specific.

Context:
\"\"\"
{context}
\"\"\"

Structure the response as follows:
1. 🧾 Overview
2. ✅ Step-by-Step Instructions
3. 📑 Required Documents
4. 🏛️ Authorities Involved
5. 💡 Legal Tips
6. ⏳ Time & Cost Estimates
7. ⚠️ Common Mistakes to Avoid
8. 🔗 Source References (hyperlinked if possible)
"""

PROMPT = PromptTemplate(
    template=TEMPLATE,
    input_variables=["legal_issue", "user_role", "urgency", "extra", "context"]
)

def generate_guidance(data: dict) -> str:
    legal_issue = data.get("legalIssue", "").strip()
    user_role = data.get("userRole", "").strip()
    urgency = data.get("urgencyLevel", "").strip()
    extra = data.get("optionalDetails", "").strip()

    if not legal_issue:
        return "❌ Legal issue is required."

    full_query = f"Legal Issue: {legal_issue}. Role: {user_role}. Urgency: {urgency}. Extra: {extra}"
    lang = detect_language(full_query)
    docs = search_qdrant(full_query, lang=lang, k=10)
    context = compress_chunks_if_needed(docs)

    llm = ChatOpenAI(temperature=0.3, model_name="gpt-4")
    chain = PROMPT | llm

    try:
        result = chain.invoke({
            "legal_issue": legal_issue,
            "user_role": user_role,
            "urgency": urgency,
            "extra": extra,
            "context": context
        })
        return str(result.content).strip()
    except Exception as e:
        import logging
        logging.exception("Guidance generation failed")
        return "❌ Failed to generate legal guidance due to a system error."