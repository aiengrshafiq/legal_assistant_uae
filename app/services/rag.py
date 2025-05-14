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
                "short_answer": "❌ No relevant documents found.",
                "detailed_answer": "",
                "sources": []
            }

        response = qa_chain(question)
        raw_answer = response["result"]

        # Split into short and detailed answer
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
            filename = metadata.get("source", "Unknown file")
            page = metadata.get("page", "N/A")
            excerpt = doc.page_content.strip().replace("\n", " ")[:300]
            sources.append({
                "filename": filename,
                "page": str(page),  # ✅ This line fixes the validation error
                "excerpt": excerpt
            })

        return {
            "short_answer": short_answer,
            "detailed_answer": detailed_answer,
            "sources": sources
        }

    except Exception as e:
        logging.exception("Error during question answering:")
        return {
            "short_answer": "❌ An error occurred while answering your question.",
            "detailed_answer": "",
            "sources": []
        }
