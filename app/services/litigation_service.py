# === File: app/services/litigation_service.py ===

import os
import fitz
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

TEMPLATE = """You are a senior UAE litigation analyst. Analyze the case based on the information provided by the user and legal context.

Case Title: {title}
Case Type: {type}
Jurisdiction: {jurisdiction}
Parties: {parties}
Claim Summary:

\"\"\"
{claim}
\"\"\"

Desired Outcome: {outcome}
Representation: {representation}

Context from similar UAE rulings and statutes:

\"\"\"
{context}
\"\"\"


Provide a detailed litigation analysis with the following structure:
1. 🧩 Key Issues Identified
2. 🛡️ Positions and Arguments (Factual, Procedural, Legal)
3. 📚 Relevant Laws and Case Precedents
4. ⚖️ Strengths & Weaknesses
5. 📝 Legal Risk Assessment (e.g., High, Medium, Low)
6. 📈 Strategic Recommendations (if any)
7. 🔗 Source References and Citations
"""

PROMPT = PromptTemplate(
    template=TEMPLATE,
    input_variables=["title", "type", "jurisdiction", "parties", "claim", "outcome", "representation", "context"]
)

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return "\n".join([page.get_text() for page in doc]).strip()
    except Exception as e:
        import logging
        logging.warning(f"[⚠️] Failed to extract PDF text: {e}")
        return ""

async def analyze_case(
    case_title,
    case_type,
    jurisdiction,
    party_roles,
    claim_description,
    evidence_summary,
    desired_outcome,
    representation,
    language,
    file
):
    base_text = f"{claim_description}\n\nEvidence:\n{evidence_summary}"

    if file and file.filename:
        file_bytes = await file.read()
        file_text = extract_text_from_pdf(file_bytes)
        base_text += f"\n\n{file_text}"

    lang = detect_language(base_text[:1000])
    results = search_qdrant(base_text, lang=lang, k=12)
    context = compress_chunks_if_needed(results)

    llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)
    chain = PROMPT | llm

    try:
        result = chain.invoke({
            "title": case_title,
            "type": case_type,
            "jurisdiction": jurisdiction,
            "parties": party_roles,
            "claim": base_text[:8000],
            "outcome": desired_outcome,
            "representation": representation,
            "context": context
        })
        return str(result.content).strip()
    except Exception as e:
        import logging
        logging.exception("Litigation analysis failed")
        return "❌ An error occurred while analyzing the case."