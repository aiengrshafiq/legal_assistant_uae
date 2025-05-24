from fastapi import APIRouter, Request
from app.qachain import setup_qa_chain
from app.models import QueryResponse

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
        if "- Short Answer:" in raw_answer and "- Detailed Answer:" in raw_answer:
            parts = raw_answer.split("- Detailed Answer:")
            short_answer = parts[0].replace("- Short Answer:", "").strip()
            detailed_answer = parts[1].strip()
        else:
            short_answer = raw_answer.strip()

        sources = []
        for doc in response.get("source_documents", []):
            metadata = doc.metadata or {}
            excerpt = doc.page_content[:300].replace("\n", " ")
            sources.append({
                "filename": metadata.get("source", "Unknown file"),
                "page": str(metadata.get("page", "N/A")),
                "excerpt": excerpt
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
