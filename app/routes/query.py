from fastapi import APIRouter, Request
from app.qachain import setup_qa_chain
from app.models import QueryResponse
#from app.services.rag import needs_clarification

router = APIRouter()

@router.post("/api/query", response_model=QueryResponse)
async def handle_query(request: Request):
    data = await request.json()
    question = data.get("question")
    result = ask_question(question)
    return {
        "short_answer": result.get("short_answer", ""),
        "detailed_answer": result.get("detailed_answer", ""),
        "sources": result.get("sources", [])
    }

def ask_question(question: str) -> dict:
    try:
        # clarification = needs_clarification(question)
        # if clarification:
        #     return {
        #         "short_answer": clarification,
        #         "detailed_answer": "",
        #         "sources": []
        #     }

        qa_chain, _ = setup_qa_chain(question)
        if qa_chain is None:
            return {
                "short_answer": "❌ No relevant documents found.",
                "detailed_answer": "",
                "sources": []
            }

        response = qa_chain(question)
        raw_answer = str(response["result"].content)

        short_answer, detailed_answer = "", ""
        if "##SHORT_ANSWER##" in raw_answer and "##DETAILED_ANSWER##" in raw_answer:
            try:
                parts = raw_answer.split("##DETAILED_ANSWER##")
                short_answer = parts[0].split("##SHORT_ANSWER##")[1].strip()
                detailed_answer = parts[1].strip()
            except Exception as parse_err:
                short_answer = "⚠️ Error parsing structured answer."
                detailed_answer = raw_answer.strip()
        else:
            short_answer = raw_answer.strip()

        sources = []
        for doc in response.get("source_documents", []):
            metadata = doc.metadata or {}
            excerpt = doc.page_content[:300].replace("\n", " ")
            
            sources.append({
                "filename": metadata.get("source", "Unknown file"),
                "page": str(metadata.get("page", "N/A")),
                "excerpt": excerpt,
                "law_name": metadata.get("law_name", ""),
                "lang": metadata.get("lang", ""),
                "article_number": metadata.get("article_number", ""),
                "clause": metadata.get("clause", ""),
                "version": metadata.get("version", ""),
                "source_url": metadata.get("source_url", "")
            })

            

        return {
            "short_answer": short_answer,
            "detailed_answer": detailed_answer,
            "sources": sources
        }

    except Exception as e:
        import logging
        logging.exception("❌ Error in ask_question:")
        return {
            "short_answer": "❌ An error occurred while answering your question.",
            "detailed_answer": "",
            "sources": []
        }
