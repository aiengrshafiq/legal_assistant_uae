
# ================================
# 📦 app/qachain.py
# ================================
from langchain.chains import RetrievalQA
from langchain.schema import Document as LCDocument
import os
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableLambda, RunnableMap
from langchain_openai import ChatOpenAI
from app.services.rag import detect_language, search_qdrant, compress_chunks_if_needed, needs_clarification

from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
load_dotenv()

from langchain_community.vectorstores import Qdrant
from langchain_openai import OpenAIEmbeddings

from qdrant_client import QdrantClient
from langchain_community.vectorstores import Qdrant

from qdrant_client.models import Distance, VectorParams, PointStruct
import uuid

qdrant_url = f"https://{os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}"
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))



TEMPLATE = """
You are a UAE legal strategist. Analyze the user’s query and provide a step-by-step legal strategy using UAE laws. Do not speculate.

Only proceed if all necessary context is available (jurisdiction, agreement status, value, etc). If anything is missing, reply only with a clarifying question and do NOT generate legal advice.

Respond in this exact format:
##SHORT_ANSWER##
(3–5 sentence summary)

##DETAILED_ANSWER##
<strong>1. Legal Issue Summary:</strong>
[2-line summary]

<strong>2. Applicable UAE Laws:</strong>
- Law Name: [Name]
- Article #: [Article Number]
- Clause: [Clause Number]
- Version: [Version]
- Link: [source_url]

<strong>3. Legal Steps:</strong>
- Serve Notice
- Mediation
- File Civil Case

<strong>4. Required Documents:</strong>
- Emirates ID, Contract Copy

<strong>5. Recommended Dispute Resolution Route:</strong>
- If arbitration clause exists: Arbitration
- Else: Civil Court
- If value < 50K AED: Small Claims Tribunal

<strong>6. Timeline & Costs:</strong>
- [e.g., 1–3 months, AED 3,000]

<strong>7. Conclusion:</strong>
[Final legal opinion]

Context:
{context}

Question:
{question}

Response:
"""


PROMPT = PromptTemplate(template=TEMPLATE, input_variables=["context", "question"])

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


def store_case_chunks_to_qdrant(text, namespace):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    raw_chunks = splitter.split_text(text)

    # Clean and filter chunks
    cleaned_chunks = [chunk.strip() for chunk in raw_chunks if chunk.strip()]
    if not cleaned_chunks:
        print(f"[WARNING] No valid content to embed for case: {namespace}")
        return

    try:
        embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        vectors = [embeddings.embed_query(chunk) for chunk in cleaned_chunks]
    except Exception as e:
        print(f"[EMBEDDING ERROR] Failed to generate embeddings: {e}")
        return

    try:
        client = QdrantClient(
            url=f"https://{os.getenv('QDRANT_HOST')}:{os.getenv('QDRANT_PORT')}",
            api_key=os.getenv("QDRANT_API_KEY")
        )

        if not client.collection_exists(namespace):
            client.create_collection(
                collection_name=namespace,
                vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
            )

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={"page_content": chunk} 
            )
            for chunk, vector in zip(cleaned_chunks, vectors)
        ]

        client.upsert(collection_name=namespace, points=points)
        print(f"[✅] Stored {len(points)} chunks in Qdrant for case: {namespace}")

    except Exception as e:
        print(f"[QDRANT ERROR] Failed to store vectors for case '{namespace}': {e}")


def ask_question_in_case(case_id: str, question: str):
    llm = ChatOpenAI(temperature=0.3, model_name="gpt-4")
    client = QdrantClient(
        url=qdrant_url,
        api_key=os.getenv("QDRANT_API_KEY")
    )
    retriever = Qdrant(
        client=client,
        collection_name=case_id,
        embeddings=embeddings
    ).as_retriever()
    chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)
    return chain.invoke(question)