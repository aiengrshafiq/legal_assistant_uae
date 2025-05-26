# === File: app/services/document_service.py ===

import os
import re
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

doc_analysis_template = """You are a senior UAE legal analyst. Analyze the uploaded document based on content and UAE legal standards.

Document Type: {doc_type}
Jurisdiction: {jurisdiction}

---
Document Content:
\"\"\"
{text}
\"\"\"

Context from UAE law and similar documents:
\"\"\"
{context}
\"\"\"

Provide the following analysis:
1. 📘 Executive Summary
2. 📌 Clause-by-Clause Breakdown
3. ⚠️ Risk Factors (highlight ambiguous language, red flags, missing clauses)
4. ✅ Compliance Assessment (alignment with UAE laws)
5. 🛠️ Suggested Improvements
6. 🔗 References (law citations or document chunks)
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
        "references": ""
    }

    # Match headings using numbered emoji pattern
    parts = re.split(r"\n\d+\.\s+📘|📌|⚠️|✅|🛠️|🔗", text)
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