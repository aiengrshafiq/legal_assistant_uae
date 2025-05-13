from openai import OpenAI
import os

from dotenv import load_dotenv
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

from app.qachain import setup_qa_chain  # your provided logic
import logging

def ask_question(question: str) -> dict:
    try:
        qa_chain, _ = setup_qa_chain(query=question, temp=0.0, k=10)
        if qa_chain is None:
            return {
                "answer": "❌ No relevant documents found. Please upload legal files or check your query.",
                "sources": []
            }

        response = qa_chain(question)
        answer = response["result"]
        sources = []

        for doc in response.get("source_documents", []):
            metadata = doc.metadata or {}
            filename = metadata.get("source", "Unknown file")
            page = metadata.get("page", "N/A")
            excerpt = doc.page_content.strip().replace("\n", " ")[:300]
            sources.append({
                "filename": filename,
                "page": page,
                "excerpt": excerpt
            })

        return {"answer": answer, "sources": sources}

    except Exception as e:
        logging.exception("Error during question answering:")
        return {"answer": "❌ An error occurred while answering your question.", "sources": []}
