# === File: app/services/document_service.py ===

import os
import re
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


doc_analysis_template = """
You are a UAE senior legal reviewer. Analyze the legal document provided, classify its clauses, and check compliance against UAE law using the context below.

📄 Document Type: {doc_type}  
📍 Jurisdiction: {jurisdiction}

---
📘 Document Content:
\"\"\"{text}\"\"\"

📚 UAE Legal Context:
\"\"\"{context}\"\"\"

---

Respond in the following structured format:

### 1. 📘 Executive Summary
- Summarize the document in plain language (purpose, type, scope)

### 2. 🔍 Clause Classification Table
| Clause | Type | Description | Risk Level |
|--------|------|-------------|------------|
| ...    | Obligation / Penalty / Deadline / Other | ... | High / Medium / Low |

### 3. ⚠️ Risk Factors
- List risky or ambiguous clauses and assign severity level

### 4. ✅ Compliance Assessment
- Compare document terms with UAE law
- Highlight any misalignment or required corrections

### 5. 📅 Obligations & Deadlines Summary
- Who is obligated, what action, and by when (if found)

### 6. 🛠️ Suggested Improvements
- Suggest clearer language, add missing clauses, reduce ambiguity

### 7. 🔗 Legal References
- For each citation: include
  - Law Name, Article #, Clause #, Version, Hyperlink

Respond formally and accurately. If content is unreadable, return: “Document is not analyzable due to poor text quality or empty input.”
"""


ANALYSIS_PROMPT = PromptTemplate(
    template=doc_analysis_template,
    input_variables=["doc_type", "jurisdiction", "text", "context"]
)

async def analyze_legal_document(text: str, doc_type: str, jurisdiction: str):
    if not text.strip():
        return "❌ No content found in the uploaded document."

    lang = detect_language(text[:1000])
    results = search_qdrant(text[:1500], lang=lang, k=10)
    context = compress_chunks_if_needed(results)
    citations = []
    for doc in results:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(
                f"{meta.get('law_name')} | Article {meta.get('article_number')} | Clause {meta.get('clause')} | Version: {meta.get('version')} | [Link]({meta.get('source_url')})"
            )

    context += "\n\n🔗 Cited UAE Laws:\n" + "\n".join(citations)


    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    chain = ANALYSIS_PROMPT | llm

    try:
        result = chain.invoke({
            "doc_type": doc_type,
            "jurisdiction": jurisdiction,
            "text": text[:8000],
            "context": context
        })
        #return str(result.content).strip()
        return parse_analysis_output(str(result.content).strip())
    except Exception as e:
        import logging
        logging.exception("❌ Document analysis failed")
        return "❌ An error occurred during document analysis."

def parse_analysis_output(text: str) -> dict:
    
    sections = {
        "summary": "",
        "clauses": "",
        "risks": [],
        "compliance": "",
        "obligations": "",
        "references": ""
    }

    # Match headings using numbered emoji pattern
    parts = re.split(r"###\s+\d+\.\s+(?:📘|🔍|⚠️|✅|📅|🛠️|🔗)\s*", text)
    if len(parts) < 6:
        return {"raw": text}

    # Clean and assign
    sections["summary"] = parts[1].strip()
    sections["clauses"] = parts[2].strip()
    risk_text = parts[3].strip()
    sections["compliance"] = parts[4].strip()
    suggestions = parts[5].strip()
    references = parts[6].strip() if len(parts) > 6 else ""

    # Risk extraction (simple heuristic)
    risks = []
    for line in risk_text.split("\n"):
        if line.strip():
            level = "Medium"
            if "high" in line.lower():
                level = "High"
            elif "low" in line.lower():
                level = "Low"
            risks.append({"description": line.strip(), "level": level})
    sections["risks"] = risks
    sections["references"] = references + "\n\n" + suggestions

    return sections