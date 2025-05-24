
from langchain.chains import RetrievalQA
from langchain.schema import Document as LCDocument
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_openai import ChatOpenAI
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed

template = """You are a UAE legal assistant. Use the context below to answer the user's legal question.

Return answer in this format:
- Short Answer: (3-5 sentence summary)
- Detailed Answer:
Use <strong>bold headings</strong>, legal references, bullet points, and end with a Conclusion.

Context:
{context}

Question:
{question}

Response:
- Short Answer:
- Detailed Answer:"""

PROMPT = PromptTemplate(template=template, input_variables=["context", "question"])

def setup_qa_chain(query: str, temp: float = 0.3, k: int = 10):
    lang = detect_language(query)
    docs = search_qdrant(query, lang, k=k)
    if not docs:
        return None, None

    context = compress_chunks_if_needed(docs)

    llm = ChatOpenAI(temperature=temp, model_name="gpt-4")

    # New Runnable-style chain
    chain = PROMPT | llm

    def run_chain(question_text):
        inputs = {"context": context, "question": question_text}
        result = chain.invoke(inputs)  # Replaces `.run()`
        return {
            "result": result,
            "source_documents": docs
        }

    return run_chain, docs


def run_case_analysis_chain(structured_input, language="en"):
    prompt = f"""
You are a litigation assistant. Analyze the following legal case:

Title: {structured_input['title']}
Type: {structured_input['type']}
Jurisdiction: {structured_input['jurisdiction']}
Parties: {structured_input['parties']}
Claim: {structured_input['claim']}
Desired Outcome: {structured_input['outcome']}
Representation: {structured_input['representation']}

Respond in structured format:
- Case Summary
- Case Strength (Low/Medium/High)
- Arguments For
- Arguments Against
- Key Risk Factors
- Estimated Duration & Cost
- Referenced UAE Laws
- Final Recommendation
"""

    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    completion = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )

    return completion.choices[0].message.content

def call_llm_chain(prompt: str) -> dict:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.chat.completions.create(
        model=os.getenv("GPT_MODEL", "gpt-4"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    content = response.choices[0].message.content
    return {
        "summary": content,
        "clauses": "",
        "risks": [],
        "compliance": "",
        "references": ""
    }


