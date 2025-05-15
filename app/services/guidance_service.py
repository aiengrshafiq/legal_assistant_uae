# ✅ services/guidance_service.py
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
GPT_MODEL = os.getenv("GPT_MODEL", "gpt-4")

def generate_guidance(data):
    legal_issue = data.get("legalIssue", "").strip()
    user_role = data.get("userRole", "")
    urgency = data.get("urgencyLevel", "")
    extra = data.get("optionalDetails", "")

    prompt = f"""
You are a highly experienced UAE legal advisor.
Provide a structured, detailed, and legally accurate step-by-step guide for the following legal matter:

Legal Issue: {legal_issue}
User Role: {user_role}
Urgency: {urgency}
Additional Info: {extra}

Structure your response as:
1. Overview
2. Step-by-Step Instructions
3. Required Documents
4. Authorities Involved
5. Legal Tips
6. Time & Cost Estimates
7. Common Mistakes to Avoid

The response should be easy to understand by a non-lawyer, yet accurate enough for legal professionals. Be concise, actionable, and UAE-specific.
"""

    response = client.chat.completions.create(
        model=GPT_MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful and professional legal advisor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()
