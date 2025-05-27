# === File: app/services/guidance_service.py ===

import os
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


TEMPLATE = """
You are a UAE legal strategy advisor. Given the user's situation and legal context, generate **accurate and practical guidance** according to UAE laws.

👤 User Role: {user_role}  
🚨 Urgency: {urgency}  
📌 Legal Issue: {legal_issue}  
📝 Additional Info: {extra}  

📚 Legal Context:
\"\"\"{context}\"\"\"

Respond in this exact structure:

### 1. 🧾 Overview
- Briefly explain the issue and its UAE legal relevance.

### 2. ✅ Step-by-Step Legal Action Plan
- Include legal steps like:
  - Serve notice  
  - File complaint with MOHRE / Notary / Court  
  - Attempt arbitration or mediation  
  - Initiate legal proceedings

### 3. 📑 Required Documents
- Emirates ID  
- Contract copies  
- Supporting evidence

### 4. 🏛️ Authorities Involved
- Mention specific UAE bodies (MOHRE, Notary Public, Civil Courts, DIFC, etc.)

### 5. 💡 Legal Tips
- Share actionable tips based on UAE practice

### 6. ⏳ Estimated Timeline & Cost
- Estimate processing time and typical legal fees

### 7. ⚠️ Common Mistakes to Avoid
- E.g., missing deadlines, not registering tenancy contract, etc.

### 8. 🔗 UAE Law References
- For each cited article, include:
  - Law Name, Article #, Clause #, Version, Hyperlink

Always tailor your response to the user's role and legal context. Respond in formal and clear language.
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

    if not legal_issue or len(legal_issue) < 5:
        return "❌ Please specify a clear legal issue to proceed (e.g., 'termination of tenancy agreement', 'salary dispute', etc.)"

    full_query = f"Legal Issue: {legal_issue}. Role: {user_role}. Urgency: {urgency}. Extra: {extra}"
    lang = detect_language(full_query)
    docs = search_qdrant(full_query, lang=lang, k=10)
    context = compress_chunks_if_needed(docs)

    citations = []
    for doc in docs:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(
                f"{meta.get('law_name')} | Article {meta.get('article_number')} | Clause {meta.get('clause')} | Version: {meta.get('version')} | [Link]({meta.get('source_url')})"
            )

    context += "\n\n🔗 Cited UAE Laws:\n" + "\n".join(citations)

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