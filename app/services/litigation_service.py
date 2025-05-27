# === File: app/services/litigation_service.py ===

import os
import fitz
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI


TEMPLATE = """
You are a senior UAE litigation strategist. Analyze this legal case using UAE law and precedents.

Use the context to cite laws (law name, article, clause, version, URL). Follow this response format:

📌 **Case Title**: {title}  
📍 **Jurisdiction**: {jurisdiction}  
📁 **Case Type**: {type}  
🧑‍⚖️ **Parties**: {parties}  
🧾 **Claim Summary**:
\"\"\"{claim}\"\"\"

🎯 **Desired Outcome**: {outcome}  
📣 **Representation Status**: {representation}

📚 **Relevant UAE Legal Context**:
\"\"\"{context}\"\"\"

---

### 1. 🧩 Key Issues Identified
- List the core legal questions or claims under dispute.

### 2. 🛡️ Positions and Arguments
- **Factual**: Describe facts supporting each side.
- **Procedural**: Identify filing issues, admissibility, timelines.
- **Legal**: Reference UAE law supporting or weakening each claim.

### 3. 📚 Applicable UAE Laws and Precedents
- Law Name: ___  
- Article: ___  
- Clause: ___  
- Version: ___  
- Source URL: ___

### 4. ⚖️ Strengths vs Weaknesses
| Factor               | Strengths (✓)                         | Weaknesses (⚠️)                      |
|----------------------|----------------------------------------|--------------------------------------|
| Legal Merits         |                                        |                                      |
| Documentation        |                                        |                                      |
| Jurisdiction Clarity |                                        |                                      |
| Procedural Validity  |                                        |                                      |

### 5. 🔥 Legal Risk Heatmap
- Risk Level: High / Medium / Low
- Key risks and risk drivers (e.g., lack of proof, weak law support)

### 6. 📈 Litigation Strategy Recommendation
- Suggested actions: Mediation → Arbitration → Court  
- Timeline estimate  
- Cost & effort estimate  
- Probability of success (if clear)

### 7. 🔗 UAE Law Citations
- Include structured references:
  - Law Name, Article, Clause, Version, Hyperlinked Source (if available)

Respond formally and precisely. If context is missing, say: "Unable to analyze due to insufficient UAE law data."
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

    if not claim_description.strip():
        return "❌ Claim description is required for litigation analysis."

    if not context.strip():
        return "❌ Insufficient UAE legal context found for proper litigation analysis. Please revise input or upload stronger case file."


    citations = []
    for doc in results:
        meta = doc.metadata or {}
        if meta.get("law_name") and meta.get("article_number"):
            citations.append(
                f"{meta.get('law_name')} | Article {meta.get('article_number')} | Clause {meta.get('clause')} | Version: {meta.get('version')} | [Link]({meta.get('source_url')})"
            )

    context += "\n\n🔗 Cited Laws:\n" + "\n".join(citations)

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