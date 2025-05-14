import os
from app import utils
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")

def setup_qa_chain(query, temp=0.0, k=10):
    query_lang = utils.detect_language(query)
    docs = utils.direct_qdrant_search(query, lang=query_lang, k=k)

    if not docs:
        return None, None

    context = "\n\n".join([doc.page_content for doc in docs])

    prompt = f"""You are a UAE legal assistant. Use the context below to answer the user's legal question.

        Always return your answer in this exact format:
        - Short Answer: (3-5 sentence summary)

        - Detailed Answer:
        Structure the detailed answer as follows:
        • Use <strong>bold headings</strong> for major sections (e.g., "Key Provisions", "Criminal Offenses", "Conclusion").
        • Highlight legal references like "Federal Decree-Law No. (51) of 2023" and "Article (272)" clearly.
        • Use numbered or bulleted lists where applicable.
        • Make it scannable and aligned for legal professionals and business readers.
        • End with a short Conclusion if applicable.

        If the answer is not present, reply:
        "Sorry, the information you're asking for isn't available in the provided documents."

        Context:
        {context}

        Question:
        {query}

        Response:
        - Short Answer:
        - Detailed Answer:"""


    def manual_qa_chain(query):
        try:
            response = client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=temp
            )
            answer = response.choices[0].message.content
            return {"result": answer, "source_documents": docs}
        except Exception as e:
            print(f"[OpenAI ERROR] {e}")
            raise

    return manual_qa_chain, docs
